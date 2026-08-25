from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import (
    FinancialFact,
    Issuer,
    MlSignalScore,
    PriceOHLCV,
    RatioDefinition,
    RatioValue,
    Sector,
    Security,
    SignalScore,
)
from app.ingestion.psx_live import CEMENT_SECTOR_COMPANIES, FERTILIZER_SECTOR_COMPANIES

# Symbols psxdata actually serves a live quote for -- see live.py's /market/live/all.
# Everything else in the DB has a real Issuer/Security row (seed_full_market sourced
# it from psxdata.symbols()) but no live pricing, and for most of them no scheduled
# price backfill either (see run_price_backfill.ps1 -- deliberately scoped to just
# this list for now). "465 companies covered" conflated "a row exists" with "this is
# actually covered" -- coverage_status below is the honest version of that distinction.
_LIVE_SYMBOLS = {c["symbol"] for c in FERTILIZER_SECTOR_COMPANIES + CEMENT_SECTOR_COMPANIES}

router = APIRouter(prefix="/companies", tags=["companies"])

# Same "internal research only, not a regulated recommendation" framing as
# app/api/ml_signals.py's _DISCLAIMER -- the composite/ML scores below are real
# (not fabricated), but is_public stays False on the underlying rows per
# settings.public_signals_enabled/ml_signals_enabled until PSX/SECP compliance
# review actually completes (see app/core/config.py). Confirmed with the project
# owner that surfacing them in this internal screener/ranking view (not a public
# launch surface) is fine for now -- the non-public gate on the stored rows and
# any future public API/export is untouched by this.
SCORE_DISCLAIMER = (
    "Experimental scoring output for internal research only, not a regulated "
    "investment recommendation. Hidden from any public-facing surface until "
    "PSX/SECP compliance review completes."
)


def _latest_by_issuer(db: Session, line_item: str) -> dict[int, float]:
    rows = db.execute(
        select(FinancialFact).where(
            FinancialFact.line_item == line_item,
            FinancialFact.superseded_by_id.is_(None),
        )
    ).scalars().all()
    latest: dict[int, tuple] = {}
    for f in rows:
        key = (f.period_end, f.id)
        if f.issuer_id not in latest or key > latest[f.issuer_id][0]:
            latest[f.issuer_id] = (key, float(f.value))
    return {issuer_id: value for issuer_id, (_, value) in latest.items()}


def _latest_ratio_by_issuer(db: Session, ratio_key: str) -> dict[int, float]:
    rows = db.execute(
        select(RatioValue, RatioDefinition)
        .join(RatioDefinition, RatioDefinition.id == RatioValue.ratio_definition_id)
        .where(RatioDefinition.key == ratio_key)
    ).all()
    latest: dict[int, tuple] = {}
    for ratio_value, _definition in rows:
        key = (ratio_value.period_end, ratio_value.id)
        if ratio_value.issuer_id not in latest or key > latest[ratio_value.issuer_id][0]:
            latest[ratio_value.issuer_id] = (key, float(ratio_value.value))
    return {issuer_id: value for issuer_id, (_, value) in latest.items()}


def _latest_signals(db: Session) -> dict[int, SignalScore]:
    """Latest non-suppressed SignalScore row per issuer, for internal research display."""
    subq = (
        select(SignalScore.issuer_id, func.max(SignalScore.as_of_date).label("max_date"))
        .where(SignalScore.suppressed.is_(False))
        .group_by(SignalScore.issuer_id)
        .subquery()
    )
    rows = db.execute(
        select(SignalScore).join(
            subq,
            (SignalScore.issuer_id == subq.c.issuer_id)
            & (SignalScore.as_of_date == subq.c.max_date),
        )
    ).scalars().all()
    return {row.issuer_id: row for row in rows}


def _latest_ml_signals(db: Session) -> dict[int, MlSignalScore]:
    """Latest MlSignalScore row per issuer (see that model's docstring: signal is never
    "SELL", a low outperformance_probability is "no edge detected", not a negative call)."""
    subq = (
        select(MlSignalScore.issuer_id, func.max(MlSignalScore.as_of_date).label("max_date"))
        .group_by(MlSignalScore.issuer_id)
        .subquery()
    )
    rows = db.execute(
        select(MlSignalScore).join(
            subq,
            (MlSignalScore.issuer_id == subq.c.issuer_id)
            & (MlSignalScore.as_of_date == subq.c.max_date),
        )
    ).scalars().all()
    return {row.issuer_id: row for row in rows}


def _f(v) -> float | None:
    return float(v) if v is not None else None


@router.get("/ratio-benchmarks")
def ratio_benchmarks(db: Session = Depends(get_db)) -> dict[str, dict]:
    """Peer-average (mean of each covered issuer's latest value) for every ratio key that has
    at least one value on file, so the Ratios tab can benchmark any ratio against the sector
    average rather than a hardcoded subset. Powers the Healthy/Average badges.
    """
    rows = db.execute(
        select(RatioValue, RatioDefinition).join(RatioDefinition, RatioDefinition.id == RatioValue.ratio_definition_id)
    ).all()
    latest_by_key_issuer: dict[str, dict[int, tuple]] = {}
    for ratio_value, definition in rows:
        by_issuer = latest_by_key_issuer.setdefault(definition.key, {})
        key = (ratio_value.period_end, ratio_value.id)
        if ratio_value.issuer_id not in by_issuer or key > by_issuer[ratio_value.issuer_id][0]:
            by_issuer[ratio_value.issuer_id] = (key, float(ratio_value.value))

    return {
        ratio_key: {
            "mean": sum(v for _, v in by_issuer.values()) / len(by_issuer),
            "count": len(by_issuer),
        }
        for ratio_key, by_issuer in latest_by_key_issuer.items()
        if by_issuer
    }


@router.get("/comparison")
def companies_comparison(db: Session = Depends(get_db)) -> list[dict]:
    """Batch comparison/screener row per covered issuer (fertilizer + cement), DB-only and fast.

    price/change_pct/pe_ratio(live)/dividend_yield(live) are deliberately NOT fetched here --
    this used to call fetch_live_snapshots() inline, which can take up to 35s and made every
    page that renders this endpoint (Screener, Ranking, Companies, Sector) block for that long.
    It also held this function's DB connection idle across that scrape, which reliably killed
    it (Windows idle-socket abort -- pool_pre_ping only validates at checkout, not mid-request).
    The frontend now fetches live quotes separately (GET /market/live/all) and merges them into
    these rows client-side, after the page has already rendered with the fast DB-only data below.
    eps/dividend_per_share are exposed so that client-side merge can reproduce the same P/E and
    dividend-yield fallback this endpoint used to compute server-side once a live price lands.

    ai_signal/ai_scores/ml_signal are real (never fabricated) but research-only -- see
    SCORE_DISCLAIMER. A field is null when that issuer has no scoring run on file yet
    (only 18 of 672 issuers do, as of this pilot), never a placeholder zero.
    """
    issuers = db.execute(
        select(Issuer).where(Issuer.securities.any(Security.is_active.is_(True)))
    ).scalars().all()
    securities = db.execute(select(Security).where(Security.is_active.is_(True))).scalars().all()
    security_by_issuer = {s.issuer_id: s for s in securities}
    sector_by_id = {s.id: s.name for s in db.execute(select(Sector)).scalars().all()}

    market_cap_by_issuer = _latest_by_issuer(db, "market_cap")
    roe_by_issuer = _latest_ratio_by_issuer(db, "roe")
    roa_by_issuer = _latest_ratio_by_issuer(db, "roa")
    debt_to_equity_by_issuer = _latest_ratio_by_issuer(db, "debt_to_equity")
    current_ratio_by_issuer = _latest_ratio_by_issuer(db, "current_ratio")
    net_margin_by_issuer = _latest_ratio_by_issuer(db, "net_profit_margin")
    revenue_growth_by_issuer = _latest_ratio_by_issuer(db, "revenue_growth_yoy")
    eps_growth_by_issuer = _latest_ratio_by_issuer(db, "eps_growth_yoy")
    eps_by_issuer = _latest_by_issuer(db, "eps")
    dps_by_issuer = _latest_by_issuer(db, "dividend_per_share")
    signal_by_issuer = _latest_signals(db)
    ml_signal_by_issuer = _latest_ml_signals(db)

    issuers_with_price = set(
        db.execute(
            select(Security.issuer_id).join(PriceOHLCV, PriceOHLCV.security_id == Security.id).distinct()
        ).scalars().all()
    )
    issuers_with_financials = set(
        db.execute(select(FinancialFact.issuer_id).distinct()).scalars().all()
    )

    rows = []
    for issuer in issuers:
        security = security_by_issuer.get(issuer.id)
        symbol = security.symbol if security else None
        has_price = issuer.id in issuers_with_price
        has_financials = issuer.id in issuers_with_financials
        if symbol in _LIVE_SYMBOLS and has_price and has_financials:
            coverage_status = "live"
        elif has_price:
            coverage_status = "historical"
        elif has_financials:
            coverage_status = "partial"
        else:
            coverage_status = "unverified"

        signal = signal_by_issuer.get(issuer.id)
        ml_signal = ml_signal_by_issuer.get(issuer.id)

        # risk_score/catalyst_risk_score deliberately excluded from this average: per
        # SignalScore's own docstring, a higher risk_score means lower measured beta,
        # not "better" in every sense -- averaging it in with the higher-is-better
        # dimensions below would silently mix polarities.
        dimension_scores = (
            [
                s
                for s in (
                    _f(signal.quality_score) if signal else None,
                    _f(signal.growth_score) if signal else None,
                    _f(signal.financial_health_score) if signal else None,
                    _f(signal.valuation_score) if signal else None,
                    _f(signal.momentum_score) if signal else None,
                )
                if s is not None
            ]
            if signal
            else []
        )
        ai_score = round(sum(dimension_scores) / len(dimension_scores), 1) if dimension_scores else None

        rows.append(
            {
                "id": issuer.id,
                "symbol": symbol,
                "name": issuer.name,
                "sector": sector_by_id.get(issuer.sector_id),
                # price/change_pct/pe_ratio/dividend_yield are null here by design -- the
                # frontend merges in live quotes (GET /market/live/all) client-side. eps/
                # dividend_per_share below let it reproduce the P/E and yield fallback.
                "price": None,
                "change_pct": None,
                "market_cap": market_cap_by_issuer.get(issuer.id),
                "pe_ratio": None,
                "dividend_yield": None,
                "eps": eps_by_issuer.get(issuer.id),
                "dividend_per_share": dps_by_issuer.get(issuer.id),
                "coverage_status": coverage_status,
                "roe": roe_by_issuer.get(issuer.id),
                "roa": roa_by_issuer.get(issuer.id),
                "debt_to_equity": debt_to_equity_by_issuer.get(issuer.id),
                "current_ratio": current_ratio_by_issuer.get(issuer.id),
                "net_profit_margin": net_margin_by_issuer.get(issuer.id),
                "revenue_growth_yoy": revenue_growth_by_issuer.get(issuer.id),
                "eps_growth_yoy": eps_growth_by_issuer.get(issuer.id),
                "ai_signal": signal.composite_signal if signal else None,
                "ai_score": ai_score,
                "ai_quality_score": _f(signal.quality_score) if signal else None,
                "ai_growth_score": _f(signal.growth_score) if signal else None,
                "ai_financial_health_score": _f(signal.financial_health_score) if signal else None,
                "ai_valuation_score": _f(signal.valuation_score) if signal else None,
                "ai_momentum_score": _f(signal.momentum_score) if signal else None,
                "ml_signal": ml_signal.signal if ml_signal else None,
                "ml_outperformance_probability": _f(ml_signal.outperformance_probability) if ml_signal else None,
                "score_disclaimer": SCORE_DISCLAIMER if (signal or ml_signal) else None,
            }
        )
    return rows
