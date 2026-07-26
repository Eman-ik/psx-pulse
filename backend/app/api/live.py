from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.ingestion.psx_live import FERTILIZER_SECTOR_COMPANIES, fetch_live_snapshots

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/live")
def live_quotes() -> dict:
    """Live-ish quotes for the Fertilizer sector pilot universe, via psxdata (see docs/source_registry.yaml).

    Not a licensed real-time feed — reflects the most recent session psxdata can see.
    """
    settings = get_settings()
    quotes = fetch_live_snapshots(FERTILIZER_SECTOR_COMPANIES)
    return {
        "data_source": "psxdata (unofficial PSX scraper, no license/SLA)",
        "disclaimer": settings.data_delay_disclaimer,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "quotes": quotes,
    }
