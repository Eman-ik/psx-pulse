"""Live-ish market data for the Fertilizer sector pilot, sourced from the psxdata library.

psxdata (https://github.com/mtauha/psxdata) scrapes PSX's own public site — no API key,
but also no SLA and no license beyond what's implied by pulling from dps.psx.com.pk directly.
See docs/source_registry.yaml. This module intentionally never claims a licensed real-time
feed: prices reflect the most recent session psxdata can see, which may be the prior trading
day outside market hours or on weekends.

Finnhub was evaluated first and dropped — it does not cover PSX-listed securities at all.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import date, timedelta

import psxdata

logger = logging.getLogger(__name__)

# psxdata exposes no request-level timeout (checked its public quote()/stocks() signatures --
# neither takes one), and a Python thread blocked on a hung socket read can't be forcibly
# cancelled. So this can only be capped at the batch level: give the whole batch this long,
# then stop waiting and return whatever completed -- the still-running threads are abandoned
# (not killed, just not waited on) rather than allowed to hang the calling request/page
# indefinitely. Real observed cost on a slow day: "90+ seconds for all 7 pilot companies" (see
# fetch_live_snapshots' docstring) -- this must stay comfortably above normal-case latency or
# it would turn "slow" into "always empty". Raised from 25 to 35 alongside the concurrency cap
# below: disabling the cache for this path (see fetch_live_snapshot's use_cache) made each
# request slower with nothing to fall back on, so a real 16-symbol concurrent run that got
# 3/16 back at cache=True got 0/16 back in 25s at cache=False -- needs real headroom to still
# be useful now that it's not silently corrupting results instead.
_LIVE_QUOTE_BATCH_TIMEOUT_S = 35

# Uncapped (one thread per company) is what caused the concurrent cache writers to race each
# other in the first place; even with caching off now, hitting a slow no-SLA public site with
# 16+ simultaneous connections is both unfriendly and more likely to get rate-limited/blocked
# by it, which would show up as this exact symptom again. Capping concurrency trades a little
# batch latency for not hammering the source.
_LIVE_QUOTE_MAX_WORKERS = 6

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

# PSX Cement sector pilot universe, confirmed via psxdata.symbols() on 2026-07-30.
# JVDCPS is Javedan Corporation Limited – Preference Shares (separate PSX listing from JVDC
# ordinary shares). All symbols verified against PSX's public sector classification.
# Reconcile periodically against psxdata.symbols() — PSX sector membership does change.
CEMENT_SECTOR_COMPANIES: list[dict[str, str]] = [
    {"symbol": "LUCK",   "name": "Lucky Cement Limited"},
    {"symbol": "MLCF",   "name": "Maple Leaf Cement Factory Limited"},
    {"symbol": "CHCC",   "name": "Cherat Cement Company Limited"},
    {"symbol": "DGKC",   "name": "D.G. Khan Cement Company Limited"},
    {"symbol": "BWCL",   "name": "Bestway Cement Limited"},
    {"symbol": "DCL",    "name": "Dewan Cement Limited"},
    {"symbol": "ACPL",   "name": "Attock Cement Pakistan Limited"},
    {"symbol": "FCCL",   "name": "Fauji Cement Company Limited"},
    {"symbol": "JVDCPS", "name": "Javedan Corporation Limited"},
    {"symbol": "GWLC",   "name": "Gharibwal Cement Limited"},
    {"symbol": "KOHC",   "name": "Kohat Cement Company Limited"},
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


def fetch_live_snapshot(symbol: str, use_cache: bool = True) -> dict | None:
    """Best-effort live-ish snapshot for one symbol. Returns None if the source has nothing.

    use_cache=False for fetch_live_snapshots' concurrent callers only (see that function):
    psxdata's on-disk parquet cache isn't safe for concurrent writers -- multiple threads
    caching different symbols at once were observed real-failing with "Parquet serialisation
    failed for key 'X_historical'" (confirmed via a direct 16-symbol concurrent run, 13/16
    failed this way). Single-symbol sequential callers (app/api/companies.py,
    app/etl/ratio_engine.py, app/etl/valuation_engine.py) keep caching -- there's no writer
    contention when only one fetch runs at a time.
    """
    try:
        quote_rows = psxdata.quote(symbol, cache=use_cache).to_dict(orient="records")
        quote_row = quote_rows[0] if quote_rows else {}
    except Exception as exc:
        logger.warning("psxdata.quote failed for %s: %s", symbol, exc)
        quote_row = {}

    last_bar: dict | None = None
    try:
        end = date.today()
        start = end - timedelta(days=14)
        bars = psxdata.stocks(symbol, start=start.isoformat(), end=end.isoformat(), cache=use_cache)
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

    Capped at _LIVE_QUOTE_BATCH_TIMEOUT_S total: symbols that haven't responded by then are
    skipped for this call (same as fetch_live_snapshot returning None) rather than left to hang
    the caller/page indefinitely -- see that constant's comment for why this can't be a per-
    request timeout instead.

    Calls fetch_live_snapshot with use_cache=False: psxdata's parquet cache isn't safe for
    concurrent writers (see that function's docstring) -- this batch is the only concurrent
    caller, so it's the only one that needs caching off.
    """
    pool = ThreadPoolExecutor(max_workers=min(len(companies), _LIVE_QUOTE_MAX_WORKERS))
    future_to_company = {
        pool.submit(fetch_live_snapshot, c["symbol"], use_cache=False): c for c in companies
    }
    done, not_done = wait(future_to_company, timeout=_LIVE_QUOTE_BATCH_TIMEOUT_S)

    if not_done:
        stuck_symbols = ", ".join(sorted(future_to_company[f]["symbol"] for f in not_done))
        logger.warning(
            "Live quote batch hit its %ss cap with %d/%d symbols still pending (%s) -- "
            "returning what completed instead of waiting further",
            _LIVE_QUOTE_BATCH_TIMEOUT_S, len(not_done), len(companies), stuck_symbols,
        )
    # wait=False: a thread stuck on a hung socket read can't be cancelled, so don't block this
    # call waiting for it to finish -- it's abandoned, not killed, and cleans up on its own
    # whenever (if ever) the underlying request returns or the process exits.
    pool.shutdown(wait=False)

    results = []
    for future in done:
        company = future_to_company[future]
        try:
            snapshot = future.result()
        except Exception as exc:
            logger.warning("Live quote fetch raised for %s, skipping: %s", company["symbol"], exc)
            continue
        if snapshot is None:
            logger.info("No live data available for %s, skipping", company["symbol"])
            continue
        snapshot["name"] = company["name"]
        results.append(snapshot)
    return results
