"""Macro Context Service — Provide economic and sector context for analysis.

Calculates/fetches:
- Company sector and subsector
- Market cap bracket (micro/small/mid/large)
- KSE-100 index level and change
- PKR/USD forex rate (placeholder for future integration)

Input: Company ID, database session, MarketDataService
Output: MacroContext (ready for StockSnapshot)
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import Issuer, FinancialFact, Sector
from app.services.market_data_service import MarketDataService
from app.schemas.stock_snapshot import MacroContext

logger = logging.getLogger(__name__)


class MacroContextService:
    """Provide macro economic and sector context."""

    # Market cap bracket thresholds (in millions PKR)
    MARKET_CAP_THRESHOLDS = {
        "micro": 500,          # < 500M
        "small": 5_000,        # 500M - 5B
        "mid": 50_000,         # 5B - 50B
        "large": float("inf"),  # 50B+
    }

    def __init__(self, db: Session, market_service: Optional[MarketDataService] = None):
        """Initialize macro context service.

        Args:
            db: SQLAlchemy session for querying company data
            market_service: Optional MarketDataService for index data
        """
        self.db = db
        self.market_service = market_service or MarketDataService()

    def analyze(self, issuer_id: int, market_cap_millions: Optional[float] = None) -> Optional[MacroContext]:
        """Analyze macro context for a company.

        Args:
            issuer_id: Company issuer ID
            market_cap_millions: Optional market cap in millions (to avoid redundant lookup)

        Returns:
            MacroContext with sector, bracket, and index data or None if lookup fails
        """
        try:
            # Fetch issuer to get sector
            issuer = self.db.execute(
                select(Issuer).where(Issuer.id == issuer_id)
            ).scalar_one_or_none()

            if not issuer:
                logger.warning(f"Issuer not found: {issuer_id}")
                return None

            # Get sector name
            sector_name = None
            if issuer.sector_id:
                sector = self.db.execute(
                    select(Sector).where(Sector.id == issuer.sector_id)
                ).scalar_one_or_none()
                if sector:
                    sector_name = sector.name

            # Determine market cap bracket
            bracket = None
            if market_cap_millions is not None:
                bracket = self._get_market_cap_bracket(market_cap_millions)
            else:
                # Try to fetch from latest market cap fact
                market_cap = self._get_latest_market_cap(issuer_id)
                if market_cap:
                    bracket = self._get_market_cap_bracket(market_cap)

            # Get KSE-100 index data
            kse_level = None
            kse_change = None
            try:
                index_snapshot = self.market_service.get_index_snapshot()
                if index_snapshot:
                    kse_level = index_snapshot.get("price")
                    kse_change = index_snapshot.get("change_pct")
            except Exception as e:
                logger.debug(f"Could not fetch KSE-100 data: {e}")

            macro = MacroContext(
                sector=sector_name,
                subsector=None,  # Future: separate subsector tracking
                market_cap_bracket=bracket,
                kse_100_level=kse_level,
                kse_100_change_pct=kse_change,
                # forex_pkr_usd: placeholder for future integration
            )

            logger.debug(
                f"{issuer_id}: sector={sector_name}, bracket={bracket}, "
                f"kse={kse_level}"
            )
            return macro

        except Exception as e:
            logger.error(f"Error analyzing macro context for {issuer_id}: {e}")
            return None

    def _get_market_cap_bracket(self, market_cap_millions: float) -> str:
        """Determine market cap bracket.

        Args:
            market_cap_millions: Market cap in millions PKR

        Returns:
            Bracket name: "micro", "small", "mid", or "large"
        """
        for bracket in ["micro", "small", "mid", "large"]:
            if market_cap_millions < self.MARKET_CAP_THRESHOLDS[bracket]:
                return bracket
        return "large"

    def _get_latest_market_cap(self, issuer_id: int) -> Optional[float]:
        """Get latest market cap from financial facts.

        Args:
            issuer_id: Company issuer ID

        Returns:
            Market cap in millions or None if not found
        """
        try:
            fact = self.db.execute(
                select(FinancialFact)
                .where(FinancialFact.issuer_id == issuer_id)
                .where(FinancialFact.line_item == "market_cap")
                .where(FinancialFact.superseded_by_id.is_(None))
                .order_by(FinancialFact.period_end.desc())
                .limit(1)
            ).scalar_one_or_none()

            if fact:
                return fact.value

            return None

        except Exception as e:
            logger.debug(f"Error fetching market cap for {issuer_id}: {e}")
            return None

    @staticmethod
    def sector_risk_profile(sector_name: Optional[str]) -> dict[str, float]:
        """Get risk profile for a sector (placeholder for future analytics).

        Args:
            sector_name: Sector name

        Returns:
            Risk metrics (volatility, beta, correlation)
        """
        # Placeholder: would query historical sector performance
        sector_profiles = {
            "Fertilizer": {"volatility": 0.35, "beta": 1.2, "correlation_market": 0.75},
            "Cement": {"volatility": 0.40, "beta": 1.4, "correlation_market": 0.80},
            "Banking": {"volatility": 0.25, "beta": 1.0, "correlation_market": 0.85},
            "Energy": {"volatility": 0.45, "beta": 1.5, "correlation_market": 0.70},
        }
        return sector_profiles.get(sector_name, {
            "volatility": 0.30,
            "beta": 1.0,
            "correlation_market": 0.75,
        })

    @staticmethod
    def sector_valuation_median(sector_name: Optional[str]) -> dict[str, float]:
        """Get median valuation metrics for a sector (placeholder).

        Args:
            sector_name: Sector name

        Returns:
            Median P/E, P/B, dividend yield
        """
        # Placeholder: would query database for sector aggregates
        sector_valuations = {
            "Fertilizer": {"pe": 7.5, "pb": 1.2, "dividend_yield": 4.5},
            "Cement": {"pe": 6.8, "pb": 1.0, "dividend_yield": 3.5},
            "Banking": {"pe": 8.5, "pb": 0.9, "dividend_yield": 5.0},
            "Energy": {"pe": 5.0, "pb": 0.7, "dividend_yield": 2.5},
        }
        return sector_valuations.get(sector_name, {
            "pe": 7.0,
            "pb": 1.0,
            "dividend_yield": 4.0,
        })
