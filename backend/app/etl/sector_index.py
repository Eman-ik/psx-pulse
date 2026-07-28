"""Custom PSX Fertilizer Sector Index (FERTIX) — equal-weighted price-return index.

No published PSX fertilizer sub-index exists, so this constructs one from first principles
using the pilot universe's active companies (is_active=True). The methodology is transparent
and reproducible from PriceOHLCV alone:

  Methodology: Equal-weighted price-return index
    - All N active companies receive equal weight (1/N each)
    - Base date: the first calendar date on which *every* active company has a price bar
    - Base level: 1000 (purely conventional, easily understood)
    - Index_t = 1000 × mean(close_i_t / close_i_base  for each company i)
    - A company missing on a given trading day uses its most recent prior close (no gap
      fabrication: only dates where at least 3 of N companies have a bar are included)

  Stored in: MarketIndex(code="FERTIX") + IndexOHLCV rows (one per trading day), using
  open=high=low=close=index_level (it's a synthetic series, not an OHLCV instrument) and
  volume=None. The existing GET /market/index/{code}/prices endpoint serves it automatically.

  Delisted companies (is_active=False) are excluded from FERTIX regardless of when they
  were delisted — their historical bars are present in PriceOHLCV but including them would
  require a base-weight-change methodology that isn't warranted at pilot scale.
"""

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import IndexOHLCV, Issuer, MarketIndex, PriceOHLCV, Security

logger = logging.getLogger(__name__)

FERTIX_CODE = "FERTIX"
FERTIX_NAME = "PSX Fertilizer Sector Index (custom, equal-weighted)"
BASE_LEVEL = 1000.0
MIN_COMPANIES_PER_DAY = 3  # require at least this many companies to have a bar before including a date


def compute_fertix(db: Session) -> dict:
    """Compute FERTIX daily levels from PriceOHLCV and upsert into IndexOHLCV.

    Returns a summary dict describing what was written.
    """
    # Collect active companies and their security records
    active_issuers = db.execute(
        select(Issuer)
        .join(Security, Security.issuer_id == Issuer.id)
        .where(Security.is_active.is_(True))
    ).scalars().all()

    if not active_issuers:
        logger.warning("No active issuers found — FERTIX cannot be computed")
        return {"status": "no_active_issuers", "bars_written": 0}

    # Load price bars for each active company: {issuer_id: {date: close_price}}
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
        logger.warning("No price bars found for any active issuer")
        return {"status": "no_price_data", "bars_written": 0}

    # Find the earliest date on which all companies have a bar (base date)
    all_dates_per_company = [set(prices.keys()) for prices in company_prices.values()]
    common_dates = sorted(set.intersection(*all_dates_per_company))
    if not common_dates:
        # Fall back: earliest date where at least MIN_COMPANIES_PER_DAY companies have bars
        all_dates = sorted(set().union(*all_dates_per_company))
        common_dates = [d for d in all_dates if sum(1 for p in company_prices.values() if d in p) >= n_companies]
        if not common_dates:
            logger.warning("No common date across all %d active companies — falling back to partial overlap", n_companies)
            all_dates = sorted(set().union(*all_dates_per_company))
            common_dates = [d for d in all_dates if sum(1 for p in company_prices.values() if d in p) >= MIN_COMPANIES_PER_DAY]
            if not common_dates:
                return {"status": "insufficient_overlap", "bars_written": 0}

    base_date = common_dates[0]
    base_prices = {issuer_id: prices[base_date] for issuer_id, prices in company_prices.items() if base_date in prices}
    n_base = len(base_prices)

    logger.info(
        "FERTIX base date: %s | %d active companies | base level: %.1f",
        base_date, n_base, BASE_LEVEL,
    )

    # Compute index levels for all trading dates (union of all company dates)
    all_trading_dates = sorted(set().union(*[set(p.keys()) for p in company_prices.values()]))

    # Track each company's last known price (fill forward within the gap)
    last_known: dict[int, float] = {}
    index_bars: list[tuple[date, float]] = []

    for trade_date in all_trading_dates:
        # Update last_known prices with today's bars
        for issuer_id, prices in company_prices.items():
            if trade_date in prices:
                last_known[issuer_id] = prices[trade_date]

        # Only include dates where enough companies have (current or recent) prices
        companies_with_data = sum(1 for iid in base_prices if iid in last_known)
        if companies_with_data < MIN_COMPANIES_PER_DAY:
            continue

        # Equal-weighted mean of each company's price relative to its base price
        normalized = [
            last_known[iid] / base_prices[iid]
            for iid in base_prices
            if iid in last_known
        ]
        if not normalized:
            continue
        index_level = BASE_LEVEL * (sum(normalized) / len(normalized))
        index_bars.append((trade_date, round(index_level, 4)))

    if not index_bars:
        return {"status": "no_bars_computed", "bars_written": 0}

    # Ensure MarketIndex row exists for FERTIX
    fertix_index = db.execute(
        select(MarketIndex).where(MarketIndex.code == FERTIX_CODE)
    ).scalar_one_or_none()
    if fertix_index is None:
        fertix_index = MarketIndex(
            code=FERTIX_CODE,
            name=FERTIX_NAME,
        )
        db.add(fertix_index)
        db.flush()

    # Upsert IndexOHLCV rows
    existing_dates = {
        row.trade_date
        for row in db.execute(
            select(IndexOHLCV.trade_date).where(IndexOHLCV.market_index_id == fertix_index.id)
        ).all()
    }

    bars_written = 0
    for trade_date, level in index_bars:
        if trade_date in existing_dates:
            continue
        db.add(IndexOHLCV(
            market_index_id=fertix_index.id,
            trade_date=trade_date,
            open=level,
            high=level,
            low=level,
            close=level,
            volume=None,
            is_delayed=False,
        ))
        bars_written += 1

    db.commit()
    logger.info("FERTIX: wrote %d new bars (total available: %d)", bars_written, len(index_bars))

    return {
        "status": "ok",
        "base_date": base_date.isoformat(),
        "base_level": BASE_LEVEL,
        "n_companies": n_base,
        "total_bars": len(index_bars),
        "bars_written": bars_written,
        "latest_level": index_bars[-1][1],
        "latest_date": index_bars[-1][0].isoformat(),
    }


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)
    with SessionLocal() as session:
        result = compute_fertix(session)
        print(result)
