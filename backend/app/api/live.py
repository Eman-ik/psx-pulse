from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.ingestion.psx_live import (
    CEMENT_SECTOR_COMPANIES,
    FERTILIZER_SECTOR_COMPANIES,
    fetch_live_snapshot,
    fetch_live_snapshots,
)

router = APIRouter(prefix="/market", tags=["market"])

_ALL_PILOT_COMPANIES = FERTILIZER_SECTOR_COMPANIES + CEMENT_SECTOR_COMPANIES
_SYMBOL_TO_NAME = {c["symbol"]: c["name"] for c in _ALL_PILOT_COMPANIES}


@router.get("/live")
def live_quotes() -> dict:
    """Live-ish quotes for the Fertilizer sector pilot universe, via psxdata."""
    settings = get_settings()
    quotes = fetch_live_snapshots(FERTILIZER_SECTOR_COMPANIES)
    return {
        "data_source": "psxdata (unofficial PSX scraper, no license/SLA)",
        "disclaimer": settings.data_delay_disclaimer,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "quotes": quotes,
    }


@router.get("/live/cement")
def live_quotes_cement() -> dict:
    """Live-ish quotes for the Cement sector pilot universe, via psxdata."""
    settings = get_settings()
    quotes = fetch_live_snapshots(CEMENT_SECTOR_COMPANIES)
    return {
        "data_source": "psxdata (unofficial PSX scraper, no license/SLA)",
        "disclaimer": settings.data_delay_disclaimer,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "quotes": quotes,
    }


@router.get("/live/all")
def live_quotes_all() -> dict:
    """Combined fertilizer+cement pilot universe in one call (same set GET
    /companies/comparison used to enrich server-side -- see that endpoint's docstring).
    Meant to be called client-side, after the page it feeds has already rendered with
    fast DB-only data, not awaited during SSR -- this is the slow (up to 35s), no-SLA
    scrape the async-loading rework moved off every page's critical path.
    """
    settings = get_settings()
    quotes = fetch_live_snapshots(_ALL_PILOT_COMPANIES)
    return {
        "data_source": "psxdata (unofficial PSX scraper, no license/SLA)",
        "disclaimer": settings.data_delay_disclaimer,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "quotes": quotes,
    }


@router.get("/quote/{symbol}")
def live_quote(symbol: str) -> dict:
    """Single-symbol live-ish quote, for a company page to fetch client-side without
    blocking its own (DB-only, fast) initial render -- see GET /companies/{id}/overview's
    docstring. Cached (unlike the batch endpoints above): a single sequential fetch has
    no concurrent-writer race on psxdata's on-disk cache, so there's no reason to disable it.
    """
    settings = get_settings()
    symbol = symbol.upper()
    quote = fetch_live_snapshot(symbol)
    if quote is None:
        raise HTTPException(status_code=404, detail=f"No live data available for {symbol}")
    quote["name"] = _SYMBOL_TO_NAME.get(symbol, symbol)
    return {
        "data_source": "psxdata (unofficial PSX scraper, no license/SLA)",
        "disclaimer": settings.data_delay_disclaimer,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "quote": quote,
    }
