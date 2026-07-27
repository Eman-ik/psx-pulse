"""Beta (systematic risk vs KSE-100), computed from real daily returns.

beta = Cov(R_issuer, R_market) / Var(R_market), computed over daily close-to-close returns on
every trading date both the security and the KSE-100 index have a bar for. This replaces the
neutral beta=1.0 placeholder assumption most issuers used before real KSE-100 data existed (see
app/ingestion/capm_seed.py) with an actual measurement -- and, for FATIMA, sits alongside (does
not delete) the analyst-sourced beta=1.02 from SCSTrade via the user-provided Fatima Fertilizer
PDF: this evidence-class "calculated_metric" row gets a later as_of_date and so takes precedence
in app/etl/valuation_engine.py's "most recent CapmAssumption row wins" lookup, but the earlier
analyst-sourced row is never deleted -- it stays in the table as history.

Below MIN_OVERLAPPING_DAYS of common trading dates, beta is not computed at all (returns None)
rather than computed on too little data to mean anything -- consistent with this project's
"no signal is better than a fabricated one" rule (see valuation_engine.py's own docstring for
the same principle applied to the Gordon Growth model).
"""

import logging
from datetime import date
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CapmAssumption, IndexOHLCV, Issuer, MarketIndex, PriceOHLCV, Security

logger = logging.getLogger(__name__)

MIN_OVERLAPPING_DAYS = 60  # ~3 trading months; below this a covariance estimate is just noise
BENCHMARK_INDEX_CODE = "KSE100"


def daily_returns(bars: Sequence[tuple[date, float]]) -> dict[date, float]:
    """Simple close-to-close returns, keyed by the *later* date of each pair."""
    sorted_bars = sorted(bars, key=lambda b: b[0])
    returns: dict[date, float] = {}
    for i in range(1, len(sorted_bars)):
        prev_close = sorted_bars[i - 1][1]
        curr_date, curr_close = sorted_bars[i]
        if prev_close > 0:
            returns[curr_date] = (curr_close - prev_close) / prev_close
    return returns


def _covariance_over_variance(company_returns: list[float], market_returns: list[float]) -> float | None:
    n = len(company_returns)
    if n < 2 or len(market_returns) != n:
        return None
    mean_c = sum(company_returns) / n
    mean_m = sum(market_returns) / n
    covariance = sum((company_returns[i] - mean_c) * (market_returns[i] - mean_m) for i in range(n)) / (n - 1)
    variance_m = sum((r - mean_m) ** 2 for r in market_returns) / (n - 1)
    if variance_m == 0:
        return None
    return covariance / variance_m


def compute_beta_from_bars(
    company_bars: Sequence[tuple[date, float]], market_bars: Sequence[tuple[date, float]]
) -> dict | None:
    """Returns {beta, start_date, end_date, n_days} or None if there isn't enough overlapping
    history (see MIN_OVERLAPPING_DAYS) or the market had zero variance over that window.
    """
    company_returns = daily_returns(company_bars)
    market_returns = daily_returns(market_bars)
    common_dates = sorted(set(company_returns) & set(market_returns))
    if len(common_dates) < MIN_OVERLAPPING_DAYS:
        return None

    beta = _covariance_over_variance(
        [company_returns[d] for d in common_dates],
        [market_returns[d] for d in common_dates],
    )
    if beta is None:
        return None
    return {"beta": beta, "start_date": common_dates[0], "end_date": common_dates[-1], "n_days": len(common_dates)}


def _get_market_wide_assumption(db: Session) -> CapmAssumption | None:
    return db.execute(
        select(CapmAssumption).where(CapmAssumption.issuer_id.is_(None)).order_by(CapmAssumption.as_of_date.desc())
    ).scalars().first()


def compute_and_store_beta(db: Session, issuer: Issuer, security: Security) -> dict | None:
    index = db.execute(select(MarketIndex).where(MarketIndex.code == BENCHMARK_INDEX_CODE)).scalar_one_or_none()
    if index is None:
        logger.warning("No %s index data ingested yet -- run app/ingestion/psx_index.py first", BENCHMARK_INDEX_CODE)
        return None
    market_wide = _get_market_wide_assumption(db)
    if market_wide is None:
        logger.warning("No market-wide CapmAssumption row -- run app/ingestion/capm_seed.py first")
        return None

    company_bars = [
        (b.trade_date, float(b.close))
        for b in db.execute(select(PriceOHLCV).where(PriceOHLCV.security_id == security.id)).scalars()
    ]
    market_bars = [
        (b.trade_date, float(b.close))
        for b in db.execute(select(IndexOHLCV).where(IndexOHLCV.market_index_id == index.id)).scalars()
    ]

    result = compute_beta_from_bars(company_bars, market_bars)
    if result is None:
        logger.info(
            "Skipping beta for %s: fewer than %d overlapping trading days with %s",
            issuer.name, MIN_OVERLAPPING_DAYS, BENCHMARK_INDEX_CODE,
        )
        return None

    as_of = result["end_date"]
    existing = db.execute(
        select(CapmAssumption).where(CapmAssumption.issuer_id == issuer.id, CapmAssumption.as_of_date == as_of)
    ).scalar_one_or_none()
    if existing is not None:
        return result

    db.add(
        CapmAssumption(
            issuer_id=issuer.id,
            as_of_date=as_of,
            beta=result["beta"],
            risk_free_rate_pct=market_wide.risk_free_rate_pct,
            base_equity_risk_premium_pct=market_wide.base_equity_risk_premium_pct,
            country_risk_premium_pct=market_wide.country_risk_premium_pct,
            source_note=(
                f"Beta computed as Cov(daily returns, KSE-100 daily returns) / Var(KSE-100 daily "
                f"returns) over {result['n_days']} overlapping trading days "
                f"({result['start_date'].isoformat()} to {as_of.isoformat()}). Risk-free rate and "
                f"equity risk premiums retained from the market-wide assumption row (see "
                f"app/ingestion/capm_seed.py). Not a third-party estimate -- fully reproducible "
                f"from app/etl/beta.py against this pilot's own ingested price_ohlcv/index_ohlcv."
            ),
        )
    )
    db.commit()
    return result


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        issuers = session.execute(select(Issuer).where(Issuer.securities.any())).scalars().all()
        for issuer in issuers:
            security = issuer.securities[0]
            outcome = compute_and_store_beta(session, issuer, security)
            print(f"{issuer.name} ({security.symbol}): {outcome}")
