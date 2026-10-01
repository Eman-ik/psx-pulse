"""Sprint 3: Leverage and solvency ratio calculations.

Calculate debt ratios, current ratio, interest coverage.
"""
from decimal import Decimal
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.models import FinancialFact


class LeverageCalculations:
    """Calculate leverage and solvency ratios."""

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
    def calculate_debt_to_equity(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate debt-to-equity ratio.

        Formula:
            Debt/Equity = Total Debt / Total Equity

        Where: Total Debt = Short-term Debt + Long-term Debt
        """
        total_debt = LeverageCalculations.get_metric(
            db, company_id, period_id, "total_debt"
        )

        # Fallback: calculate from short and long-term debt
        if not total_debt:
            short_term = LeverageCalculations.get_metric(
                db, company_id, period_id, "short_term_debt"
            )
            long_term = LeverageCalculations.get_metric(
                db, company_id, period_id, "long_term_debt"
            )
            if short_term and long_term:
                total_debt_val = float(short_term.value) + float(long_term.value)
            elif long_term:
                total_debt_val = float(long_term.value)
            else:
                return {"value": None, "status": "incomplete"}
        else:
            total_debt_val = float(total_debt.value)

        equity = LeverageCalculations.get_metric(
            db, company_id, period_id, "total_equity"
        )

        if not equity:
            return {"value": None, "status": "incomplete"}

        equity_val = float(equity.value)
        if equity_val == 0:
            return {"value": None, "status": "incomplete"}

        ratio = total_debt_val / equity_val
        return {
            "value": Decimal(str(round(ratio, 2))),
            "status": "complete",
            "source_facts": [equity.id] if equity else [],
        }

    @staticmethod
    def calculate_current_ratio(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate current ratio (liquidity).

        Formula:
            Current Ratio = Current Assets / Current Liabilities
        """
        current_assets = LeverageCalculations.get_metric(
            db, company_id, period_id, "current_assets"
        )
        current_liabilities = LeverageCalculations.get_metric(
            db, company_id, period_id, "current_liabilities"
        )

        if not current_assets or not current_liabilities:
            return {"value": None, "status": "incomplete"}

        liabilities_val = float(current_liabilities.value)
        if liabilities_val == 0:
            return {"value": None, "status": "incomplete"}

        ratio = float(current_assets.value) / liabilities_val
        return {
            "value": Decimal(str(round(ratio, 2))),
            "status": "complete",
            "source_facts": [current_assets.id, current_liabilities.id],
        }

    @staticmethod
    def calculate_interest_coverage(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate interest coverage ratio.

        Formula:
            Interest Coverage = Operating Profit / Finance Cost

        Higher ratio = better ability to cover interest payments
        """
        operating_profit = LeverageCalculations.get_metric(
            db, company_id, period_id, "operating_profit"
        )
        finance_cost = LeverageCalculations.get_metric(
            db, company_id, period_id, "finance_cost"
        )

        if not operating_profit or not finance_cost:
            return {"value": None, "status": "incomplete"}

        finance_cost_val = float(finance_cost.value)

        # Finance cost is usually negative, take absolute value
        if finance_cost_val == 0:
            return {"value": None, "status": "incomplete"}

        finance_cost_abs = abs(finance_cost_val)
        ratio = float(operating_profit.value) / finance_cost_abs

        return {
            "value": Decimal(str(round(ratio, 2))),
            "status": "complete",
            "source_facts": [operating_profit.id, finance_cost.id],
        }
