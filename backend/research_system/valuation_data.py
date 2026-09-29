"""
Valuation Data Management

Handles:
- Market snapshots (daily price, shares, market cap)
- Valuation input aggregation
- Valuation snapshot storage
- Historical valuation queries
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from .schema import (
    Security, MarketSnapshot, ValuationInput, ValuationSnapshot,
    Sector
)
from .valuation_engine import ValuationEngine


class ValuationDataManager:
    """Manages valuation data storage and retrieval."""

    def __init__(self, session: Session):
        self.session = session
        self.engine = ValuationEngine(session)

    def record_market_snapshot(
        self,
        security_id: int,
        snapshot_date: date,
        close_price: Decimal,
        shares_outstanding: Decimal,
        trading_volume: Optional[Decimal] = None
    ) -> MarketSnapshot:
        """Record daily market snapshot."""
        market_cap = self.engine.calculate_market_cap(close_price, shares_outstanding)

        snapshot = MarketSnapshot(
            security_id=security_id,
            snapshot_date=snapshot_date,
            close_price=close_price,
            shares_outstanding=shares_outstanding,
            market_cap=market_cap,
            trading_volume=trading_volume
        )

        self.session.add(snapshot)
        self.session.commit()

        return snapshot

    def calculate_and_store_valuation(
        self,
        security_id: int,
        snapshot_date: date,
        close_price: Decimal,
        shares_outstanding: Decimal
    ) -> Optional[ValuationSnapshot]:
        """Calculate valuation metrics and store snapshot."""
        # Record market snapshot
        self.record_market_snapshot(
            security_id, snapshot_date, close_price, shares_outstanding
        )

        # Calculate valuation snapshot
        snapshot = self.engine.create_valuation_snapshot(
            security_id, close_price, shares_outstanding, snapshot_date
        )

        if snapshot:
            self.session.add(snapshot)
            self.session.commit()

        return snapshot

    def get_latest_valuation(
        self,
        security_id: int,
        as_of_date: Optional[date] = None
    ) -> Optional[ValuationSnapshot]:
        """Get most recent valuation snapshot."""
        query = self.session.query(ValuationSnapshot).filter(
            ValuationSnapshot.security_id == security_id
        )

        if as_of_date:
            query = query.filter(ValuationSnapshot.snapshot_date <= as_of_date)

        return query.order_by(desc(ValuationSnapshot.snapshot_date)).first()

    def get_valuation_history(
        self,
        security_id: int,
        days: int = 365
    ) -> List[ValuationSnapshot]:
        """Get valuation history for last N days."""
        cutoff_date = date.today() - timedelta(days=days)

        snapshots = self.session.query(ValuationSnapshot).filter(
            ValuationSnapshot.security_id == security_id,
            ValuationSnapshot.snapshot_date >= cutoff_date
        ).order_by(ValuationSnapshot.snapshot_date).all()

        return snapshots

    def calculate_historical_stats(
        self,
        security_id: int,
        metric: str,
        years: int = 5
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate historical statistics for a valuation metric.
        Returns: median, min, max, 25th percentile, 75th percentile.
        """
        cutoff_date = date.today() - timedelta(days=years * 365)

        snapshots = self.session.query(ValuationSnapshot).filter(
            ValuationSnapshot.security_id == security_id,
            ValuationSnapshot.snapshot_date >= cutoff_date
        ).order_by(ValuationSnapshot.snapshot_date).all()

        if not snapshots:
            return {
                "current": None,
                "median": None,
                "min": None,
                "max": None,
                "p25": None,
                "p75": None,
            }

        # Extract values for metric
        values = []
        current_value = None

        for snapshot in snapshots:
            value = getattr(snapshot, metric, None)
            if value:
                values.append(float(value))
                current_value = float(value)  # Latest is last

        if not values:
            return {
                "current": None,
                "median": None,
                "min": None,
                "max": None,
                "p25": None,
                "p75": None,
            }

        # Sort for percentile calculations
        sorted_values = sorted(values)
        count = len(sorted_values)

        # Calculate statistics
        median_idx = count // 2
        median = Decimal(str(sorted_values[median_idx]))

        p25_idx = count // 4
        p25 = Decimal(str(sorted_values[p25_idx]))

        p75_idx = (3 * count) // 4
        p75 = Decimal(str(sorted_values[p75_idx]))

        return {
            "current": Decimal(str(current_value)) if current_value else None,
            "median": median,
            "min": Decimal(str(min(values))),
            "max": Decimal(str(max(values))),
            "p25": p25,
            "p75": p75,
            "count": count,
        }

    def get_peer_valuation_comparison(
        self,
        peer_tickers: List[str],
        as_of_date: Optional[date] = None
    ) -> Dict[str, Dict]:
        """
        Get valuation comparison for peer group.
        Returns dict of {ticker: valuation metrics}.
        """
        if as_of_date is None:
            as_of_date = date.today()

        result = {}

        for ticker in peer_tickers:
            security = self.session.query(Security).filter(
                Security.ticker == ticker
            ).first()

            if not security:
                continue

            valuation = self.get_latest_valuation(security.security_id, as_of_date)

            if valuation:
                result[ticker] = {
                    "pe_ratio": float(valuation.pe_ratio) if valuation.pe_ratio else None,
                    "pb_ratio": float(valuation.pb_ratio) if valuation.pb_ratio else None,
                    "ps_ratio": float(valuation.ps_ratio) if valuation.ps_ratio else None,
                    "ev_ebitda": float(valuation.ev_ebitda_ratio) if valuation.ev_ebitda_ratio else None,
                    "fcf_yield": float(valuation.fcf_yield) if valuation.fcf_yield else None,
                    "dividend_yield": float(valuation.dividend_yield) if valuation.dividend_yield else None,
                    "enterprise_value": float(valuation.enterprise_value) if valuation.enterprise_value else None,
                }

        return result

    def get_sector_valuation_medians(
        self,
        sector_id: int,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate median valuation metrics for all companies in a sector.
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get all securities in sector
        securities = self.session.query(Security).filter(
            Security.sector_id == sector_id
        ).all()

        if not securities:
            return {}

        # Collect latest valuations
        valuations = []
        for security in securities:
            valuation = self.get_latest_valuation(security.security_id, as_of_date)
            if valuation:
                valuations.append(valuation)

        if not valuations:
            return {}

        # Calculate medians
        metrics = ["pe_ratio", "pb_ratio", "ps_ratio", "ev_ebitda_ratio", "fcf_yield", "dividend_yield"]

        result = {}
        for metric in metrics:
            values = []
            for v in valuations:
                val = getattr(v, metric, None)
                if val:
                    values.append(float(val))

            if values:
                sorted_values = sorted(values)
                median_idx = len(sorted_values) // 2
                result[metric] = Decimal(str(sorted_values[median_idx]))

        return result
