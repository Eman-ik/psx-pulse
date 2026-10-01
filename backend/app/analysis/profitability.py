"""Sprint 3: Profitability ratio calculations.

Calculate margins, ROE, ROA from financial facts.
"""
from decimal import Decimal
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.models import FinancialFact


class ProfitabilityCalculations:
    """Calculate profitability ratios from financial facts."""

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
    def calculate_gross_margin(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate gross profit margin.

        Formula:
            Gross Margin % = Gross Profit / Revenue × 100
        """
        gross_profit = ProfitabilityCalculations.get_metric(
            db, company_id, period_id, "gross_profit"
        )
        revenue = ProfitabilityCalculations.get_metric(
            db, company_id, period_id, "revenue"
        )

        if not gross_profit or not revenue:
            return {
                "value": None,
                "status": "incomplete",
                "missing": ["gross_profit" if not gross_profit else "", "revenue" if not revenue else ""],
            }

        revenue_val = float(revenue.value)
        if revenue_val == 0:
            return {"value": None, "status": "incomplete", "missing": ["Revenue is zero"]}

        margin = (float(gross_profit.value) / revenue_val) * 100
        return {
            "value": Decimal(str(round(margin, 2))),
            "status": "complete",
            "source_facts": [gross_profit.id, revenue.id],
        }

    @staticmethod
    def calculate_operating_margin(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate operating profit margin.

        Formula:
            Operating Margin % = Operating Profit / Revenue × 100
        """
        operating_profit = ProfitabilityCalculations.get_metric(
            db, company_id, period_id, "operating_profit"
        )
        revenue = ProfitabilityCalculations.get_metric(
            db, company_id, period_id, "revenue"
        )

        if not operating_profit or not revenue:
            return {"value": None, "status": "incomplete"}

        revenue_val = float(revenue.value)
        if revenue_val == 0:
            return {"value": None, "status": "incomplete"}

        margin = (float(operating_profit.value) / revenue_val) * 100
        return {
            "value": Decimal(str(round(margin, 2))),
            "status": "complete",
            "source_facts": [operating_profit.id, revenue.id],
        }

    @staticmethod
    def calculate_net_margin(
        db: Session,
        company_id: int,
        period_id: int,
    ) -> Dict:
        """Calculate net profit margin.

        Formula:
            Net Margin % = Net Income / Revenue × 100
        """
        net_income = ProfitabilityCalculations.get_metric(
            db, company_id, period_id, "net_income"
        )
        revenue = ProfitabilityCalculations.get_metric(
            db, company_id, period_id, "revenue"
        )

        if not net_income or not revenue:
            return {"value": None, "status": "incomplete"}

        revenue_val = float(revenue.value)
        if revenue_val == 0:
            return {"value": None, "status": "incomplete"}

        margin = (float(net_income.value) / revenue_val) * 100
        return {
            "value": Decimal(str(round(margin, 2))),
            "status": "complete",
            "source_facts": [net_income.id, revenue.id],
        }

    @staticmethod
    def calculate_roe(
        db: Session,
        company_id: int,
        current_period_id: int,
        prior_period_id: int,
    ) -> Dict:
        """Calculate return on equity.

        Formula:
            ROE % = Net Income / Average Shareholder Equity × 100

            Where: Average Equity = (Opening Equity + Closing Equity) / 2
        """
        current_ni = ProfitabilityCalculations.get_metric(
            db, company_id, current_period_id, "net_income"
        )
        current_equity = ProfitabilityCalculations.get_metric(
            db, company_id, current_period_id, "total_equity"
        )
        prior_equity = ProfitabilityCalculations.get_metric(
            db, company_id, prior_period_id, "total_equity"
        )

        if not current_ni or not current_equity or not prior_equity:
            return {"value": None, "status": "incomplete"}

        net_income_val = float(current_ni.value)
        avg_equity = (float(current_equity.value) + float(prior_equity.value)) / 2

        if avg_equity == 0:
            return {"value": None, "status": "incomplete"}

        roe = (net_income_val / avg_equity) * 100
        return {
            "value": Decimal(str(round(roe, 2))),
            "status": "complete",
            "source_facts": [current_ni.id, current_equity.id, prior_equity.id],
        }

    @staticmethod
    def calculate_roa(
        db: Session,
        company_id: int,
        current_period_id: int,
        prior_period_id: int,
    ) -> Dict:
        """Calculate return on assets.

        Formula:
            ROA % = Net Income / Average Total Assets × 100
        """
        current_ni = ProfitabilityCalculations.get_metric(
            db, company_id, current_period_id, "net_income"
        )
        current_assets = ProfitabilityCalculations.get_metric(
            db, company_id, current_period_id, "total_assets"
        )
        prior_assets = ProfitabilityCalculations.get_metric(
            db, company_id, prior_period_id, "total_assets"
        )

        if not current_ni or not current_assets or not prior_assets:
            return {"value": None, "status": "incomplete"}

        net_income_val = float(current_ni.value)
        avg_assets = (float(current_assets.value) + float(prior_assets.value)) / 2

        if avg_assets == 0:
            return {"value": None, "status": "incomplete"}

        roa = (net_income_val / avg_assets) * 100
        return {
            "value": Decimal(str(round(roa, 2))),
            "status": "complete",
            "source_facts": [current_ni.id, current_assets.id, prior_assets.id],
        }
