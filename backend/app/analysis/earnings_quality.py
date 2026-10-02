"""Earnings Quality Engine — identifies whether reported profit reflects underlying earnings.

Reported profit increased 31%, but underlying operating earnings increased only ~12%.
Roughly one-third of the earnings improvement came from higher other income, so headline
EPS growth overstates the improvement in the core business.
"""

from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import FinancialFact


class EarningsQualityEngine:
    """Assess quality and sustainability of reported earnings."""

    @staticmethod
    def get_metric_value(db: Session, issuer_id: int, period_end, metric: str) -> Optional[float]:
        """Get metric value for a specific period_end date."""
        result = db.execute(
            select(FinancialFact.value).where(
                FinancialFact.issuer_id == issuer_id,
                FinancialFact.period_end == period_end,
                FinancialFact.line_item == metric,
                FinancialFact.superseded_by_id.is_(None),
            )
        ).scalar_one_or_none()
        return float(result) if result is not None else None

    @staticmethod
    def get_latest_period(db: Session, issuer_id: int):
        """Get latest period_end with financial facts."""
        result = db.execute(
            select(FinancialFact.period_end)
            .where(FinancialFact.issuer_id == issuer_id)
            .order_by(FinancialFact.period_end.desc())
            .limit(1)
        ).scalar_one_or_none()
        return result

    @staticmethod
    def analyze(db: Session, issuer_id: int, period_id: Optional[int] = None) -> Dict:
        """Assess earnings quality in a period."""
        if period_id is None:
            period_id = EarningsQualityEngine.get_latest_period(db, issuer_id)
        if period_id is None:
            return {
                "status": "no_data",
                "quality": "Unknown",
                "narrative": "Insufficient financial data.",
            }

        pat = EarningsQualityEngine.get_metric_value(db, issuer_id, period_id, "profit_after_tax")
        ebit = EarningsQualityEngine.get_metric_value(db, issuer_id, period_id, "operating_profit")
        ocf = EarningsQualityEngine.get_metric_value(db, issuer_id, period_id, "operating_cash_flow")
        other_income = EarningsQualityEngine.get_metric_value(db, issuer_id, period_id, "other_income")
        finance_cost = EarningsQualityEngine.get_metric_value(db, issuer_id, period_id, "finance_cost")
        revenue = EarningsQualityEngine.get_metric_value(db, issuer_id, period_id, "revenue")
        tax_expense = EarningsQualityEngine.get_metric_value(db, issuer_id, period_id, "tax_expense")

        issues = []
        positive_indicators = []

        # Check 1: PAT vs OCF
        if pat and ocf:
            if ocf > pat * 1.1:
                positive_indicators.append("Operating cash flow exceeds reported earnings, supporting earnings quality.")
            elif ocf < pat * 0.7:
                issues.append(f"Operating cash flow ({ocf:.0f}) is much weaker than reported earnings ({pat:.0f}), suggesting quality concerns.")

        # Check 2: Other income contribution
        if other_income and pat and ebit:
            other_income_pct = other_income / pat * 100 if pat > 0 else 0
            if other_income_pct > 25:
                issues.append(f"Other income represents {other_income_pct:.0f}% of reported profit, overstating core business earnings.")
            elif other_income_pct > 10:
                issues.append(f"Other income contributes {other_income_pct:.0f}% to reported profit.")

        # Check 3: Finance cost trend
        if finance_cost and ebit and revenue:
            finance_cost_pct = finance_cost / ebit * 100 if ebit > 0 else 0
            if finance_cost_pct > 30:
                issues.append(f"Finance costs consume {finance_cost_pct:.0f}% of EBIT, materially reducing net earnings.")

        # Check 4: Tax rate normality
        if tax_expense and pat:
            if ebit:
                tax_rate = tax_expense / ebit * 100 if ebit > 0 else 0
                if tax_rate < 5:
                    issues.append("Tax rate is unusually low; earnings may include one-off tax benefits.")
                elif tax_rate > 40:
                    issues.append("Tax rate is unusually high; reported earnings may be suppressed by extraordinary tax charges.")

        # Check 5: Operating leverage
        if revenue and ebit and pat:
            ebit_margin = ebit / revenue * 100 if revenue > 0 else 0
            pat_margin = pat / revenue * 100 if revenue > 0 else 0
            if ebit_margin > 0 and pat_margin > 0:
                leverage_ratio = ebit_margin / pat_margin
                if leverage_ratio > 2:
                    issues.append(f"EBIT margin ({ebit_margin:.1f}%) is {leverage_ratio:.1f}x the net margin, indicating significant below-the-line erosion.")

        # Overall quality score (0-100)
        quality_score = 100
        quality_score -= len(issues) * 15
        quality_score = max(20, quality_score)

        if quality_score >= 80:
            quality = "High"
            narrative = "Reported earnings are well-supported by operating cash flow and operating metrics. "
        elif quality_score >= 60:
            quality = "Moderate"
            narrative = "Reported earnings are partially supported by operating cash flow. "
        else:
            quality = "Low"
            narrative = "Reported earnings should be treated with caution due to quality concerns. "

        if positive_indicators:
            narrative += " ".join(positive_indicators) + " "
        if issues:
            narrative += " ".join(issues)

        return {
            "status": "complete",
            "quality": quality,
            "quality_score": quality_score,
            "issues": issues,
            "positive_indicators": positive_indicators,
            "narrative": narrative,
            "metrics_analyzed": {
                "pat": pat,
                "ocf": ocf,
                "ebit": ebit,
                "other_income": other_income,
                "finance_cost": finance_cost,
            },
        }
