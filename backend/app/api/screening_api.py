"""API endpoints for fundamental analysis screening funnel."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.session import get_db
from app.db.models import Issuer, Security, FinancialFact, RatioValue, RatioDefinition
from app.research_system.screening_funnel import (
    ScreeningFunnel, ScreeningResult, ScreeningSession
)
from app.universe import load_snapshot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/screening", tags=["screening"])


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
        "fcf_yield_sector": 2.0,  # Placeholder for cement sector average
    }


@router.get("/run")
def run_screening_funnel(db: Session = Depends(get_db)):
    """Run the screening funnel on all companies in the universe."""
    try:
        # Load universe
        universe = load_snapshot()
        symbols = [e.symbol for e in universe]

        # Fetch all securities matching the universe symbols
        securities_list = db.query(Security).filter(Security.symbol.in_(symbols)).all()

        session = ScreeningSession(
            created_at=datetime.now(),
            ticker_count=len(securities_list),
        )

        funnel = ScreeningFunnel()

        for security in securities_list:
            symbol = security.symbol
            issuer = security.issuer

            # Screen 1: Basic Quality
            financials_data = fetch_company_fundamentals(db, symbol)

            screen_1_passes, screen_1_reasons = funnel.screen_1_basic_quality(
                company_data={"symbol": symbol},
                is_active=security.is_active,
                has_recent_prices=True,
                balance_sheet_health={
                    "debt_to_equity": financials_data.get("debt_to_equity"),
                    "current_ratio": financials_data.get("current_ratio"),
                }
            )

            # Determine sector
            sector_entry = next((e for e in universe if e.symbol == symbol), None)
            sector = sector_entry.sector if sector_entry else "UNKNOWN"

            result = ScreeningResult(
                symbol=symbol,
                name=issuer.name or symbol,
                sector=sector,
                screen_1_basic_quality=screen_1_passes,
                screen_1_reasons=screen_1_reasons,
            )

            if not screen_1_passes:
                session.results.append(result)
                continue

            session.passed_screen_1 += 1

            # Screen 2: Financial Quality
            screen_2_passes, screen_2_score, screen_2_reasons = funnel.screen_2_financial_quality(
                company_data={"symbol": symbol},
                financials=financials_data if financials_data else None,
            )

            result.screen_2_financial_quality = screen_2_passes
            result.screen_2_score = screen_2_score
            result.screen_2_reasons = screen_2_reasons

            if screen_2_passes is False:
                session.results.append(result)
                continue

            session.passed_screen_2 += 1

            # Screen 3: Valuation
            peers = []
            valuation_data = fetch_valuation_metrics(db, symbol, peers)

            screen_3_passes, screen_3_score, screen_3_reasons = funnel.screen_3_valuation(
                company_data={"symbol": symbol},
                valuation_metrics=valuation_data if valuation_data else None,
            )

            result.screen_3_valuation = screen_3_passes
            result.screen_3_score = screen_3_score
            result.screen_3_reasons = screen_3_reasons

            if screen_3_passes is False:
                session.results.append(result)
                continue

            session.passed_screen_3 += 1

            # Screen 4: Peer Comparison (simplified for now)
            screen_4_passes = True
            screen_4_score = 65.0
            screen_4_reasons = []

            result.screen_4_peer_comparison = screen_4_passes
            result.screen_4_score = screen_4_score
            result.screen_4_reasons = screen_4_reasons

            if screen_4_passes:
                session.passed_screen_4 += 1

                # Compute composite score
                non_none_scores = [
                    result.screen_2_score,
                    result.screen_3_score,
                    result.screen_4_score,
                ]
                result.composite_watchlist_score = sum(non_none_scores) / len(non_none_scores) if non_none_scores else 0
                result.tier = "watchlist"
                session.watchlist_companies.append(symbol)

            session.results.append(result)

        # Sort watchlist by composite score
        watchlist_results = [r for r in session.results if r.passes_all_screens]
        watchlist_results.sort(key=lambda r: r.composite_watchlist_score, reverse=True)

        return {
            "session": {
                "created_at": session.created_at.isoformat(),
                "ticker_count": session.ticker_count,
                "passed_screen_1": session.passed_screen_1,
                "passed_screen_2": session.passed_screen_2,
                "passed_screen_3": session.passed_screen_3,
                "passed_screen_4": session.passed_screen_4,
                "watchlist_count": len(watchlist_results),
            },
            "funnel": {
                "screen_1": session.passed_screen_1,
                "screen_2": session.passed_screen_2,
                "screen_3": session.passed_screen_3,
                "screen_4": session.passed_screen_4,
                "watchlist": len(watchlist_results),
            },
            "watchlist": [
                {
                    "rank": i + 1,
                    "symbol": r.symbol,
                    "name": r.name,
                    "sector": r.sector,
                    "composite_score": r.composite_watchlist_score,
                    "screen_2_score": r.screen_2_score,
                    "screen_3_score": r.screen_3_score,
                    "screen_4_score": r.screen_4_score,
                }
                for i, r in enumerate(watchlist_results)
            ],
            "details": [
                {
                    "symbol": r.symbol,
                    "name": r.name,
                    "sector": r.sector,
                    "stage_reached": r.stage_reached,
                    "screen_1": {
                        "passes": r.screen_1_basic_quality,
                        "reasons": r.screen_1_reasons,
                    },
                    "screen_2": {
                        "passes": r.screen_2_financial_quality,
                        "score": r.screen_2_score,
                        "reasons": r.screen_2_reasons,
                    } if r.screen_2_financial_quality is not None else None,
                    "screen_3": {
                        "passes": r.screen_3_valuation,
                        "score": r.screen_3_score,
                        "reasons": r.screen_3_reasons,
                    } if r.screen_3_valuation is not None else None,
                    "screen_4": {
                        "passes": r.screen_4_peer_comparison,
                        "score": r.screen_4_score,
                        "reasons": r.screen_4_reasons,
                    } if r.screen_4_peer_comparison is not None else None,
                }
                for r in session.results
            ]
        }

    except Exception as e:
        logger.error(f"Screening funnel error: {e}", exc_info=True)
        return {"error": str(e), "session": {}, "funnel": {}, "watchlist": [], "details": []}
