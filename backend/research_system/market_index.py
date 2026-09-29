"""
Market Index Engine - Sprint M1

Index Master data management and daily price tracking for PSX indices.

Features:
- Index definition and lifecycle management
- Daily index price storage (OHLCV)
- Index constituent tracking with historical weights
- Index return calculations
- Index joining/rebalancing support
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .schema_market import IndexMaster, IndexPrice, IndexConstituent, IndexType


class MarketIndexEngine:
    """Manage PSX index definitions and daily price data."""

    def __init__(self, session: Session):
        self.session = session

    # ════════════════════════════════════════════════════════════════════════════
    # INDEX MASTER MANAGEMENT
    # ════════════════════════════════════════════════════════════════════════════

    def create_index(
        self,
        index_code: str,
        index_name: str,
        index_type: IndexType = IndexType.MARKET,
        base_date: Optional[date] = None,
        base_value: Decimal = Decimal("100"),
        provider: str = "PSX",
        description: Optional[str] = None,
    ) -> IndexMaster:
        """Create a new index definition."""
        # Check if index already exists
        existing = self.session.query(IndexMaster).filter_by(index_code=index_code).first()
        if existing:
            raise ValueError(f"Index {index_code} already exists")

        index = IndexMaster(
            index_code=index_code,
            index_name=index_name,
            index_type=index_type,
            base_date=base_date or date.today(),
            base_value=base_value,
            provider=provider,
            description=description,
            active=True,
        )

        self.session.add(index)
        self.session.commit()
        return index

    def get_index(self, index_code: str) -> Optional[IndexMaster]:
        """Get index by code."""
        return self.session.query(IndexMaster).filter_by(index_code=index_code).first()

    def list_active_indices(self) -> List[IndexMaster]:
        """List all active indices."""
        return self.session.query(IndexMaster).filter_by(active=True).all()

    def list_indices_by_type(self, index_type: IndexType) -> List[IndexMaster]:
        """List indices by type."""
        return (
            self.session.query(IndexMaster)
            .filter(IndexMaster.index_type == index_type, IndexMaster.active == True)
            .all()
        )

    def deactivate_index(self, index_code: str) -> None:
        """Deactivate an index."""
        index = self.get_index(index_code)
        if not index:
            raise ValueError(f"Index {index_code} not found")
        index.active = False
        self.session.commit()

    # ════════════════════════════════════════════════════════════════════════════
    # INDEX PRICE MANAGEMENT
    # ════════════════════════════════════════════════════════════════════════════

    def record_index_price(
        self,
        index_code: str,
        date: date,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: Optional[int] = None,
        turnover: Optional[Decimal] = None,
    ) -> IndexPrice:
        """Record daily index price (OHLCV)."""
        index = self.get_index(index_code)
        if not index:
            raise ValueError(f"Index {index_code} not found")

        # Check if price already exists for this date
        existing = (
            self.session.query(IndexPrice)
            .filter_by(index_id=index.index_id, date=date)
            .first()
        )
        if existing:
            # Update existing record
            existing.open = open
            existing.high = high
            existing.low = low
            existing.close = close
            existing.volume = volume
            existing.turnover = turnover
            existing.updated_at = datetime.utcnow()
            self.session.commit()
            return existing

        # Create new record
        price = IndexPrice(
            index_id=index.index_id,
            date=date,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            turnover=turnover,
        )

        self.session.add(price)
        self.session.commit()
        return price

    def get_index_price(self, index_code: str, date: date) -> Optional[IndexPrice]:
        """Get index price for specific date."""
        index = self.get_index(index_code)
        if not index:
            return None

        return (
            self.session.query(IndexPrice)
            .filter_by(index_id=index.index_id, date=date)
            .first()
        )

    def get_index_prices(
        self,
        index_code: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[IndexPrice]:
        """Get index prices in date range."""
        index = self.get_index(index_code)
        if not index:
            return []

        query = self.session.query(IndexPrice).filter_by(index_id=index.index_id)

        if from_date:
            query = query.filter(IndexPrice.date >= from_date)
        if to_date:
            query = query.filter(IndexPrice.date <= to_date)

        query = query.order_by(IndexPrice.date)

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_latest_index_price(self, index_code: str) -> Optional[IndexPrice]:
        """Get most recent index price."""
        index = self.get_index(index_code)
        if not index:
            return None

        return (
            self.session.query(IndexPrice)
            .filter_by(index_id=index.index_id)
            .order_by(desc(IndexPrice.date))
            .first()
        )

    def get_index_prices_range(
        self, index_code: str, days: int = 30
    ) -> List[IndexPrice]:
        """Get index prices for last N days."""
        from_date = date.today() - timedelta(days=days)
        return self.get_index_prices(index_code, from_date=from_date)

    # ════════════════════════════════════════════════════════════════════════════
    # INDEX CALCULATIONS
    # ════════════════════════════════════════════════════════════════════════════

    def calculate_daily_return(self, index_code: str, date: date) -> Optional[float]:
        """Calculate daily return as percentage."""
        price = self.get_index_price(index_code, date)
        if not price or not price.open or price.open == 0:
            return None

        return float((price.close - price.open) / price.open * 100)

    def calculate_period_return(
        self, index_code: str, from_date: date, to_date: date
    ) -> Optional[float]:
        """Calculate return over period."""
        start_price = self.get_index_price(index_code, from_date)
        end_price = self.get_index_price(index_code, to_date)

        if not start_price or not end_price:
            return None
        if not start_price.close or start_price.close == 0:
            return None

        return float((end_price.close - start_price.close) / start_price.close * 100)

    def calculate_moving_average(
        self, index_code: str, days: int, as_of_date: Optional[date] = None
    ) -> Optional[Decimal]:
        """Calculate moving average for index."""
        if as_of_date is None:
            as_of_date = date.today()

        from_date = as_of_date - timedelta(days=days)
        prices = self.get_index_prices(index_code, from_date=from_date, to_date=as_of_date)

        if not prices:
            return None

        closes = [p.close for p in prices if p.close]
        if not closes:
            return None

        return sum(closes) / len(closes)

    def get_high_low_range(
        self, index_code: str, days: int, as_of_date: Optional[date] = None
    ) -> Optional[Tuple[Decimal, Decimal]]:
        """Get high and low for period."""
        if as_of_date is None:
            as_of_date = date.today()

        from_date = as_of_date - timedelta(days=days)
        prices = self.get_index_prices(index_code, from_date=from_date, to_date=as_of_date)

        if not prices:
            return None

        highs = [p.high for p in prices if p.high]
        lows = [p.low for p in prices if p.low]

        if not highs or not lows:
            return None

        return (max(highs), min(lows))

    def calculate_volatility(
        self, index_code: str, days: int = 20, as_of_date: Optional[date] = None
    ) -> Optional[float]:
        """Calculate realized volatility (std dev of daily returns)."""
        if as_of_date is None:
            as_of_date = date.today()

        prices = self.get_index_prices_range(index_code, days=days)

        if len(prices) < 2:
            return None

        returns = []
        for i in range(1, len(prices)):
            if prices[i].close and prices[i - 1].close and prices[i - 1].close != 0:
                daily_return = float(
                    (prices[i].close - prices[i - 1].close) / prices[i - 1].close * 100
                )
                returns.append(daily_return)

        if not returns:
            return None

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return float(variance ** 0.5)

    # ════════════════════════════════════════════════════════════════════════════
    # INDEX CONSTITUENTS
    # ════════════════════════════════════════════════════════════════════════════

    def add_constituent(
        self,
        index_code: str,
        security_id: int,
        effective_from: date,
        weight: Optional[Decimal] = None,
    ) -> IndexConstituent:
        """Add security to index."""
        index = self.get_index(index_code)
        if not index:
            raise ValueError(f"Index {index_code} not found")

        # Check if security already a constituent (and currently active)
        active_constituent = (
            self.session.query(IndexConstituent)
            .filter(
                IndexConstituent.index_id == index.index_id,
                IndexConstituent.security_id == security_id,
                IndexConstituent.effective_to == None,
            )
            .first()
        )

        if active_constituent:
            raise ValueError(
                f"Security {security_id} is already in index {index_code}"
            )

        constituent = IndexConstituent(
            index_id=index.index_id,
            security_id=security_id,
            effective_from=effective_from,
            effective_to=None,
            weight=weight,
        )

        self.session.add(constituent)
        self.session.commit()
        return constituent

    def remove_constituent(
        self, index_code: str, security_id: int, effective_to: date
    ) -> None:
        """Remove security from index."""
        index = self.get_index(index_code)
        if not index:
            raise ValueError(f"Index {index_code} not found")

        constituent = (
            self.session.query(IndexConstituent)
            .filter(
                IndexConstituent.index_id == index.index_id,
                IndexConstituent.security_id == security_id,
                IndexConstituent.effective_to == None,
            )
            .first()
        )

        if not constituent:
            raise ValueError(f"Security {security_id} not in index {index_code}")

        constituent.effective_to = effective_to
        self.session.commit()

    def get_index_constituents(
        self, index_code: str, as_of_date: Optional[date] = None
    ) -> List[Dict]:
        """Get current constituents of index."""
        if as_of_date is None:
            as_of_date = date.today()

        index = self.get_index(index_code)
        if not index:
            return []

        constituents = (
            self.session.query(IndexConstituent)
            .filter(
                IndexConstituent.index_id == index.index_id,
                IndexConstituent.effective_from <= as_of_date,
            )
            .filter(
                (IndexConstituent.effective_to == None)
                | (IndexConstituent.effective_to >= as_of_date)
            )
            .all()
        )

        return [
            {
                "security_id": c.security_id,
                "effective_from": c.effective_from,
                "effective_to": c.effective_to,
                "weight": float(c.weight) if c.weight else None,
            }
            for c in constituents
        ]

    def update_constituent_weight(
        self, index_code: str, security_id: int, new_weight: Decimal
    ) -> None:
        """Update constituent weight (e.g., for rebalancing)."""
        index = self.get_index(index_code)
        if not index:
            raise ValueError(f"Index {index_code} not found")

        constituent = (
            self.session.query(IndexConstituent)
            .filter(
                IndexConstituent.index_id == index.index_id,
                IndexConstituent.security_id == security_id,
                IndexConstituent.effective_to == None,
            )
            .first()
        )

        if not constituent:
            raise ValueError(f"Security {security_id} not in index {index_code}")

        constituent.weight = new_weight
        constituent.updated_at = datetime.utcnow()
        self.session.commit()

    # ════════════════════════════════════════════════════════════════════════════
    # INDEX STATISTICS
    # ════════════════════════════════════════════════════════════════════════════

    def get_index_statistics(self, index_code: str, days: int = 252) -> Dict:
        """Get comprehensive index statistics."""
        index = self.get_index(index_code)
        if not index:
            raise ValueError(f"Index {index_code} not found")

        latest = self.get_latest_index_price(index_code)
        if not latest:
            return {"error": "No price data available"}

        from_date = latest.date - timedelta(days=days)
        prices = self.get_index_prices(index_code, from_date=from_date)

        if not prices:
            return {"error": "Insufficient data"}

        # Calculate returns
        first_close = prices[0].close
        latest_close = latest.close

        period_return = (
            float((latest_close - first_close) / first_close * 100)
            if first_close and first_close != 0
            else None
        )

        # High/Low
        highs = [p.high for p in prices if p.high]
        lows = [p.low for p in prices if p.low]
        period_high = max(highs) if highs else None
        period_low = min(lows) if lows else None

        return {
            "index_code": index_code,
            "index_name": index.index_name,
            "latest_price": float(latest.close),
            "latest_date": latest.date.isoformat(),
            "period_days": days,
            "period_return_pct": period_return,
            "period_high": float(period_high) if period_high else None,
            "period_low": float(period_low) if period_low else None,
            "volatility_pct": self.calculate_volatility(index_code, days=days),
            "constituents": len(self.get_index_constituents(index_code)),
        }
