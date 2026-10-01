"""Sprint 3: Growth rate calculations.

Calculate year-over-year growth rates for revenue, profit, and earnings.
"""
from decimal import Decimal
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from app.models import Company, Period, FinancialFact


class GrowthCalculations:
    """Calculate growth rates from financial facts."""

    @staticmethod
    def get_metric_for_period(
        db: Session,
        company_id: int,
        period_id: int,
        metric: str,
    ) -> Optional[FinancialFact]:
        """Get validated financial fact for metric in period.

        Returns None if fact missing or not validated.
        """
        fact = db.query(FinancialFact).filter(
            FinancialFact.company_id == company_id,
            FinancialFact.period_id == period_id,
            FinancialFact.metric == metric,
            FinancialFact.validation_status == "validated",
        ).first()
        return fact

    @staticmethod
    def calculate_revenue_growth(
        db: Session,
        company_id: int,
        current_period_id: int,
        prior_period_id: int,
    ) -> Dict:
        """Calculate revenue growth rate (current - prior) / prior.

        Formula:
            Revenue Growth % = (Current Revenue - Prior Revenue) / Prior Revenue × 100

        Args:
            current_period_id: Current year period
            prior_period_id: Previous year period

        Returns:
            {
                'value': Decimal (as percentage),
                'status': 'complete' or 'incomplete',
                'source_facts': [fact_ids],
                'missing': [metric_names]
            }
        """
        current_revenue = GrowthCalculations.get_metric_for_period(
            db, company_id, current_period_id, "revenue"
        )
        prior_revenue = GrowthCalculations.get_metric_for_period(
            db, company_id, prior_period_id, "revenue"
        )

        if not current_revenue or not prior_revenue:
            missing = []
            if not current_revenue:
                missing.append("revenue (current period)")
            if not prior_revenue:
                missing.append("revenue (prior period)")
            return {
                "value": None,
                "status": "incomplete",
                "source_facts": [],
                "missing": missing,
            }

        current_val = float(current_revenue.value)
        prior_val = float(prior_revenue.value)

        if prior_val == 0:
            return {
                "value": None,
                "status": "incomplete",
                "source_facts": [current_revenue.id, prior_revenue.id],
                "missing": ["Prior revenue is zero (cannot calculate growth)"],
            }

        growth = ((current_val - prior_val) / prior_val) * 100

        return {
            "value": Decimal(str(round(growth, 2))),
            "status": "complete",
            "source_facts": [current_revenue.id, prior_revenue.id],
            "missing": [],
        }

    @staticmethod
    def calculate_profit_growth(
        db: Session,
        company_id: int,
        current_period_id: int,
        prior_period_id: int,
    ) -> Dict:
        """Calculate net profit growth rate.

        Formula:
            Profit Growth % = (Current Net Income - Prior Net Income) / Prior Net Income × 100
        """
        current_profit = GrowthCalculations.get_metric_for_period(
            db, company_id, current_period_id, "net_income"
        )
        prior_profit = GrowthCalculations.get_metric_for_period(
            db, company_id, prior_period_id, "net_income"
        )

        if not current_profit or not prior_profit:
            missing = []
            if not current_profit:
                missing.append("net_income (current period)")
            if not prior_profit:
                missing.append("net_income (prior period)")
            return {
                "value": None,
                "status": "incomplete",
                "source_facts": [],
                "missing": missing,
            }

        current_val = float(current_profit.value)
        prior_val = float(prior_profit.value)

        if prior_val == 0:
            return {
                "value": None,
                "status": "incomplete",
                "source_facts": [current_profit.id, prior_profit.id],
                "missing": ["Prior net income is zero (cannot calculate growth)"],
            }

        growth = ((current_val - prior_val) / prior_val) * 100

        return {
            "value": Decimal(str(round(growth, 2))),
            "status": "complete",
            "source_facts": [current_profit.id, prior_profit.id],
            "missing": [],
        }

    @staticmethod
    def calculate_eps_growth(
        db: Session,
        company_id: int,
        current_period_id: int,
        prior_period_id: int,
    ) -> Dict:
        """Calculate earnings per share growth rate.

        Formula:
            EPS Growth % = (Current EPS - Prior EPS) / Prior EPS × 100

        Note: Uses reported EPS if available, otherwise calculates from net_income / shares.
        """
        current_eps = GrowthCalculations.get_metric_for_period(
            db, company_id, current_period_id, "earnings_per_share"
        )
        prior_eps = GrowthCalculations.get_metric_for_period(
            db, company_id, prior_period_id, "earnings_per_share"
        )

        # Fallback: calculate EPS from net_income / shares if not directly available
        if not current_eps:
            current_ni = GrowthCalculations.get_metric_for_period(
                db, company_id, current_period_id, "net_income"
            )
            current_shares = GrowthCalculations.get_metric_for_period(
                db, company_id, current_period_id, "weighted_shares_outstanding"
            )
            if current_ni and current_shares and float(current_shares.value) > 0:
                current_eps_val = Decimal(
                    str(float(current_ni.value) / float(current_shares.value))
                )
            else:
                current_eps_val = None
        else:
            current_eps_val = current_eps.value

        if not prior_eps:
            prior_ni = GrowthCalculations.get_metric_for_period(
                db, company_id, prior_period_id, "net_income"
            )
            prior_shares = GrowthCalculations.get_metric_for_period(
                db, company_id, prior_period_id, "weighted_shares_outstanding"
            )
            if prior_ni and prior_shares and float(prior_shares.value) > 0:
                prior_eps_val = Decimal(
                    str(float(prior_ni.value) / float(prior_shares.value))
                )
            else:
                prior_eps_val = None
        else:
            prior_eps_val = prior_eps.value

        if not current_eps_val or not prior_eps_val:
            missing = []
            if not current_eps_val:
                missing.append("eps (current period)")
            if not prior_eps_val:
                missing.append("eps (prior period)")
            return {
                "value": None,
                "status": "incomplete",
                "source_facts": [],
                "missing": missing,
            }

        current_val = float(current_eps_val)
        prior_val = float(prior_eps_val)

        if prior_val == 0:
            return {
                "value": None,
                "status": "incomplete",
                "source_facts": [current_eps.id, prior_eps.id] if current_eps and prior_eps else [],
                "missing": ["Prior EPS is zero (cannot calculate growth)"],
            }

        growth = ((current_val - prior_val) / prior_val) * 100

        return {
            "value": Decimal(str(round(growth, 2))),
            "status": "complete",
            "source_facts": [
                current_eps.id if current_eps else current_eps.id,
                prior_eps.id if prior_eps else prior_eps.id,
            ],
            "missing": [],
        }
