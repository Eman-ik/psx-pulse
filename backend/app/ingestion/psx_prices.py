"""Historical EOD OHLCV backfill for pilot securities, via psxdata.stocks().

Anomalous rows (psxdata's own OHLC-constraint check) are skipped rather than stored —
better to have a gap than a silently wrong bar. See docs/source_registry.yaml.
"""

import logging
from datetime import date

import psxdata
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import IngestionRun, PriceOHLCV, Security
from app.ingestion.runs import ingestion_run

logger = logging.getLogger(__name__)


def backfill_security_prices(db: Session, security: Security, start: date, end: date, run: IngestionRun) -> dict[str, int]:
    """Fetches [start, end] history for one security and inserts any missing daily bars.

    Idempotent: only inserts dates not already present for this security (checked against the
    uq_price_ohlcv_security_date constraint too, as a second line of defense).
    """
    empty = {"inserted": 0, "skipped_existing": 0, "skipped_anomaly": 0, "fetched": 0}
    try:
        bars = psxdata.stocks(security.symbol, start=start.isoformat(), end=end.isoformat())
    except Exception as exc:
        logger.warning("psxdata.stocks failed for %s: %s", security.symbol, exc)
        run.add_error(f"{security.symbol}: {type(exc).__name__}: {exc}")
        db.commit()
        return empty

    if bars is None or len(bars) == 0:
        run.add_error(f"{security.symbol}: no bars returned for {start}..{end}")
        db.commit()
        return empty

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
                source="psxdata",
                ingestion_run_id=run.id,
                is_synthetic=False,
                quality_status="verified",
            )
        )
        existing_dates.add(trade_date)
        inserted += 1

    run.rows_inserted += inserted
    db.commit()
    return {
        "inserted": inserted,
        "skipped_existing": skipped_existing,
        "skipped_anomaly": skipped_anomaly,
        "fetched": len(bars),
    }


def backfill_all(db: Session, securities: list[Security], start: date, end: date) -> dict[str, dict]:
    results = {}
    with ingestion_run(
        db, "psxdata", table="price_ohlcv", start=start.isoformat(), end=end.isoformat(),
        symbols=[s.symbol for s in securities], psxdata_version=getattr(psxdata, "__version__", None),
    ) as run:
        for security in securities:
            logger.info("Backfilling %s from %s to %s", security.symbol, start, end)
            results[security.symbol] = backfill_security_prices(db, security, start, end, run)
    return results


def db_active_securities(db: Session) -> list[Security]:
    """Every active Security already on file (seeded by seed_full_market -- this doesn't
    seed identity rows itself, it just reads what's there), for a genuine full-market
    price backfill rather than the fertilizer+cement-only pilot scope."""
    return list(db.execute(select(Security).where(Security.is_active.is_(True))).scalars().all())


if __name__ == "__main__":
    import sys
    from datetime import timedelta

    from app.db.session import SessionLocal
    from app.ingestion.seed_identity import seed_cement_sector, seed_fertilizer_sector

    logging.basicConfig(level=logging.INFO)

    # Usage: python -m app.ingestion.psx_prices [years] [sector]
    # sector: "fertilizer" (default), "cement", "pilot" (both), or "market" (every
    # active Security, ~466 as of 2026-08 -- NOT what "all" used to mean here: it was
    # silently just fertilizer+cement, which is exactly why every other ticker's price
    # data went stale and started dropping out of app/etl/ml_signal_engine.py's
    # "full PSX universe" pool (31 symbols shrank to 13 within the same day). "all" is
    # kept as an alias for "market" -- the old fert+cement-only meaning is gone, since
    # nothing should reasonably expect "all" to mean "two of ~40 sectors".
    years = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    sector_arg = sys.argv[2] if len(sys.argv) > 2 else "fertilizer"
    end_date = date.today()
    start_date = end_date - timedelta(days=365 * years)

    with SessionLocal() as session:
        securities: list[Security] = []
        if sector_arg in ("fertilizer", "pilot"):
            securities += seed_fertilizer_sector(session)
        if sector_arg in ("cement", "pilot"):
            securities += seed_cement_sector(session)
        if sector_arg in ("market", "all"):
            securities = db_active_securities(session)

        summary = backfill_all(session, securities, start_date, end_date)
        for symbol, stats in summary.items():
            print(f"{symbol}: {stats}")
