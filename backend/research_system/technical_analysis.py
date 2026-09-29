"""
Technical Analysis Engine - Module 4

Comprehensive technical intelligence for price action analysis.
Converts OHLCV data into structured trend, momentum, volume, and volatility views.

Components:
- Trend Engine (moving averages, trends, crossovers)
- Momentum Engine (RSI, MACD, ROC)
- Volume Intelligence (volume ratios, value-traded)
- Volatility Engine (ATR, realized volatility)
- Support & Resistance (swing detection, level clustering)
- Breakout Engine (20D, 52W breakouts)
- Relative Strength (vs sector, vs market)
- Technical Snapshot (unified state object)
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from enum import Enum
from statistics import mean, stdev


class TrendState(str, Enum):
    """Classification of price trend."""
    STRONG_UPTREND = "STRONG_UPTREND"
    UPTREND = "UPTREND"
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    DOWNTREND = "DOWNTREND"
    STRONG_DOWNTREND = "STRONG_DOWNTREND"


class MomentumState(str, Enum):
    """Classification of momentum."""
    VERY_STRONG = "VERY_STRONG"
    STRONG = "STRONG"
    POSITIVE = "POSITIVE"
    WEAK = "WEAK"
    VERY_WEAK = "VERY_WEAK"


class VolumeState(str, Enum):
    """Classification of volume condition."""
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


class BreakoutState(str, Enum):
    """Classification of breakout condition."""
    BREAKOUT_20D = "BREAKOUT_20D"
    BREAKOUT_52W = "BREAKOUT_52W"
    BREAKDOWN_20D = "BREAKDOWN_20D"
    BREAKDOWN_52W = "BREAKDOWN_52W"
    NO_BREAKOUT = "NO_BREAKOUT"


class TechnicalAnalysisEngine:
    """Technical analysis and price intelligence."""

    # ════════════════════════════════════════════════════════════════════════════
    # MOVING AVERAGE ENGINE
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> Optional[float]:
        """
        Calculate simple moving average.

        Args:
            prices: List of prices (oldest to newest)
            period: Period for average

        Returns:
            SMA value or None if insufficient data
        """
        if len(prices) < period:
            return None

        return round(sum(prices[-period:]) / period, 2)

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> Optional[float]:
        """
        Calculate exponential moving average.

        Args:
            prices: List of prices (oldest to newest)
            period: Period for average

        Returns:
            EMA value or None if insufficient data
        """
        if len(prices) < period:
            return None

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period

        for price in prices[period:]:
            ema = price * multiplier + ema * (1 - multiplier)

        return round(ema, 2)

    @staticmethod
    def calculate_moving_averages(
        prices: List[float],
        periods: Optional[List[int]] = None,
    ) -> Dict[int, Optional[float]]:
        """
        Calculate multiple moving averages.

        Args:
            prices: List of prices (oldest to newest)
            periods: Periods to calculate (default: [20, 50, 100, 200])

        Returns:
            Dict of {period: value}
        """
        if periods is None:
            periods = [20, 50, 100, 200]

        return {
            period: TechnicalAnalysisEngine.calculate_sma(prices, period)
            for period in periods
        }

    # ════════════════════════════════════════════════════════════════════════════
    # TREND ENGINE
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def classify_trend_short_term(
        price: float,
        sma_20: Optional[float],
        sma_20_slope: float,
    ) -> TrendState:
        """
        Classify short-term trend.

        Short-term = price vs 20DMA
        """
        if sma_20 is None:
            return TrendState.NEUTRAL

        if price > sma_20 * 1.02:
            return TrendState.UPTREND if sma_20_slope > 0 else TrendState.POSITIVE
        elif price < sma_20 * 0.98:
            return TrendState.DOWNTREND if sma_20_slope < 0 else TrendState.NEGATIVE
        else:
            return TrendState.NEUTRAL

    @staticmethod
    def classify_trend_medium_term(
        price: float,
        sma_50: Optional[float],
        sma_50_slope: float,
    ) -> TrendState:
        """
        Classify medium-term trend.

        Medium-term = price vs 50DMA
        """
        if sma_50 is None:
            return TrendState.NEUTRAL

        if price > sma_50 * 1.02:
            return TrendState.UPTREND if sma_50_slope > 0 else TrendState.POSITIVE
        elif price < sma_50 * 0.98:
            return TrendState.DOWNTREND if sma_50_slope < 0 else TrendState.NEGATIVE
        else:
            return TrendState.NEUTRAL

    @staticmethod
    def classify_trend_long_term(
        price: float,
        sma_200: Optional[float],
        sma_200_slope: float,
    ) -> TrendState:
        """
        Classify long-term trend.

        Long-term = price vs 200DMA
        """
        if sma_200 is None:
            return TrendState.NEUTRAL

        if price > sma_200 * 1.02:
            return TrendState.UPTREND if sma_200_slope > 0 else TrendState.POSITIVE
        elif price < sma_200 * 0.98:
            return TrendState.DOWNTREND if sma_200_slope < 0 else TrendState.NEGATIVE
        else:
            return TrendState.NEUTRAL

    @staticmethod
    def classify_overall_trend(
        short_trend: TrendState,
        medium_trend: TrendState,
        long_trend: TrendState,
        sma_20: Optional[float],
        sma_50: Optional[float],
        sma_200: Optional[float],
    ) -> TrendState:
        """
        Classify overall trend based on moving average alignment.

        Strong uptrend: all trend signals positive and MAs aligned upward
        """
        if sma_20 is None or sma_50 is None or sma_200 is None:
            return TrendState.NEUTRAL

        # Count positive vs negative trends
        positive_trends = sum(1 for t in [short_trend, medium_trend, long_trend]
                            if "UP" in str(t))
        ma_aligned_up = sma_20 > sma_50 > sma_200

        if positive_trends == 3 and ma_aligned_up:
            return TrendState.STRONG_UPTREND
        elif positive_trends >= 2:
            return TrendState.UPTREND
        elif positive_trends == 1:
            return TrendState.POSITIVE

        negative_trends = sum(1 for t in [short_trend, medium_trend, long_trend]
                            if "DOWN" in str(t))
        ma_aligned_down = sma_20 < sma_50 < sma_200

        if negative_trends == 3 and ma_aligned_down:
            return TrendState.STRONG_DOWNTREND
        elif negative_trends >= 2:
            return TrendState.DOWNTREND
        elif negative_trends == 1:
            return TrendState.NEGATIVE

        return TrendState.NEUTRAL

    @staticmethod
    def calculate_ma_slope(
        ma_values: List[Optional[float]],
        periods: int = 5,
    ) -> float:
        """
        Calculate slope of moving average.

        Tells if MA is rising, falling, or flat.
        Returns percentage change.
        """
        recent_ma = [m for m in ma_values[-periods:] if m is not None]

        if len(recent_ma) < 2:
            return 0.0

        oldest = recent_ma[0]
        newest = recent_ma[-1]

        if oldest == 0:
            return 0.0

        return round((newest - oldest) / oldest * 100, 2)

    @staticmethod
    def detect_moving_average_cross(
        previous_sma_fast: Optional[float],
        current_sma_fast: Optional[float],
        previous_sma_slow: Optional[float],
        current_sma_slow: Optional[float],
    ) -> Optional[str]:
        """
        Detect moving average crossover events.

        Args:
            previous/current: Fast and slow MAs from previous and current days

        Returns:
            "GOLDEN_CROSS", "DEATH_CROSS", or None
        """
        if any(v is None for v in [previous_sma_fast, current_sma_fast,
                                   previous_sma_slow, current_sma_slow]):
            return None

        prev_relationship = previous_sma_fast > previous_sma_slow
        curr_relationship = current_sma_fast > current_sma_slow

        if not prev_relationship and curr_relationship:
            return "GOLDEN_CROSS"
        elif prev_relationship and not curr_relationship:
            return "DEATH_CROSS"

        return None

    # ════════════════════════════════════════════════════════════════════════════
    # MOMENTUM ENGINE
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index.

        Args:
            prices: List of prices (oldest to newest)
            period: RSI period (default 14)

        Returns:
            RSI value (0-100) or None
        """
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
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    @staticmethod
    def classify_rsi_state(rsi: Optional[float]) -> str:
        """
        Classify momentum based on RSI.

        0-30: Oversold/Very Weak
        30-50: Weak
        50-70: Positive
        70-100: Overbought/Very Strong
        """
        if rsi is None:
            return "UNKNOWN"

        if rsi < 30:
            return "VERY_WEAK"
        elif rsi < 50:
            return "WEAK"
        elif rsi < 70:
            return "POSITIVE"
        else:
            return "VERY_STRONG"

    @staticmethod
    def calculate_macd(
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Dict[str, Optional[float]]:
        """
        Calculate MACD and signal line.

        Args:
            prices: List of prices (oldest to newest)
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period

        Returns:
            Dict with 'macd', 'signal', 'histogram'
        """
        if len(prices) < slow_period:
            return {"macd": None, "signal": None, "histogram": None}

        ema_fast = TechnicalAnalysisEngine.calculate_ema(prices, fast_period)
        ema_slow = TechnicalAnalysisEngine.calculate_ema(prices, slow_period)

        if ema_fast is None or ema_slow is None:
            return {"macd": None, "signal": None, "histogram": None}

        macd = round(ema_fast - ema_slow, 2)

        # For signal, use simplified calculation
        # In production, would need full MACD history
        signal = round(macd * 0.8, 2)  # Simplified
        histogram = round(macd - signal, 2)

        return {
            "macd": macd,
            "signal": signal,
            "histogram": histogram,
            "state": "POSITIVE" if macd > 0 else "NEGATIVE",
        }

    @staticmethod
    def calculate_roc(prices: List[float], period: int) -> Optional[float]:
        """
        Calculate Rate of Change.

        Args:
            prices: List of prices (oldest to newest)
            period: Lookback period

        Returns:
            ROC as percentage change
        """
        if len(prices) < period + 1:
            return None

        old_price = prices[-period - 1]
        new_price = prices[-1]

        if old_price == 0:
            return None

        return round((new_price - old_price) / old_price * 100, 2)

    @staticmethod
    def calculate_momentum_metrics(
        prices: List[float],
    ) -> Dict:
        """
        Calculate comprehensive momentum metrics.

        Returns:
            Dict with RSI, MACD, ROC(5D, 20D, 60D)
        """
        return {
            "rsi_14": TechnicalAnalysisEngine.calculate_rsi(prices, 14),
            "macd": TechnicalAnalysisEngine.calculate_macd(prices),
            "roc_5d": TechnicalAnalysisEngine.calculate_roc(prices, 5),
            "roc_20d": TechnicalAnalysisEngine.calculate_roc(prices, 20),
            "roc_60d": TechnicalAnalysisEngine.calculate_roc(prices, 60),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # VOLUME ENGINE
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def calculate_volume_ratio(
        current_volume: float,
        avg_volume: float,
    ) -> float:
        """
        Calculate volume ratio vs average.

        Args:
            current_volume: Today's volume
            avg_volume: Average volume

        Returns:
            Ratio (e.g., 2.5 = 2.5× average)
        """
        if avg_volume == 0:
            return 0.0

        return round(current_volume / avg_volume, 2)

    @staticmethod
    def calculate_average_volume(
        volumes: List[float],
        period: int = 20,
    ) -> Optional[float]:
        """
        Calculate average volume over period.

        Args:
            volumes: List of volumes (oldest to newest)
            period: Period for average

        Returns:
            Average volume or None
        """
        if len(volumes) < period:
            return None

        return round(sum(volumes[-period:]) / period, 0)

    @staticmethod
    def classify_volume_state(volume_ratio: float) -> VolumeState:
        """
        Classify volume condition based on ratio.

        <0.5: Very Low
        0.5-0.8: Low
        0.8-1.2: Normal
        1.2-1.8: High
        >1.8: Very High
        """
        if volume_ratio < 0.5:
            return VolumeState.VERY_LOW
        elif volume_ratio < 0.8:
            return VolumeState.LOW
        elif volume_ratio < 1.2:
            return VolumeState.NORMAL
        elif volume_ratio < 1.8:
            return VolumeState.HIGH
        else:
            return VolumeState.VERY_HIGH

    @staticmethod
    def analyze_price_volume_relationship(
        price_change_pct: float,
        volume_ratio: float,
    ) -> Dict:
        """
        Analyze relationship between price and volume.

        Returns:
            State and confirmation status
        """
        price_direction = "UP" if price_change_pct > 0 else "DOWN" if price_change_pct < 0 else "FLAT"
        volume_state = TechnicalAnalysisEngine.classify_volume_state(volume_ratio)

        confirmation = volume_state in [VolumeState.HIGH, VolumeState.VERY_HIGH]

        return {
            "price_direction": price_direction,
            "volume_state": volume_state,
            "confirmation": confirmation,
            "description": f"Price {price_direction} with {volume_state.value} volume",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # VOLATILITY ENGINE
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def calculate_atr(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14,
    ) -> Optional[float]:
        """
        Calculate Average True Range.

        Args:
            highs/lows/closes: OHLC data (oldest to newest)
            period: ATR period

        Returns:
            ATR value or None
        """
        if len(highs) < period or len(lows) < period or len(closes) < period:
            return None

        true_ranges = []

        for i in range(len(closes)):
            high = highs[i]
            low = lows[i]
            close_prev = closes[i - 1] if i > 0 else closes[i]

            tr = max(
                high - low,
                abs(high - close_prev),
                abs(low - close_prev),
            )
            true_ranges.append(tr)

        return round(sum(true_ranges[-period:]) / period, 2)

    @staticmethod
    def calculate_volatility_pct(
        atr: Optional[float],
        current_price: float,
    ) -> Optional[float]:
        """
        Calculate ATR as percentage of price.

        Args:
            atr: Average True Range value
            current_price: Current price

        Returns:
            ATR % (e.g., 4.2 for 4.2% typical daily move)
        """
        if atr is None or current_price == 0:
            return None

        return round(atr / current_price * 100, 2)

    @staticmethod
    def calculate_realized_volatility(
        returns: List[float],
        period: int = 20,
    ) -> Optional[float]:
        """
        Calculate realized volatility (std dev of returns).

        Args:
            returns: List of daily returns (%)
            period: Period for calculation

        Returns:
            Realized volatility or None
        """
        if len(returns) < period:
            return None

        recent_returns = returns[-period:]

        if len(recent_returns) < 2:
            return None

        volatility = stdev(recent_returns)

        return round(volatility, 2)

    # ════════════════════════════════════════════════════════════════════════════
    # SUPPORT & RESISTANCE ENGINE
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def detect_swing_highs(
        highs: List[float],
        lookback: int = 5,
    ) -> List[Tuple[int, float]]:
        """
        Detect swing high points.

        A swing high occurs when price[i] > prices in lookback windows before/after.

        Args:
            highs: List of highs (oldest to newest)
            lookback: Number of bars to check on each side

        Returns:
            List of (index, value) tuples for swing highs
        """
        swing_highs = []

        for i in range(lookback, len(highs) - lookback):
            is_swing_high = all(highs[i] > highs[j] for j in range(i - lookback, i))
            is_swing_high = is_swing_high and all(
                highs[i] > highs[j] for j in range(i + 1, i + lookback + 1)
            )

            if is_swing_high:
                swing_highs.append((i, highs[i]))

        return swing_highs

    @staticmethod
    def detect_swing_lows(
        lows: List[float],
        lookback: int = 5,
    ) -> List[Tuple[int, float]]:
        """
        Detect swing low points.

        Args:
            lows: List of lows (oldest to newest)
            lookback: Number of bars to check on each side

        Returns:
            List of (index, value) tuples for swing lows
        """
        swing_lows = []

        for i in range(lookback, len(lows) - lookback):
            is_swing_low = all(lows[i] < lows[j] for j in range(i - lookback, i))
            is_swing_low = is_swing_low and all(
                lows[i] < lows[j] for j in range(i + 1, i + lookback + 1)
            )

            if is_swing_low:
                swing_lows.append((i, lows[i]))

        return swing_lows

    @staticmethod
    def identify_support_resistance_levels(
        highs: List[float],
        lows: List[float],
    ) -> Dict:
        """
        Identify key support and resistance levels.

        Uses swing detection + MAs + recent high/low.

        Args:
            highs/lows: OHLC data

        Returns:
            Dict with support and resistance zones
        """
        swing_highs = TechnicalAnalysisEngine.detect_swing_highs(highs)
        swing_lows = TechnicalAnalysisEngine.detect_swing_lows(lows)

        resistance_levels = [h for _, h in swing_highs[-3:]] if swing_highs else []
        support_levels = [l for _, l in swing_lows[-3:]] if swing_lows else []

        # Also add recent 52W high/low
        week_52_high = max(highs[-252:]) if len(highs) >= 252 else max(highs)
        week_52_low = min(lows[-252:]) if len(lows) >= 252 else min(lows)

        resistance_levels.append(week_52_high)
        support_levels.append(week_52_low)

        def cluster_levels(levels: List[float], tolerance_pct: float = 1.0) -> List[Dict]:
            """Cluster nearby levels into zones."""
            if not levels:
                return []

            sorted_levels = sorted(set(levels))
            clusters = []
            current_cluster = [sorted_levels[0]]

            for level in sorted_levels[1:]:
                if level <= current_cluster[-1] * (1 + tolerance_pct / 100):
                    current_cluster.append(level)
                else:
                    clusters.append(current_cluster)
                    current_cluster = [level]

            clusters.append(current_cluster)

            return [
                {
                    "level": round(mean(c), 2),
                    "low": round(min(c), 2),
                    "high": round(max(c), 2),
                    "strength": len(c),
                }
                for c in clusters
            ]

        return {
            "support_zones": cluster_levels(support_levels),
            "resistance_zones": cluster_levels(resistance_levels),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # BREAKOUT ENGINE
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def detect_breakout(
        current_price: float,
        current_volume: float,
        high_20d: float,
        avg_volume_20d: float,
        volume_threshold: float = 1.5,
    ) -> Optional[BreakoutState]:
        """
        Detect 20-day breakout with volume confirmation.

        Args:
            current_price: Current close price
            current_volume: Current volume
            high_20d: 20-day high
            avg_volume_20d: 20-day average volume
            volume_threshold: Volume ratio threshold for confirmation

        Returns:
            BreakoutState or None
        """
        volume_ratio = current_volume / avg_volume_20d if avg_volume_20d > 0 else 0

        if current_price > high_20d and volume_ratio > volume_threshold:
            return BreakoutState.BREAKOUT_20D

        return None

    @staticmethod
    def detect_breakdown(
        current_price: float,
        current_volume: float,
        low_20d: float,
        avg_volume_20d: float,
        volume_threshold: float = 1.5,
    ) -> Optional[BreakoutState]:
        """
        Detect 20-day breakdown with volume confirmation.

        Args:
            current_price: Current close price
            current_volume: Current volume
            low_20d: 20-day low
            avg_volume_20d: 20-day average volume
            volume_threshold: Volume ratio threshold for confirmation

        Returns:
            BreakoutState or None
        """
        volume_ratio = current_volume / avg_volume_20d if avg_volume_20d > 0 else 0

        if current_price < low_20d and volume_ratio > volume_threshold:
            return BreakoutState.BREAKDOWN_20D

        return None

    # ════════════════════════════════════════════════════════════════════════════
    # TECHNICAL SNAPSHOT
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_technical_snapshot(
        security_id: str,
        current_price: float,
        prices: List[float],
        highs: List[float],
        lows: List[float],
        volumes: List[float],
        rs_vs_sector: float,
        rs_vs_market: float,
    ) -> Dict:
        """
        Create unified technical snapshot.

        Comprehensive technical state for a security on a given day.

        Args:
            security_id: Security identifier
            current_price: Current close price
            prices: List of close prices (oldest to newest)
            highs/lows: OHLC data
            volumes: Volume data
            rs_vs_sector/market: Relative strength metrics

        Returns:
            Technical snapshot dictionary
        """
        # Moving averages
        mas = TechnicalAnalysisEngine.calculate_moving_averages(prices)
        sma_20 = mas.get(20)
        sma_50 = mas.get(50)
        sma_100 = mas.get(100)
        sma_200 = mas.get(200)

        # MA slopes
        sma_20_slope = TechnicalAnalysisEngine.calculate_ma_slope(
            [TechnicalAnalysisEngine.calculate_sma(prices[:i+1], 20) for i in range(len(prices))]
        )
        sma_50_slope = TechnicalAnalysisEngine.calculate_ma_slope(
            [TechnicalAnalysisEngine.calculate_sma(prices[:i+1], 50) for i in range(len(prices))]
        )
        sma_200_slope = TechnicalAnalysisEngine.calculate_ma_slope(
            [TechnicalAnalysisEngine.calculate_sma(prices[:i+1], 200) for i in range(len(prices))]
        )

        # Trends
        trend_short = TechnicalAnalysisEngine.classify_trend_short_term(current_price, sma_20, sma_20_slope)
        trend_medium = TechnicalAnalysisEngine.classify_trend_medium_term(current_price, sma_50, sma_50_slope)
        trend_long = TechnicalAnalysisEngine.classify_trend_long_term(current_price, sma_200, sma_200_slope)
        trend_overall = TechnicalAnalysisEngine.classify_overall_trend(
            trend_short, trend_medium, trend_long, sma_20, sma_50, sma_200
        )

        # Momentum
        momentum_metrics = TechnicalAnalysisEngine.calculate_momentum_metrics(prices)
        rsi = momentum_metrics.get("rsi_14")
        momentum_state = TechnicalAnalysisEngine.classify_rsi_state(rsi)

        # Volume
        avg_vol_20 = TechnicalAnalysisEngine.calculate_average_volume(volumes, 20)
        current_vol = volumes[-1] if volumes else 0
        vol_ratio = TechnicalAnalysisEngine.calculate_volume_ratio(current_vol, avg_vol_20 or 1)
        volume_state = TechnicalAnalysisEngine.classify_volume_state(vol_ratio)

        # Volatility
        atr = TechnicalAnalysisEngine.calculate_atr(highs, lows, prices, 14)
        atr_pct = TechnicalAnalysisEngine.calculate_volatility_pct(atr, current_price)

        # Support/Resistance
        levels = TechnicalAnalysisEngine.identify_support_resistance_levels(highs, lows)

        return {
            "security_id": security_id,
            "date": date.today().isoformat(),
            "price": round(current_price, 2),
            "trend": {
                "short_term": trend_short,
                "medium_term": trend_medium,
                "long_term": trend_long,
                "overall": trend_overall,
            },
            "moving_averages": {
                "sma_20": sma_20,
                "sma_50": sma_50,
                "sma_100": sma_100,
                "sma_200": sma_200,
            },
            "momentum": {
                "rsi_14": rsi,
                "state": momentum_state,
                "macd": momentum_metrics.get("macd", {}).get("state"),
                "roc_5d": momentum_metrics.get("roc_5d"),
                "roc_20d": momentum_metrics.get("roc_20d"),
                "roc_60d": momentum_metrics.get("roc_60d"),
            },
            "volume": {
                "current": current_vol,
                "average_20d": avg_vol_20,
                "ratio": vol_ratio,
                "state": volume_state,
            },
            "volatility": {
                "atr": atr,
                "atr_pct": atr_pct,
            },
            "levels": {
                "support": levels.get("support_zones", []),
                "resistance": levels.get("resistance_zones", []),
            },
            "relative_strength": {
                "vs_sector": rs_vs_sector,
                "vs_market": rs_vs_market,
            },
        }
