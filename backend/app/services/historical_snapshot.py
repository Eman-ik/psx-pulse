"""Historical snapshots — unified view of a company on a specific date.

Merges Stages 1-3 into single coherent snapshot:
- Whether company was in investable universe (Stage 2)
- Financial features (Stage 3, calculated from Stage 1)
- Price data (from market database)
- Data quality indicators

This is the complete "state of the company" as it would have been known on any date.
"""

from datetime import date
from typing import Optional, List
import logging

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import Security, PriceOHLCV
from app.services.historical_financials import get_financials_as_of
from app.services.historical_universe import historical_universe
from app.services.historical_feature_engine import HistoricalFeatureEngine, HistoricalFeatures

logger = logging.getLogger(__name__)


class HistoricalSnapshot:
    """Complete snapshot of a company at a point in time."""

    def __init__(
        self,
        symbol: str,
        issuer_id: int,
        as_of_date: date,
        # Universe membership
        is_listed: bool = False,
        has_price_coverage: bool = False,
        has_fundamentals_coverage: bool = False,
        # Price data
        close_price: Optional[float] = None,
        price_date: Optional[date] = None,
        # Features
        features: Optional[HistoricalFeatures] = None,
        # Quality
        snapshot_quality: str = "unknown",  # complete | partial | insufficient
    ):
        self.symbol = symbol
        self.issuer_id = issuer_id
        self.as_of_date = as_of_date

        self.is_listed = is_listed
        self.has_price_coverage = has_price_coverage
        self.has_fundamentals_coverage = has_fundamentals_coverage

        self.close_price = close_price
        self.price_date = price_date

        self.features = features
        self.snapshot_quality = snapshot_quality

    def is_investable(self) -> bool:
        """Returns true if company meets minimum criteria for backtesting."""
        return (
            self.is_listed
            and self.has_price_coverage
            and self.has_fundamentals_coverage
            and self.features
            and self.features.data_quality == "available"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "symbol": self.symbol,
            "issuer_id": self.issuer_id,
            "as_of_date": self.as_of_date.isoformat(),
            "universe_membership": {
                "is_listed": self.is_listed,
                "has_price_coverage": self.has_price_coverage,
                "has_fundamentals_coverage": self.has_fundamentals_coverage,
                "investable": self.is_investable(),
            },
            "price": {
                "close": self.close_price,
                "date": self.price_date.isoformat() if self.price_date else None,
            },
            "features": self.features.to_dict() if self.features else None,
            "snapshot_quality": self.snapshot_quality,
        }


class HistoricalSnapshotEngine:
    """Generate historical snapshots by merging Stages 1-3."""

    def __init__(self, db: Session):
        self.db = db
        self.feature_engine = HistoricalFeatureEngine(db)

    def snapshot(
        self, symbol: str, as_of_date: date, scope: str = "standalone"
    ) -> HistoricalSnapshot:
        """Generate complete snapshot for a company as-of a date.

        Combines:
        - Universe membership (Stage 2)
        - Features (Stage 3, using Stage 1 data)
        - Price data

        Args:
            symbol: Company ticker
            as_of_date: Snapshot date
            scope: standalone or consolidated

        Returns:
            HistoricalSnapshot with all available data
        """
        try:
            # Resolve symbol to issuer_id and security_id
            security = self.db.execute(
                select(Security).where(
                    Security.symbol == symbol.upper(), Security.is_active.is_(True)
                )
            ).scalar_one_or_none()

            if not security:
                logger.warning(f"No active security for {symbol}")
                return HistoricalSnapshot(
                    symbol=symbol.upper(),
                    issuer_id=0,
                    as_of_date=as_of_date,
                    snapshot_quality="insufficient",
                )

            issuer_id = security.issuer_id
            security_id = security.id

            # Check listing date
            is_listed = security.listing_date is None or security.listing_date <= as_of_date

            # Stage 2: Check universe membership
            universe = historical_universe(self.db, as_of_date)
            security_in_universe = any(s["symbol"] == symbol.upper() for s in universe["securities"])

            # Extract coverage for this security
            has_price = False
            has_fundamentals = False
            if security_in_universe:
                for sec_data in universe["securities"]:
                    if sec_data["symbol"] == symbol.upper():
                        has_price = sec_data["price_coverage"]["available"]
                        has_fundamentals = sec_data["fundamentals_coverage"]["available"]
                        break

            # Stage 3: Calculate features
            features = self.feature_engine.calculate(symbol, as_of_date, scope=scope)

            # Get price on as_of_date or most recent before it
            close_price, price_date = self._get_price_as_of(security_id, as_of_date)

            # Determine overall snapshot quality
            snapshot_quality = self._assess_quality(
                is_listed, has_price, has_fundamentals, features, close_price
            )

            snapshot = HistoricalSnapshot(
                symbol=symbol.upper(),
                issuer_id=issuer_id,
                as_of_date=as_of_date,
                is_listed=is_listed,
                has_price_coverage=has_price,
                has_fundamentals_coverage=has_fundamentals,
                close_price=close_price,
                price_date=price_date,
                features=features,
                snapshot_quality=snapshot_quality,
            )

            logger.debug(
                f"{symbol} snapshot as-of {as_of_date}: "
                f"listed={is_listed}, price={has_price}, fundamentals={has_fundamentals}, "
                f"investable={snapshot.is_investable()}"
            )
            return snapshot

        except Exception as e:
            logger.error(f"Error creating snapshot for {symbol} as-of {as_of_date}: {e}")
            return HistoricalSnapshot(
                symbol=symbol.upper(),
                issuer_id=0,
                as_of_date=as_of_date,
                snapshot_quality="insufficient",
            )

    def _get_price_as_of(
        self, security_id: int, as_of_date: date
    ) -> tuple[Optional[float], Optional[date]]:
        """Get closing price on or before as_of_date.

        Args:
            security_id: Security ID
            as_of_date: Reference date

        Returns:
            Tuple of (close_price, price_date) or (None, None)
        """
        try:
            # Get most recent price on or before as_of_date
            price = self.db.execute(
                select(PriceOHLCV)
                .where(
                    PriceOHLCV.security_id == security_id,
                    PriceOHLCV.trade_date <= as_of_date,
                )
                .order_by(PriceOHLCV.trade_date.desc())
                .limit(1)
            ).scalar_one_or_none()

            if price:
                return float(price.close), price.trade_date
            return None, None

        except Exception as e:
            logger.debug(f"Error getting price for security {security_id}: {e}")
            return None, None

    @staticmethod
    def _assess_quality(
        is_listed: bool,
        has_price: bool,
        has_fundamentals: bool,
        features: HistoricalFeatures,
        close_price: Optional[float],
    ) -> str:
        """Assess overall snapshot quality.

        Args:
            is_listed: Whether security was listed
            has_price: Whether price coverage exists
            has_fundamentals: Whether fundamental coverage exists
            features: Calculated features
            close_price: Closing price value

        Returns:
            Quality indicator: complete | partial | insufficient
        """
        if not is_listed or not close_price:
            return "insufficient"

        if (
            has_price
            and has_fundamentals
            and features
            and features.data_quality == "available"
        ):
            return "complete"

        if has_price or has_fundamentals:
            return "partial"

        return "insufficient"

    def snapshot_batch(
        self, symbols: List[str], as_of_date: date, scope: str = "standalone"
    ) -> List[HistoricalSnapshot]:
        """Generate snapshots for multiple symbols on same date.

        Args:
            symbols: List of ticker symbols
            as_of_date: Snapshot date
            scope: standalone or consolidated

        Returns:
            List of HistoricalSnapshot objects
        """
        snapshots = []
        for symbol in symbols:
            snapshot = self.snapshot(symbol, as_of_date, scope=scope)
            snapshots.append(snapshot)
        return snapshots
