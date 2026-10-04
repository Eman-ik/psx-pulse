"""Historical feature engine — calculate features using only data available at a point in time.

For backtesting, we need features calculated using ONLY data that was actually published by
a given date. This service applies all financial calculations using historical data.

Key: Uses Stage 1 (historical financials) to get facts, ensures no lookahead bias.
"""

from datetime import date
from typing import Optional, List
import logging

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import FinancialFact, Security
from app.services.historical_financials import get_financials_as_of

logger = logging.getLogger(__name__)


class HistoricalFeatures:
    """Feature vector for a company at a point in time."""

    def __init__(
        self,
        symbol: str,
        issuer_id: int,
        as_of_date: date,
        periods_available: int = 0,
        latest_period_end: Optional[date] = None,
        # Growth metrics
        revenue_growth_pct: Optional[float] = None,
        pat_growth_pct: Optional[float] = None,
        # Profitability metrics
        net_margin_pct: Optional[float] = None,
        gross_margin_pct: Optional[float] = None,
        roa_pct: Optional[float] = None,
        roe_pct: Optional[float] = None,
        # Leverage metrics
        debt_to_equity: Optional[float] = None,
        current_ratio: Optional[float] = None,
        interest_coverage: Optional[float] = None,
        # Cash flow
        ocf_to_pat_ratio: Optional[float] = None,
        # Coverage
        data_quality: str = "unknown",  # insufficient | available
    ):
        self.symbol = symbol
        self.issuer_id = issuer_id
        self.as_of_date = as_of_date
        self.periods_available = periods_available
        self.latest_period_end = latest_period_end

        self.revenue_growth_pct = revenue_growth_pct
        self.pat_growth_pct = pat_growth_pct

        self.net_margin_pct = net_margin_pct
        self.gross_margin_pct = gross_margin_pct
        self.roa_pct = roa_pct
        self.roe_pct = roe_pct

        self.debt_to_equity = debt_to_equity
        self.current_ratio = current_ratio
        self.interest_coverage = interest_coverage

        self.ocf_to_pat_ratio = ocf_to_pat_ratio
        self.data_quality = data_quality

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        latest_period_end = self.latest_period_end
        if isinstance(latest_period_end, str):
            latest_period_end_str = latest_period_end
        else:
            latest_period_end_str = latest_period_end.isoformat() if latest_period_end else None

        return {
            "symbol": self.symbol,
            "issuer_id": self.issuer_id,
            "as_of_date": self.as_of_date.isoformat() if isinstance(self.as_of_date, date) else self.as_of_date,
            "periods_available": self.periods_available,
            "latest_period_end": latest_period_end_str,
            "growth": {
                "revenue_pct": self.revenue_growth_pct,
                "pat_pct": self.pat_growth_pct,
            },
            "profitability": {
                "net_margin_pct": self.net_margin_pct,
                "gross_margin_pct": self.gross_margin_pct,
                "roa_pct": self.roa_pct,
                "roe_pct": self.roe_pct,
            },
            "leverage": {
                "debt_to_equity": self.debt_to_equity,
                "current_ratio": self.current_ratio,
                "interest_coverage": self.interest_coverage,
            },
            "cash_flow": {
                "ocf_to_pat_ratio": self.ocf_to_pat_ratio,
            },
            "data_quality": self.data_quality,
        }

    def to_vector(self) -> List[Optional[float]]:
        """Convert to feature vector for ML (excludes metadata)."""
        return [
            self.revenue_growth_pct,
            self.pat_growth_pct,
            self.net_margin_pct,
            self.gross_margin_pct,
            self.roa_pct,
            self.roe_pct,
            self.debt_to_equity,
            self.current_ratio,
            self.interest_coverage,
            self.ocf_to_pat_ratio,
        ]


class HistoricalFeatureEngine:
    """Calculate features using only data available as-of a specific date."""

    def __init__(self, db: Session):
        self.db = db

    def calculate(
        self, symbol: str, as_of_date: date, scope: str = "standalone"
    ) -> HistoricalFeatures:
        """Calculate features for a company as-of a specific date.

        Uses ONLY financial facts published on or before as_of_date (no lookahead).

        Args:
            db: Database session
            symbol: Company ticker symbol
            as_of_date: Calculation date (facts must be published <= this date)
            scope: standalone or consolidated

        Returns:
            HistoricalFeatures object with calculated metrics
        """
        try:
            # Resolve symbol to issuer_id
            security = self.db.execute(
                select(Security).where(
                    Security.symbol == symbol.upper(), Security.is_active.is_(True)
                )
            ).scalar_one_or_none()

            if not security:
                logger.warning(f"No active security for {symbol}")
                return HistoricalFeatures(
                    symbol=symbol.upper(),
                    issuer_id=0,
                    as_of_date=as_of_date,
                    data_quality="insufficient",
                )

            issuer_id = security.issuer_id

            # Get all facts available as-of the date
            facts_response = get_financials_as_of(
                self.db, symbol, as_of_date, scope=scope
            )

            if "error" in facts_response:
                logger.warning(f"No financials for {symbol} as-of {as_of_date}")
                return HistoricalFeatures(
                    symbol=symbol.upper(),
                    issuer_id=issuer_id,
                    as_of_date=as_of_date,
                    data_quality="insufficient",
                )

            facts_list = facts_response.get("facts", [])

            if not facts_list:
                return HistoricalFeatures(
                    symbol=symbol.upper(),
                    issuer_id=issuer_id,
                    as_of_date=as_of_date,
                    data_quality="insufficient",
                )

            # Group facts by period_end
            by_period = self._group_by_period(facts_list)
            periods = sorted(by_period.keys())

            if len(periods) < 2:
                logger.debug(f"Insufficient periods for {symbol}: {len(periods)}")
                return HistoricalFeatures(
                    symbol=symbol.upper(),
                    issuer_id=issuer_id,
                    as_of_date=as_of_date,
                    periods_available=len(periods),
                    data_quality="insufficient",
                )

            # Get latest two periods
            latest = by_period[periods[-1]]
            prior = by_period[periods[-2]]

            # Calculate metrics
            revenue_growth = self._calculate_growth(
                latest.get("revenue"), prior.get("revenue")
            )
            pat_growth = self._calculate_growth(
                latest.get("profit_after_tax"), prior.get("profit_after_tax")
            )
            net_margin = self._calculate_margin(
                latest.get("profit_after_tax"), latest.get("revenue")
            )
            gross_margin = self._calculate_margin(
                latest.get("gross_profit"), latest.get("revenue")
            )
            roa = self._calculate_return(
                latest.get("profit_after_tax"), latest.get("total_assets")
            )
            roe = self._calculate_return(
                latest.get("profit_after_tax"), latest.get("total_equity")
            )
            debt_to_equity = self._calculate_ratio(
                latest.get("total_debt"), latest.get("total_equity")
            )
            current_ratio = self._calculate_ratio(
                latest.get("current_assets"), latest.get("current_liabilities")
            )
            interest_coverage = self._calculate_ratio(
                latest.get("ebit"), latest.get("interest_expense")
            )
            ocf_to_pat = self._calculate_ratio(
                latest.get("operating_cash_flow"), latest.get("profit_after_tax")
            )

            features = HistoricalFeatures(
                symbol=symbol.upper(),
                issuer_id=issuer_id,
                as_of_date=as_of_date,
                periods_available=len(periods),
                latest_period_end=periods[-1],
                revenue_growth_pct=revenue_growth,
                pat_growth_pct=pat_growth,
                net_margin_pct=net_margin,
                gross_margin_pct=gross_margin,
                roa_pct=roa,
                roe_pct=roe,
                debt_to_equity=debt_to_equity,
                current_ratio=current_ratio,
                interest_coverage=interest_coverage,
                ocf_to_pat_ratio=ocf_to_pat,
                data_quality="available",
            )

            logger.debug(
                f"{symbol} as-of {as_of_date}: revenue_growth={revenue_growth}%, "
                f"pat_growth={pat_growth}%, roe={roe}%"
            )
            return features

        except Exception as e:
            logger.error(f"Error calculating features for {symbol} as-of {as_of_date}: {e}")
            return HistoricalFeatures(
                symbol=symbol.upper(),
                issuer_id=0,
                as_of_date=as_of_date,
                data_quality="insufficient",
            )

    @staticmethod
    def _group_by_period(facts_list: List[dict]) -> dict:
        """Group financial facts by period_end.

        Args:
            facts_list: List of fact dicts with line_item, value, period_end

        Returns:
            Dict mapping period_end (as date) → {line_item: value}
        """
        by_period = {}

        for fact in facts_list:
            period_str = fact["period_end"]
            # Convert string to date if needed
            if isinstance(period_str, str):
                from datetime import datetime as dt
                period_key = dt.strptime(period_str, "%Y-%m-%d").date()
            else:
                period_key = period_str

            line_item = fact["line_item"]
            value = fact["value"]

            if period_key not in by_period:
                by_period[period_key] = {}

            # Prefer consolidated scope if available
            if fact.get("scope") == "consolidated":
                by_period[period_key][line_item] = value
            elif line_item not in by_period[period_key]:
                by_period[period_key][line_item] = value

        return by_period

    @staticmethod
    def _calculate_growth(current: Optional[float], prior: Optional[float]) -> Optional[float]:
        """Calculate YoY growth percentage."""
        if current is None or prior is None or prior == 0:
            return None
        return ((current - prior) / abs(prior)) * 100

    @staticmethod
    def _calculate_margin(metric: Optional[float], revenue: Optional[float]) -> Optional[float]:
        """Calculate margin as % of revenue."""
        if metric is None or revenue is None or revenue == 0:
            return None
        return (metric / revenue) * 100

    @staticmethod
    def _calculate_return(earnings: Optional[float], base: Optional[float]) -> Optional[float]:
        """Calculate return on asset/equity as %."""
        if earnings is None or base is None or base == 0:
            return None
        return (earnings / abs(base)) * 100

    @staticmethod
    def _calculate_ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
        """Calculate simple ratio."""
        if numerator is None or denominator is None or denominator == 0:
            return None
        return numerator / denominator
