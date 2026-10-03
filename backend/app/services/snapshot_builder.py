"""Snapshot Builder — Constructs StockSnapshot from market and financial data.

Takes raw data from MarketDataService and other sources, normalizes it,
and assembles a complete StockSnapshot for the research pipeline.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.services.market_data_service import MarketDataService
from app.schemas.stock_snapshot import (
    StockSnapshot,
    MarketData,
    FinancialMetrics,
    ValuationData,
    TechnicalIndicators,
    MacroContext,
    DataQuality,
)

logger = logging.getLogger(__name__)


class SnapshotBuilder:
    """Constructs a complete StockSnapshot from heterogeneous data sources."""

    def __init__(self, db: Optional[Session] = None):
        """Initialize builder with optional database session."""
        self.db = db
        self.market_service = MarketDataService(db=db)

    def build(self, ticker: str, company_name: Optional[str] = None) -> Optional[StockSnapshot]:
        """Build a complete snapshot for a company.

        Args:
            ticker: Company ticker symbol
            company_name: Optional company name (for display)

        Returns:
            Complete StockSnapshot or None if build fails
        """
        logger.debug(f"Building snapshot for {ticker}")

        try:
            # Fetch market snapshot
            market_snapshot = self.market_service.get_snapshot(ticker)
            if not market_snapshot:
                logger.warning(f"Could not fetch market data for {ticker}")
                return None

            # Build market data section
            market_data = MarketData(
                ticker=ticker,
                price=market_snapshot.get("price"),
                price_date=date.today(),
                change_pct=market_snapshot.get("change_pct"),
                volume=market_snapshot.get("volume"),
                market_cap=market_snapshot.get("market_cap"),
                source="PSX",
            )

            # Build financial metrics (placeholder - would fetch from database)
            financials = self._build_financials(ticker)

            # Build valuation data (placeholder - would fetch from database)
            valuation = self._build_valuation(ticker)

            # Build technical data (placeholder - would fetch from database)
            technical = self._build_technical(ticker)

            # Build macro context (placeholder - would fetch from market service)
            macro = self._build_macro()

            # Build data quality metadata
            quality = DataQuality(
                snapshot_time=datetime.utcnow(),
                market_data_confidence=self._assess_market_confidence(market_snapshot),
                financial_data_confidence="low",  # Placeholder
                market_data_freshness_days=0,
            )

            # Assemble snapshot
            snapshot = StockSnapshot(
                ticker=ticker,
                company_name=company_name,
                market=market_data,
                financials=financials,
                valuation=valuation,
                technical=technical,
                macro=macro,
                quality=quality,
            )

            logger.info(f"Built snapshot for {ticker}")
            return snapshot

        except Exception as e:
            logger.error(f"Error building snapshot for {ticker}: {e}")
            return None

    def _build_financials(self, ticker: str) -> Optional[FinancialMetrics]:
        """Build financial metrics from database.

        Placeholder: Would query ResearchContext for multi-period metrics.
        """
        return None

    def _build_valuation(self, ticker: str) -> Optional[ValuationData]:
        """Build valuation multiples.

        Placeholder: Would calculate P/E, P/B, etc. from market and financial data.
        """
        return None

    def _build_technical(self, ticker: str) -> Optional[TechnicalIndicators]:
        """Build technical indicators.

        Placeholder: Would fetch 52-week range and trend from price history.
        """
        return None

    def _build_macro(self) -> Optional[MacroContext]:
        """Build macro context.

        Placeholder: Would fetch KSE-100 level and market conditions.
        """
        macro = MacroContext()

        # Try to fetch KSE-100 snapshot
        try:
            index_snapshot = self.market_service.get_index_snapshot()
            if index_snapshot:
                macro.kse_100_level = index_snapshot.get("price")
                macro.kse_100_change_pct = index_snapshot.get("change_pct")
        except Exception as e:
            logger.debug(f"Could not fetch index snapshot: {e}")

        return macro

    def _assess_market_confidence(self, market_snapshot: dict) -> str:
        """Assess confidence in market data.

        Args:
            market_snapshot: Raw market data from service

        Returns:
            "high", "medium", or "low"
        """
        if not market_snapshot:
            return "low"

        # High confidence: has price and volume
        if market_snapshot.get("price") and market_snapshot.get("volume"):
            return "high"

        # Medium: has price but missing volume
        if market_snapshot.get("price"):
            return "medium"

        return "low"
