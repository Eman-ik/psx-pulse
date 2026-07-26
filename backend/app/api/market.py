from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.db.models import PriceOHLCV

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/{security_id}/prices")
def list_prices(
    security_id: int,
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
) -> dict:
    settings = get_settings()
    stmt = select(PriceOHLCV).where(PriceOHLCV.security_id == security_id)
    if start:
        stmt = stmt.where(PriceOHLCV.trade_date >= start)
    if end:
        stmt = stmt.where(PriceOHLCV.trade_date <= end)
    bars = db.execute(stmt.order_by(PriceOHLCV.trade_date)).scalars().all()
    return {
        "delayed_data_notice": settings.data_delay_disclaimer,
        "bars": [
            {
                "date": b.trade_date.isoformat(),
                "open": float(b.open),
                "high": float(b.high),
                "low": float(b.low),
                "close": float(b.close),
                "volume": b.volume,
                "is_delayed": b.is_delayed,
            }
            for b in bars
        ],
    }
