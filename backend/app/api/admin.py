from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/flags")
def get_flags() -> dict:
    """Exposes the compliance gate flags read-only, so the frontend can show gated states honestly."""
    settings = get_settings()
    return {
        "public_launch_enabled": settings.public_launch_enabled,
        "public_signals_enabled": settings.public_signals_enabled,
        "commercial_data_enabled": settings.commercial_data_enabled,
    }
