import logging

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import MacroObservation, MacroSeries, SectorRiskSnapshot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/macro", tags=["macro"])


@router.get("/series")
def list_series(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(MacroSeries)).scalars().all()
    return [
        {"code": s.code, "name": s.name, "source": s.source, "frequency": s.frequency, "unit": s.unit}
        for s in rows
    ]


@router.get("/series/{code}")
def get_series(code: str, db: Session = Depends(get_db)) -> dict | None:
    series = db.execute(select(MacroSeries).where(MacroSeries.code == code)).scalar_one_or_none()
    if series is None:
        return None
    observations = db.execute(
        select(MacroObservation)
        .where(MacroObservation.macro_series_id == series.id)
        .order_by(MacroObservation.period)
    ).scalars().all()
    return {
        "code": series.code,
        "name": series.name,
        "source": series.source,
        "unit": series.unit,
        "observations": [{"period": o.period.isoformat(), "value": float(o.value)} for o in observations],
    }


@router.get("/risk-snapshot")
def latest_risk_snapshot(db: Session = Depends(get_db)) -> dict | None:
    row = db.execute(
        select(SectorRiskSnapshot).order_by(SectorRiskSnapshot.as_of_date.desc())
    ).scalars().first()
    if row is None:
        return None
    return {
        "as_of_date": row.as_of_date.isoformat(),
        "overall_risk": row.overall_risk,
        "geopolitical": row.geopolitical,
        "economy": row.economy,
        "imf_program": row.imf_program,
        "currency_pkr": row.currency_pkr,
        "key_positives": row.key_positives,
        "key_negatives": row.key_negatives,
    }


@router.get("/live-snapshot")
def live_macro_snapshot(db: Session = Depends(get_db)) -> dict:
    """Scraped real-time macro indicators for the WorldMonitor ticker banner.

    Sources (no API key required):
      - USD/PKR: jsDelivr-hosted open currency rates (fawazahmed0), updated daily
      - Brent Crude: Yahoo Finance chart API (ICE BZ=F front-month contract)
      - CPI fallback: World Bank open data (annual Pakistan CPI YoY %)
    DB-sourced (populated by ingestion/sbp_macro.py when SBP_EASYDATA_API_KEY is set):
      - SBP Policy Rate, Monthly CPI, SBP FX Reserves
    """
    result: dict[str, dict] = {}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; psx-research-platform/1.0)"}

    # ── USD/PKR ─────────────────────────────────────────────────────────────
    try:
        r = httpx.get(
            "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json",
            headers=headers,
            timeout=8,
        )
        if r.is_success:
            data = r.json()
            pkr = float(data["usd"]["pkr"])
            result["pkr_usd"] = {"value": pkr, "source": "Open Currency Rates (daily)"}
    except Exception as exc:
        logger.warning("USD/PKR scrape failed: %s", exc)

    # ── Brent Crude (ICE front-month BZ=F) ──────────────────────────────────
    try:
        r = httpx.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/BZ=F",
            params={"interval": "1d", "range": "5d"},
            headers=headers,
            timeout=8,
        )
        if r.is_success:
            meta = r.json()["chart"]["result"][0]["meta"]
            result["brent_crude"] = {
                "value": float(meta["regularMarketPrice"]),
                "prev_close": float(meta.get("chartPreviousClose", meta["regularMarketPrice"])),
                "source": "Yahoo Finance (ICE Brent)",
            }
    except Exception as exc:
        logger.warning("Brent Crude scrape failed: %s", exc)

    # ── CPI fallback — World Bank open data (annual, no key required) ────────
    try:
        r = httpx.get(
            "https://api.worldbank.org/v2/country/PK/indicator/FP.CPI.TOTL.ZG",
            params={"format": "json", "mrv": 3},
            headers=headers,
            timeout=8,
        )
        if r.is_success:
            obs = [o for o in r.json()[1] if o.get("value") is not None]
            if obs:
                latest = obs[0]
                prev = obs[1] if len(obs) > 1 else None
                result["cpi_wb"] = {
                    "value": float(latest["value"]),
                    "period": str(latest["date"]),
                    "prev_value": float(prev["value"]) if prev else None,
                    "source": "World Bank (annual CPI %)",
                }
    except Exception as exc:
        logger.warning("World Bank CPI scrape failed: %s", exc)

    # ── DB-sourced indicators (SBP EasyData ingestion) ───────────────────────
    db_codes: dict[str, str] = {
        "SBP_POLICY_RATE": "sbp_rate",
        "NATIONAL_CPI_YOY": "cpi_monthly",
        "SBP_GROSS_RESERVES": "fx_reserves",
        "PKR_USD_RATE": "pkr_usd_monthly",
    }
    for code, key in db_codes.items():
        series = db.execute(select(MacroSeries).where(MacroSeries.code == code)).scalar_one_or_none()
        if series is None:
            continue
        rows = db.execute(
            select(MacroObservation)
            .where(MacroObservation.macro_series_id == series.id)
            .order_by(MacroObservation.period.desc())
            .limit(2)
        ).scalars().all()
        if not rows:
            continue
        latest_obs = rows[0]
        prev_obs = rows[1] if len(rows) > 1 else None
        result[key] = {
            "value": float(latest_obs.value),
            "period": latest_obs.period.isoformat(),
            "prev_value": float(prev_obs.value) if prev_obs else None,
            "unit": series.unit,
        }

    return result
