"""Momentum screener for PSX securities."""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.models import PriceOHLCV, Security


@dataclass
class MomentumSignal:
    """A momentum signal for a security."""
    symbol: str
    name: str
    sector: str
    price: float

    # Returns over different periods
    return_1m: Optional[float]  # 1-month return %
    return_3m: Optional[float]  # 3-month return %
    return_6m: Optional[float]  # 6-month return %
    return_12m: Optional[float]  # 12-month return %

    # Momentum indicators
    momentum_score: float  # 0-100
    strongest_period: str  # Which period has best return
    trend: str  # "Strong Uptrend" | "Uptrend" | "Neutral" | "Downtrend" | "Strong Downtrend"


@dataclass
class MomentumScreeningSession:
    """Results from a momentum screening session."""
    created_at: datetime
    total_screened: int
    signals: List[MomentumSignal]


class MomentumScreener:
    """Momentum-based screener."""

    @staticmethod
    def calculate_return(start_price: float, end_price: float) -> float:
        """Calculate return percentage."""
        if start_price == 0:
            return 0
        return (end_price - start_price) / start_price * 100

    @staticmethod
    def get_price_at_date(
        db: Session,
        security_id: int,
        target_date: datetime,
    ) -> Optional[float]:
        """Get the close price at or before target date."""
        price = db.execute(
            select(PriceOHLCV)
            .where(
                PriceOHLCV.security_id == security_id,
                PriceOHLCV.trade_date <= target_date,
            )
            .order_by(PriceOHLCV.trade_date.desc())
            .limit(1)
        ).scalar_one_or_none()

        return float(price.close) if price else None

    @staticmethod
    def screen_security(
        db: Session,
        security: Security,
        latest_date: datetime,
        latest_price: float,
    ) -> Optional[MomentumSignal]:
        """Screen a single security for momentum signals."""

        # Calculate dates for lookback periods
        date_1m_ago = latest_date - timedelta(days=30)
        date_3m_ago = latest_date - timedelta(days=90)
        date_6m_ago = latest_date - timedelta(days=180)
        date_12m_ago = latest_date - timedelta(days=365)

        # Get prices at each lookback period
        price_1m_ago = MomentumScreener.get_price_at_date(db, security.id, date_1m_ago)
        price_3m_ago = MomentumScreener.get_price_at_date(db, security.id, date_3m_ago)
        price_6m_ago = MomentumScreener.get_price_at_date(db, security.id, date_6m_ago)
        price_12m_ago = MomentumScreener.get_price_at_date(db, security.id, date_12m_ago)

        # Calculate returns
        return_1m = MomentumScreener.calculate_return(price_1m_ago, latest_price) if price_1m_ago else None
        return_3m = MomentumScreener.calculate_return(price_3m_ago, latest_price) if price_3m_ago else None
        return_6m = MomentumScreener.calculate_return(price_6m_ago, latest_price) if price_6m_ago else None
        return_12m = MomentumScreener.calculate_return(price_12m_ago, latest_price) if price_12m_ago else None

        # Need at least one valid return
        if not any([return_1m, return_3m, return_6m, return_12m]):
            return None

        # Determine strongest period
        returns_with_period = [
            (return_1m, "1M") if return_1m else None,
            (return_3m, "3M") if return_3m else None,
            (return_6m, "6M") if return_6m else None,
            (return_12m, "12M") if return_12m else None,
        ]
        returns_with_period = [x for x in returns_with_period if x is not None]
        strongest_period = max(returns_with_period, key=lambda x: x[0])[1] if returns_with_period else "N/A"

        # Calculate momentum score (0-100)
        momentum_score = 50  # Base score

        # Weight returns by recency: 1M > 3M > 6M > 12M
        if return_1m:
            if return_1m > 5:
                momentum_score += 15
            elif return_1m > 0:
                momentum_score += 8
            elif return_1m > -5:
                momentum_score -= 5
            else:
                momentum_score -= 15

        if return_3m:
            if return_3m > 10:
                momentum_score += 12
            elif return_3m > 0:
                momentum_score += 6
            elif return_3m > -10:
                momentum_score -= 4
            else:
                momentum_score -= 10

        if return_6m:
            if return_6m > 20:
                momentum_score += 10
            elif return_6m > 0:
                momentum_score += 5
            elif return_6m > -20:
                momentum_score -= 3
            else:
                momentum_score -= 8

        if return_12m:
            if return_12m > 30:
                momentum_score += 8
            elif return_12m > 0:
                momentum_score += 4
            elif return_12m > -30:
                momentum_score -= 2
            else:
                momentum_score -= 6

        momentum_score = max(0, min(100, momentum_score))  # Clamp 0-100

        # Determine trend
        avg_return = sum(
            r for r in [return_1m, return_3m, return_6m, return_12m] if r is not None
        ) / sum(
            1 for r in [return_1m, return_3m, return_6m, return_12m] if r is not None
        )

        if avg_return > 15:
            trend = "Strong Uptrend"
        elif avg_return > 5:
            trend = "Uptrend"
        elif avg_return > -5:
            trend = "Neutral"
        elif avg_return > -15:
            trend = "Downtrend"
        else:
            trend = "Strong Downtrend"

        return MomentumSignal(
            symbol=security.symbol,
            name=security.issuer.name if security.issuer else security.symbol,
            sector=security.issuer.sector.name if security.issuer and security.issuer.sector else "UNKNOWN",
            price=latest_price,
            return_1m=return_1m,
            return_3m=return_3m,
            return_6m=return_6m,
            return_12m=return_12m,
            momentum_score=momentum_score,
            strongest_period=strongest_period,
            trend=trend,
        )

    @staticmethod
    def run_screening(db: Session) -> MomentumScreeningSession:
        """Run momentum screening on all active securities."""

        # Get latest trading date
        latest_date = db.execute(
            select(func.max(PriceOHLCV.trade_date))
        ).scalar()

        if not latest_date:
            return MomentumScreeningSession(
                created_at=datetime.utcnow(),
                total_screened=0,
                signals=[],
            )

        # Get all active securities with latest prices
        securities = db.execute(
            select(Security).where(Security.is_active.is_(True))
        ).scalars().all()

        signals = []
        for security in securities:
            # Get latest price
            latest = db.execute(
                select(PriceOHLCV)
                .where(
                    PriceOHLCV.security_id == security.id,
                    PriceOHLCV.trade_date == latest_date,
                )
            ).scalar_one_or_none()

            if latest:
                signal = MomentumScreener.screen_security(
                    db, security, latest_date, float(latest.close)
                )
                if signal:
                    signals.append(signal)

        # Sort by momentum score descending
        signals.sort(key=lambda x: x.momentum_score, reverse=True)

        return MomentumScreeningSession(
            created_at=datetime.utcnow(),
            total_screened=len(securities),
            signals=signals,
        )
