"""Historical EOD OHLCV backfill for pilot securities, via psxdata.stocks().

Anomalous rows (psxdata's own OHLC-constraint check) are skipped rather than stored —
better to have a gap than a silently wrong bar. See docs/source_registry.yaml.
"""

import logging
from datetime import date

import psxdata
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PriceOHLCV, Security

logger = logging.getLogger(__name__)


def backfill_security_prices(db: Session, security: Security, start: date, end: date) -> dict[str, int]:
    """Fetches [start, end] history for one security and inserts any missing daily bars.

    Idempotent: only inserts dates not already present for this security (checked against the
    uq_price_ohlcv_security_date constraint too, as a second line of defense).
    """
    try:
        bars = psxdata.stocks(security.symbol, start=start.isoformat(), end=end.isoformat())
    except Exception as exc:
        logger.warning("psxdata.stocks failed for %s: %s", security.symbol, exc)
        return {"inserted": 0, "skipped_existing": 0, "skipped_anomaly": 0, "fetched": 0}

    if bars is None or len(bars) == 0:
        return {"inserted": 0, "skipped_existing": 0, "skipped_anomaly": 0, "fetched": 0}

    existing_dates = set(
        db.execute(
            select(PriceOHLCV.trade_date).where(
                PriceOHLCV.security_id == security.id,
                PriceOHLCV.trade_date >= start,
                PriceOHLCV.trade_date <= end,
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
            logger.info("Skipping anomalous bar for %s on %s", security.symbol, trade_date)
            continue

        db.add(
            PriceOHLCV(
                security_id=security.id,
                trade_date=trade_date,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"]) if row["volume"] == row["volume"] else None,
                adjusted=False,
                is_delayed=True,
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


def backfill_all(db: Session, securities: list[Security], start: date, end: date) -> dict[str, dict]:
    results = {}
    for security in securities:
        logger.info("Backfilling %s from %s to %s", security.symbol, start, end)
        results[security.symbol] = backfill_security_prices(db, security, start, end)
    return results


if __name__ == "__main__":
    import sys
    from datetime import timedelta

    from app.db.session import SessionLocal
    from app.ingestion.seed_identity import seed_fertilizer_sector

    logging.basicConfig(level=logging.INFO)

    years = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    end_date = date.today()
    start_date = end_date - timedelta(days=365 * years)

    with SessionLocal() as session:
        securities = seed_fertilizer_sector(session)
        summary = backfill_all(session, securities, start_date, end_date)
        for symbol, stats in summary.items():
            print(f"{symbol}: {stats}")
