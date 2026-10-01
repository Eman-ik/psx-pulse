"""Sprint 3: Cash flow analysis calculations.

Calculate FCF, margins, conversion rates.
"""
from decimal import Decimal
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.models import FinancialFact


class CashFlowCalculations:
    """Calculate cash flow metrics."""

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
    def calculate_operating_cf_margin(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate operating cash flow as % of revenue.

        Formula:
            Operating CF Margin % = Operating Cash Flow / Revenue × 100

        Indicates what % of revenue converts to actual cash.
        """
        operating_cf = CashFlowCalculations.get_metric(
            db, company_id, period_id, "operating_cash_flow"
        )
        revenue = CashFlowCalculations.get_metric(
            db, company_id, period_id, "revenue"
        )

        if not operating_cf or not revenue:
            return {"value": None, "status": "incomplete"}

        revenue_val = float(revenue.value)
        if revenue_val == 0:
            return {"value": None, "status": "incomplete"}

        margin = (float(operating_cf.value) / revenue_val) * 100
        return {
            "value": Decimal(str(round(margin, 2))),
            "status": "complete",
            "source_facts": [operating_cf.id, revenue.id],
        }

    @staticmethod
    def calculate_fcf(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate free cash flow.

        Formula:
            FCF = Operating Cash Flow - Capital Expenditures

        Or use pre-calculated FCF if available.
        """
        # Try direct FCF first
        fcf = CashFlowCalculations.get_metric(
            db, company_id, period_id, "free_cash_flow"
        )

        if fcf:
            return {
                "value": fcf.value,
                "status": "complete",
                "source_facts": [fcf.id],
            }

        # Calculate from components
        operating_cf = CashFlowCalculations.get_metric(
            db, company_id, period_id, "operating_cash_flow"
        )
        investing_cf = CashFlowCalculations.get_metric(
            db, company_id, period_id, "investing_cash_flow"
        )

        if not operating_cf or not investing_cf:
            return {"value": None, "status": "incomplete"}

        # Investing CF is typically negative (outflow), so add it to operating CF
        fcf_val = float(operating_cf.value) + float(investing_cf.value)

        return {
            "value": Decimal(str(round(fcf_val, 2))),
            "status": "complete",
            "source_facts": [operating_cf.id, investing_cf.id],
        }

    @staticmethod
    def calculate_fcf_margin(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate free cash flow as % of revenue.

        Formula:
            FCF Margin % = Free Cash Flow / Revenue × 100

        Shows quality of earnings - what % of revenue converts to free cash.
        """
        fcf_result = CashFlowCalculations.calculate_fcf(
            db, company_id, period_id
        )

        if fcf_result["status"] == "incomplete":
            return {"value": None, "status": "incomplete"}

        revenue = CashFlowCalculations.get_metric(
            db, company_id, period_id, "revenue"
        )

        if not revenue:
            return {"value": None, "status": "incomplete"}

        revenue_val = float(revenue.value)
        if revenue_val == 0:
            return {"value": None, "status": "incomplete"}

        margin = (float(fcf_result["value"]) / revenue_val) * 100
        return {
            "value": Decimal(str(round(margin, 2))),
            "status": "complete",
            "source_facts": fcf_result["source_facts"] + [revenue.id],
        }

    @staticmethod
    def calculate_fcf_conversion(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate FCF to net income conversion rate.

        Formula:
            FCF Conversion % = Free Cash Flow / Net Income × 100

        Higher % = higher quality earnings (more converted to cash).
        """
        fcf_result = CashFlowCalculations.calculate_fcf(
            db, company_id, period_id
        )

        if fcf_result["status"] == "incomplete":
            return {"value": None, "status": "incomplete"}

        net_income = CashFlowCalculations.get_metric(
            db, company_id, period_id, "net_income"
        )

        if not net_income:
            return {"value": None, "status": "incomplete"}

        net_income_val = float(net_income.value)
        if net_income_val == 0:
            return {"value": None, "status": "incomplete"}

        conversion = (float(fcf_result["value"]) / net_income_val) * 100
        return {
            "value": Decimal(str(round(conversion, 2))),
            "status": "complete",
            "source_facts": fcf_result["source_facts"] + [net_income.id],
        }
