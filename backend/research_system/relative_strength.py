"""
Relative Strength Engine - Sprint M5

Market relative strength analysis: identifying outperformers vs underperformers,
detecting divergences, and tracking momentum vs market.

Features:
- Relative strength calculation (security vs market index)
- Relative strength divergence detection
- Price-volume divergence identification
- Outperformer/underperformer tracking
- Relative momentum analysis
- Strength rating classification
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .schema_market import IndexPrice, IndexMaster, MarketSnapshot


class RelativeStrengthEngine:
    """Analyze and track relative strength metrics."""

    def __init__(self, session: Session):
        self.session = session

    # ════════════════════════════════════════════════════════════════════════════
    # RELATIVE STRENGTH CALCULATION
    # ════════════════════════════════════════════════════════════════════════════

    def calculate_relative_strength(
        self,
        index_code: str,
        security_return: float,
        days: int = 20,
    ) -> Dict:
        """
        Calculate relative strength of a security vs the market index.

        Args:
            index_code: Reference index code (e.g., "KSE-100")
            security_return: Security's return percentage
            days: Period to measure relative strength over

        Returns:
            Dict with relative strength metrics
        """
        from_date = date.today() - timedelta(days=days)

        # Get index prices
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            return {"error": "Index not found"}

        index_prices = (
            self.session.query(IndexPrice)
            .filter(
                IndexPrice.index_id == index.index_id,
                IndexPrice.date >= from_date,
            )
            .order_by(IndexPrice.date)
            .all()
        )

        if len(index_prices) < 2:
            return {"error": "Insufficient index data"}

        # Calculate index return
        index_return = (
            float((index_prices[-1].close - index_prices[0].close) / index_prices[0].close * 100)
            if index_prices[0].close
            else 0
        )

        # Relative strength = security return - index return
        relative_strength = security_return - index_return

        return {
            "period_days": days,
            "security_return_pct": round(security_return, 2),
            "index_return_pct": round(index_return, 2),
            "relative_strength_pct": round(relative_strength, 2),
            "outperforming": relative_strength > 0,
            "outperformance_magnitude": abs(relative_strength),
            "strength_rating": self._classify_strength(relative_strength),
        }

    def calculate_relative_momentum(
        self,
        index_code: str,
        security_return: float,
        security_volatility: Optional[float] = None,
        days: int = 20,
    ) -> Dict:
        """
        Calculate relative momentum (adjusted for volatility).

        Risk-adjusted relative strength metric.
        """
        rs = self.calculate_relative_strength(index_code, security_return, days)

        if "error" in rs:
            return rs

        # Risk-adjusted momentum = RS / volatility (higher vol = lower score)
        if security_volatility and security_volatility > 0:
            risk_adjusted = rs["relative_strength_pct"] / security_volatility
        else:
            risk_adjusted = 0

        return {
            **rs,
            "volatility_pct": security_volatility,
            "risk_adjusted_momentum": round(risk_adjusted, 2),
            "momentum_rating": self._classify_momentum(risk_adjusted),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # DIVERGENCE DETECTION
    # ════════════════════════════════════════════════════════════════════════════

    def detect_price_volume_divergence(
        self,
        index_code: str,
        price_trend: str,
        volume_trend: str,
    ) -> Dict:
        """
        Detect divergences between price and volume trends.

        Args:
            index_code: Reference index
            price_trend: "up", "down", or "flat"
            volume_trend: "up", "down", or "flat"

        Returns:
            Divergence detection with signal
        """
        # Define divergence patterns
        divergence = None
        signal = "NEUTRAL"
        strength = "NONE"

        if price_trend == "up" and volume_trend == "down":
            divergence = "BEARISH"
            signal = "PRICE_VOLUME_DIVERGENCE_BEARISH"
            strength = "WEAK_UP"
        elif price_trend == "down" and volume_trend == "up":
            divergence = "BULLISH"
            signal = "PRICE_VOLUME_DIVERGENCE_BULLISH"
            strength = "STRONG_DOWN"
        elif price_trend == "up" and volume_trend == "up":
            divergence = None
            signal = "PRICE_VOLUME_ALIGNED_UP"
            strength = "STRONG_UP"
        elif price_trend == "down" and volume_trend == "down":
            divergence = None
            signal = "PRICE_VOLUME_ALIGNED_DOWN"
            strength = "STRONG_DOWN"

        return {
            "price_trend": price_trend,
            "volume_trend": volume_trend,
            "divergence": divergence,
            "signal": signal,
            "move_strength": strength,
            "interpretation": self._interpret_divergence(divergence, strength),
        }

    def detect_breadth_price_divergence(
        self,
        index_code: str,
        days: int = 20,
    ) -> Dict:
        """
        Detect divergence between price movement and breadth.

        When index moves but breadth doesn't follow, indicates weakness/hidden strength.
        """
        from_date = date.today() - timedelta(days=days)

        # Get index prices
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            return {"error": "Index not found"}

        index_prices = (
            self.session.query(IndexPrice)
            .filter(
                IndexPrice.index_id == index.index_id,
                IndexPrice.date >= from_date,
            )
            .order_by(IndexPrice.date)
            .all()
        )

        snapshots = (
            self.session.query(MarketSnapshot)
            .filter(
                MarketSnapshot.index_id == index.index_id,
                MarketSnapshot.date >= from_date,
            )
            .order_by(MarketSnapshot.date)
            .all()
        )

        if len(index_prices) < 2 or not snapshots:
            return {"error": "Insufficient data"}

        # Price trend
        price_change = index_prices[-1].close - index_prices[0].close if index_prices[0].close else 0
        price_trend = "up" if price_change > 0 else "down" if price_change < 0 else "flat"

        # Breadth trend
        latest_breadth = snapshots[-1].breadth_percent
        oldest_breadth = snapshots[0].breadth_percent
        breadth_trend = "up" if latest_breadth > oldest_breadth else "down" if latest_breadth < oldest_breadth else "flat"

        # Detect divergence
        divergence = None
        signal = "HEALTHY"

        if price_trend == "up" and latest_breadth < 50:
            divergence = "BEARISH"
            signal = "NARROW_RALLY"
        elif price_trend == "down" and latest_breadth > 50:
            divergence = "BULLISH"
            signal = "HIDDEN_STRENGTH"
        elif price_trend == "up" and latest_breadth >= 60:
            divergence = None
            signal = "HEALTHY_RALLY"
        elif price_trend == "down" and latest_breadth <= 40:
            divergence = None
            signal = "HEALTHY_DECLINE"

        return {
            "period_days": days,
            "price_trend": price_trend,
            "breadth_pct": round(latest_breadth, 1),
            "breadth_trend": breadth_trend,
            "divergence": divergence,
            "signal": signal,
            "interpretation": self._interpret_breadth_divergence(price_trend, latest_breadth),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # OUTPERFORMER/UNDERPERFORMER TRACKING
    # ════════════════════════════════════════════════════════════════════════════

    def rank_outperformers(
        self,
        index_code: str,
        securities_returns: Dict[str, float],
        days: int = 20,
    ) -> List[Dict]:
        """
        Rank securities by relative strength.

        Args:
            index_code: Reference index
            securities_returns: Dict of {security_id: return_pct}
            days: Period to measure

        Returns:
            List of securities ranked by relative strength
        """
        ranked = []

        for security_id, return_pct in securities_returns.items():
            rs = self.calculate_relative_strength(index_code, return_pct, days)

            if "error" not in rs:
                ranked.append({
                    "security_id": security_id,
                    "return_pct": round(return_pct, 2),
                    "relative_strength_pct": rs["relative_strength_pct"],
                    "outperforming": rs["outperforming"],
                    "strength_rating": rs["strength_rating"],
                })

        # Sort by relative strength (highest first)
        ranked.sort(key=lambda x: x["relative_strength_pct"], reverse=True)

        # Add ranking
        for i, item in enumerate(ranked):
            item["rank"] = i + 1

        return ranked

    def get_strength_distribution(
        self,
        index_code: str,
        securities_returns: Dict[str, float],
        days: int = 20,
    ) -> Dict:
        """
        Analyze distribution of relative strength across securities.

        Shows how many are outperforming vs underperforming.
        """
        ranked = self.rank_outperformers(index_code, securities_returns, days)

        outperformers = [s for s in ranked if s["outperforming"]]
        underperformers = [s for s in ranked if not s["outperforming"]]

        total = len(ranked)
        outperf_pct = (len(outperformers) / total * 100) if total > 0 else 0

        return {
            "total_securities": total,
            "outperformers": len(outperformers),
            "underperformers": len(underperformers),
            "outperformer_pct": round(outperf_pct, 1),
            "distribution_quality": self._classify_distribution(outperf_pct),
            "strongest_security": ranked[0]["security_id"] if ranked else None,
            "weakest_security": ranked[-1]["security_id"] if ranked else None,
            "avg_relative_strength": round(
                sum(s["relative_strength_pct"] for s in ranked) / total, 2
            ) if total > 0 else 0,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # RELATIVE STRENGTH TRENDS
    # ════════════════════════════════════════════════════════════════════════════

    def analyze_strength_momentum(
        self,
        index_code: str,
        security_return: float,
        days: int = 20,
    ) -> Dict:
        """
        Analyze momentum of relative strength (is RS accelerating/decelerating?).
        """
        from_date = date.today() - timedelta(days=days)
        mid_date = date.today() - timedelta(days=days // 2)

        # Get index prices for two periods
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            return {"error": "Index not found"}

        first_prices = (
            self.session.query(IndexPrice)
            .filter(
                IndexPrice.index_id == index.index_id,
                IndexPrice.date >= from_date,
                IndexPrice.date < mid_date,
            )
            .order_by(IndexPrice.date)
            .all()
        )

        second_prices = (
            self.session.query(IndexPrice)
            .filter(
                IndexPrice.index_id == index.index_id,
                IndexPrice.date >= mid_date,
            )
            .order_by(IndexPrice.date)
            .all()
        )

        if len(first_prices) < 2 or len(second_prices) < 2:
            return {"error": "Insufficient data"}

        # Calculate index returns for each period
        first_index_return = (
            float((first_prices[-1].close - first_prices[0].close) / first_prices[0].close * 100)
            if first_prices[0].close
            else 0
        )

        second_index_return = (
            float((second_prices[-1].close - second_prices[0].close) / second_prices[0].close * 100)
            if second_prices[0].close
            else 0
        )

        # For simplicity, assume security had proportional return in each period
        # (In real scenario, would track security prices)
        first_rs = security_return * 0.5 - first_index_return
        second_rs = security_return * 0.5 - second_index_return

        rs_momentum = second_rs - first_rs

        return {
            "period_days": days,
            "first_period_rs": round(first_rs, 2),
            "second_period_rs": round(second_rs, 2),
            "rs_momentum": round(rs_momentum, 2),
            "accelerating": rs_momentum > 0,
            "momentum_strength": "Strong" if abs(rs_momentum) > 1 else "Moderate" if abs(rs_momentum) > 0.5 else "Weak",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # STRENGTH RATING REPORTS
    # ════════════════════════════════════════════════════════════════════════════

    def get_market_strength_report(
        self,
        index_code: str,
        days: int = 20,
    ) -> Dict:
        """
        Generate comprehensive market strength report.

        Analyzes overall market health from relative strength perspective.
        """
        from_date = date.today() - timedelta(days=days)

        # Get snapshots
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            return {"error": "Index not found"}

        snapshots = (
            self.session.query(MarketSnapshot)
            .filter(
                MarketSnapshot.index_id == index.index_id,
                MarketSnapshot.date >= from_date,
            )
            .order_by(MarketSnapshot.date)
            .all()
        )

        if not snapshots:
            return {"error": "No data"}

        # Calculate average metrics
        avg_breadth = sum(s.breadth_percent for s in snapshots) / len(snapshots)
        avg_ad_ratio = sum(s.advance_decline_ratio for s in snapshots) / len(snapshots)

        latest = snapshots[-1]
        oldest = snapshots[0]

        return {
            "period_days": days,
            "latest_date": latest.date.isoformat(),
            "breadth_metrics": {
                "current_pct": round(latest.breadth_percent, 1),
                "average_pct": round(avg_breadth, 1),
                "trend": "improving" if latest.breadth_percent > oldest.breadth_percent else "deteriorating",
            },
            "advance_decline": {
                "current_ratio": round(latest.advance_decline_ratio, 2),
                "average_ratio": round(avg_ad_ratio, 2),
                "interpretation": "healthy" if avg_ad_ratio > 1.0 else "weak",
            },
            "market_health": self._rate_market_health(avg_breadth, avg_ad_ratio),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _classify_strength(relative_strength: float) -> str:
        """Classify relative strength level."""
        if relative_strength >= 5:
            return "VERY_STRONG"
        elif relative_strength >= 2:
            return "STRONG"
        elif relative_strength >= -2:
            return "NEUTRAL"
        elif relative_strength >= -5:
            return "WEAK"
        else:
            return "VERY_WEAK"

    @staticmethod
    def _classify_momentum(risk_adjusted_momentum: float) -> str:
        """Classify momentum rating."""
        if risk_adjusted_momentum >= 2:
            return "VERY_STRONG"
        elif risk_adjusted_momentum >= 1:
            return "STRONG"
        elif risk_adjusted_momentum >= 0:
            return "NEUTRAL"
        elif risk_adjusted_momentum >= -1:
            return "WEAK"
        else:
            return "VERY_WEAK"

    @staticmethod
    def _interpret_divergence(divergence: Optional[str], strength: str) -> str:
        """Interpret divergence pattern."""
        if divergence == "BEARISH":
            return "Weakness detected: Price up but volume declining. Caution advised."
        elif divergence == "BULLISH":
            return "Hidden strength: Price down but volume increasing. Potential reversal."
        elif strength == "STRONG_UP":
            return "Healthy rally: Price and volume aligned to upside."
        elif strength == "STRONG_DOWN":
            return "Healthy decline: Price and volume aligned to downside."
        else:
            return "Mixed signals present."

    @staticmethod
    def _interpret_breadth_divergence(price_trend: str, breadth_pct: float) -> str:
        """Interpret breadth-price divergence."""
        if price_trend == "up" and breadth_pct < 50:
            return "Narrow rally: Index up but breadth weak. Quality of advance questionable."
        elif price_trend == "down" and breadth_pct > 50:
            return "Hidden strength: Index down but breadth improving. Selling may be nearing end."
        elif price_trend == "up" and breadth_pct >= 60:
            return "Healthy rally: Broad-based advance. Quality of rally good."
        elif price_trend == "down" and breadth_pct <= 40:
            return "Healthy decline: Broad-based selling. Weakness confirmed."
        else:
            return "Mixed breadth and price signals."

    @staticmethod
    def _classify_distribution(outperformer_pct: float) -> str:
        """Classify distribution quality."""
        if outperformer_pct >= 70:
            return "BROAD"
        elif outperformer_pct >= 50:
            return "BALANCED"
        elif outperformer_pct >= 30:
            return "CONCENTRATED"
        else:
            return "HIGHLY_CONCENTRATED"

    @staticmethod
    def _rate_market_health(breadth_pct: float, ad_ratio: float) -> str:
        """Rate overall market health."""
        breadth_score = 1 if breadth_pct >= 55 else 0
        ad_score = 1 if ad_ratio >= 1.2 else 0

        score = breadth_score + ad_score

        if score == 2:
            return "EXCELLENT"
        elif score == 1:
            return "GOOD"
        else:
            return "WEAK"
