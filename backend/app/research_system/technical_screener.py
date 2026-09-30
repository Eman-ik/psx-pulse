"""Technical screener for PSX securities."""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PriceOHLCV, Security, RatioValue, RatioDefinition


@dataclass
class TechnicalSignal:
    """A technical signal for a security."""
    symbol: str
    name: str
    sector: str
    price: float
    change_pct: float

    # Technical indicators
    price_vs_20dma: float  # % above/below 20 DMA
    price_vs_50dma: float  # % above/below 50 DMA
    price_vs_200dma: float  # % above/below 200 DMA
    rsi: Optional[float]  # RSI value (0-100)
    volume_vs_avg: float  # Current volume vs 20-day average

    # Signals
    above_200dma: bool  # Price > 200 DMA
    price_near_52week_high: bool  # Within 5% of 52-week high
    price_near_52week_low: bool  # Within 5% of 52-week low
    volume_spike: bool  # Volume > 2x average

    # Score (0-100)
    technical_score: float


@dataclass
class TechnicalScreeningSession:
    """Results from a technical screening session."""
    created_at: datetime
    total_screened: int
    signals: List[TechnicalSignal]


class TechnicalScreener:
    """Technical analysis screener."""

    @staticmethod
    def calculate_moving_average(prices: List[float], period: int) -> Optional[float]:
        """Calculate simple moving average."""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return None

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def screen_security(
        db: Session,
        security: Security,
        latest_date: datetime,
    ) -> Optional[TechnicalSignal]:
        """Screen a single security for technical signals."""

        # Get latest price
        latest = db.execute(
            select(PriceOHLCV)
            .where(
                PriceOHLCV.security_id == security.id,
                PriceOHLCV.trade_date == latest_date,
            )
        ).scalar_one_or_none()

        if not latest:
            return None

        # Get historical prices (200 days for 200 DMA)
        historical = db.execute(
            select(PriceOHLCV)
            .where(PriceOHLCV.security_id == security.id)
            .order_by(PriceOHLCV.trade_date.desc())
            .limit(200)
        ).scalars().all()

        if len(historical) < 20:
            return None

        prices = [float(p.close) for p in reversed(historical)]
        volumes = [p.volume or 0 for p in reversed(historical)]

        current_price = float(latest.close)

        # Get previous close for change calculation
        if len(prices) > 1:
            prev_close = prices[-2]
            change_pct = (current_price - prev_close) / prev_close * 100
        else:
            change_pct = 0

        # Calculate moving averages
        ma_20 = TechnicalScreener.calculate_moving_average(prices, 20)
        ma_50 = TechnicalScreener.calculate_moving_average(prices, 50)
        ma_200 = TechnicalScreener.calculate_moving_average(prices, 200)

        # Calculate distances from MAs
        price_vs_20dma = ((current_price - ma_20) / ma_20 * 100) if ma_20 else 0
        price_vs_50dma = ((current_price - ma_50) / ma_50 * 100) if ma_50 else 0
        price_vs_200dma = ((current_price - ma_200) / ma_200 * 100) if ma_200 else 0

        # Calculate RSI
        rsi = TechnicalScreener.calculate_rsi(prices)

        # Volume analysis
        avg_volume = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
        volume_vs_avg = (latest.volume / avg_volume) if avg_volume > 0 else 1

        # 52-week high/low
        prices_52week = prices[-252:] if len(prices) >= 252 else prices
        high_52week = max(prices_52week)
        low_52week = min(prices_52week)

        # Signals
        above_200dma = current_price > ma_200 if ma_200 else False
        price_near_52week_high = (current_price > high_52week * 0.95) if high_52week > 0 else False
        price_near_52week_low = (current_price < low_52week * 1.05) if low_52week > 0 else False
        volume_spike = volume_vs_avg > 2.0

        # Calculate technical score (0-100)
        score = 50  # Base score

        # Price positioning (20 points)
        if above_200dma:
            score += 10
        if price_vs_50dma > 0:
            score += 5
        if price_vs_20dma > 5:
            score += 5

        # Momentum (20 points)
        if rsi and rsi < 30:
            score += 10  # Oversold
        elif rsi and rsi > 70:
            score -= 5  # Overbought

        # Volatility/Volume (20 points)
        if volume_spike:
            score += 10

        # Support/Resistance (20 points)
        if price_near_52week_low:
            score += 10  # Near support
        if price_near_52week_high:
            score += 5  # Approaching resistance

        # Trend (20 points)
        if change_pct > 2:
            score += 8
        elif change_pct < -2:
            score -= 8

        score = max(0, min(100, score))  # Clamp 0-100

        return TechnicalSignal(
            symbol=security.symbol,
            name=security.issuer.name if security.issuer else security.symbol,
            sector=security.issuer.sector.name if security.issuer and security.issuer.sector else "UNKNOWN",
            price=current_price,
            change_pct=change_pct,
            price_vs_20dma=price_vs_20dma,
            price_vs_50dma=price_vs_50dma,
            price_vs_200dma=price_vs_200dma,
            rsi=rsi,
            volume_vs_avg=volume_vs_avg,
            above_200dma=above_200dma,
            price_near_52week_high=price_near_52week_high,
            price_near_52week_low=price_near_52week_low,
            volume_spike=volume_spike,
            technical_score=score,
        )

    @staticmethod
    def run_screening(db: Session) -> TechnicalScreeningSession:
        """Run technical screening on all active securities."""

        # Get latest trading date
        from sqlalchemy import func
        latest_date = db.execute(
            select(func.max(PriceOHLCV.trade_date))
        ).scalar()

        if not latest_date:
            return TechnicalScreeningSession(
                created_at=datetime.utcnow(),
                total_screened=0,
                signals=[],
            )

        # Get all active securities
        securities = db.execute(
            select(Security).where(Security.is_active.is_(True))
        ).scalars().all()

        signals = []
        for security in securities:
            signal = TechnicalScreener.screen_security(db, security, latest_date)
            if signal:
                signals.append(signal)

        # Sort by technical score descending
        signals.sort(key=lambda x: x.technical_score, reverse=True)

        return TechnicalScreeningSession(
            created_at=datetime.utcnow(),
            total_screened=len(securities),
            signals=signals,
        )
