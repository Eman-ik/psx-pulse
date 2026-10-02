"""API endpoints for fundamental analysis screening funnel."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.api.data_status import freshness
from app.db.session import get_db
from app.db.models import Issuer, PriceOHLCV, Security, FinancialFact, RatioValue, RatioDefinition
from app.research_system.screening_funnel import (
    ScreeningFunnel, ScreeningResult, ScreeningSession
)
from app.universe import load_snapshot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/research/screening", tags=["research"])


def get_issuer_by_symbol(db: Session, symbol: str):
    """Get issuer by symbol."""
    security = db.query(Security).filter(Security.symbol == symbol).first()
    if not security:
        return None
    return security.issuer


def get_latest_fact(db: Session, issuer_id: int, line_item: str) -> float | None:
    """Get latest value for a financial fact line item."""
    row = db.execute(
        select(FinancialFact)
        .where(
            FinancialFact.issuer_id == issuer_id,
            FinancialFact.line_item == line_item,
            FinancialFact.superseded_by_id.is_(None),
        )
        .order_by(FinancialFact.period_end.desc())
        .limit(1)
    ).scalar()
    return float(row.value) if row else None


def get_latest_ratio(db: Session, issuer_id: int, ratio_key: str) -> float | None:
    """Get latest ratio value."""
    row = db.execute(
        select(RatioValue)
        .join(RatioDefinition, RatioDefinition.id == RatioValue.ratio_definition_id)
        .where(
            RatioValue.issuer_id == issuer_id,
            RatioDefinition.key == ratio_key,
        )
        .order_by(RatioValue.period_end.desc())
        .limit(1)
    ).scalar()
    return float(row.value) if row else None


def fetch_company_fundamentals(db: Session, symbol: str) -> dict:
    """Fetch all available financial data for a company using FinancialFact."""
    issuer = get_issuer_by_symbol(db, symbol)
    if not issuer:
        return {}

    # Fetch ratios (these are pre-computed)
    revenue_growth = get_latest_ratio(db, issuer.id, "revenue_growth_yoy")
    eps_growth = get_latest_ratio(db, issuer.id, "eps_growth_yoy")
    net_margin = get_latest_ratio(db, issuer.id, "net_profit_margin")
    roe = get_latest_ratio(db, issuer.id, "roe")
    roic = get_latest_ratio(db, issuer.id, "roic")
    de_ratio = get_latest_ratio(db, issuer.id, "debt_to_equity")
    current_ratio = get_latest_ratio(db, issuer.id, "current_ratio")

    # Fetch raw facts
    net_income = get_latest_fact(db, issuer.id, "profit_after_tax")
    ocf = get_latest_fact(db, issuer.id, "operating_cash_flow")

    # Get prior year D/E for trend
    two_year_facts = db.execute(
        select(FinancialFact)
        .where(
            FinancialFact.issuer_id == issuer.id,
            FinancialFact.line_item.in_(["total_debt", "total_equity"]),
            FinancialFact.superseded_by_id.is_(None),
        )
        .order_by(FinancialFact.period_end.desc())
        .limit(10)
    ).scalars().all()

    de_prior = None
    if len(two_year_facts) >= 4:
        # Group by period to find prior year
        periods = {}
        for fact in two_year_facts:
            if fact.period_end not in periods:
                periods[fact.period_end] = {}
            periods[fact.period_end][fact.line_item] = float(fact.value)

        sorted_periods = sorted(periods.keys(), reverse=True)
        if len(sorted_periods) >= 2:
            prior_period = periods[sorted_periods[1]]
            if "total_debt" in prior_period and "total_equity" in prior_period:
                equity = prior_period["total_equity"]
                if equity > 0:
                    de_prior = prior_period["total_debt"] / equity

    return {
        "revenue_growth_yoy": revenue_growth,
        "eps_growth_yoy": eps_growth,
        "net_profit_margin": net_margin,
        "roe": roe,
        "roic": roic,
        "operating_cash_flow": ocf,
        "net_income": net_income,
        "debt_to_equity": de_ratio,
        "debt_to_equity_prior_year": de_prior,
        "current_ratio": current_ratio,
        "cash_flow_quality": (ocf / net_income) if (ocf and net_income and net_income > 0) else None,
    }


def fetch_valuation_metrics(db: Session, symbol: str, peers: list[dict]) -> dict:
    """Fetch valuation metrics including peer comparisons."""
    issuer = get_issuer_by_symbol(db, symbol)
    if not issuer:
        return {}

    pe = get_latest_ratio(db, issuer.id, "pe_ratio")
    pb = get_latest_ratio(db, issuer.id, "pb_ratio")
    div_yield = get_latest_ratio(db, issuer.id, "dividend_yield")
    fcf_yield = get_latest_ratio(db, issuer.id, "fcf_yield")

    # Calculate peer medians
    peer_pe_ratios = [p.get("pe_ratio") for p in peers if p.get("pe_ratio")]
    peer_pb_ratios = [p.get("pb_ratio") for p in peers if p.get("pb_ratio")]
    peer_div_yields = [p.get("div_yield") for p in peers if p.get("div_yield")]

    pe_median = sorted(peer_pe_ratios)[len(peer_pe_ratios)//2] if peer_pe_ratios else None
    pb_median = sorted(peer_pb_ratios)[len(peer_pb_ratios)//2] if peer_pb_ratios else None
    div_median = sorted(peer_div_yields)[len(peer_div_yields)//2] if peer_div_yields else None

    return {
        "pe_ratio": pe,
        "pb_ratio": pb,
        "pe_sector_median": pe_median,
        "pb_sector_median": pb_median,
        "dividend_yield": div_yield,
        "fcf_yield": fcf_yield,
    }


# Peer percentile -> fundamentals key; a percentile is only computed when at least
# MIN_PEERS companies in the sector (including this one) have the metric.
PEER_METRICS = {
    "roe_percentile": "roe",
    "revenue_growth_percentile": "revenue_growth_yoy",
    "margin_percentile": "net_profit_margin",
}
MIN_PEERS = 3


def _peer_percentiles(symbol: str, sector: str, fundamentals: dict[str, dict], sectors: dict[str, str]) -> dict:
    out = {}
    for pct_key, metric in PEER_METRICS.items():
        own = fundamentals[symbol].get(metric)
        values = [f[metric] for s, f in fundamentals.items() if sectors.get(s) == sector and f.get(metric) is not None]
        if own is not None and len(values) >= MIN_PEERS:
            out[pct_key] = round(sum(v <= own for v in values) / len(values) * 100)
    return out


@router.get("/run")
def run_screening_funnel(db: Session = Depends(get_db)):
    """Run the screening funnel. A stage with no data to judge is reported as not evaluated
    (null), never as a pass or a fail, and the company stops there."""
    universe = load_snapshot()
    sectors = {e.symbol: e.sector for e in universe}
    securities_list = db.query(Security).filter(Security.symbol.in_(sectors)).all()
    fundamentals = {s.symbol: fetch_company_fundamentals(db, s.symbol) for s in securities_list}

    session = ScreeningSession(created_at=datetime.now(), ticker_count=len(securities_list))
    funnel = ScreeningFunnel()
    stage_counts = {n: {"passed": 0, "failed": 0, "not_evaluated": 0} for n in range(1, 5)}

    def record(stage: int, outcome) -> bool:
        stage_counts[stage]["passed" if outcome is True else "failed" if outcome is False else "not_evaluated"] += 1
        return outcome is True

    for security in securities_list:
        symbol, sector = security.symbol, sectors.get(security.symbol, "UNKNOWN")
        financials_data = fundamentals[symbol]
        prices = freshness(db, PriceOHLCV, PriceOHLCV.security_id == security.id)

        s1, s1_reasons = funnel.screen_1_basic_quality(
            company_data={"symbol": symbol},
            is_active=security.is_active,
            has_recent_prices=not prices["stale"],
            balance_sheet_health={
                "debt_to_equity": financials_data.get("debt_to_equity"),
                "current_ratio": financials_data.get("current_ratio"),
            },
        )
        result = ScreeningResult(symbol=symbol, name=security.issuer.name or symbol, sector=sector,
                                 screen_1_basic_quality=s1, screen_1_reasons=s1_reasons)
        session.results.append(result)
        if not record(1, s1):
            continue

        s2, s2_score, s2_reasons = funnel.screen_2_financial_quality({"symbol": symbol}, financials_data)
        result.screen_2_financial_quality, result.screen_2_score, result.screen_2_reasons = s2, s2_score, s2_reasons
        if not record(2, s2):
            continue

        s3, s3_score, s3_reasons = funnel.screen_3_valuation({"symbol": symbol}, fetch_valuation_metrics(db, symbol, []))
        result.screen_3_valuation, result.screen_3_score, result.screen_3_reasons = s3, s3_score, s3_reasons
        if not record(3, s3):
            continue

        s4, s4_score, s4_reasons = funnel.screen_4_peer_comparison(
            {"symbol": symbol}, _peer_percentiles(symbol, sector, fundamentals, sectors) or None
        )
        result.screen_4_peer_comparison, result.screen_4_score, result.screen_4_reasons = s4, s4_score, s4_reasons
        record(4, s4)

    watchlist_results = sorted((r for r in session.results if r.passes_all_screens), key=lambda r: r.symbol)

    def stage(r, n, passes, reasons, score=None):
        # Present for every stage the company reached; passes is null when it couldn't be judged.
        if r.stage_reached < n:
            return None
        return {"passes": passes, "reasons": reasons} | ({} if score is None else {"score": score})

    return {
        "session": {
            "created_at": session.created_at.isoformat(),
            "ticker_count": session.ticker_count,
            "watchlist_count": len(watchlist_results),
        },
        "funnel": {f"screen_{n}": c["passed"] for n, c in stage_counts.items()} | {"watchlist": len(watchlist_results)},
        "stage_counts": {f"screen_{n}": c for n, c in stage_counts.items()},
        "watchlist": [
            {
                "symbol": r.symbol,
                "name": r.name,
                "sector": r.sector,
                "screen_2_score": r.screen_2_score,
                "screen_3_score": r.screen_3_score,
                "screen_4_score": r.screen_4_score,
            }
            for r in watchlist_results
        ],
        "details": [
            {
                "symbol": r.symbol,
                "name": r.name,
                "sector": r.sector,
                "stage_reached": r.stage_reached,
                "screen_1": stage(r, 1, r.screen_1_basic_quality, r.screen_1_reasons),
                "screen_2": stage(r, 2, r.screen_2_financial_quality, r.screen_2_reasons, r.screen_2_score),
                "screen_3": stage(r, 3, r.screen_3_valuation, r.screen_3_reasons, r.screen_3_score),
                "screen_4": stage(r, 4, r.screen_4_peer_comparison, r.screen_4_reasons, r.screen_4_score),
            }
            for r in session.results
        ],
    }
