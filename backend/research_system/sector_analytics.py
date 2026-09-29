"""
Sector Analytics Engine - Sprint M4

Sector-level market analysis: performance tracking, relative strength,
and sector contribution analysis.

Features:
- Sector performance tracking (1D, 1W, 1M, 3M, 6M, YTD, 1Y returns)
- Sector ranking and relative strength vs market
- Sector volume and value analysis
- Sector breadth and participation metrics
- Top/bottom performing sectors identification
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .schema_market import SectorSnapshot, IndexPrice, IndexMaster


class SectorPerformanceEngine:
    """Calculate and analyze sector-level performance."""

    def __init__(self, session: Session):
        self.session = session

    # ════════════════════════════════════════════════════════════════════════════
    # SECTOR SNAPSHOT RECORDING
    # ════════════════════════════════════════════════════════════════════════════

    def record_sector_snapshot(
        self,
        index_code: str,
        date: date,
        return_1d: Optional[Decimal] = None,
        return_1w: Optional[Decimal] = None,
        return_1m: Optional[Decimal] = None,
        return_3m: Optional[Decimal] = None,
        return_6m: Optional[Decimal] = None,
        return_ytd: Optional[Decimal] = None,
        return_1y: Optional[Decimal] = None,
        volume: Optional[int] = None,
        value_traded: Optional[Decimal] = None,
        advancers: Optional[int] = None,
        decliners: Optional[int] = None,
    ) -> SectorSnapshot:
        """
        Record daily sector snapshot with returns over multiple timeframes.

        Args:
            index_code: Reference index (e.g., "KSE-100")
            date: Trading date
            return_1d: 1-day return (%)
            return_1w: 1-week return (%)
            return_1m: 1-month return (%)
            return_3m: 3-month return (%)
            return_6m: 6-month return (%)
            return_ytd: Year-to-date return (%)
            return_1y: 1-year return (%)
            volume: Total volume traded in sector
            value_traded: Total value traded (PKR)
            advancers: Number of advancing stocks in sector
            decliners: Number of declining stocks in sector

        Returns:
            SectorSnapshot record
        """
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            raise ValueError(f"Index {index_code} not found")

        # Check if snapshot already exists
        existing = (
            self.session.query(SectorSnapshot)
            .filter_by(index_id=index.index_id, date=date)
            .first()
        )

        if existing:
            # Update existing
            existing.return_1d = return_1d
            existing.return_1w = return_1w
            existing.return_1m = return_1m
            existing.return_3m = return_3m
            existing.return_6m = return_6m
            existing.return_ytd = return_ytd
            existing.return_1y = return_1y
            existing.volume = volume
            existing.value_traded = value_traded
            existing.advancers = advancers
            existing.decliners = decliners
            self.session.commit()
            return existing

        # Create new
        snapshot = SectorSnapshot(
            index_id=index.index_id,
            date=date,
            return_1d=return_1d,
            return_1w=return_1w,
            return_1m=return_1m,
            return_3m=return_3m,
            return_6m=return_6m,
            return_ytd=return_ytd,
            return_1y=return_1y,
            volume=volume,
            value_traded=value_traded,
            advancers=advancers,
            decliners=decliners,
        )

        self.session.add(snapshot)
        self.session.commit()
        return snapshot

    def get_sector_snapshot(self, index_code: str, date: date) -> Optional[SectorSnapshot]:
        """Get sector snapshot for specific date."""
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            return None

        return (
            self.session.query(SectorSnapshot)
            .filter_by(index_id=index.index_id, date=date)
            .first()
        )

    def get_sector_snapshots(
        self,
        index_code: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[SectorSnapshot]:
        """Get sector snapshots in date range."""
        index = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if not index:
            return []

        query = self.session.query(SectorSnapshot).filter_by(index_id=index.index_id)

        if from_date:
            query = query.filter(SectorSnapshot.date >= from_date)
        if to_date:
            query = query.filter(SectorSnapshot.date <= to_date)

        query = query.order_by(SectorSnapshot.date)

        if limit:
            query = query.limit(limit)

        return query.all()

    # ════════════════════════════════════════════════════════════════════════════
    # SECTOR RANKING AND PERFORMANCE
    # ════════════════════════════════════════════════════════════════════════════

    def get_sector_performance_summary(
        self, index_code: str, date: Optional[date] = None
    ) -> Dict:
        """Get sector performance summary for a date."""
        if date is None:
            date = date.today()

        snapshot = self.get_sector_snapshot(index_code, date)

        if not snapshot:
            return {"error": "No data for date"}

        return {
            "date": snapshot.date.isoformat(),
            "performance": {
                "return_1d": float(snapshot.return_1d) if snapshot.return_1d else None,
                "return_1w": float(snapshot.return_1w) if snapshot.return_1w else None,
                "return_1m": float(snapshot.return_1m) if snapshot.return_1m else None,
                "return_3m": float(snapshot.return_3m) if snapshot.return_3m else None,
                "return_6m": float(snapshot.return_6m) if snapshot.return_6m else None,
                "return_ytd": float(snapshot.return_ytd) if snapshot.return_ytd else None,
                "return_1y": float(snapshot.return_1y) if snapshot.return_1y else None,
            },
            "participation": {
                "advancers": snapshot.advancers,
                "decliners": snapshot.decliners,
                "breadth_pct": self._calculate_breadth_pct(snapshot),
            },
            "volume": {
                "shares": snapshot.volume,
                "value_pkr": float(snapshot.value_traded) if snapshot.value_traded else None,
            },
        }

    def get_relative_sector_strength(
        self, index_code: str, period_days: int = 20
    ) -> Dict:
        """
        Calculate sector return relative to market return.

        Shows if sector is outperforming or underperforming index.
        """
        from_date = date.today() - timedelta(days=period_days)

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

        index_return = (
            float((index_prices[-1].close - index_prices[0].close) / index_prices[0].close * 100)
            if index_prices[0].close
            else 0
        )

        # Get sector snapshots
        sector_snapshots = self.get_sector_snapshots(
            index_code, from_date=from_date, to_date=date.today()
        )

        if not sector_snapshots:
            return {"error": "Insufficient sector data"}

        # Use average 1D return as sector return proxy
        sector_returns = [
            float(s.return_1d) for s in sector_snapshots if s.return_1d
        ]
        sector_avg = sum(sector_returns) / len(sector_returns) if sector_returns else 0

        # Relative strength = sector return - index return
        relative_strength = sector_avg - index_return

        return {
            "period_days": period_days,
            "index_return_pct": round(index_return, 2),
            "sector_avg_return_pct": round(sector_avg, 2),
            "relative_strength_pct": round(relative_strength, 2),
            "outperforming": relative_strength > 0,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # SECTOR BREADTH ANALYSIS
    # ════════════════════════════════════════════════════════════════════════════

    def get_sector_breadth_summary(
        self, index_code: str, as_of_date: Optional[date] = None
    ) -> Dict:
        """Analyze sector breadth (participation in price movement)."""
        if as_of_date is None:
            as_of_date = date.today()

        snapshot = self.get_sector_snapshot(index_code, as_of_date)

        if not snapshot:
            return {"error": "No data"}

        breadth_pct = self._calculate_breadth_pct(snapshot)
        total_stocks = (snapshot.advancers or 0) + (snapshot.decliners or 0)

        return {
            "date": snapshot.date.isoformat(),
            "total_stocks": total_stocks,
            "advancers": snapshot.advancers,
            "decliners": snapshot.decliners,
            "breadth_pct": round(breadth_pct, 1),
            "breadth_strength": self._classify_breadth_strength(breadth_pct),
            "healthy_participation": breadth_pct >= 50,
        }

    def get_breadth_trend(
        self, index_code: str, days: int = 20
    ) -> Dict:
        """Analyze breadth trend over period."""
        from_date = date.today() - timedelta(days=days)
        snapshots = self.get_sector_snapshots(index_code, from_date=from_date)

        if len(snapshots) < 2:
            return {"error": "Insufficient data"}

        breadths = [self._calculate_breadth_pct(s) for s in snapshots]

        # Calculate trend
        first_half_avg = sum(breadths[:len(breadths)//2]) / (len(breadths)//2)
        second_half_avg = sum(breadths[len(breadths)//2:]) / (len(breadths) - len(breadths)//2)
        trend = second_half_avg - first_half_avg

        return {
            "period_days": days,
            "latest_breadth_pct": round(breadths[-1], 1),
            "average_breadth_pct": round(sum(breadths) / len(breadths), 1),
            "breadth_trend_change": round(trend, 1),
            "improving": trend > 0,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # SECTOR MOMENTUM AND ANALYSIS
    # ════════════════════════════════════════════════════════════════════════════

    def get_sector_momentum(
        self, index_code: str, days: int = 20
    ) -> Dict:
        """
        Analyze sector momentum (rate of change of returns).

        Shows if sector performance is accelerating or decelerating.
        """
        from_date = date.today() - timedelta(days=days)
        snapshots = self.get_sector_snapshots(index_code, from_date=from_date)

        if len(snapshots) < 2:
            return {"error": "Insufficient data"}

        # Split into two periods
        mid_point = len(snapshots) // 2
        first_half_returns = [
            float(s.return_1d) for s in snapshots[:mid_point] if s.return_1d
        ]
        second_half_returns = [
            float(s.return_1d) for s in snapshots[mid_point:] if s.return_1d
        ]

        first_half_avg = sum(first_half_returns) / len(first_half_returns) if first_half_returns else 0
        second_half_avg = sum(second_half_returns) / len(second_half_returns) if second_half_returns else 0

        momentum = second_half_avg - first_half_avg

        return {
            "period_days": days,
            "first_half_avg_return": round(first_half_avg, 2),
            "second_half_avg_return": round(second_half_avg, 2),
            "momentum_pct": round(momentum, 2),
            "accelerating": momentum > 0,
            "momentum_strength": "Strong" if abs(momentum) > 1 else "Moderate" if abs(momentum) > 0.5 else "Weak",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # SECTOR STATISTICS
    # ════════════════════════════════════════════════════════════════════════════

    def get_sector_statistics(
        self, index_code: str, days: int = 252
    ) -> Dict:
        """Get comprehensive sector statistics over period."""
        from_date = date.today() - timedelta(days=days)
        snapshots = self.get_sector_snapshots(index_code, from_date=from_date)

        if not snapshots:
            return {"error": "No data"}

        returns = [float(s.return_1d) for s in snapshots if s.return_1d]

        if not returns:
            return {"error": "Insufficient return data"}

        # Calculate statistics
        avg_return = sum(returns) / len(returns)
        max_return = max(returns)
        min_return = min(returns)

        # Volatility (std deviation)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5

        # Up/down days
        up_days = sum(1 for r in returns if r > 0)
        down_days = sum(1 for r in returns if r < 0)

        return {
            "period_days": days,
            "trading_days": len(snapshots),
            "average_return_pct": round(avg_return, 2),
            "max_return_pct": round(max_return, 2),
            "min_return_pct": round(min_return, 2),
            "volatility_pct": round(volatility, 2),
            "up_days": up_days,
            "down_days": down_days,
            "up_day_pct": round(up_days / len(returns) * 100, 1) if returns else 0,
        }

    def get_performance_across_periods(
        self, index_code: str, as_of_date: Optional[date] = None
    ) -> Dict:
        """Get sector performance across multiple timeframes."""
        if as_of_date is None:
            as_of_date = date.today()

        snapshot = self.get_sector_snapshot(index_code, as_of_date)

        if not snapshot:
            return {"error": "No data"}

        return {
            "date": snapshot.date.isoformat(),
            "returns": {
                "1_day": float(snapshot.return_1d) if snapshot.return_1d else None,
                "1_week": float(snapshot.return_1w) if snapshot.return_1w else None,
                "1_month": float(snapshot.return_1m) if snapshot.return_1m else None,
                "3_months": float(snapshot.return_3m) if snapshot.return_3m else None,
                "6_months": float(snapshot.return_6m) if snapshot.return_6m else None,
                "ytd": float(snapshot.return_ytd) if snapshot.return_ytd else None,
                "1_year": float(snapshot.return_1y) if snapshot.return_1y else None,
            },
            "trend": self._identify_trend([
                float(snapshot.return_1d) if snapshot.return_1d else 0,
                float(snapshot.return_1w) if snapshot.return_1w else 0,
                float(snapshot.return_1m) if snapshot.return_1m else 0,
            ]),
        }

    def get_sector_report(self, index_code: str, as_of_date: Optional[date] = None) -> Dict:
        """Generate comprehensive sector report."""
        if as_of_date is None:
            as_of_date = date.today()

        return {
            "summary": self.get_sector_performance_summary(index_code, as_of_date),
            "relative_strength": self.get_relative_sector_strength(index_code, period_days=20),
            "breadth": self.get_sector_breadth_summary(index_code, as_of_date),
            "momentum": self.get_sector_momentum(index_code, days=20),
            "statistics": self.get_sector_statistics(index_code, days=252),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _calculate_breadth_pct(snapshot: SectorSnapshot) -> float:
        """Calculate breadth percentage for a sector."""
        total = (snapshot.advancers or 0) + (snapshot.decliners or 0)
        if total == 0:
            return 0
        return (snapshot.advancers / total) * 100 if snapshot.advancers else 0

    @staticmethod
    def _classify_breadth_strength(breadth_pct: float) -> str:
        """Classify breadth strength."""
        if breadth_pct >= 70:
            return "VERY_STRONG"
        elif breadth_pct >= 60:
            return "STRONG"
        elif breadth_pct >= 40:
            return "NEUTRAL"
        elif breadth_pct >= 30:
            return "WEAK"
        else:
            return "VERY_WEAK"

    @staticmethod
    def _identify_trend(returns: List[float]) -> str:
        """Identify trend from returns (1D, 1W, 1M)."""
        if not returns:
            return "UNKNOWN"

        if all(r > 0 for r in returns):
            return "UPTREND"
        elif all(r < 0 for r in returns):
            return "DOWNTREND"
        else:
            return "MIXED"
