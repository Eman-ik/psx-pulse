"""Custom PSX Sector Indices — equal-weighted price-return indices per sector.

No published PSX fertilizer or cement sub-indices exist, so these are constructed from
first principles using each sector's active companies (is_active=True). Methodology:

  Equal-weighted price-return index
  - All N active companies in the sector receive equal weight (1/N each)
  - Base date: the first calendar date on which *every* active company has a price bar
  - Base level: 1000 (purely conventional, easily understood)
  - Index_t = 1000 × mean(close_i_t / close_i_base  for each company i)
  - A company missing on a given trading day uses its most recent prior close (no gap
    fabrication: only dates where at least MIN_COMPANIES_PER_DAY companies have a bar
    are included)

  Stored in: MarketIndex(code=<CODE>) + IndexOHLCV rows (one per trading day), using
  open=high=low=close=index_level (synthetic series, not an OHLCV instrument) and
  volume=None. The existing GET /market/index/{code}/prices endpoint serves it automatically.

  Delisted companies (is_active=False) are excluded regardless of when they were delisted.
"""

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import IndexOHLCV, Issuer, MarketIndex, PriceOHLCV, Sector, Security

logger = logging.getLogger(__name__)

FERTIX_CODE = "FERTIX"
FERTIX_NAME = "PSX Fertilizer Sector Index (custom, equal-weighted)"
CEMENTIX_CODE = "CEMENTIX"
CEMENTIX_NAME = "PSX Cement Sector Index (custom, equal-weighted)"
BASE_LEVEL = 1000.0
MIN_COMPANIES_PER_DAY = 3


def compute_sector_index(db: Session, sector_name: str, index_code: str, index_name: str) -> dict:
    """Compute daily index levels for all active companies in sector_name, upsert into IndexOHLCV.

    Returns a summary dict describing what was written.
    """
    # Resolve sector
    sector = db.execute(select(Sector).where(Sector.name == sector_name)).scalar_one_or_none()
    if sector is None:
        logger.warning("Sector '%s' not found — index %s cannot be computed", sector_name, index_code)
        return {"status": "sector_not_found", "bars_written": 0}

    # Collect active companies in this sector
    active_issuers = db.execute(
        select(Issuer)
        .join(Security, Security.issuer_id == Issuer.id)
        .where(Issuer.sector_id == sector.id, Security.is_active.is_(True))
    ).scalars().all()

    if not active_issuers:
        logger.warning("No active issuers found in sector '%s' — %s cannot be computed", sector_name, index_code)
        return {"status": "no_active_issuers", "bars_written": 0}

    # Load price bars per company: {issuer_id: {date: close}}
    company_prices: dict[int, dict[date, float]] = {}
    for issuer in active_issuers:
        security = db.execute(
            select(Security).where(Security.issuer_id == issuer.id, Security.is_active.is_(True))
        ).scalars().first()
        if security is None:
            continue
        bars = db.execute(
            select(PriceOHLCV.trade_date, PriceOHLCV.close)
            .where(PriceOHLCV.security_id == security.id)
            .order_by(PriceOHLCV.trade_date)
        ).all()
        if bars:
            company_prices[issuer.id] = {row.trade_date: float(row.close) for row in bars}

    n_companies = len(company_prices)
    if n_companies == 0:
        logger.warning("No price bars found for any active issuer in sector '%s'", sector_name)
        return {"status": "no_price_data", "bars_written": 0}

    # Find base date (first date all companies have a bar, with fallback)
    all_dates_per_company = [set(prices.keys()) for prices in company_prices.values()]
    common_dates = sorted(set.intersection(*all_dates_per_company))
    if not common_dates:
        all_dates = sorted(set().union(*all_dates_per_company))
        common_dates = [d for d in all_dates if sum(1 for p in company_prices.values() if d in p) >= n_companies]
        if not common_dates:
            logger.warning("No common date across all %d active companies in '%s' — falling back to partial overlap", n_companies, sector_name)
            all_dates = sorted(set().union(*all_dates_per_company))
            common_dates = [d for d in all_dates if sum(1 for p in company_prices.values() if d in p) >= MIN_COMPANIES_PER_DAY]
            if not common_dates:
                return {"status": "insufficient_overlap", "bars_written": 0}

    base_date = common_dates[0]
    base_prices = {issuer_id: prices[base_date] for issuer_id, prices in company_prices.items() if base_date in prices}
    n_base = len(base_prices)

    logger.info("%s base date: %s | %d active companies | base level: %.1f", index_code, base_date, n_base, BASE_LEVEL)

    # Compute index levels across all trading dates
    all_trading_dates = sorted(set().union(*[set(p.keys()) for p in company_prices.values()]))
    last_known: dict[int, float] = {}
    index_bars: list[tuple[date, float]] = []

    for trade_date in all_trading_dates:
        for issuer_id, prices in company_prices.items():
            if trade_date in prices:
                last_known[issuer_id] = prices[trade_date]

        companies_with_data = sum(1 for iid in base_prices if iid in last_known)
        if companies_with_data < MIN_COMPANIES_PER_DAY:
            continue

        normalized = [last_known[iid] / base_prices[iid] for iid in base_prices if iid in last_known]
        if not normalized:
            continue
        index_level = BASE_LEVEL * (sum(normalized) / len(normalized))
        index_bars.append((trade_date, round(index_level, 4)))

    if not index_bars:
        return {"status": "no_bars_computed", "bars_written": 0}

    # Ensure MarketIndex row exists
    market_index = db.execute(select(MarketIndex).where(MarketIndex.code == index_code)).scalar_one_or_none()
    if market_index is None:
        market_index = MarketIndex(code=index_code, name=index_name)
        db.add(market_index)
        db.flush()

    # Upsert IndexOHLCV rows
    existing_dates = {
        row.trade_date
        for row in db.execute(
            select(IndexOHLCV.trade_date).where(IndexOHLCV.market_index_id == market_index.id)
        ).all()
    }

    bars_written = 0
    for trade_date, level in index_bars:
        if trade_date in existing_dates:
            continue
        db.add(IndexOHLCV(
            market_index_id=market_index.id,
            trade_date=trade_date,
            open=level, high=level, low=level, close=level,
            volume=None,
            is_delayed=False,
        ))
        bars_written += 1

    db.commit()
    logger.info("%s: wrote %d new bars (total available: %d)", index_code, bars_written, len(index_bars))

    return {
        "status": "ok",
        "index_code": index_code,
        "sector": sector_name,
        "base_date": base_date.isoformat(),
        "base_level": BASE_LEVEL,
        "n_companies": n_base,
        "total_bars": len(index_bars),
        "bars_written": bars_written,
        "latest_level": index_bars[-1][1],
        "latest_date": index_bars[-1][0].isoformat(),
    }


def compute_fertix(db: Session) -> dict:
    return compute_sector_index(db, "Fertilizer", FERTIX_CODE, FERTIX_NAME)


def compute_cementix(db: Session) -> dict:
    return compute_sector_index(db, "Cement", CEMENTIX_CODE, CEMENTIX_NAME)


if __name__ == "__main__":
    import sys
    import logging as _logging
    from app.db.session import SessionLocal

    _logging.basicConfig(level=_logging.INFO)
    sector_arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    with SessionLocal() as session:
        if sector_arg in ("fertilizer", "all"):
            print(compute_fertix(session))
        if sector_arg in ("cement", "all"):
            print(compute_cementix(session))
