"""Sprint 3: Shareholder return calculations.

Calculate dividend yield, payout ratio, dividend growth.
"""
from decimal import Decimal
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.models import FinancialFact


class ShareholderCalculations:
    """Calculate shareholder-related metrics."""

    @staticmethod
    def get_metric(
        db: Session,
        company_id: int,
        period_id: int,
        metric: str,
    ) -> Optional[FinancialFact]:
        """Get validated financial fact for metric."""
        return db.query(FinancialFact).filter(
            FinancialFact.company_id == company_id,
            FinancialFact.period_id == period_id,
            FinancialFact.metric == metric,
            FinancialFact.validation_status == "validated",
        ).first()

    @staticmethod
    def calculate_dividend_yield(
        db: Session,
        company_id: int,
        period_id: int,
        current_price: Decimal,
    ) -> Dict:
        """Calculate dividend yield.

        Formula:
            Dividend Yield % = Dividend Per Share / Current Stock Price × 100

        Args:
            current_price: Current stock price in PKR
        """
        dps = ShareholderCalculations.get_metric(
            db, company_id, period_id, "dividend_per_share"
        )

        if not dps:
            return {"value": None, "status": "incomplete"}

        if current_price == 0:
            return {"value": None, "status": "incomplete"}

        yield_pct = (float(dps.value) / float(current_price)) * 100
        return {
            "value": Decimal(str(round(yield_pct, 2))),
            "status": "complete",
            "source_facts": [dps.id],
        }

    @staticmethod
    def calculate_payout_ratio(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate dividend payout ratio.

        Formula:
            Payout Ratio % = Total Dividends / Net Income × 100

        Or: Dividends Per Share / Earnings Per Share × 100
        """
        # Try using per-share metrics first
        dps = ShareholderCalculations.get_metric(
            db, company_id, period_id, "dividend_per_share"
        )
        eps = ShareholderCalculations.get_metric(
            db, company_id, period_id, "earnings_per_share"
        )

        if dps and eps:
            eps_val = float(eps.value)
            if eps_val == 0:
                return {"value": None, "status": "incomplete"}

            payout = (float(dps.value) / eps_val) * 100
            return {
                "value": Decimal(str(round(payout, 2))),
                "status": "complete",
                "source_facts": [dps.id, eps.id],
            }

        # Fallback: use total amounts
        dividends = ShareholderCalculations.get_metric(
            db, company_id, period_id, "dividends_paid"
        )
        net_income = ShareholderCalculations.get_metric(
            db, company_id, period_id, "net_income"
        )

        if not dividends or not net_income:
            return {"value": None, "status": "incomplete"}

        net_income_val = float(net_income.value)
        if net_income_val == 0:
            return {"value": None, "status": "incomplete"}

        payout = (float(dividends.value) / net_income_val) * 100
        return {
            "value": Decimal(str(round(payout, 2))),
            "status": "complete",
            "source_facts": [dividends.id, net_income.id],
        }

    @staticmethod
    def calculate_dividend_growth(
        db: Session,
        company_id: int,
        current_period_id: int,
        prior_period_id: int,
    ) -> Dict:
        """Calculate dividend per share growth rate.

        Formula:
            Dividend Growth % = (Current DPS - Prior DPS) / Prior DPS × 100
        """
        current_dps = ShareholderCalculations.get_metric(
            db, company_id, current_period_id, "dividend_per_share"
        )
        prior_dps = ShareholderCalculations.get_metric(
            db, company_id, prior_period_id, "dividend_per_share"
        )

        if not current_dps or not prior_dps:
            return {"value": None, "status": "incomplete"}

        prior_val = float(prior_dps.value)
        if prior_val == 0:
            return {"value": None, "status": "incomplete"}

        growth = ((float(current_dps.value) - prior_val) / prior_val) * 100
        return {
            "value": Decimal(str(round(growth, 2))),
            "status": "complete",
            "source_facts": [current_dps.id, prior_dps.id],
        }

    @staticmethod
    def calculate_eps_to_dps_ratio(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate EPS to DPS ratio (earnings retention).

        Formula:
            EPS/DPS = Earnings Per Share / Dividend Per Share

        Shows how many times earnings can cover dividend payments.
        """
        eps = ShareholderCalculations.get_metric(
            db, company_id, period_id, "earnings_per_share"
        )
        dps = ShareholderCalculations.get_metric(
            db, company_id, period_id, "dividend_per_share"
        )

        if not eps or not dps:
            return {"value": None, "status": "incomplete"}

        dps_val = float(dps.value)
        if dps_val == 0:
            return {"value": None, "status": "incomplete"}

        ratio = float(eps.value) / dps_val
        return {
            "value": Decimal(str(round(ratio, 2))),
            "status": "complete",
            "source_facts": [eps.id, dps.id],
        }
