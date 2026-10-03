"""Financial Context Service — Calculate financial metrics from database facts.

Queries financial facts and computes:
- Revenue, PAT growth (%)
- Profitability: net margin, gross margin, ROA, ROE
- Leverage: debt-to-equity, current ratio
- Cash flow quality: OCF/PAT ratio
- Interest coverage

Input: Company ID, database session
Output: FinancialMetrics (ready for StockSnapshot)
"""

import logging
from typing import Optional, List, Tuple
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import FinancialFact
from app.schemas.stock_snapshot import FinancialMetrics

logger = logging.getLogger(__name__)


class FinancialContextService:
    """Calculate financial metrics from database facts."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy session for querying financial facts
        """
        self.db = db

    def analyze(self, issuer_id: int) -> Optional[FinancialMetrics]:
        """Analyze financial metrics for a company.

        Args:
            issuer_id: Company issuer ID

        Returns:
            FinancialMetrics with calculated values or None if insufficient data
        """
        try:
            # Fetch financial facts from database
            facts = self._fetch_facts(issuer_id)
            if not facts:
                logger.warning(f"No financial facts for issuer {issuer_id}")
                return None

            # Group facts by period
            by_period = self._group_by_period(facts)
            periods = sorted(by_period.keys())

            if len(periods) < 2:
                logger.debug(f"Insufficient periods for {issuer_id}: {len(periods)}")
                return None

            # Get latest two periods for comparisons
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

            metrics = FinancialMetrics(
                revenue_growth_pct=revenue_growth,
                pat_growth_pct=pat_growth,
                net_margin_pct=net_margin,
                gross_margin_pct=gross_margin,
                roa_pct=roa,
                roe_pct=roe,
                current_ratio=current_ratio,
                debt_to_equity=debt_to_equity,
                interest_coverage=interest_coverage,
                ocf_to_pat_ratio=ocf_to_pat,
                latest_period_end=periods[-1],
                periods_available=len(periods),
            )

            logger.debug(
                f"{issuer_id}: revenue_growth={revenue_growth}%, "
                f"pat_growth={pat_growth}%, roe={roe}%"
            )
            return metrics

        except Exception as e:
            logger.error(f"Error analyzing financials for {issuer_id}: {e}")
            return None

    def _fetch_facts(self, issuer_id: int) -> List[FinancialFact]:
        """Fetch all financial facts for a company.

        Args:
            issuer_id: Company ID

        Returns:
            List of FinancialFact objects, ordered by period_end desc
        """
        try:
            facts = self.db.execute(
                select(FinancialFact)
                .where(FinancialFact.issuer_id == issuer_id)
                .where(FinancialFact.superseded_by_id.is_(None))
                .where(FinancialFact.period_type.in_(["annual", "quarterly"]))
                .order_by(FinancialFact.period_end.desc())
            ).scalars().all()

            return list(facts)

        except Exception as e:
            logger.error(f"Error fetching facts for {issuer_id}: {e}")
            return []

    def _group_by_period(self, facts: List[FinancialFact]) -> dict[date, dict[str, float]]:
        """Group financial facts by period.

        Args:
            facts: List of FinancialFact objects

        Returns:
            Dict mapping period_end → {line_item: value}
        """
        by_period = {}

        for fact in facts:
            if fact.period_end not in by_period:
                by_period[fact.period_end] = {}

            # Use consolidated scope if available, else standalone
            if fact.scope == "consolidated":
                by_period[fact.period_end][fact.line_item] = fact.value
            elif fact.line_item not in by_period[fact.period_end]:
                by_period[fact.period_end][fact.line_item] = fact.value

        return by_period

    @staticmethod
    def _calculate_growth(current: Optional[float], prior: Optional[float]) -> Optional[float]:
        """Calculate year-over-year growth percentage.

        Args:
            current: Current period value
            prior: Prior period value

        Returns:
            Growth % or None if insufficient data
        """
        if current is None or prior is None or prior == 0:
            return None

        return ((current - prior) / abs(prior)) * 100

    @staticmethod
    def _calculate_margin(metric: Optional[float], revenue: Optional[float]) -> Optional[float]:
        """Calculate margin as % of revenue.

        Args:
            metric: Numerator (e.g., profit_after_tax)
            revenue: Denominator (revenue)

        Returns:
            Margin % or None if insufficient data
        """
        if metric is None or revenue is None or revenue == 0:
            return None

        return (metric / revenue) * 100

    @staticmethod
    def _calculate_return(earnings: Optional[float], base: Optional[float]) -> Optional[float]:
        """Calculate return on asset/equity as %.

        Args:
            earnings: Profit/earnings
            base: Assets or equity

        Returns:
            Return % or None if insufficient data
        """
        if earnings is None or base is None or base == 0:
            return None

        return (earnings / abs(base)) * 100

    @staticmethod
    def _calculate_ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
        """Calculate simple ratio.

        Args:
            numerator: Top number
            denominator: Bottom number

        Returns:
            Ratio or None if insufficient data
        """
        if numerator is None or denominator is None or denominator == 0:
            return None

        return numerator / denominator
