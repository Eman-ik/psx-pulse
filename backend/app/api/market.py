from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.db.models import CorporateAction, IndexOHLCV, MarketIndex, PriceOHLCV, Security, Sector, Issuer
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


@router.get("/overview/snapshot")
def market_snapshot(db: Session = Depends(get_db)) -> dict:
    """Market overview snapshot: indices, breadth, movers, sectors."""
    settings = get_settings()

    # Get latest trading date
    latest_date = db.execute(
        select(func.max(PriceOHLCV.trade_date))
    ).scalar()

    if not latest_date:
        return {"error": "No price data available"}

    # Get index data for KSE-100, KSE-30, KMI-30
    indices_data = {}
    for code in ["KSE-100", "KSE-30", "KMI-30"]:
        index = db.execute(select(MarketIndex).where(MarketIndex.code == code)).scalar_one_or_none()
        if index:
            latest = db.execute(
                select(IndexOHLCV)
                .where(IndexOHLCV.market_index_id == index.id, IndexOHLCV.trade_date == latest_date)
            ).scalar_one_or_none()

            if latest:
                # Get previous close for change calculation
                prev = db.execute(
                    select(IndexOHLCV)
                    .where(IndexOHLCV.market_index_id == index.id, IndexOHLCV.trade_date < latest_date)
                    .order_by(desc(IndexOHLCV.trade_date))
                    .limit(1)
                ).scalar_one_or_none()

                prev_close = prev.close if prev else latest.open
                change = latest.close - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0

                indices_data[code] = {
                    "name": index.name,
                    "level": float(latest.close),
                    "change": float(change),
                    "change_pct": float(change_pct),
                    "high": float(latest.high),
                    "low": float(latest.low),
                    "volume": latest.volume,
                }

    # Get market breadth (advancers vs decliners)
    all_securities = db.execute(
        select(Security).where(Security.is_active.is_(True))
    ).scalars().all()

    advancers = 0
    decliners = 0
    unchanged = 0

    for security in all_securities:
        latest = db.execute(
            select(PriceOHLCV)
            .where(PriceOHLCV.security_id == security.id, PriceOHLCV.trade_date == latest_date)
        ).scalar_one_or_none()

        if latest:
            prev = db.execute(
                select(PriceOHLCV)
                .where(PriceOHLCV.security_id == security.id, PriceOHLCV.trade_date < latest_date)
                .order_by(desc(PriceOHLCV.trade_date))
                .limit(1)
            ).scalar_one_or_none()

            if prev:
                if latest.close > prev.close:
                    advancers += 1
                elif latest.close < prev.close:
                    decliners += 1
                else:
                    unchanged += 1

    # Get top gainers and losers
    gainers = []
    losers = []

    for security in all_securities[:50]:  # Sample for performance
        latest = db.execute(
            select(PriceOHLCV)
            .where(PriceOHLCV.security_id == security.id, PriceOHLCV.trade_date == latest_date)
        ).scalar_one_or_none()

        if latest:
            prev = db.execute(
                select(PriceOHLCV)
                .where(PriceOHLCV.security_id == security.id, PriceOHLCV.trade_date < latest_date)
                .order_by(desc(PriceOHLCV.trade_date))
                .limit(1)
            ).scalar_one_or_none()

            if prev and prev.close > 0:
                change_pct = (latest.close - prev.close) / prev.close * 100
                gainers.append({
                    "symbol": security.symbol,
                    "name": security.issuer.name if security.issuer else security.symbol,
                    "price": float(latest.close),
                    "change_pct": float(change_pct),
                    "volume": latest.volume,
                })

    gainers.sort(key=lambda x: x["change_pct"], reverse=True)
    losers = sorted(gainers, key=lambda x: x["change_pct"])[:5]
    gainers = gainers[:5]

    return {
        "timestamp": latest_date.isoformat(),
        "indices": indices_data,
        "breadth": {
            "advancers": advancers,
            "decliners": decliners,
            "unchanged": unchanged,
            "total": len(all_securities),
        },
        "gainers": gainers,
        "losers": losers,
        "data_delay_notice": settings.data_delay_disclaimer,
    }
