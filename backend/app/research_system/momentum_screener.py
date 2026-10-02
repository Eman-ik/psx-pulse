"""Price-return momentum for PSX securities, computed from stored EOD closes.

Returns over different horizons are reported side by side, never averaged into one "trend"
(a 10% 1-month move and a 10% 12-month move are not the same signal). A lookback price is
used only if a bar exists within MAX_ANCHOR_GAP_DAYS before the target date; otherwise that
horizon is reported as unavailable instead of silently reaching further back.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import PriceOHLCV, Security

MAX_ANCHOR_GAP_DAYS = 7
HORIZON_DAYS = {"1m": 30, "3m": 91, "6m": 182, "12m": 365}


@dataclass
class MomentumSignal:
    symbol: str
    name: str
    sector: str
    price: float
    return_1m: Optional[float]
    return_3m: Optional[float]
    return_6m: Optional[float]
    return_12m: Optional[float]
    momentum_12_1: Optional[float]  # return from 12 months ago to 1 month ago (skips the latest month)
    unavailable: List[str] = field(default_factory=list)


@dataclass
class MomentumScreeningSession:
    created_at: datetime
    total_screened: int
    signals: List[MomentumSignal]


def _return(start: Optional[float], end: Optional[float]) -> Optional[float]:
    if start is None or end is None or start == 0:
        return None
    return (end - start) / start * 100


class MomentumScreener:
    @staticmethod
    def get_price_at_date(db: Session, security_id: int, target_date: date) -> Optional[float]:
        """Close on the last bar at or before target_date, if that bar is close enough to it."""
        bar = db.execute(
            select(PriceOHLCV)
            .where(
                PriceOHLCV.security_id == security_id,
                PriceOHLCV.trade_date <= target_date,
                PriceOHLCV.trade_date >= target_date - timedelta(days=MAX_ANCHOR_GAP_DAYS),
            )
            .order_by(PriceOHLCV.trade_date.desc())
            .limit(1)
        ).scalar_one_or_none()
        return float(bar.close) if bar else None

    @staticmethod
    def screen_security(db: Session, security: Security, latest_date: date, latest_price: float) -> Optional[MomentumSignal]:
        anchors = {
            key: MomentumScreener.get_price_at_date(db, security.id, latest_date - timedelta(days=days))
            for key, days in HORIZON_DAYS.items()
        }
        returns = {key: _return(price, latest_price) for key, price in anchors.items()}
        if all(r is None for r in returns.values()):
            return None
        return MomentumSignal(
            symbol=security.symbol,
            name=security.issuer.name if security.issuer else security.symbol,
            sector=security.issuer.sector.name if security.issuer and security.issuer.sector else "UNKNOWN",
            price=latest_price,
            return_1m=returns["1m"],
            return_3m=returns["3m"],
            return_6m=returns["6m"],
            return_12m=returns["12m"],
            momentum_12_1=_return(anchors["12m"], anchors["1m"]),
            unavailable=[key for key, r in returns.items() if r is None],
        )

    @staticmethod
    def run_screening(db: Session) -> MomentumScreeningSession:
        latest_date = db.execute(select(func.max(PriceOHLCV.trade_date))).scalar()
        securities = db.execute(select(Security).where(Security.is_active.is_(True))).scalars().all()
        signals = []
        if latest_date:
            for security in securities:
                latest = db.execute(
                    select(PriceOHLCV).where(PriceOHLCV.security_id == security.id, PriceOHLCV.trade_date == latest_date)
                ).scalar_one_or_none()
                if latest:
                    signal = MomentumScreener.screen_security(db, security, latest_date, float(latest.close))
                    if signal:
                        signals.append(signal)
        signals.sort(key=lambda s: s.symbol)
        return MomentumScreeningSession(created_at=datetime.utcnow(), total_screened=len(securities), signals=signals)
