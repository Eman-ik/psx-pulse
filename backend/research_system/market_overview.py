"""
Market Overview Engine - Sprint M2

Daily market snapshot calculation: advancers, decliners, volume, 52-week metrics.

Features:
- Market snapshot recording (daily market health)
- Advance/decline ratio calculation
- Breadth percentage calculation
- 52-week high/low tracking
- Market status reporting
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .schema_market import MarketSnapshot, IndexPrice, IndexMaster


class MarketOverviewEngine:
    """Calculate daily market overview metrics."""

    def __init__(self, session: Session):
        self.session = session

    def record_market_snapshot(
        self,
        index_code: str,
        date: date,
        advancers: int,
        decliners: int,
        unchanged: int = 0,
        total_volume: Optional[int] = None,
        total_value_traded: Optional[Decimal] = None,
        upper_locks: int = 0,
        lower_locks: int = 0,
        new_52w_highs: int = 0,
        new_52w_lows: int = 0,
    ) -> MarketSnapshot:
        """
        Record daily market snapshot.

        Args:
            index_code: Reference index (e.g., "KSE-100")
            date: Trading date
            advancers: Number of advancing stocks
            decliners: Number of declining stocks
            unchanged: Number of unchanged stocks
            total_volume: Total volume traded
            total_value_traded: Total value traded (PKR)
            upper_locks: Stocks hitting upper circuit
            lower_locks: Stocks hitting lower circuit
            new_52w_highs: Stocks making new 52-week highs
            new_52w_lows: Stocks making new 52-week lows

        Returns:
            MarketSnapshot record
        """
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            raise ValueError(f"Index {index_code} not found")

        # Check if snapshot already exists
        existing = (
            self.session.query(MarketSnapshot)
            .filter_by(index_id=index.index_id, date=date)
            .first()
        )

        if existing:
            # Update existing
            existing.advancers = advancers
            existing.decliners = decliners
            existing.unchanged = unchanged
            existing.total_volume = total_volume
            existing.total_value_traded = total_value_traded
            existing.upper_locks = upper_locks
            existing.lower_locks = lower_locks
            existing.new_52w_highs = new_52w_highs
            existing.new_52w_lows = new_52w_lows
            self.session.commit()
            return existing

        # Create new
        snapshot = MarketSnapshot(
            index_id=index.index_id,
            date=date,
            advancers=advancers,
            decliners=decliners,
            unchanged=unchanged,
            total_volume=total_volume,
            total_value_traded=total_value_traded,
            upper_locks=upper_locks,
            lower_locks=lower_locks,
            new_52w_highs=new_52w_highs,
            new_52w_lows=new_52w_lows,
        )

        self.session.add(snapshot)
        self.session.commit()
        return snapshot

    def get_latest_snapshot(self, index_code: str) -> Optional[MarketSnapshot]:
        """Get most recent market snapshot."""
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            return None

        return (
            self.session.query(MarketSnapshot)
            .filter_by(index_id=index.index_id)
            .order_by(desc(MarketSnapshot.date))
            .first()
        )

    def get_snapshot(self, index_code: str, date: date) -> Optional[MarketSnapshot]:
        """Get snapshot for specific date."""
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            return None

        return (
            self.session.query(MarketSnapshot)
            .filter_by(index_id=index.index_id, date=date)
            .first()
        )

    def get_snapshots(
        self,
        index_code: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[MarketSnapshot]:
        """Get snapshots in date range."""
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            return []

        query = self.session.query(MarketSnapshot).filter_by(index_id=index.index_id)

        if from_date:
            query = query.filter(MarketSnapshot.date >= from_date)
        if to_date:
            query = query.filter(MarketSnapshot.date <= to_date)

        query = query.order_by(MarketSnapshot.date)

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_market_status(self, index_code: str = "KSE-100") -> Dict:
        """
        Get current market status.

        Returns comprehensive market overview with key metrics.
        """
        snapshot = self.get_latest_snapshot(index_code)
        if not snapshot:
            return {"error": "No market data available"}

        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        latest_price = (
            self.session.query(IndexPrice)
            .filter_by(index_id=index.index_id)
            .order_by(desc(IndexPrice.date))
            .first()
        )

        # Calculate metrics
        total_stocks = snapshot.advancers + snapshot.decliners + (snapshot.unchanged or 0)

        return {
            "index_code": index_code,
            "index_name": index.index_name,
            "date": snapshot.date.isoformat(),
            "index_level": float(latest_price.close) if latest_price else None,
            "index_daily_return_pct": latest_price.daily_return if latest_price else None,
            "advancers": snapshot.advancers,
            "decliners": snapshot.decliners,
            "unchanged": snapshot.unchanged,
            "total_traded": total_stocks,
            "advance_decline_ratio": snapshot.advance_decline_ratio,
            "breadth_percent": snapshot.breadth_percent,
            "volume": snapshot.total_volume,
            "value_traded": float(snapshot.total_value_traded)
            if snapshot.total_value_traded
            else None,
            "upper_locks": snapshot.upper_locks,
            "lower_locks": snapshot.lower_locks,
            "new_52w_highs": snapshot.new_52w_highs,
            "new_52w_lows": snapshot.new_52w_lows,
        }

    def get_market_summary(
        self, index_code: str = "KSE-100", days: int = 30
    ) -> Dict:
        """
        Get market summary over period.

        Shows trends in participation and momentum.
        """
        from_date = date.today() - timedelta(days=days)
        snapshots = self.get_snapshots(index_code, from_date=from_date)

        if not snapshots:
            return {"error": "Insufficient data"}

        # Calculate averages and trends
        avg_advancers = sum(s.advancers for s in snapshots) / len(snapshots)
        avg_decliners = sum(s.decliners for s in snapshots) / len(snapshots)
        avg_breadth = sum(s.breadth_percent for s in snapshots) / len(snapshots)

        # Latest vs oldest
        latest = snapshots[-1]
        oldest = snapshots[0]

        return {
            "period_days": days,
            "trading_days": len(snapshots),
            "latest_snapshot": {
                "date": latest.date.isoformat(),
                "advancers": latest.advancers,
                "decliners": latest.decliners,
                "a_d_ratio": latest.advance_decline_ratio,
                "breadth_percent": latest.breadth_percent,
            },
            "averages": {
                "advancers": round(avg_advancers, 1),
                "decliners": round(avg_decliners, 1),
                "breadth_percent": round(avg_breadth, 1),
            },
            "statistics": {
                "best_day_advancers": max(s.advancers for s in snapshots),
                "worst_day_advancers": min(s.advancers for s in snapshots),
                "best_day_decliners": max(s.decliners for s in snapshots),
                "worst_day_decliners": min(s.decliners for s in snapshots),
            },
            "trend": self._detect_market_trend(snapshots),
        }

    def calculate_advance_decline_line(
        self, index_code: str, days: int = 252
    ) -> List[Dict]:
        """
        Calculate advance-decline line (cumulative A/D).

        Used to detect divergences between index and breadth.
        """
        from_date = date.today() - timedelta(days=days)
        snapshots = self.get_snapshots(index_code, from_date=from_date)

        if not snapshots:
            return []

        cumulative_ad = 0
        result = []

        for snapshot in snapshots:
            ad_value = snapshot.advancers - snapshot.decliners
            cumulative_ad += ad_value
            result.append(
                {
                    "date": snapshot.date.isoformat(),
                    "advancers": snapshot.advancers,
                    "decliners": snapshot.decliners,
                    "daily_ad": ad_value,
                    "cumulative_ad": cumulative_ad,
                }
            )

        return result

    def get_breadth_divergence(self, index_code: str, days: int = 20) -> Dict:
        """
        Detect breadth-index divergence.

        When index goes up but breadth goes down (or vice versa), it indicates
        either weakness (narrow rally) or hidden strength (narrow decline).
        """
        snapshots = self.get_snapshots(index_code, limit=days)

        if len(snapshots) < 2:
            return {"error": "Insufficient data"}

        # Calculate breadth trend
        breadths = [s.breadth_percent for s in snapshots]
        breadth_trend = "improving" if breadths[-1] > breadths[0] else "deteriorating"

        # Get index prices
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        prices = (
            self.session.query(IndexPrice)
            .filter_by(index_id=index.index_id)
            .order_by(IndexPrice.date)
            .limit(days)
            .all()
        )

        if prices:
            price_trend = (
                "up"
                if prices[-1].close > prices[0].close
                else "down"
                if prices[-1].close < prices[0].close
                else "flat"
            )
        else:
            price_trend = "unknown"

        # Detect divergence
        divergence = None
        if price_trend == "up" and breadth_trend == "deteriorating":
            divergence = "BEARISH"  # Rally on narrow breadth
        elif price_trend == "down" and breadth_trend == "improving":
            divergence = "BULLISH"  # Decline on improving breadth (selling pressure easing)

        return {
            "period_days": days,
            "price_trend": price_trend,
            "breadth_trend": breadth_trend,
            "divergence": divergence,
            "interpretation": self._interpret_breadth(price_trend, breadth_trend, divergence),
        }

    def get_market_health_score(self, index_code: str, days: int = 20) -> Dict:
        """
        Generate market health score (0-100).

        Based on:
        - Breadth percentage (% above 50-day MA would be ideal)
        - Advance-decline ratio
        - New highs vs new lows
        """
        snapshot = self.get_latest_snapshot(index_code)
        if not snapshot:
            return {"error": "No data"}

        score = 50  # Start at neutral

        # Breadth component (0-30 points)
        breadth_pct = snapshot.breadth_percent
        if breadth_pct >= 70:
            breadth_score = 30
        elif breadth_pct >= 60:
            breadth_score = 25
        elif breadth_pct >= 50:
            breadth_score = 20
        elif breadth_pct >= 40:
            breadth_score = 15
        elif breadth_pct >= 30:
            breadth_score = 10
        else:
            breadth_score = 5

        # A/D ratio component (0-30 points)
        ad_ratio = snapshot.advance_decline_ratio
        if ad_ratio >= 2.0:
            ad_score = 30
        elif ad_ratio >= 1.5:
            ad_score = 25
        elif ad_ratio >= 1.0:
            ad_score = 20
        elif ad_ratio >= 0.75:
            ad_score = 15
        elif ad_ratio >= 0.5:
            ad_score = 10
        else:
            ad_score = 5

        # Momentum component (0-40 points)
        # New highs vs new lows
        if snapshot.new_52w_highs > 0 and snapshot.new_52w_lows == 0:
            momentum_score = 40
        elif snapshot.new_52w_highs > snapshot.new_52w_lows * 2:
            momentum_score = 30
        elif snapshot.new_52w_highs > snapshot.new_52w_lows:
            momentum_score = 20
        elif snapshot.new_52w_highs == snapshot.new_52w_lows:
            momentum_score = 10
        else:
            momentum_score = 0

        total_score = breadth_score + ad_score + momentum_score

        return {
            "health_score": total_score,
            "rating": self._rate_health(total_score),
            "components": {
                "breadth": {"score": breadth_score, "pct": breadth_pct},
                "advance_decline": {"score": ad_score, "ratio": float(ad_ratio)},
                "momentum": {"score": momentum_score, "highs": snapshot.new_52w_highs, "lows": snapshot.new_52w_lows},
            },
            "interpretation": f"Market health {'strong' if total_score >= 70 else 'weak' if total_score <= 40 else 'neutral'}",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _detect_market_trend(snapshots: List[MarketSnapshot]) -> str:
        """Detect market trend from recent snapshots."""
        if len(snapshots) < 3:
            return "unknown"

        recent_breadth = [s.breadth_percent for s in snapshots[-3:]]
        avg_recent = sum(recent_breadth) / len(recent_breadth)

        if avg_recent >= 65:
            return "strong_up"
        elif avg_recent >= 55:
            return "moderate_up"
        elif avg_recent >= 45:
            return "neutral"
        elif avg_recent >= 35:
            return "moderate_down"
        else:
            return "strong_down"

    @staticmethod
    def _interpret_breadth(price_trend: str, breadth_trend: str, divergence: Optional[str]) -> str:
        """Generate interpretation of breadth."""
        if divergence == "BEARISH":
            return "Weak rally: Index up but breadth declining. Caution advised."
        elif divergence == "BULLISH":
            return "Hidden strength: Selling pressure easing while index down. Potential reversal."
        elif price_trend == "up" and breadth_trend == "improving":
            return "Healthy rally: Index and breadth both improving. Strong signal."
        elif price_trend == "down" and breadth_trend == "deteriorating":
            return "Healthy decline: Index and breadth both weak. Selling continues."
        else:
            return "Mixed signals: Price and breadth moving in different directions."

    @staticmethod
    def _rate_health(score: int) -> str:
        """Rate market health based on score."""
        if score >= 80:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Weak"
        else:
            return "Poor"
