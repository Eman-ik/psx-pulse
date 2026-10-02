"""Technical indicators for PSX securities, computed from stored EOD closes.

Deliberately no composite score: the old 0-100 blend added mean-reversion signals (near a
low, RSI < 30) to momentum signals (near a high) with uncalibrated weights, so its number had
no demonstrated relationship to returns. Each indicator is reported on its own, and any
indicator without enough history is None rather than a default that reads as a real reading.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import PriceOHLCV, Security

LOOKBACK_TARGET_DAYS = 252  # about one year of PSX trading days
NEAR_EXTREME_PCT = 5.0
VOLUME_SPIKE_MULTIPLE = 2.0


@dataclass
class TechnicalSignal:
    symbol: str
    name: str
    sector: str
    price: float
    change_pct: Optional[float]
    bars_available: int

    price_vs_20dma: Optional[float]
    price_vs_50dma: Optional[float]
    price_vs_200dma: Optional[float]
    above_20dma: Optional[bool]
    above_50dma: Optional[bool]
    above_200dma: Optional[bool]
    rsi: Optional[float]

    volume_vs_avg: Optional[float]
    volume_spike: Optional[bool]

    lookback_days: int
    lookback_complete: bool
    lookback_high: float
    lookback_low: float
    near_lookback_high: bool
    near_lookback_low: bool


@dataclass
class TechnicalScreeningSession:
    created_at: datetime
    total_screened: int
    signals: List[TechnicalSignal]


def _pct_vs(price: float, reference: Optional[float]) -> Optional[float]:
    return None if not reference else (price - reference) / reference * 100


class TechnicalScreener:
    @staticmethod
    def calculate_moving_average(prices: List[float], period: int) -> Optional[float]:
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """Simple-average RSI over the last `period` changes."""
        if len(prices) < period + 1:
            return None
        changes = [b - a for a, b in zip(prices[-period - 1:-1], prices[-period:])]
        avg_gain = sum(c for c in changes if c > 0) / period
        avg_loss = sum(-c for c in changes if c < 0) / period
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        return 100 - 100 / (1 + avg_gain / avg_loss)

    @staticmethod
    def screen_security(db: Session, security: Security, latest_date) -> Optional[TechnicalSignal]:
        historical = db.execute(
            select(PriceOHLCV)
            .where(PriceOHLCV.security_id == security.id, PriceOHLCV.trade_date <= latest_date)
            .order_by(PriceOHLCV.trade_date.desc())
            .limit(LOOKBACK_TARGET_DAYS)
        ).scalars().all()
        if not historical or historical[0].trade_date != latest_date:
            return None

        bars = list(reversed(historical))
        prices = [float(b.close) for b in bars]
        price = prices[-1]

        mas = {n: TechnicalScreener.calculate_moving_average(prices, n) for n in (20, 50, 200)}
        vs = {n: _pct_vs(price, ma) for n, ma in mas.items()}

        prior_volumes = [b.volume for b in bars[-21:-1] if b.volume is not None]
        latest_volume = bars[-1].volume
        volume_vs_avg = None
        if latest_volume is not None and len(prior_volumes) == 20 and sum(prior_volumes) > 0:
            volume_vs_avg = latest_volume / (sum(prior_volumes) / 20)

        high, low = max(prices), min(prices)
        return TechnicalSignal(
            symbol=security.symbol,
            name=security.issuer.name if security.issuer else security.symbol,
            sector=security.issuer.sector.name if security.issuer and security.issuer.sector else "UNKNOWN",
            price=price,
            change_pct=_pct_vs(price, prices[-2]) if len(prices) > 1 else None,
            bars_available=len(prices),
            price_vs_20dma=vs[20],
            price_vs_50dma=vs[50],
            price_vs_200dma=vs[200],
            above_20dma=None if vs[20] is None else vs[20] > 0,
            above_50dma=None if vs[50] is None else vs[50] > 0,
            above_200dma=None if vs[200] is None else vs[200] > 0,
            rsi=TechnicalScreener.calculate_rsi(prices),
            volume_vs_avg=volume_vs_avg,
            volume_spike=None if volume_vs_avg is None else volume_vs_avg > VOLUME_SPIKE_MULTIPLE,
            lookback_days=len(prices),
            lookback_complete=len(prices) >= LOOKBACK_TARGET_DAYS,
            lookback_high=high,
            lookback_low=low,
            near_lookback_high=price >= high * (1 - NEAR_EXTREME_PCT / 100),
            near_lookback_low=price <= low * (1 + NEAR_EXTREME_PCT / 100),
        )

    @staticmethod
    def run_screening(db: Session) -> TechnicalScreeningSession:
        latest_date = db.execute(select(func.max(PriceOHLCV.trade_date))).scalar()
        securities = db.execute(select(Security).where(Security.is_active.is_(True))).scalars().all()
        signals = []
        if latest_date:
            for security in securities:
                signal = TechnicalScreener.screen_security(db, security, latest_date)
                if signal:
                    signals.append(signal)
        signals.sort(key=lambda s: s.symbol)
        return TechnicalScreeningSession(created_at=datetime.utcnow(), total_screened=len(securities), signals=signals)
