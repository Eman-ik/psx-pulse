"""Live-ish market data for the Fertilizer sector pilot, sourced from the psxdata library.

psxdata (https://github.com/mtauha/psxdata) scrapes PSX's own public site — no API key,
but also no SLA and no license beyond what's implied by pulling from dps.psx.com.pk directly.
See docs/source_registry.yaml. This module intentionally never claims a licensed real-time
feed: prices reflect the most recent session psxdata can see, which may be the prior trading
day outside market hours or on weekends.

Finnhub was evaluated first and dropped — it does not cover PSX-listed securities at all.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import psxdata

logger = logging.getLogger(__name__)

# PSX's own "FERTILIZER" sector classification, confirmed via psxdata.symbols() on 2026-07-26.
# AGLNCPS (Agritech non-voting preference shares) is a second security under the AGL issuer
# and is intentionally left out of this live-quote list; it belongs in the full identity-master
# ingestion (Milestone 2), not this quick live-pricing slice. Reconcile this list periodically
# against psxdata.symbols() — PSX sector membership does change.
#
# FFBL was removed 2026-07-27: it merged into FFC (Scheme of Arrangement sanctioned by the
# Lahore High Court, 2024-12-13 — see the "Certified True Copy of the Order..." announcement
# on file) and stopped trading around 2024-12-20 (confirmed: psxdata.stocks("FFBL", ...) returns
# zero bars for all of 2025-2026, even though psxdata.symbols()/quote() still list it as a stale
# cached entry).
#
# ENGRO was removed the same day: a 3-party "Scheme of Arrangement of Dawood Hercules
# Corporation Limited, Engro Corporation Limited and DH Partners Limited" (Book Closure Notice
# published 2024-12-27) and stopped trading after 2025-01-03, independently confirmed the same
# way (psxdata.stocks("ENGRO", ...) returns zero bars for 2025-2026). Note DAWH (Dawood
# Hercules, ENGRO's own parent and already an untracked ownership-graph stub) also shows no
# recent trading via psxdata as of this check — the surviving-entity mechanics of this
# restructuring aren't independently confirmed from headline announcement titles alone.
#
# Both removed companies' historical price/financial/announcement data stays in the DB and
# their overview pages are still reachable; Security.is_active=False just keeps them out of the
# pilot's active company lists (see app/api/companies.py, comparison.py, sectors.py,
# screener.py). Reproducible via app/ingestion/mark_delisted_securities.py.
FERTILIZER_SECTOR_COMPANIES: list[dict[str, str]] = [
    {"symbol": "FFC", "name": "Fauji Fertilizer Company Limited"},
    {"symbol": "EFERT", "name": "Engro Fertilizers Limited"},
    {"symbol": "FATIMA", "name": "Fatima Fertilizer Company Limited"},
    {"symbol": "AGL", "name": "Agritech Limited"},
    {"symbol": "AHCL", "name": "Arif Habib Corporation Limited"},
]


def _clean(value: object) -> object:
    """Convert pandas/numpy NaN to None so the response is valid, serializable JSON."""
    try:
        if value is None:
            return None
        if isinstance(value, float) and value != value:  # NaN != NaN
            return None
        return value
    except Exception:
        return None


def fetch_live_snapshot(symbol: str) -> dict | None:
    """Best-effort live-ish snapshot for one symbol. Returns None if the source has nothing."""
    try:
        quote_rows = psxdata.quote(symbol).to_dict(orient="records")
        quote_row = quote_rows[0] if quote_rows else {}
    except Exception as exc:
        logger.warning("psxdata.quote failed for %s: %s", symbol, exc)
        quote_row = {}

    last_bar: dict | None = None
    try:
        end = date.today()
        start = end - timedelta(days=14)
        bars = psxdata.stocks(symbol, start=start.isoformat(), end=end.isoformat())
        if bars is not None and len(bars) > 0:
            bars = bars.sort_values("date")
            row = bars.iloc[-1]
            last_bar = {
                "date": row["date"].date().isoformat() if hasattr(row["date"], "date") else str(row["date"]),
                "open": _clean(float(row["open"])),
                "high": _clean(float(row["high"])),
                "low": _clean(float(row["low"])),
                "close": _clean(float(row["close"])),
                "volume": _clean(int(row["volume"]) if row["volume"] == row["volume"] else None),
            }
    except Exception as exc:
        logger.warning("psxdata.stocks failed for %s: %s", symbol, exc)

    if not quote_row and last_bar is None:
        return None

    price = _clean(quote_row.get("price"))
    if price is None and last_bar is not None:
        price = last_bar["close"]

    return {
        "symbol": symbol,
        "price": price,
        "change_pct": _clean(quote_row.get("change_pct")),
        "change_1y_pct": _clean(quote_row.get("change_1y_pct")),
        "pe_ratio": _clean(quote_row.get("pe_ratio")),
        "dividend_yield": _clean(quote_row.get("dividend_yield")),
        "volume_avg_30d": _clean(quote_row.get("volume_avg_30d")),
        "day_open": last_bar["open"] if last_bar else None,
        "day_high": last_bar["high"] if last_bar else None,
        "day_low": last_bar["low"] if last_bar else None,
        "day_close": last_bar["close"] if last_bar else None,
        "volume": last_bar["volume"] if last_bar else None,
        "as_of_date": last_bar["date"] if last_bar else None,
        # Not available from psxdata — left explicit rather than fabricated.
        "circuit_upper": None,
        "circuit_lower": None,
    }


def fetch_live_snapshots(companies: list[dict[str, str]] = FERTILIZER_SECTOR_COMPANIES) -> list[dict]:
    """Fetches each symbol independently so one bad/suspended ticker doesn't fail the whole batch.

    Runs the (blocking, network-bound) per-symbol fetches concurrently -- psxdata scrapes PSX's
    own site with no SLA, and each fetch_live_snapshot call makes two sequential HTTP round
    trips (quote + recent bars); observed serially taking 90+ seconds for all 7 pilot companies
    on a slow day, which made every page that shows live prices (the dashboard first among them)
    look broken rather than just slow. A thread pool is enough here since these are I/O-bound
    calls, not CPU-bound work.
    """
    with ThreadPoolExecutor(max_workers=len(companies)) as pool:
        snapshots = list(pool.map(lambda c: fetch_live_snapshot(c["symbol"]), companies))

    results = []
    for company, snapshot in zip(companies, snapshots):
        if snapshot is None:
            logger.info("No live data available for %s, skipping", company["symbol"])
            continue
        snapshot["name"] = company["name"]
        results.append(snapshot)
    return results
