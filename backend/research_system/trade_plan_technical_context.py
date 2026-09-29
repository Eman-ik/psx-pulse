"""
Trade Plan Technical Context Integration - Module 6, Sprint R3

Pulls technical data from Module 4 to inform trade plan decisions.

Context provided:
- Support & resistance zones (from swing detection)
- ATR (Average True Range) for stop sizing
- Trend direction & strength
- Momentum indicators (RSI, MACD ranges)
- Volatility assessment

This module bridges technical analysis (Module 4) with trade planning (Module 6).
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal

from .technical_analysis import TechnicalAnalysisEngine, TrendState, MomentumState


# ════════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ════════════════════════════════════════════════════════════════════════════════

class SupportResistanceZone:
    """A clustered support or resistance level."""

    def __init__(self, level: float, low: float, high: float, strength: int):
        self.level = level      # Center of zone
        self.low = low          # Bottom of zone
        self.high = high        # Top of zone
        self.strength = strength  # Number of touches


class TechnicalContext:
    """Complete technical context for a security."""

    def __init__(
        self,
        ticker: str,
        current_price: float,
        # Support & Resistance
        support_zones: List[SupportResistanceZone],
        resistance_zones: List[SupportResistanceZone],
        # ATR & Volatility
        atr: Optional[float],
        atr_pct: Optional[float],
        # Trend
        trend_state: Optional[str],
        trend_strength: Optional[str],
        # Momentum
        momentum_state: Optional[str],
        rsi: Optional[float],
        macd_histogram: Optional[float],
        # Summary
        description: str,
    ):
        self.ticker = ticker
        self.current_price = current_price
        self.support_zones = support_zones
        self.resistance_zones = resistance_zones
        self.atr = atr
        self.atr_pct = atr_pct
        self.trend_state = trend_state
        self.trend_strength = trend_strength
        self.momentum_state = momentum_state
        self.rsi = rsi
        self.macd_histogram = macd_histogram
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response dict."""
        return {
            "ticker": self.ticker,
            "current_price": self.current_price,
            "support_zones": [
                {"level": z.level, "low": z.low, "high": z.high, "strength": z.strength}
                for z in self.support_zones
            ],
            "resistance_zones": [
                {"level": z.level, "low": z.low, "high": z.high, "strength": z.strength}
                for z in self.resistance_zones
            ],
            "atr": self.atr,
            "atr_pct": self.atr_pct,
            "trend": {
                "state": self.trend_state,
                "strength": self.trend_strength,
            },
            "momentum": {
                "state": self.momentum_state,
                "rsi": self.rsi,
                "macd_histogram": self.macd_histogram,
            },
            "description": self.description,
        }


# ════════════════════════════════════════════════════════════════════════════════
# TECHNICAL CONTEXT EXTRACTION
# ════════════════════════════════════════════════════════════════════════════════

class TechnicalContextExtractor:
    """Extract technical context for trade planning."""

    @staticmethod
    def extract_from_price_data(
        ticker: str,
        current_price: float,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: Optional[List[float]] = None,
        trend_state: Optional[TrendState] = None,
        momentum_state: Optional[MomentumState] = None,
        rsi: Optional[float] = None,
        macd_histogram: Optional[float] = None,
    ) -> TechnicalContext:
        """
        Extract complete technical context from OHLCV data.

        Args:
            ticker: Security ticker
            current_price: Current price
            highs: List of highs (oldest to newest)
            lows: List of lows (oldest to newest)
            closes: List of closes (oldest to newest)
            volumes: List of volumes (optional)
            trend_state: TrendState enum (optional)
            momentum_state: MomentumState enum (optional)
            rsi: RSI value (optional)
            macd_histogram: MACD histogram value (optional)

        Returns:
            TechnicalContext object
        """
        # Support & Resistance
        support_resistance = TechnicalAnalysisEngine.identify_support_resistance_levels(
            highs, lows
        )

        support_zones = [
            SupportResistanceZone(
                level=z["level"],
                low=z["low"],
                high=z["high"],
                strength=z["strength"],
            )
            for z in support_resistance.get("support_zones", [])
        ]

        resistance_zones = [
            SupportResistanceZone(
                level=z["level"],
                low=z["low"],
                high=z["high"],
                strength=z["strength"],
            )
            for z in support_resistance.get("resistance_zones", [])
        ]

        # ATR & Volatility
        atr = TechnicalAnalysisEngine.calculate_atr(highs, lows, closes, period=14)
        atr_pct = (
            TechnicalAnalysisEngine.calculate_volatility_pct(atr, current_price)
            if atr
            else None
        )

        # Build description
        descriptions = []

        if support_zones:
            descriptions.append(
                f"Support: {support_zones[-1].level:.2f} (±{abs(support_zones[-1].high - support_zones[-1].level):.2f})"
            )

        if resistance_zones:
            descriptions.append(
                f"Resistance: {resistance_zones[-1].level:.2f} (±{abs(resistance_zones[-1].high - resistance_zones[-1].level):.2f})"
            )

        if atr:
            descriptions.append(f"ATR: {atr:.2f} ({atr_pct:.1f}% of price)")

        if trend_state:
            descriptions.append(f"Trend: {trend_state.value}")

        if momentum_state:
            descriptions.append(f"Momentum: {momentum_state.value}")

        if rsi is not None:
            descriptions.append(f"RSI: {rsi:.0f}")

        description = " | ".join(descriptions)

        return TechnicalContext(
            ticker=ticker,
            current_price=current_price,
            support_zones=support_zones,
            resistance_zones=resistance_zones,
            atr=atr,
            atr_pct=atr_pct,
            trend_state=trend_state.value if trend_state else None,
            trend_strength=None,  # Could be enhanced with trend strength calculation
            momentum_state=momentum_state.value if momentum_state else None,
            rsi=rsi,
            macd_histogram=macd_histogram,
            description=description,
        )

    @staticmethod
    def validate_stop_against_support(
        stop_price: float,
        support_zones: List[SupportResistanceZone],
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that stop-loss respects technical support.

        Args:
            stop_price: Proposed stop-loss price
            support_zones: List of support zones

        Returns:
            (is_valid, warning_message)
        """
        if not support_zones:
            return True, None

        # Find nearest support below stop
        nearest_support = None
        for zone in sorted(support_zones, key=lambda z: z.level, reverse=True):
            if zone.level < stop_price:
                nearest_support = zone
                break

        if nearest_support is None:
            # Stop is below all support zones
            return (
                True,
                f"Stop ({stop_price:.2f}) is below all support zones. May be too aggressive.",
            )

        # Check if stop is within 1 ATR of support
        distance_to_support = stop_price - nearest_support.level
        if distance_to_support < 5:  # Less than 5 PKR from support
            return (
                True,
                f"Stop ({stop_price:.2f}) is very close to support ({nearest_support.level:.2f}). Risk of whipsaw.",
            )

        return True, None

    @staticmethod
    def validate_entry_against_resistance(
        entry_price: float,
        resistance_zones: List[SupportResistanceZone],
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that entry price respects technical resistance.

        Args:
            entry_price: Proposed entry price
            resistance_zones: List of resistance zones

        Returns:
            (is_valid, warning_message)
        """
        if not resistance_zones:
            return True, None

        # Find nearest resistance above entry
        nearest_resistance = None
        for zone in sorted(resistance_zones, key=lambda z: z.level):
            if zone.level > entry_price:
                nearest_resistance = zone
                break

        if nearest_resistance is None:
            # Entry is above all resistance zones (breakout scenario)
            return (
                True,
                f"Entry ({entry_price:.2f}) is above all resistance zones. Breakout trade.",
            )

        distance_to_resistance = nearest_resistance.level - entry_price
        distance_pct = (distance_to_resistance / entry_price) * 100

        if distance_pct < 5:
            return (
                True,
                f"Entry ({entry_price:.2f}) is within 5% of resistance ({nearest_resistance.level:.2f}). High risk of rejection.",
            )

        return True, None

    @staticmethod
    def suggest_atr_stop(
        entry_price: float,
        atr: float,
        multiplier: float = 2.0,
    ) -> float:
        """
        Suggest ATR-based stop-loss.

        Formula:
            Stop = Entry - (ATR × Multiplier)

        Args:
            entry_price: Entry price
            atr: Average True Range
            multiplier: Number of ATRs (default 2.0)

        Returns:
            Suggested stop-loss price
        """
        stop = entry_price - (atr * multiplier)
        return round(stop, 2)

    @staticmethod
    def suggest_atr_targets(
        entry_price: float,
        atr: float,
        target_multipliers: List[float] = None,
    ) -> List[float]:
        """
        Suggest ATR-based profit targets.

        Formula:
            Target N = Entry + (ATR × Multiplier N)

        Args:
            entry_price: Entry price
            atr: Average True Range
            target_multipliers: List of ATR multipliers (default [2, 3, 4])

        Returns:
            List of suggested targets
        """
        if target_multipliers is None:
            target_multipliers = [2.0, 3.0, 4.0]

        targets = [
            round(entry_price + (atr * mult), 2)
            for mult in target_multipliers
        ]
        return targets


# ════════════════════════════════════════════════════════════════════════════════
# TRADE PLAN ENHANCEMENT
# ════════════════════════════════════════════════════════════════════════════════

def enhance_trade_plan_with_technical_context(
    trade_plan: Dict[str, Any],
    technical_context: TechnicalContext,
) -> Dict[str, Any]:
    """
    Enhance trade plan dict with technical context and suggestions.

    Args:
        trade_plan: Trade plan dictionary
        technical_context: TechnicalContext object

    Returns:
        Enhanced trade plan with technical fields
    """
    stop_price = trade_plan.get("stop_price")
    entry_price = trade_plan.get("entry_price")

    # Validate against technical levels
    stop_valid, stop_warning = TechnicalContextExtractor.validate_stop_against_support(
        stop_price,
        technical_context.support_zones,
    )

    entry_valid, entry_warning = TechnicalContextExtractor.validate_entry_against_resistance(
        entry_price,
        technical_context.resistance_zones,
    )

    # Suggest ATR-based stops/targets
    atr_stop = None
    atr_targets = None

    if technical_context.atr and entry_price:
        atr_stop = TechnicalContextExtractor.suggest_atr_stop(
            entry_price,
            technical_context.atr,
            multiplier=2.0,
        )
        atr_targets = TechnicalContextExtractor.suggest_atr_targets(
            entry_price,
            technical_context.atr,
            target_multipliers=[2.0, 3.0, 4.0],
        )

    return {
        **trade_plan,
        "technical_context": technical_context.to_dict(),
        "technical_validation": {
            "stop_valid": stop_valid,
            "stop_warning": stop_warning,
            "entry_valid": entry_valid,
            "entry_warning": entry_warning,
        },
        "atr_suggestions": {
            "atr_based_stop": atr_stop,
            "atr_based_targets": atr_targets,
        },
    }


# ════════════════════════════════════════════════════════════════════════════════
# API INTEGRATION
# ════════════════════════════════════════════════════════════════════════════════

def api_get_technical_context(
    ticker: str,
    current_price: float,
    highs: List[float],
    lows: List[float],
    closes: List[float],
) -> Dict[str, Any]:
    """
    API handler: Get technical context for trade planning.

    GET /api/securities/{ticker}/technical-context
    """
    try:
        context = TechnicalContextExtractor.extract_from_price_data(
            ticker=ticker,
            current_price=current_price,
            highs=highs,
            lows=lows,
            closes=closes,
        )

        return {
            "success": True,
            "technical_context": context.to_dict(),
        }

    except Exception as e:
        return {"error": str(e)}


def api_enhance_trade_plan_with_technicals(
    trade_plan_dict: Dict[str, Any],
    ticker: str,
    current_price: float,
    highs: List[float],
    lows: List[float],
    closes: List[float],
) -> Dict[str, Any]:
    """
    API handler: Enhance trade plan with technical analysis.

    POST /api/trade-plans/{id}/enhance-with-technicals
    {
        "trade_plan": {...},
        "ticker": "DGKC",
        "current_price": 200,
        "highs": [...],
        "lows": [...],
        "closes": [...]
    }
    """
    try:
        context = TechnicalContextExtractor.extract_from_price_data(
            ticker=ticker,
            current_price=current_price,
            highs=highs,
            lows=lows,
            closes=closes,
        )

        enhanced = enhance_trade_plan_with_technical_context(
            trade_plan_dict,
            context,
        )

        return {
            "success": True,
            "enhanced_trade_plan": enhanced,
        }

    except Exception as e:
        return {"error": str(e)}
