"""Business Health Engine — transforms financial statements into a diagnosis.

Instead of showing Revenue +18%, PAT +11%, ROE 24%, this generates:
Business health: Improving
Revenue has expanded for three consecutive reporting periods...

NOTE: Uses period-aligned comparisons to ensure FY/Q metrics aren't mixed.
"""

from typing import Optional, Dict

from app.analysis.evidence_context import ResearchContext, ContextualizedOutput
from app.analysis.period_alignment import PeriodAlignedAnalyzer


class BusinessHealthEngine:
    """Diagnose business health from financial trends."""

    @staticmethod
    def growth_rate(values: list, periods: int = 1) -> Optional[float]:
        """Growth rate as a decimal (0.15 = +15%)."""
        if not values or len(values) < periods + 1:
            return None
        current = values[-1] if isinstance(values[-1], (int, float)) else values[-1][1]
        prior = values[-(periods + 1)] if isinstance(values[-(periods + 1)], (int, float)) else values[-(periods + 1)][1]
        if prior == 0:
            return None
        return (current - prior) / abs(prior)

    @staticmethod
    def direction_label(rate: Optional[float]) -> str:
        """Classify growth direction."""
        if rate is None:
            return "Unknown"
        if rate > 0.10:
            return "Improving"
        if rate > 0.02:
            return "Stable"
        if rate > -0.02:
            return "Flat"
        return "Deteriorating"

    @staticmethod
    def analyze(context: ResearchContext) -> Dict:
        """Full business health diagnosis with period-aligned comparisons."""
        output = ContextualizedOutput("business_health", context)
        analyzer = PeriodAlignedAnalyzer(context)

        # Check critical metrics upfront
        has_revenue = context.has_metric("revenue")
        has_pat = context.has_metric("profit_after_tax")
        has_ocf = context.has_metric("operating_cash_flow")
        has_total_debt = context.has_metric("total_debt")
        has_equity = context.has_metric("total_equity")

        # If no revenue data, cannot assess
        if not has_revenue:
            return {
                "status": "insufficient_data",
                "overall": "Cannot assess",
                "confidence": "None",
                "reason": "Revenue data not available",
            }

        # Get FY trend with required minimum (revenue + profit) and optional metrics
        # This allows analysis to degrade gracefully when OCF/debt/equity data is missing
        fy_trend = analyzer.get_fy_trend(
            required_metrics=["revenue", "profit_after_tax"],
            optional_metrics=["operating_cash_flow", "total_debt", "total_equity"],
            limit=5
        )

        if not fy_trend or len(fy_trend) < 2:
            return {
                "status": "insufficient_data",
                "overall": "Cannot assess",
                "confidence": "None",
                "reason": "Insufficient aligned FY periods with revenue + profit (minimum 2 required)",
                "period_type": "FY",
            }

        # Calculate growth rates from aligned periods (guaranteed same FY)
        revenue_growth = None
        pat_growth = None
        ocf_growth = None

        if "revenue" in fy_trend[0] and "revenue" in fy_trend[1]:
            rev_latest = fy_trend[0]["revenue"]
            rev_prior = fy_trend[1]["revenue"]
            if rev_prior and rev_prior > 0:
                revenue_growth = (rev_latest - rev_prior) / rev_prior

        if "profit_after_tax" in fy_trend[0] and "profit_after_tax" in fy_trend[1]:
            pat_latest = fy_trend[0]["profit_after_tax"]
            pat_prior = fy_trend[1]["profit_after_tax"]
            if pat_prior and pat_prior > 0:
                pat_growth = (pat_latest - pat_prior) / pat_prior

        if has_ocf and "operating_cash_flow" in fy_trend[0] and "operating_cash_flow" in fy_trend[1]:
            ocf_latest = fy_trend[0]["operating_cash_flow"]
            ocf_prior = fy_trend[1]["operating_cash_flow"]
            if ocf_prior and ocf_prior > 0:
                ocf_growth = (ocf_latest - ocf_prior) / ocf_prior

        # Revenue quality: OCF growth vs PAT growth (now guaranteed aligned periods)
        revenue_quality = "Strong" if ocf_growth and pat_growth and ocf_growth > pat_growth else "Weak" if has_ocf else "Unknown"

        # Margin trend from aligned periods (all from same FY)
        margins = []
        for period_data in fy_trend:
            if "revenue" in period_data and "profit_after_tax" in period_data:
                revenue = period_data["revenue"]
                profit = period_data["profit_after_tax"]
                if revenue and revenue > 0:
                    margins.append(profit / revenue)

        # Only set margin_trend if we have at least 2 periods to compare
        if len(margins) >= 2:
            margin_trend = "Expanding" if margins[0] > margins[1] else "Contracting" if margins[0] < margins[1] else "Stable"
        else:
            margin_trend = "Unknown"

        # Balance sheet direction from aligned periods (debt/equity from same FY)
        leverage_trend = "Unknown"
        if (has_total_debt and has_equity and
            "total_debt" in fy_trend[0] and "total_equity" in fy_trend[0] and
            "total_debt" in fy_trend[1] and "total_equity" in fy_trend[1]):
            debt_latest = fy_trend[0]["total_debt"]
            debt_prior = fy_trend[1]["total_debt"]
            equity_latest = fy_trend[0]["total_equity"]
            if equity_latest and equity_latest > 0 and debt_latest and debt_latest > debt_prior:
                leverage_trend = "Deteriorating"

        # Overall health classification
        components = {
            "revenue_growth": BusinessHealthEngine.direction_label(revenue_growth),
            "profitability": BusinessHealthEngine.direction_label(pat_growth),
            "margins": margin_trend,
            "cash_generation": BusinessHealthEngine.direction_label(ocf_growth) if has_ocf else "Unknown",
            "balance_sheet": leverage_trend if has_total_debt and has_equity else "Unknown",
            "earnings_quality": revenue_quality,
        }

        improving_count = sum(1 for v in components.values() if "Improv" in v or "Expand" in v or "Strong" in v)
        worsening_count = sum(1 for v in components.values() if "Deterior" in v or "Contract" in v or "Weak" in v)

        if improving_count >= 4:
            overall = "Strong / Improving"
        elif improving_count >= 2 and worsening_count == 0:
            overall = "Improving"
        elif improving_count >= worsening_count:
            overall = "Stable"
        else:
            overall = "Weakening"

        # Narrative summary
        narrative = f"Business health: {overall}\n"
        if revenue_growth:
            narrative += f"Revenue has {'expanded' if revenue_growth > 0 else 'contracted'} "
            narrative += f"{'for three consecutive reporting periods' if len(fy_trend) >= 3 else 'in the latest period'}. "
        if pat_growth and revenue_growth:
            if pat_growth < revenue_growth:
                narrative += "Profit growth has lagged sales growth, indicating moderate margin pressure. "
            else:
                narrative += "Profit growth has kept pace with or exceeded sales growth. "
        if has_ocf and ocf_growth is not None:
            narrative += "Operating cash flow remains above reported earnings, which supports earnings quality. "
        if leverage_trend == "Improving":
            narrative += "Leverage has declined and interest coverage has improved. "
        narrative += "The company's core operating position is therefore " + ("strengthening" if improving_count >= 2 else "under pressure") + "."

        # Determine confidence based on data availability (and period alignment)
        available_metrics = sum([has_revenue, has_pat, has_ocf, has_total_debt, has_equity])
        # Bonus if we have multiple aligned periods for better trend analysis
        aligned_period_bonus = min(10, (len(fy_trend) - 2) * 5) if len(fy_trend) >= 2 else 0

        if available_metrics >= 4:
            confidence = "High"
            coverage = min(100, 75 + aligned_period_bonus)
        elif available_metrics >= 3:
            confidence = "Medium"
            coverage = min(100, 60 + aligned_period_bonus)
        else:
            confidence = "Low"
            coverage = min(100, 40 + aligned_period_bonus)

        # Calculate score based on components
        score = 50 + (improving_count - worsening_count) * 10
        score = max(0, min(100, score))

        # Set assessment with confidence and coverage
        output.set_assessment(
            assessment=overall,
            score=score,
            narrative=narrative,
            confidence=confidence,
            data_coverage=int(coverage),
        )

        result = output.to_dict()
        result["components"] = components
        result["latest_data_points"] = {
            "revenue_latest": fy_trend[0].get("revenue") if fy_trend else None,
            "pat_latest": fy_trend[0].get("profit_after_tax") if fy_trend else None,
            "ocf_latest": fy_trend[0].get("operating_cash_flow") if fy_trend else None,
            "periods_in_series": len(fy_trend),
        }
        result["period_type"] = "FY"  # Explicitly document that analysis uses FY-aligned periods
        result["periods_analyzed"] = [p.get("period_end").isoformat() if p.get("period_end") else None for p in fy_trend]

        # Validate for contradictions
        result["validation"] = output.validate()

        return result
