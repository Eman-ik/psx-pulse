"""
Trade Plan Market Context Integration - Module 6, Sprint R4

Pulls market regime and sector performance from Module 3 to inform trade plan decisions.

Context provided:
- Market regime (BULLISH, NEUTRAL, BEARISH, BEARISH BROAD)
- Market breadth & health
- Sector trend vs market
- Sector performance vs historical
- Liquidity conditions
- Upcoming macro events

This module bridges market analysis (Module 3) with trade planning (Module 6).
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


# ════════════════════════════════════════════════════════════════════════════════
# ENUMS & CONSTANTS
# ════════════════════════════════════════════════════════════════════════════════

class MarketRegime(str, Enum):
    """Market regime classification."""
    STRONG_BULLISH = "STRONG_BULLISH"      # All-in, broad participation
    BULLISH = "BULLISH"                    # Rising, healthy breadth
    NEUTRAL = "NEUTRAL"                    # Mixed signals
    BEARISH = "BEARISH"                    # Falling, narrow participation
    BEARISH_BROAD = "BEARISH_BROAD"        # Falling on broad weakness
    CRASH = "CRASH"                        # Severe decline


class SectorTrend(str, Enum):
    """Sector trend relative to market."""
    LEADING = "LEADING"              # Outperforming market
    IN_LINE = "IN_LINE"              # Tracking market
    LAGGING = "LAGGING"              # Underperforming market
    DIVERGING = "DIVERGING"          # Significant divergence


class MarketHealth(str, Enum):
    """Overall market health assessment."""
    EXCELLENT = "EXCELLENT"          # Strong, broad, healthy
    GOOD = "GOOD"                    # Positive conditions
    NEUTRAL = "NEUTRAL"              # Mixed conditions
    WEAK = "WEAK"                    # Negative conditions
    CRITICAL = "CRITICAL"            # Severe stress


# ════════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ════════════════════════════════════════════════════════════════════════════════

class SectorContext:
    """Sector performance and trend context."""

    def __init__(
        self,
        sector_name: str,
        return_1d: Optional[float],
        return_1m: Optional[float],
        return_3m: Optional[float],
        return_ytd: Optional[float],
        trend: SectorTrend,
        vs_market_1m: Optional[float],
        breadth_pct: Optional[float],
        participation: str,
    ):
        self.sector_name = sector_name
        self.return_1d = return_1d
        self.return_1m = return_1m
        self.return_3m = return_3m
        self.return_ytd = return_ytd
        self.trend = trend
        self.vs_market_1m = vs_market_1m  # Outperformance vs KSE-100
        self.breadth_pct = breadth_pct    # % of stocks above 50DMA
        self.participation = participation  # HIGH, NORMAL, LOW

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response dict."""
        return {
            "sector": self.sector_name,
            "returns": {
                "1d": self.return_1d,
                "1m": self.return_1m,
                "3m": self.return_3m,
                "ytd": self.return_ytd,
            },
            "trend": self.trend.value if self.trend else None,
            "vs_market_1m": self.vs_market_1m,
            "breadth_pct": self.breadth_pct,
            "participation": self.participation,
        }


class MarketContext:
    """Complete market and sector context."""

    def __init__(
        self,
        regime: MarketRegime,
        regime_confidence: float,
        market_health: MarketHealth,
        breadth_pct: float,
        breadth_trend: str,
        sector_context: Optional[SectorContext],
        market_return_1d: float,
        market_return_1m: float,
        market_return_3m: float,
        market_volume_ratio: Optional[float],
        upcoming_events: Optional[List[str]],
        description: str,
    ):
        self.regime = regime
        self.regime_confidence = regime_confidence
        self.market_health = market_health
        self.breadth_pct = breadth_pct
        self.breadth_trend = breadth_trend
        self.sector_context = sector_context
        self.market_return_1d = market_return_1d
        self.market_return_1m = market_return_1m
        self.market_return_3m = market_return_3m
        self.market_volume_ratio = market_volume_ratio
        self.upcoming_events = upcoming_events or []
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response dict."""
        return {
            "regime": {
                "classification": self.regime.value,
                "confidence": self.regime_confidence,
            },
            "market_health": self.market_health.value,
            "breadth": {
                "pct_above_50dma": self.breadth_pct,
                "trend": self.breadth_trend,
            },
            "market_returns": {
                "1d": self.market_return_1d,
                "1m": self.market_return_1m,
                "3m": self.market_return_3m,
            },
            "market_volume_ratio": self.market_volume_ratio,
            "sector": self.sector_context.to_dict() if self.sector_context else None,
            "upcoming_events": self.upcoming_events,
            "description": self.description,
        }


# ════════════════════════════════════════════════════════════════════════════════
# MARKET CONTEXT EXTRACTION
# ════════════════════════════════════════════════════════════════════════════════

class MarketContextExtractor:
    """Extract market and sector context for trade planning."""

    @staticmethod
    def classify_regime(
        breadth_pct: float,
        market_return_1m: float,
        trend: str,
    ) -> tuple[MarketRegime, float]:
        """
        Classify market regime from breadth and returns.

        Args:
            breadth_pct: Percentage of stocks above 50DMA
            market_return_1m: 1-month market return (%)
            trend: Trend direction (UPTREND, NEUTRAL, DOWNTREND)

        Returns:
            (regime, confidence_0_to_1)
        """
        confidence = 0.7  # Base confidence

        # Strong bullish: >65% breadth + positive returns + uptrend
        if breadth_pct > 65 and market_return_1m > 0 and trend == "UPTREND":
            return MarketRegime.STRONG_BULLISH, 0.9

        # Bullish: >55% breadth + positive returns
        if breadth_pct > 55 and market_return_1m > 0:
            return MarketRegime.BULLISH, 0.8

        # Neutral: 45-55% breadth or mixed signals
        if 45 <= breadth_pct <= 55 or trend == "NEUTRAL":
            return MarketRegime.NEUTRAL, 0.6

        # Bearish Broad: <35% breadth (severe weakness) - CHECK FIRST
        if breadth_pct < 35:
            return MarketRegime.BEARISH_BROAD, 0.9

        # Bearish: <45% breadth + negative returns
        if breadth_pct < 45 and market_return_1m < 0:
            return MarketRegime.BEARISH, 0.8

        return MarketRegime.NEUTRAL, 0.6

    @staticmethod
    def assess_market_health(
        breadth_pct: float,
        market_volume_ratio: Optional[float],
        regime: MarketRegime,
    ) -> MarketHealth:
        """
        Assess overall market health.

        Args:
            breadth_pct: Percentage of stocks above 50DMA
            market_volume_ratio: Current volume vs 20-day average
            regime: Market regime classification

        Returns:
            MarketHealth assessment
        """
        if regime == MarketRegime.STRONG_BULLISH and breadth_pct > 65:
            return MarketHealth.EXCELLENT

        if regime == MarketRegime.BULLISH and breadth_pct > 55:
            return MarketHealth.GOOD

        if regime == MarketRegime.NEUTRAL:
            return MarketHealth.NEUTRAL

        if regime == MarketRegime.BEARISH:
            return MarketHealth.WEAK

        if regime == MarketRegime.BEARISH_BROAD or regime == MarketRegime.CRASH:
            return MarketHealth.CRITICAL

        return MarketHealth.NEUTRAL

    @staticmethod
    def classify_sector_trend(
        sector_return_1m: float,
        market_return_1m: float,
        sector_breadth_pct: float,
    ) -> SectorTrend:
        """
        Classify sector trend relative to market.

        Args:
            sector_return_1m: Sector 1-month return (%)
            market_return_1m: Market 1-month return (%)
            sector_breadth_pct: % of sector stocks above 50DMA

        Returns:
            SectorTrend classification
        """
        outperformance = sector_return_1m - market_return_1m

        if outperformance > 5 and sector_breadth_pct > 60:
            return SectorTrend.LEADING

        if -5 <= outperformance <= 5:
            return SectorTrend.IN_LINE

        if outperformance < -5 and sector_breadth_pct < 40:
            return SectorTrend.LAGGING

        return SectorTrend.DIVERGING

    @staticmethod
    def extract_market_context(
        regime: MarketRegime,
        regime_confidence: float,
        breadth_pct: float,
        breadth_trend: str,
        market_return_1d: float,
        market_return_1m: float,
        market_return_3m: float,
        sector_name: Optional[str] = None,
        sector_return_1d: Optional[float] = None,
        sector_return_1m: Optional[float] = None,
        sector_return_3m: Optional[float] = None,
        sector_return_ytd: Optional[float] = None,
        sector_breadth_pct: Optional[float] = None,
        market_volume_ratio: Optional[float] = None,
        upcoming_events: Optional[List[str]] = None,
    ) -> MarketContext:
        """
        Extract complete market context.

        Args:
            regime: Market regime (BULLISH, NEUTRAL, BEARISH, etc.)
            regime_confidence: Confidence in regime (0-1)
            breadth_pct: % of stocks above 50DMA
            breadth_trend: Trend direction (IMPROVING, STABLE, DETERIORATING)
            market_return_1d/1m/3m: Market returns
            sector_name: Stock's sector name (optional)
            sector_return_*: Sector returns (optional)
            sector_breadth_pct: % of sector stocks above 50DMA (optional)
            market_volume_ratio: Current vs 20-day volume
            upcoming_events: List of upcoming macro events

        Returns:
            MarketContext object
        """
        # Assess market health
        health = MarketContextExtractor.assess_market_health(
            breadth_pct,
            market_volume_ratio,
            regime,
        )

        # Build sector context if provided
        sector_context = None
        if sector_name and sector_return_1m is not None:
            outperformance = sector_return_1m - market_return_1m
            trend = MarketContextExtractor.classify_sector_trend(
                sector_return_1m,
                market_return_1m,
                sector_breadth_pct or 50,
            )

            participation = "HIGH" if (sector_breadth_pct or 50) > 60 else \
                           "NORMAL" if 40 <= (sector_breadth_pct or 50) <= 60 else "LOW"

            sector_context = SectorContext(
                sector_name=sector_name,
                return_1d=sector_return_1d,
                return_1m=sector_return_1m,
                return_3m=sector_return_3m,
                return_ytd=sector_return_ytd,
                trend=trend,
                vs_market_1m=outperformance,
                breadth_pct=sector_breadth_pct,
                participation=participation,
            )

        # Build description
        descriptions = []
        descriptions.append(f"Regime: {regime.value} ({regime_confidence:.0%} confidence)")
        descriptions.append(f"Health: {health.value}")
        descriptions.append(f"Breadth: {breadth_pct:.0f}% above 50DMA ({breadth_trend})")
        if market_return_1m != 0:
            descriptions.append(
                f"Market: {market_return_1m:+.1f}% (1M) | {market_return_3m:+.1f}% (3M)"
            )
        if sector_context:
            descriptions.append(
                f"Sector: {sector_context.trend.value} vs market "
                f"({sector_context.vs_market_1m:+.1f}%)"
            )

        description = " | ".join(descriptions)

        return MarketContext(
            regime=regime,
            regime_confidence=regime_confidence,
            market_health=health,
            breadth_pct=breadth_pct,
            breadth_trend=breadth_trend,
            sector_context=sector_context,
            market_return_1d=market_return_1d,
            market_return_1m=market_return_1m,
            market_return_3m=market_return_3m,
            market_volume_ratio=market_volume_ratio,
            upcoming_events=upcoming_events or [],
            description=description,
        )


# ════════════════════════════════════════════════════════════════════════════════
# TRADE PLAN VALIDATION
# ════════════════════════════════════════════════════════════════════════════════

class MarketContextValidator:
    """Validate trade plans against market context."""

    @staticmethod
    def validate_entry_against_regime(
        entry_price: float,
        current_price: float,
        regime: MarketRegime,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate entry decision against market regime.

        Args:
            entry_price: Planned entry price
            current_price: Current price
            regime: Current market regime

        Returns:
            (is_reasonable, warning_message)
        """
        is_counter_trend = entry_price > current_price if regime in [
            MarketRegime.BEARISH,
            MarketRegime.BEARISH_BROAD,
        ] else entry_price < current_price if regime == MarketRegime.STRONG_BULLISH else None

        if regime == MarketRegime.BEARISH_BROAD:
            return (
                True,
                f"Market in {regime.value}. Entering long-only trades is high risk. Consider waiting for regime change.",
            )

        if regime == MarketRegime.CRASH:
            return (
                True,
                f"Market in {regime.value}. Do NOT enter new longs until regime stabilizes.",
            )

        return True, None

    @staticmethod
    def validate_sector_exposure(
        sector_name: str,
        sector_context: Optional[SectorContext],
        portfolio_sector_allocation: Optional[float] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate sector exposure given market conditions.

        Args:
            sector_name: Stock's sector
            sector_context: Sector performance context
            portfolio_sector_allocation: Current % in this sector

        Returns:
            (is_acceptable, warning_message)
        """
        if not sector_context:
            return True, None

        # Warn if sector lagging and we're adding to it
        if sector_context.trend == SectorTrend.LAGGING:
            return (
                True,
                f"{sector_name} is LAGGING the market ({sector_context.vs_market_1m:+.1f}%). Consider waiting for outperformance.",
            )

        # Warn if sector participation weak
        if sector_context.participation == "LOW":
            return (
                True,
                f"{sector_name} has low participation ({sector_context.breadth_pct:.0f}% above 50DMA). High stock-pick risk.",
            )

        return True, None

    @staticmethod
    def validate_breadth_for_entry(
        breadth_pct: float,
        regime: MarketRegime,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate market breadth for entry decisions.

        Args:
            breadth_pct: % of stocks above 50DMA
            regime: Market regime

        Returns:
            (is_acceptable, warning_message)
        """
        if breadth_pct < 30 and regime != MarketRegime.STRONG_BULLISH:
            return (
                True,
                f"Market breadth only {breadth_pct:.0f}%. Very narrow participation. High risk of reversal.",
            )

        if breadth_pct > 80 and regime == MarketRegime.STRONG_BULLISH:
            return (
                True,
                f"Market breadth {breadth_pct:.0f}% (extremely high). Possible euphoria/top. Consider profit-taking levels.",
            )

        return True, None


# ════════════════════════════════════════════════════════════════════════════════
# TRADE PLAN ENHANCEMENT
# ════════════════════════════════════════════════════════════════════════════════

def enhance_trade_plan_with_market_context(
    trade_plan: Dict[str, Any],
    market_context: MarketContext,
) -> Dict[str, Any]:
    """
    Enhance trade plan with market context and validation.

    Args:
        trade_plan: Trade plan dictionary
        market_context: MarketContext object

    Returns:
        Enhanced trade plan with market context
    """
    entry_price = trade_plan.get("entry_price")
    current_price = trade_plan.get("current_price") or entry_price
    sector = trade_plan.get("ticker")  # Will use market_context.sector_context if available

    # Validate against regime
    entry_valid, entry_warning = MarketContextValidator.validate_entry_against_regime(
        entry_price,
        current_price,
        market_context.regime,
    )

    # Validate sector exposure
    sector_valid, sector_warning = MarketContextValidator.validate_sector_exposure(
        sector or "Unknown",
        market_context.sector_context,
    )

    # Validate breadth
    breadth_valid, breadth_warning = MarketContextValidator.validate_breadth_for_entry(
        market_context.breadth_pct,
        market_context.regime,
    )

    # Compile all warnings
    warnings = []
    if entry_warning:
        warnings.append(entry_warning)
    if sector_warning:
        warnings.append(sector_warning)
    if breadth_warning:
        warnings.append(breadth_warning)

    return {
        **trade_plan,
        "market_context": market_context.to_dict(),
        "market_validation": {
            "entry_decision_valid": entry_valid,
            "sector_exposure_valid": sector_valid,
            "breadth_valid": breadth_valid,
        },
        "market_warnings": warnings,
    }


# ════════════════════════════════════════════════════════════════════════════════
# API INTEGRATION
# ════════════════════════════════════════════════════════════════════════════════

def api_get_market_context(
    regime: str,
    regime_confidence: float,
    breadth_pct: float,
    breadth_trend: str,
    market_return_1d: float,
    market_return_1m: float,
    market_return_3m: float,
) -> Dict[str, Any]:
    """
    API handler: Get market context for trade planning.

    GET /api/market/context
    """
    try:
        # Parse regime string to enum
        regime_enum = MarketRegime[regime] if regime in [r.name for r in MarketRegime] else MarketRegime.NEUTRAL

        context = MarketContextExtractor.extract_market_context(
            regime=regime_enum,
            regime_confidence=regime_confidence,
            breadth_pct=breadth_pct,
            breadth_trend=breadth_trend,
            market_return_1d=market_return_1d,
            market_return_1m=market_return_1m,
            market_return_3m=market_return_3m,
        )

        return {
            "success": True,
            "market_context": context.to_dict(),
        }

    except Exception as e:
        return {"error": str(e)}


def api_enhance_trade_plan_with_market(
    trade_plan_dict: Dict[str, Any],
    regime: str,
    regime_confidence: float,
    breadth_pct: float,
    breadth_trend: str,
    market_return_1d: float,
    market_return_1m: float,
    market_return_3m: float,
    sector_name: Optional[str] = None,
    sector_return_1m: Optional[float] = None,
) -> Dict[str, Any]:
    """
    API handler: Enhance trade plan with market analysis.

    POST /api/trade-plans/{id}/enhance-with-market
    """
    try:
        # Parse regime
        regime_enum = MarketRegime[regime] if regime in [r.name for r in MarketRegime] else MarketRegime.NEUTRAL

        context = MarketContextExtractor.extract_market_context(
            regime=regime_enum,
            regime_confidence=regime_confidence,
            breadth_pct=breadth_pct,
            breadth_trend=breadth_trend,
            market_return_1d=market_return_1d,
            market_return_1m=market_return_1m,
            market_return_3m=market_return_3m,
            sector_name=sector_name,
            sector_return_1m=sector_return_1m,
        )

        enhanced = enhance_trade_plan_with_market_context(
            trade_plan_dict,
            context,
        )

        return {
            "success": True,
            "enhanced_trade_plan": enhanced,
        }

    except Exception as e:
        return {"error": str(e)}
