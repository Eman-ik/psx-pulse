"""Historical EOD OHLCV backfill for PSX benchmark indices, via psxdata.stocks().

Mirrors app/ingestion/psx_prices.py's pattern exactly (same psxdata call shape, same
anomaly-skip policy) but writes to index_ohlcv/market_index instead of price_ohlcv/security,
since an index isn't a company and doesn't belong in the identity master.
"""

import logging
from datetime import date

import psxdata
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import IndexOHLCV, MarketIndex

logger = logging.getLogger(__name__)

# code must match psxdata's symbol for psxdata.stocks(), confirmed working 2026-07-27.
TRACKED_INDICES: list[dict[str, str]] = [
    {"code": "KSE100", "name": "KSE-100 Index"},
]


def get_or_create_index(db: Session, code: str, name: str) -> MarketIndex:
    index = db.execute(select(MarketIndex).where(MarketIndex.code == code)).scalar_one_or_none()
    if index is None:
        index = MarketIndex(code=code, name=name)
        db.add(index)
        db.flush()
        logger.info("Created market_index %s", code)
    return index


def backfill_index_prices(db: Session, index: MarketIndex, start: date, end: date) -> dict[str, int]:
    """Fetches [start, end] history for one index and inserts any missing daily bars.

    Idempotent: only inserts dates not already present for this index.
    """
    try:
        bars = psxdata.stocks(index.code, start=start.isoformat(), end=end.isoformat())
    except Exception as exc:
        logger.warning("psxdata.stocks failed for index %s: %s", index.code, exc)
        return {"inserted": 0, "skipped_existing": 0, "skipped_anomaly": 0, "fetched": 0}

    if bars is None or len(bars) == 0:
        return {"inserted": 0, "skipped_existing": 0, "skipped_anomaly": 0, "fetched": 0}

    existing_dates = set(
        db.execute(
            select(IndexOHLCV.trade_date).where(
                IndexOHLCV.market_index_id == index.id,
                IndexOHLCV.trade_date >= start,
                IndexOHLCV.trade_date <= end,
            )
        )
        .scalars()
        .all()
    )

    inserted = skipped_existing = skipped_anomaly = 0
    for _, row in bars.iterrows():
        trade_date = row["date"].date() if hasattr(row["date"], "date") else row["date"]
        if trade_date in existing_dates:
            skipped_existing += 1
            continue
        if bool(row.get("is_anomaly", False)):
            skipped_anomaly += 1
            logger.info("Skipping anomalous bar for index %s on %s", index.code, trade_date)
            continue

        db.add(
            IndexOHLCV(
                market_index_id=index.id,
                trade_date=trade_date,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"]) if row["volume"] == row["volume"] else None,
                is_delayed=True,
                source="psxdata",
            )
        )
        existing_dates.add(trade_date)
        inserted += 1

    db.commit()
    return {
        "inserted": inserted,
        "skipped_existing": skipped_existing,
        "skipped_anomaly": skipped_anomaly,
        "fetched": len(bars),
    }


def backfill_all(db: Session, start: date, end: date) -> dict[str, dict]:
    results = {}
    for spec in TRACKED_INDICES:
        index = get_or_create_index(db, spec["code"], spec["name"])
        logger.info("Backfilling index %s from %s to %s", index.code, start, end)
        results[index.code] = backfill_index_prices(db, index, start, end)
    return results


if __name__ == "__main__":
    import sys
    from datetime import timedelta

    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    years = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    end_date = date.today()
    start_date = end_date - timedelta(days=365 * years)

    with SessionLocal() as session:
        summary = backfill_all(session, start_date, end_date)
        for code, stats in summary.items():
            print(f"{code}: {stats}")
