"""
Market Breadth Engine - Sprint M3

Analyze market breadth: % of stocks trading above moving averages.
Detect market regime: BULLISH_BROAD, BEARISH_NARROW, etc.

Key insight: Index can be up, but if few stocks participate, it's weak.
Example: KSE-100 +1.5% but only 34% above 50DMA = narrow, risky rally.

Features:
- Calculate % above 20/50/100/200 day moving averages
- Market regime classification (deterministic rules, not ML)
- Breadth indicators (new highs/lows, A/D ratio)
- Breadth divergence detection
- Regime confidence scoring
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from .schema_market import MarketBreadth, MarketRegime, IndexPrice, IndexMaster, MarketSnapshot
from .market_index import MarketIndexEngine


class BreadthStrength(str, Enum):
    """Breadth strength classification."""
    VERY_WEAK = "VERY_WEAK"       # <30% above 50DMA
    WEAK = "WEAK"                 # 30-40% above 50DMA
    NEUTRAL = "NEUTRAL"           # 40-60% above 50DMA
    STRONG = "STRONG"             # 60-70% above 50DMA
    VERY_STRONG = "VERY_STRONG"   # >70% above 50DMA


class BreadthEngine:
    """Calculate market breadth and regime classification."""

    def __init__(self, session: Session):
        self.session = session
        self.index_engine = MarketIndexEngine(session)

    def calculate_market_breadth(
        self,
        index_code: str,
        date: date,
        num_stocks: int,
    ) -> MarketBreadth:
        """
        Calculate market breadth for a given date.

        This requires historical price data for all constituents.
        In production, this would be called with actual stock prices.

        Args:
            index_code: Index to analyze (e.g., "KSE-100")
            date: Analysis date
            num_stocks: Total number of stocks to analyze

        Returns:
            MarketBreadth record with % above each moving average
        """
        # Get index reference
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            raise ValueError(f"Index {index_code} not found")

        # This is where we would:
        # 1. Get all constituents for this index
        # 2. Get price history for each constituent
        # 3. Calculate moving averages for each
        # 4. Count how many are above each MA level
        #
        # For now, return structure for storage
        # In production, integrate with real stock price data

        # Check if breadth already exists for this date
        existing = (
            self.session.query(MarketBreadth)
            .filter_by(date=date)
            .first()
        )

        if existing:
            return existing

        # Create new breadth record (values calculated elsewhere)
        breadth = MarketBreadth(
            date=date,
            pct_above_20dma=None,
            pct_above_50dma=None,
            pct_above_100dma=None,
            pct_above_200dma=None,
            advance_decline_ratio=None,
            new_highs=None,
            new_lows=None,
            market_regime=None,
            regime_confidence=None,
        )

        self.session.add(breadth)
        self.session.commit()
        return breadth

    def record_breadth_snapshot(
        self,
        date: date,
        pct_above_20dma: float,
        pct_above_50dma: float,
        pct_above_100dma: float,
        pct_above_200dma: float,
        advance_decline_ratio: float,
        new_highs: int = 0,
        new_lows: int = 0,
    ) -> MarketBreadth:
        """
        Record daily breadth snapshot.

        Args:
            date: Trading date
            pct_above_20dma: % of stocks above 20-day MA
            pct_above_50dma: % of stocks above 50-day MA
            pct_above_100dma: % of stocks above 100-day MA
            pct_above_200dma: % of stocks above 200-day MA
            advance_decline_ratio: Advancers / Decliners
            new_highs: Stocks making new 52W highs
            new_lows: Stocks making new 52W lows

        Returns:
            MarketBreadth record
        """
        # Check if exists
        existing = self.session.query(MarketBreadth).filter_by(date=date).first()
        if existing:
            existing.pct_above_20dma = pct_above_20dma
            existing.pct_above_50dma = pct_above_50dma
            existing.pct_above_100dma = pct_above_100dma
            existing.pct_above_200dma = pct_above_200dma
            existing.advance_decline_ratio = advance_decline_ratio
            existing.new_highs = new_highs
            existing.new_lows = new_lows

            # Classify regime
            regime, confidence = self._classify_regime(
                pct_above_50dma, pct_above_200dma, advance_decline_ratio, new_highs, new_lows
            )
            existing.market_regime = regime
            existing.regime_confidence = confidence

            self.session.commit()
            return existing

        # Create new
        regime, confidence = self._classify_regime(
            pct_above_50dma, pct_above_200dma, advance_decline_ratio, new_highs, new_lows
        )

        breadth = MarketBreadth(
            date=date,
            pct_above_20dma=pct_above_20dma,
            pct_above_50dma=pct_above_50dma,
            pct_above_100dma=pct_above_100dma,
            pct_above_200dma=pct_above_200dma,
            advance_decline_ratio=advance_decline_ratio,
            new_highs=new_highs,
            new_lows=new_lows,
            market_regime=regime,
            regime_confidence=confidence,
        )

        self.session.add(breadth)
        self.session.commit()
        return breadth

    def get_latest_breadth(self) -> Optional[MarketBreadth]:
        """Get most recent breadth snapshot."""
        return (
            self.session.query(MarketBreadth)
            .order_by(desc(MarketBreadth.date))
            .first()
        )

    def get_breadth(self, date: date) -> Optional[MarketBreadth]:
        """Get breadth for specific date."""
        return self.session.query(MarketBreadth).filter_by(date=date).first()

    def get_breadth_history(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[MarketBreadth]:
        """Get breadth history over period."""
        query = self.session.query(MarketBreadth)

        if from_date:
            query = query.filter(MarketBreadth.date >= from_date)
        if to_date:
            query = query.filter(MarketBreadth.date <= to_date)

        query = query.order_by(MarketBreadth.date)

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_breadth_statistics(self, days: int = 20) -> Dict:
        """Get breadth statistics over period."""
        from_date = date.today() - timedelta(days=days)
        breadths = self.get_breadth_history(from_date=from_date)

        if not breadths:
            return {"error": "No breadth data"}

        pcts_50 = [b.pct_above_50dma for b in breadths if b.pct_above_50dma]
        pcts_200 = [b.pct_above_200dma for b in breadths if b.pct_above_200dma]
        ad_ratios = [b.advance_decline_ratio for b in breadths if b.advance_decline_ratio]

        if not pcts_50:
            return {"error": "Insufficient data"}

        return {
            "period_days": days,
            "snapshots": len(breadths),
            "pct_above_50dma": {
                "current": pcts_50[-1] if pcts_50 else None,
                "average": sum(pcts_50) / len(pcts_50),
                "high": max(pcts_50),
                "low": min(pcts_50),
            },
            "pct_above_200dma": {
                "current": pcts_200[-1] if pcts_200 else None,
                "average": sum(pcts_200) / len(pcts_200),
                "high": max(pcts_200),
                "low": min(pcts_200),
            },
            "ad_ratio": {
                "current": ad_ratios[-1] if ad_ratios else None,
                "average": sum(ad_ratios) / len(ad_ratios),
                "high": max(ad_ratios),
                "low": min(ad_ratios),
            },
            "regime_analysis": self._analyze_regime_trend(breadths),
        }

    def detect_breadth_divergence(self, days: int = 10) -> Dict:
        """
        Detect divergence between price and breadth.

        When index goes up but breadth goes down (or vice versa), it signals:
        - Index up + Breadth down = Weak rally (few stocks pushing index)
        - Index down + Breadth up = Potential reversal (selling pressure easing)
        """
        # Get latest market snapshot (price data)
        index = self.session.query(IndexMaster).filter_by(index_code="KSE-100").first()
        if not index:
            return {"error": "No index data"}

        from_date = date.today() - timedelta(days=days)
        prices = (
            self.session.query(IndexPrice)
            .filter(
                IndexPrice.index_id == index.index_id,
                IndexPrice.date >= from_date,
            )
            .order_by(IndexPrice.date)
            .all()
        )

        breadths = self.get_breadth_history(from_date=from_date)

        if not prices or not breadths:
            return {"error": "Insufficient data"}

        # Calculate trends
        price_trend = "up" if prices[-1].close > prices[0].close else "down"
        breadth_trend = (
            "improving" if breadths[-1].pct_above_50dma > breadths[0].pct_above_50dma
            else "deteriorating"
        )

        # Detect divergence
        divergence = None
        signal = None

        if price_trend == "up" and breadth_trend == "deteriorating":
            divergence = "BEARISH"
            signal = "Index rallying on narrow breadth - weak, risky"

        elif price_trend == "down" and breadth_trend == "improving":
            divergence = "BULLISH"
            signal = "Index declining but breadth improving - selling pressure easing"

        elif price_trend == "up" and breadth_trend == "improving":
            divergence = "NONE"
            signal = "Healthy rally - index and breadth both strong"

        elif price_trend == "down" and breadth_trend == "deteriorating":
            divergence = "NONE"
            signal = "Healthy decline - index and breadth both weak"

        return {
            "period_days": days,
            "price_trend": price_trend,
            "breadth_trend": breadth_trend,
            "divergence": divergence,
            "signal": signal,
            "latest_breadth_50dma": breadths[-1].pct_above_50dma,
        }

    def get_breadth_strength(self, pct_above_50dma: float) -> BreadthStrength:
        """Classify breadth strength."""
        if pct_above_50dma >= 70:
            return BreadthStrength.VERY_STRONG
        elif pct_above_50dma >= 60:
            return BreadthStrength.STRONG
        elif pct_above_50dma >= 40:
            return BreadthStrength.NEUTRAL
        elif pct_above_50dma >= 30:
            return BreadthStrength.WEAK
        else:
            return BreadthStrength.VERY_WEAK

    def get_breadth_report(self) -> Dict:
        """Generate comprehensive breadth report."""
        latest = self.get_latest_breadth()
        if not latest:
            return {"error": "No breadth data"}

        divergence = self.detect_breadth_divergence(days=20)
        stats = self.get_breadth_statistics(days=30)
        strength = self.get_breadth_strength(latest.pct_above_50dma)

        return {
            "date": latest.date.isoformat(),
            "breadth": {
                "above_20dma": latest.pct_above_20dma,
                "above_50dma": latest.pct_above_50dma,
                "above_100dma": latest.pct_above_100dma,
                "above_200dma": latest.pct_above_200dma,
            },
            "regime": {
                "classification": latest.market_regime.value if latest.market_regime else None,
                "confidence": latest.regime_confidence,
            },
            "breadth_strength": strength.value,
            "advance_decline": {
                "ratio": latest.advance_decline_ratio,
                "new_highs": latest.new_highs,
                "new_lows": latest.new_lows,
            },
            "divergence_analysis": divergence,
            "statistics": stats,
            "interpretation": self._generate_interpretation(latest, strength, divergence),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # REGIME CLASSIFICATION (DETERMINISTIC RULES)
    # ════════════════════════════════════════════════════════════════════════════

    def _classify_regime(
        self,
        pct_above_50dma: float,
        pct_above_200dma: float,
        ad_ratio: float,
        new_highs: int,
        new_lows: int,
    ) -> Tuple[MarketRegime, float]:
        """
        Classify market regime using deterministic rules.

        NOT ML-based. Rules are explicit and visible.

        Returns: (regime, confidence score 0-1)
        """
        confidence = 0.5  # Start at neutral

        # Rule 1: Check long-term trend (200DMA)
        if pct_above_200dma >= 65:
            long_term = "bullish"
            confidence += 0.15
        elif pct_above_200dma <= 35:
            long_term = "bearish"
            confidence += 0.15
        else:
            long_term = "neutral"

        # Rule 2: Check short-term breadth (50DMA)
        if pct_above_50dma >= 70:
            short_term = "strong"
            confidence += 0.15
        elif pct_above_50dma >= 55:
            short_term = "moderate"
            confidence += 0.10
        elif pct_above_50dma <= 30:
            short_term = "weak"
            confidence += 0.15
        else:
            short_term = "neutral"

        # Rule 3: Check participation (A/D ratio)
        if ad_ratio >= 1.5:
            participation = "broad"
            confidence += 0.10
        elif ad_ratio >= 0.75:
            participation = "moderate"
        else:
            participation = "narrow"
            confidence -= 0.10

        # Rule 4: Check momentum (new highs vs lows)
        if new_highs > new_lows * 2:
            momentum = "strong"
            confidence += 0.10
        elif new_highs > new_lows:
            momentum = "moderate"
        else:
            momentum = "weak"
            confidence -= 0.10

        # Classify regime
        if long_term == "bullish":
            if short_term == "strong" and participation == "broad":
                regime = MarketRegime.BULLISH_BROAD
            else:
                regime = MarketRegime.BULLISH_NARROW

        elif long_term == "bearish":
            if short_term == "weak" and participation == "narrow":
                regime = MarketRegime.BEARISH_BROAD  # Broad selling
            else:
                regime = MarketRegime.BEARISH_NARROW

        else:  # Neutral long-term
            if short_term == "strong":
                regime = MarketRegime.BULLISH_NARROW
            elif short_term == "weak":
                regime = MarketRegime.BEARISH_NARROW
            else:
                regime = MarketRegime.NEUTRAL

        # Check for high volatility
        if ad_ratio < 0.5 or ad_ratio > 3.0:
            if abs(pct_above_50dma - 50) > 20:
                regime = MarketRegime.HIGH_VOLATILITY
                confidence = 0.6

        # Clamp confidence
        confidence = min(1.0, max(0.0, confidence))

        return regime, confidence

    def _analyze_regime_trend(self, breadths: List[MarketBreadth]) -> Dict:
        """Analyze how regime has changed over time."""
        if len(breadths) < 2:
            return {"error": "Insufficient data"}

        regimes = [b.market_regime for b in breadths if b.market_regime]
        if not regimes:
            return {"error": "No regime data"}

        latest_regime = regimes[-1]
        prev_regime = regimes[-2] if len(regimes) >= 2 else regimes[-1]

        regime_changed = latest_regime != prev_regime
        regime_stability = sum(1 for i in range(1, len(regimes)) if regimes[i] == regimes[i - 1]) / len(regimes)

        return {
            "latest_regime": latest_regime.value,
            "previous_regime": prev_regime.value,
            "regime_changed": regime_changed,
            "regime_stability": round(regime_stability, 2),
            "interpretation": self._interpret_regime_trend(latest_regime, prev_regime),
        }

    @staticmethod
    def _interpret_regime_trend(current: MarketRegime, previous: MarketRegime) -> str:
        """Interpret regime changes."""
        if current == MarketRegime.BULLISH_BROAD and previous != MarketRegime.BULLISH_BROAD:
            return "Rally broadening - healthy development"
        elif current == MarketRegime.BULLISH_NARROW and previous == MarketRegime.BULLISH_BROAD:
            return "Rally narrowing - caution advised"
        elif current == MarketRegime.BEARISH_BROAD and previous != MarketRegime.BEARISH_BROAD:
            return "Selling becoming broad - increased pressure"
        elif current == MarketRegime.BEARISH_NARROW and previous == MarketRegime.BEARISH_BROAD:
            return "Selling pressure easing - potential reversal"
        elif current == MarketRegime.HIGH_VOLATILITY:
            return "High volatility environment - expect choppy action"
        elif current == MarketRegime.NEUTRAL:
            return "Market in consolidation - direction unclear"
        return "Regime stable"

    @staticmethod
    def _generate_interpretation(
        breadth: MarketBreadth, strength: BreadthStrength, divergence: Dict
    ) -> str:
        """Generate plain-English interpretation of breadth."""
        parts = []

        # Breadth strength
        if strength == BreadthStrength.VERY_STRONG:
            parts.append("Very strong breadth")
        elif strength == BreadthStrength.STRONG:
            parts.append("Strong breadth")
        elif strength == BreadthStrength.NEUTRAL:
            parts.append("Neutral breadth")
        elif strength == BreadthStrength.WEAK:
            parts.append("Weak breadth")
        else:
            parts.append("Very weak breadth")

        # Regime
        if breadth.market_regime:
            parts.append(f"({breadth.market_regime.value})")

        # Divergence
        if divergence.get("divergence"):
            parts.append(f"- {divergence['signal']}")

        return " ".join(parts)
