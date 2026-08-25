from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.db.models import CorporateAction, IndexOHLCV, MarketIndex, PriceOHLCV
from app.etl.price_adjustment import apply_adjustment
from app.etl.sector_index import compute_fertix

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/{security_id}/prices")
def list_prices(
    security_id: int,
    start: date | None = None,
    end: date | None = None,
    adjusted: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    settings = get_settings()
    stmt = select(PriceOHLCV).where(PriceOHLCV.security_id == security_id)
    if start:
        stmt = stmt.where(PriceOHLCV.trade_date >= start)
    if end:
        stmt = stmt.where(PriceOHLCV.trade_date <= end)
    bars = db.execute(stmt.order_by(PriceOHLCV.trade_date)).scalars().all()

    if not adjusted:
        return {
            "adjusted": False,
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

    actions = db.execute(
        select(CorporateAction).where(CorporateAction.security_id == security_id)
    ).scalars().all()
    unverified_count = sum(1 for a in actions if not a.verified)
    return {
        "adjusted": True,
        "adjustment_methodology": (
            "Backward-adjusted for cash dividends (PSX PKR_PCT convention, PKR 10 face value) "
            "and splits/bonus/rights issues (see app/etl/price_adjustment.py for the exact "
            "formula and what it deliberately skips). "
            + (
                f"{unverified_count} of {len(actions)} corporate action(s) on file for this "
                "security are unverified — detected algorithmically from a real price "
                "discontinuity a fresh re-scrape confirmed, but not yet cross-checked against "
                "an actual PSX announcement."
                if unverified_count
                else ""
            )
        ),
        "corporate_actions_on_file": len(actions),
        "unverified_corporate_actions": unverified_count,
        "delayed_data_notice": settings.data_delay_disclaimer,
        "bars": apply_adjustment(bars, actions),
    }


@router.get("/index/{code}/prices")
def list_index_prices(
    code: str,
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
) -> dict | None:
    settings = get_settings()
    index = db.execute(select(MarketIndex).where(MarketIndex.code == code)).scalar_one_or_none()
    if index is None:
        return None
    stmt = select(IndexOHLCV).where(IndexOHLCV.market_index_id == index.id)
    if start:
        stmt = stmt.where(IndexOHLCV.trade_date >= start)
    if end:
        stmt = stmt.where(IndexOHLCV.trade_date <= end)
    bars = db.execute(stmt.order_by(IndexOHLCV.trade_date)).scalars().all()
    return {
        "code": index.code,
        "name": index.name,
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
