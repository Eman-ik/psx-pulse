"""Macro series ingestion from SBP EasyData (https://easydata.sbp.org.pk).

Requires a free SBP EasyData account + generated API key (90-day validity), which is a
credential only you can create — see backend/.env.example. This module simply logs a
warning and no-ops when SBP_EASYDATA_API_KEY is unset, rather than failing the whole
ingestion run.

Series keys below were confirmed by browsing easydata.sbp.org.pk directly (see
docs/source_registry.yaml) — not guessed. National CPI is itself PBS-compiled data that
SBP republishes on this portal; using it here avoids needing a second PBS-specific scraper
for the same figure.
"""

import logging
from datetime import date

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import MacroObservation, MacroSeries

logger = logging.getLogger(__name__)

# code -> (series_key, display name, frequency, unit)
SERIES = {
    "SBP_POLICY_RATE": (
        "TS_GP_IR_SIRPR_AH.SBPOL0030",
        "State Bank of Pakistan's Policy (Target) Rate",
        "daily",
        "percent",
    ),
    "KIBOR_6M": (
        "TS_GP_BAM_SIRKIBOR_D.KIBOR0030",
        "Six-Months Karachi Interbank Offer Rate",
        "daily",
        "percent",
    ),
    "PKR_USD_RATE": (
        "TS_GP_ER_FAERPKR_M.E00220",
        "Average Exchange Rate of Pak Rupees per U.S. Dollar",
        "monthly",
        "PKR",
    ),
    "SBP_GROSS_RESERVES": (
        "TS_GP_BOP_BPM6SUM_M.P00730",
        "SBP Gross Foreign Reserves",
        "monthly",
        "million_usd",
    ),
    "CURRENT_ACCOUNT_BALANCE": (
        "TS_GP_BOP_BPM6SUM_M.P00010",
        "Current Account Balance",
        "monthly",
        "million_usd",
    ),
    "NATIONAL_CPI_YOY": (
        "TS_GP_PT_CPI_M.P00011516",
        "National CPI, an Inflation Measure (Year-on-Year basis)",
        "monthly",
        "percent",
    ),
}


def fetch_series_data(series_key: str, start_date: date, end_date: date) -> list[dict]:
    settings = get_settings()
    if not settings.sbp_easydata_api_key:
        logger.warning(
            "SBP_EASYDATA_API_KEY not set — skipping %s. Sign up free at "
            "https://easydata.sbp.org.pk, generate a key under My Data Basket > My Account, "
            "and add it to backend/.env.",
            series_key,
        )
        return []

    url = f"{settings.sbp_easydata_base_url}/series/{series_key}/data"
    params = {
        "api_key": settings.sbp_easydata_api_key,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "format": "json",
    }
    try:
        response = httpx.get(url, params=params, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("SBP EasyData request failed for %s: %s", series_key, exc)
        return []

    payload = response.json()
    columns = payload.get("columns", [])
    rows = payload.get("rows", [])
    try:
        date_idx = columns.index("Observation Date")
        value_idx = columns.index("Observation Value")
    except ValueError:
        logger.warning("Unexpected SBP EasyData response shape for %s: columns=%s", series_key, columns)
        return []

    return [{"date": row[date_idx], "value": row[value_idx]} for row in rows]


def _get_or_create_series(db: Session, code: str, name: str, frequency: str, unit: str) -> MacroSeries:
    series = db.execute(select(MacroSeries).where(MacroSeries.code == code)).scalar_one_or_none()
    if series is None:
        series = MacroSeries(code=code, name=name, source="SBP", frequency=frequency, unit=unit)
        db.add(series)
        db.flush()
    return series


def ingest_series(db: Session, code: str, start_date: date, end_date: date) -> dict[str, int]:
    series_key, name, frequency, unit = SERIES[code]
    rows = fetch_series_data(series_key, start_date, end_date)
    if not rows:
        return {"inserted": 0, "skipped": 0, "fetched": 0}

    series = _get_or_create_series(db, code, name, frequency, unit)
    existing_periods = set(
        db.execute(
            select(MacroObservation.period).where(MacroObservation.macro_series_id == series.id)
        )
        .scalars()
        .all()
    )

    inserted = skipped = 0
    for row in rows:
        try:
            period = date.fromisoformat(row["date"][:10])
            value = float(row["value"])
        except (ValueError, TypeError, KeyError):
            skipped += 1
            continue
        if period in existing_periods:
            skipped += 1
            continue
        db.add(MacroObservation(macro_series_id=series.id, period=period, value=value))
        existing_periods.add(period)
        inserted += 1

    db.commit()
    return {"inserted": inserted, "skipped": skipped, "fetched": len(rows)}


def ingest_all(db: Session, start_date: date, end_date: date) -> dict[str, dict]:
    return {code: ingest_series(db, code, start_date, end_date) for code in SERIES}


if __name__ == "__main__":
    import sys
    from datetime import timedelta

    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    years = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    end = date.today()
    start = end - timedelta(days=365 * years)

    with SessionLocal() as session:
        summary = ingest_all(session, start, end)
        for code, stats in summary.items():
            print(f"{code}: {stats}")
