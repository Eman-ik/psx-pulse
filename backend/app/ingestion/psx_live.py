"""Live-ish market data for the Fertilizer sector pilot, sourced from the psxdata library.

psxdata (https://github.com/mtauha/psxdata) scrapes PSX's own public site — no API key,
but also no SLA and no license beyond what's implied by pulling from dps.psx.com.pk directly.
See docs/source_registry.yaml. This module intentionally never claims a licensed real-time
feed: prices reflect the most recent session psxdata can see, which may be the prior trading
day outside market hours or on weekends.

Finnhub was evaluated first and dropped — it does not cover PSX-listed securities at all.
"""

import logging
from datetime import date, timedelta

import psxdata

logger = logging.getLogger(__name__)

# PSX's own "FERTILIZER" sector classification, confirmed via psxdata.symbols() on 2026-07-26.
# AGLNCPS (Agritech non-voting preference shares) is a second security under the AGL issuer
# and is intentionally left out of this live-quote list; it belongs in the full identity-master
# ingestion (Milestone 2), not this quick live-pricing slice. Reconcile this list periodically
# against psxdata.symbols() — PSX sector membership does change (e.g. FFBL was historically
# expected to be amalgamated into FFC; as of this check it is still listed separately).
FERTILIZER_SECTOR_COMPANIES: list[dict[str, str]] = [
    {"symbol": "FFC", "name": "Fauji Fertilizer Company Limited"},
    {"symbol": "EFERT", "name": "Engro Fertilizers Limited"},
    {"symbol": "FATIMA", "name": "Fatima Fertilizer Company Limited"},
    {"symbol": "FFBL", "name": "Fauji Fertilizer Bin Qasim Limited"},
    {"symbol": "ENGRO", "name": "Engro Corporation Limited"},
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
    """Fetches each symbol independently so one bad/suspended ticker doesn't fail the whole batch."""
    results = []
    for company in companies:
        snapshot = fetch_live_snapshot(company["symbol"])
        if snapshot is None:
            logger.info("No live data available for %s, skipping", company["symbol"])
            continue
        snapshot["name"] = company["name"]
        results.append(snapshot)
    return results
