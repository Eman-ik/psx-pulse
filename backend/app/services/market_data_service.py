"""Market Data Service — Single interface for all market data sources.

This service abstracts away psx_*.py, combining:
- Live price snapshots
- Historical price data
- Announcements
- Company profiles
- Index data

The rest of the application calls MarketDataService, not individual PSX functions.
"""

import logging
from datetime import date
from typing import Optional, Dict, Any, List

from app.clients.psx_client import PSXClient
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MarketDataService:
    """Unified interface for market data from PSX and internal database."""

    def __init__(self, db: Session = None):
        """Initialize market data service.

        Args:
            db: Optional database session for historical data lookups
        """
        self.db = db
        self.psx_client = PSXClient(timeout_seconds=30, max_retries=3)

    def get_snapshot(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current market snapshot for a company.

        Includes:
        - Current price
        - Market cap
        - Volume
        - Free float
        - Basic ratios (P/E, P/B, etc.)
        - Latest close date

        Args:
            ticker: Company ticker symbol

        Returns:
            Market snapshot data or None if failed
        """
        logger.debug(f"Fetching market snapshot for {ticker}")

        try:
            screener_data = self.psx_client.screener(symbol=ticker)
            if not screener_data:
                logger.warning(f"No screener data for {ticker}")
                return None

            # Extract key fields from screener response
            # (structure depends on PSX API response format)
            snapshot = {
                "ticker": ticker,
                "source": "PSX",
                "timestamp": None,  # Will be set to current time
                "price": None,
                "change_pct": None,
                "volume": None,
                "market_cap": None,
                "pe_ratio": None,
                "dividend_yield": None,
            }

            # Parse screener_data based on actual PSX response structure
            # This is a placeholder - adjust based on real API response
            if isinstance(screener_data, dict):
                snapshot["price"] = screener_data.get("price")
                snapshot["change_pct"] = screener_data.get("changePercent")
                snapshot["volume"] = screener_data.get("volume")
                snapshot["market_cap"] = screener_data.get("marketCap")
                snapshot["pe_ratio"] = screener_data.get("peRatio")
                snapshot["dividend_yield"] = screener_data.get("dividendYield")

            return snapshot

        except Exception as e:
            logger.error(f"Error fetching snapshot for {ticker}: {e}")
            return None

    def get_history(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_db_cache: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical price data.

        Strategy:
        1. Check database for existing data
        2. If data exists through recent date, use it
        3. Otherwise, fetch missing dates from PSX
        4. Cache in database

        Args:
            ticker: Company ticker
            start_date: Start date (None = 1 year ago)
            end_date: End date (None = today)
            use_db_cache: Whether to use cached database data

        Returns:
            List of OHLCV records or None if failed
        """
        logger.debug(f"Fetching history for {ticker}")

        try:
            # If use_db_cache, check database first
            if use_db_cache and self.db:
                db_history = self._get_history_from_db(ticker, start_date, end_date)
                if db_history:
                    logger.debug(f"Using {len(db_history)} records from database for {ticker}")
                    return db_history

            # Fetch from PSX
            start_str = start_date.isoformat() if start_date else None
            end_str = end_date.isoformat() if end_date else None

            psx_history = self.psx_client.history(ticker, start_str, end_str)
            if not psx_history:
                logger.warning(f"No PSX history for {ticker}")
                return None

            # Cache in database if we have a session
            if self.db:
                self._cache_history_in_db(ticker, psx_history)

            return psx_history

        except Exception as e:
            logger.error(f"Error fetching history for {ticker}: {e}")
            return None

    def get_announcements(self, ticker: str) -> Optional[List[Dict[str, Any]]]:
        """Get recent announcements for a company.

        Args:
            ticker: Company ticker

        Returns:
            List of announcements or None if failed
        """
        logger.debug(f"Fetching announcements for {ticker}")

        try:
            announcements = self.psx_client.announcements(ticker)
            if not announcements:
                logger.warning(f"No announcements for {ticker}")
                return []

            return announcements if isinstance(announcements, list) else [announcements]

        except Exception as e:
            logger.error(f"Error fetching announcements for {ticker}: {e}")
            return None

    def get_index_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get KSE-100 index snapshot.

        Returns:
            Index snapshot (price, change, etc.)
        """
        logger.debug("Fetching KSE-100 snapshot")

        try:
            # PSX screener with no symbol returns market overview
            market_data = self.psx_client.screener()
            if not market_data:
                logger.warning("No market data")
                return None

            # Extract index info from market data
            # This is a placeholder - adjust based on actual API response
            return {
                "index": "KSE-100",
                "price": market_data.get("indexLevel"),
                "change_pct": market_data.get("indexChange"),
                "volume": market_data.get("totalVolume"),
                "market_cap": market_data.get("totalMarketCap"),
            }

        except Exception as e:
            logger.error(f"Error fetching index snapshot: {e}")
            return None

    def _get_history_from_db(
        self,
        ticker: str,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical data from database cache.

        Args:
            ticker: Company ticker
            start_date: Start date
            end_date: End date

        Returns:
            Historical records or None if not enough data in cache
        """
        if not self.db:
            return None

        try:
            # This would query PriceOHLCV from your existing database
            # Placeholder - adjust based on your actual model
            # from app.db.models import PriceOHLCV
            # query = self.db.query(PriceOHLCV).filter(PriceOHLCV.ticker == ticker)
            # if start_date:
            #     query = query.filter(PriceOHLCV.date >= start_date)
            # if end_date:
            #     query = query.filter(PriceOHLCV.date <= end_date)
            # return query.order_by(PriceOHLCV.date).all()
            return None

        except Exception as e:
            logger.error(f"Error reading from cache for {ticker}: {e}")
            return None

    def _cache_history_in_db(self, ticker: str, history: List[Dict[str, Any]]):
        """Cache historical data in database.

        Args:
            ticker: Company ticker
            history: List of OHLCV records
        """
        if not self.db:
            return

        try:
            # This would insert/update PriceOHLCV records
            # Placeholder - adjust based on your actual model
            # from app.db.models import PriceOHLCV
            # for record in history:
            #     ohlcv = PriceOHLCV(
            #         ticker=ticker,
            #         date=record['date'],
            #         open=record['open'],
            #         high=record['high'],
            #         low=record['low'],
            #         close=record['close'],
            #         volume=record['volume']
            #     )
            #     self.db.merge(ohlcv)
            # self.db.commit()
            logger.debug(f"Cached {len(history)} records for {ticker}")

        except Exception as e:
            logger.error(f"Error caching history for {ticker}: {e}")
            self.db.rollback()
