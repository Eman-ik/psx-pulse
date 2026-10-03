"""Technical Calculator — Compute technical indicators from price history.

Calculates:
- Support/resistance levels (52-week high/low)
- Trend detection (uptrend/downtrend/consolidation)
- Trend strength (0-100%)
- Average volume metrics
- Price momentum

Input: List of OHLCV records
Output: TechnicalIndicators (ready for StockSnapshot)
"""

import logging
from typing import Optional, List, Dict, Any
from statistics import mean, stdev
from datetime import datetime, timedelta

from app.schemas.stock_snapshot import TechnicalIndicators

logger = logging.getLogger(__name__)


class TechnicalCalculator:
    """Compute technical indicators from price history."""

    @staticmethod
    def calculate(
        ticker: str,
        price_history: List[Dict[str, Any]]
    ) -> Optional[TechnicalIndicators]:
        """Calculate all technical indicators from price history.

        Args:
            ticker: Stock ticker for logging
            price_history: List of OHLCV dicts with keys:
                          date, open, high, low, close, volume

        Returns:
            TechnicalIndicators with all computed values
        """
        if not price_history or len(price_history) < 2:
            logger.warning(f"Insufficient price history for {ticker}: {len(price_history)} records")
            return None

        try:
            # Extract prices and volumes
            closes = [p.get("close") for p in price_history if p.get("close")]
            highs = [p.get("high") for p in price_history if p.get("high")]
            lows = [p.get("low") for p in price_history if p.get("low")]
            volumes = [p.get("volume") for p in price_history if p.get("volume")]

            if not closes or not volumes:
                logger.warning(f"Missing price data for {ticker}")
                return None

            current_price = closes[-1]
            support_52w = min(lows) if lows else None
            resistance_52w = max(highs) if highs else None

            # Trend detection
            trend, trend_strength = TechnicalCalculator._detect_trend(closes)

            # Average volume (last 30 trading days ≈ 21-22 days, use available)
            avg_volume = TechnicalCalculator._calculate_avg_volume(volumes)

            indicators = TechnicalIndicators(
                support_52w_low=support_52w,
                resistance_52w_high=resistance_52w,
                current_price=current_price,
                avg_volume_30d=int(avg_volume) if avg_volume else None,
                trend=trend,
                trend_strength=trend_strength,
            )

            logger.debug(
                f"{ticker}: trend={trend} ({trend_strength}%), "
                f"support={support_52w:.2f}, resistance={resistance_52w:.2f}"
            )
            return indicators

        except Exception as e:
            logger.error(f"Error calculating technicals for {ticker}: {e}")
            return None

    @staticmethod
    def _detect_trend(closes: List[float]) -> tuple[Optional[str], Optional[float]]:
        """Detect trend direction and strength.

        Algorithm:
        - Split into recent (last 20%) and older (prior 80%)
        - Compare average price movement
        - Trend strength: how consistently the direction holds (0-100%)

        Args:
            closes: List of closing prices (chronological order)

        Returns:
            (trend_name, trend_strength_percent)
            where trend_name in ["uptrend", "downtrend", "consolidation"]
        """
        if len(closes) < 5:
            return None, None

        # Recent vs historical average
        split_idx = max(1, len(closes) // 5)
        recent_avg = mean(closes[-split_idx:])
        historical_avg = mean(closes[:-split_idx]) if len(closes) > split_idx else closes[0]

        change_pct = ((recent_avg - historical_avg) / historical_avg * 100) if historical_avg else 0

        # Determine trend type
        if abs(change_pct) < 2:
            trend = "consolidation"
            strength = 0.0
        elif change_pct > 2:
            trend = "uptrend"
            strength = min(100.0, change_pct * 10)  # Scale: 2% change → 20% strength
        else:
            trend = "downtrend"
            strength = min(100.0, abs(change_pct) * 10)

        # Consistency check: how often does direction hold?
        if len(closes) >= 10:
            consistency = TechnicalCalculator._trend_consistency(closes[-10:], trend)
            strength = (strength + consistency) / 2

        return trend, round(strength, 1)

    @staticmethod
    def _trend_consistency(recent_closes: List[float], trend: str) -> float:
        """Assess how consistently the trend holds over recent period.

        Args:
            recent_closes: Last ~10 closing prices
            trend: Direction we're checking ("uptrend" or "downtrend")

        Returns:
            Consistency score (0-100%)
        """
        if len(recent_closes) < 3:
            return 50.0

        consistent_moves = 0
        for i in range(1, len(recent_closes)):
            prev_price = recent_closes[i - 1]
            curr_price = recent_closes[i]

            if trend == "uptrend" and curr_price > prev_price:
                consistent_moves += 1
            elif trend == "downtrend" and curr_price < prev_price:
                consistent_moves += 1

        return (consistent_moves / len(recent_closes)) * 100

    @staticmethod
    def _calculate_avg_volume(volumes: List[float]) -> Optional[float]:
        """Calculate average trading volume.

        Uses recent 20 trading days if available, falls back to all data.

        Args:
            volumes: List of trading volumes

        Returns:
            Average volume or None
        """
        if not volumes:
            return None

        # Prefer recent 20 days
        recent_count = min(20, len(volumes))
        return mean(volumes[-recent_count:])

    @staticmethod
    def distance_from_support(current: float, support: float) -> Optional[float]:
        """Calculate distance from support level as percentage.

        Args:
            current: Current price
            support: Support level

        Returns:
            Distance as percentage or None if support > current
        """
        if support is None or current is None or support >= current:
            return None
        return ((current - support) / support) * 100

    @staticmethod
    def distance_from_resistance(current: float, resistance: float) -> Optional[float]:
        """Calculate distance from resistance level as percentage.

        Args:
            current: Current price
            resistance: Resistance level

        Returns:
            Distance as percentage or None if resistance < current
        """
        if resistance is None or current is None or resistance <= current:
            return None
        return ((resistance - current) / resistance) * 100
