from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.ingestion.psx_live import CEMENT_SECTOR_COMPANIES, FERTILIZER_SECTOR_COMPANIES, fetch_live_snapshots

router = APIRouter(prefix="/market", tags=["market"])


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
