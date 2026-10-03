"""Snapshot Builder — Constructs StockSnapshot from market and financial data.

Takes raw data from MarketDataService and other sources, normalizes it,
and assembles a complete StockSnapshot for the research pipeline.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.services.market_data_service import MarketDataService
from app.services.technical_calculator import TechnicalCalculator
from app.services.financial_context_service import FinancialContextService
from app.services.macro_context_service import MacroContextService
from app.services.announcement_normalizer import AnnouncementNormalizer
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

            # Build macro context (sector, market cap bracket, index data)
            macro = self._build_macro(ticker, market_cap=market_data.market_cap)

            # Build recent events (normalized announcements)
            recent_events = self._build_recent_events(ticker)

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
                recent_events=recent_events,
                quality=quality,
            )

            logger.info(f"Built snapshot for {ticker}")
            return snapshot

        except Exception as e:
            logger.error(f"Error building snapshot for {ticker}: {e}")
            return None

    def _build_financials(self, ticker: str) -> Optional[FinancialMetrics]:
        """Build financial metrics from database facts.

        Queries financial facts and calculates:
        - Revenue and PAT growth
        - Profitability margins (net, gross)
        - Return on assets and equity
        - Leverage ratios
        - Cash flow quality
        """
        if not self.db:
            logger.debug(f"No database session for financial analysis of {ticker}")
            return None

        try:
            # Get issuer ID from ticker
            from app.db.models import Issuer

            issuer = self.db.execute(
                select(Issuer).where(Issuer.symbol == ticker)
            ).scalar_one_or_none()

            if not issuer:
                logger.debug(f"Issuer not found for {ticker}")
                return None

            # Use FinancialContextService to calculate metrics
            service = FinancialContextService(self.db)
            financials = service.analyze(issuer.id)
            return financials

        except Exception as e:
            logger.error(f"Error building financial metrics for {ticker}: {e}")
            return None

    def _build_valuation(self, ticker: str) -> Optional[ValuationData]:
        """Build valuation multiples.

        Placeholder: Would calculate P/E, P/B, etc. from market and financial data.
        """
        return None

    def _build_technical(self, ticker: str) -> Optional[TechnicalIndicators]:
        """Build technical indicators from historical price data.

        Fetches 1-year price history and computes:
        - Support/resistance (52-week high/low)
        - Trend direction and strength
        - Average volume
        """
        try:
            from datetime import timedelta as td

            # Fetch 52-week price history
            history = self.market_service.get_history(
                ticker,
                start_date=date.today() - td(days=365),
                use_db_cache=True
            )

            if not history:
                logger.debug(f"No price history available for {ticker}")
                return None

            # Calculate technical indicators
            technical = TechnicalCalculator.calculate(ticker, history)
            return technical

        except Exception as e:
            logger.error(f"Error building technical indicators for {ticker}: {e}")
            return None

    def _build_macro(self, ticker: str, market_cap: Optional[float] = None) -> Optional[MacroContext]:
        """Build macro context from sector and economic data.

        Queries:
        - Company sector from Issuer.sector
        - Market cap bracket based on market cap
        - KSE-100 index level and change
        """
        if not self.db:
            logger.debug("No database session for macro context")
            return None

        try:
            # Get issuer ID from ticker
            from app.db.models import Issuer as IssuerModel

            issuer = self.db.execute(
                select(IssuerModel).join(Security).where(Security.symbol == ticker)
            ).scalar_one_or_none()

            if not issuer:
                logger.debug(f"Issuer not found for {ticker}")
                return None

            # Use MacroContextService to build context
            service = MacroContextService(self.db, self.market_service)
            macro = service.analyze(issuer.id, market_cap_millions=market_cap)
            return macro

        except Exception as e:
            logger.error(f"Error building macro context for {ticker}: {e}")
            return None

    def _build_recent_events(self, ticker: str) -> list:
        """Build recent events from normalized announcements.

        Fetches recent announcements and normalizes them into
        structured RecentEvent objects with category, sentiment, materiality.
        """
        try:
            # Fetch announcements from market service
            announcements = self.market_service.get_announcements(ticker)
            if not announcements:
                logger.debug(f"No announcements for {ticker}")
                return []

            # Normalize announcements
            normalizer = AnnouncementNormalizer()
            events = normalizer.normalize_batch(ticker, announcements)

            # Filter to only material events (moderate or higher)
            material_events = [
                e for e in events
                if normalizer.is_material_event(
                    {"title": e.title, "body": e.body},
                    materiality_threshold="moderate"
                )
            ]

            # Limit to 10 most recent material events
            return material_events[:10]

        except Exception as e:
            logger.error(f"Error building recent events for {ticker}: {e}")
            return []

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
