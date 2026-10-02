"""Earnings Quality Engine v2 — using Evidence Context for integrity.

Identifies whether reported profit reflects underlying earnings.
NOW WITH: Separate confidence/coverage from assessment.
"""

from typing import Optional, Dict

from app.analysis.evidence_context import ResearchContext, ContextualizedOutput
from app.analysis.period_alignment import PeriodAlignedAnalyzer


class EarningsQualityEngine:
    """Assess quality and sustainability of reported earnings."""

    @staticmethod
    def analyze(context: ResearchContext) -> Dict:
        """Assess earnings quality using period-aligned Evidence Context."""
        output = ContextualizedOutput("earnings_quality", context)
        analyzer = PeriodAlignedAnalyzer(context)

        # Check critical metrics upfront
        has_pat = context.has_metric("profit_after_tax")
        has_ocf = context.has_metric("operating_cash_flow")
        has_ebit = context.has_metric("operating_profit")
        has_other_income = context.has_metric("other_income")
        has_finance_cost = context.has_metric("finance_cost")
        has_revenue = context.has_metric("revenue")
        has_tax_expense = context.has_metric("tax_expense")

        if not has_pat:
            return {
                "status": "insufficient_data",
                "quality": "Cannot assess",
                "confidence": "None",
                "reason": "Profit after tax not available",
                "period_type": "Q",
            }

        # Get aligned FY period data (most reliable for earnings quality assessment)
        aligned_fy = context.get_aligned_values(
            ["profit_after_tax", "operating_cash_flow", "operating_profit",
             "other_income", "finance_cost", "revenue", "tax_expense"],
            period_type="FY",
            limit=1
        )

        if not aligned_fy:
            # Fall back to Q if FY not available
            aligned_fy = context.get_aligned_values(
                ["profit_after_tax", "operating_cash_flow", "operating_profit",
                 "other_income", "finance_cost", "revenue", "tax_expense"],
                period_type="Q",
                limit=1
            )

        if not aligned_fy:
            return {
                "status": "insufficient_data",
                "quality": "Cannot assess",
                "confidence": "None",
                "reason": "No aligned period data available",
                "period_type": "FY/Q",
            }

        latest = aligned_fy[0]
        period_type = context.get_period_type(latest.get("period_end"))

        # Gather values from aligned period
        pat = latest.get("profit_after_tax")
        ocf = latest.get("operating_cash_flow")
        ebit = latest.get("operating_profit")
        other_income = latest.get("other_income")
        finance_cost = latest.get("finance_cost")
        revenue = latest.get("revenue")
        tax_expense = latest.get("tax_expense")

        issues = []
        positive_indicators = []
        critical_missing = []

        # ============================================================================
        # INTEGRITY CHECK: Can we actually claim "HIGH" quality?
        # ============================================================================
        if ocf is None:
            critical_missing.append("operating_cash_flow")
        if ebit is None:
            critical_missing.append("operating_profit")

        # Check 1: PAT vs OCF (core quality indicator, period-aligned)
        if ocf is not None and pat is not None:
            if ocf > pat * 1.1:
                positive_indicators.append("Operating cash flow exceeds reported earnings, supporting quality.")
            elif ocf < pat * 0.7:
                issues.append(
                    f"Operating cash flow ({ocf:.0f}) is materially weaker than reported "
                    f"earnings ({pat:.0f}), indicating potential quality concerns."
                )
        elif ocf is None:
            # Cannot make high-confidence quality claims without this
            issues.append("Operating cash flow unavailable—cannot validate earnings against cash reality.")

        # Check 2: Other income contribution (period-aligned ratio)
        if other_income is not None and pat is not None:
            other_income_pct = (other_income / pat) * 100 if pat > 0 else 0
            if other_income_pct > 25:
                issues.append(
                    f"Other income represents {other_income_pct:.0f}% of reported profit, "
                    f"suggesting core business earnings are overstated."
                )
            elif other_income_pct > 10:
                issues.append(
                    f"Other income contributes {other_income_pct:.0f}% to reported profit."
                )

        # Check 3: Finance cost burden (period-aligned ratio)
        if finance_cost is not None and ebit is not None:
            finance_cost_pct = (finance_cost / ebit) * 100 if ebit > 0 else 0
            if finance_cost_pct > 30:
                issues.append(
                    f"Finance costs consume {finance_cost_pct:.0f}% of EBIT, "
                    f"materially reducing net earnings."
                )

        # Check 4: Tax rate anomalies (period-aligned ratio)
        if tax_expense is not None and ebit is not None:
            tax_rate = (tax_expense / ebit) * 100 if ebit > 0 else 0
            if tax_rate < 5:
                issues.append("Tax rate unusually low; earnings may include one-off tax benefits.")
            elif tax_rate > 40:
                issues.append("Tax rate unusually high; reported earnings may be suppressed by tax charges.")

        # Check 5: Operating leverage (period-aligned margins)
        if revenue is not None and ebit is not None:
            ebit_margin = (ebit / revenue) * 100 if revenue > 0 else 0
            if pat is not None:
                pat_margin = (pat / revenue) * 100 if revenue > 0 else 0
                if ebit_margin > 0 and pat_margin > 0:
                    leverage_ratio = ebit_margin / pat_margin
                    if leverage_ratio > 2:
                        issues.append(
                            f"EBIT margin ({ebit_margin:.1f}%) is {leverage_ratio:.1f}x the net margin, "
                            f"indicating significant below-the-line erosion."
                        )

        # ============================================================================
        # ASSIGN QUALITY AND CONFIDENCE
        # ============================================================================

        if critical_missing:
            # Cannot claim HIGH without OCF or EBIT
            quality = "Moderate (provisional)"
            confidence = "Low"
            data_coverage = 60
            narrative = (
                "Earnings quality cannot be assessed with high confidence due to missing "
                f"critical metrics: {', '.join(critical_missing)}. "
                "Core validation (OCF vs. reported earnings) is unavailable. "
            )
            if issues:
                narrative += f"Available checks reveal: {issues[0]}"

        elif issues:
            # Has issues, so at best Moderate
            quality = "Moderate"
            confidence = "Medium"
            data_coverage = 85
            narrative = f"Reported earnings show quality concerns: {' '.join(issues[:2])}"
            if positive_indicators:
                narrative += f" However, {positive_indicators[0]}"

        else:
            # No issues, has OCF supporting evidence
            if has_ocf:
                quality = "High"
                confidence = "High"
                data_coverage = 95
                narrative = "Reported earnings are well-supported by operating cash flow. " + " ".join(positive_indicators)
            else:
                # No issues but no OCF either
                quality = "Appears strong"
                confidence = "Medium"
                data_coverage = 75
                narrative = "Available metrics suggest earnings quality, but cash-flow validation unavailable. "

        # ============================================================================
        # FORMAT OUTPUT WITH EVIDENCE CONTEXT
        # ============================================================================
        output.set_assessment(
            assessment=quality,
            score=EarningsQualityEngine._calculate_score(issues, positive_indicators, confidence),
            narrative=narrative,
            confidence=confidence,
            data_coverage=data_coverage,
        )

        result = output.to_dict()
        result["issues"] = issues
        result["positive_indicators"] = positive_indicators
        result["quality_rationale"] = {
            "has_ocf_validation": ocf is not None,
            "has_ebit_validation": ebit is not None,
            "issues_count": len(issues),
            "positive_signals": len(positive_indicators),
        }
        result["period_type"] = period_type  # Explicitly document which period type was analyzed
        result["period_end"] = latest.get("period_end").isoformat() if latest.get("period_end") else None

        # Validation: check for contradictions with context
        validation = output.validate()
        result["validation"] = validation

        return result

    @staticmethod
    def _calculate_score(issues: list, indicators: list, confidence: str) -> float:
        """Score from 0-100."""
        base = 75
        base -= len(issues) * 15
        base += len(indicators) * 8

        if confidence == "Low":
            base *= 0.6
        elif confidence == "Medium":
            base *= 0.85

        return max(20, min(100, base))
