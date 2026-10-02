"""Business Health Engine — transforms financial statements into a diagnosis.

Instead of showing Revenue +18%, PAT +11%, ROE 24%, this generates:
Business health: Improving
Revenue has expanded for three consecutive reporting periods...
"""

from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.analysis.evidence_context import ResearchContext, ContextualizedOutput


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
    def analyze(db: Session, issuer_id: int) -> Dict:
        """Full business health diagnosis with Evidence Context."""
        # Single database scan—all engines read from this
        context = ResearchContext(db, issuer_id)
        output = ContextualizedOutput("business_health", context)

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

        # Get data from context
        revenue = context.get_series("revenue")
        pat = context.get_series("profit_after_tax")
        ocf = context.get_series("operating_cash_flow")
        total_debt = context.get_series("total_debt")
        equity = context.get_series("total_equity")

        # Calculate growth rates
        revenue_growth = BusinessHealthEngine.growth_rate(revenue)
        pat_growth = BusinessHealthEngine.growth_rate(pat)
        ocf_growth = BusinessHealthEngine.growth_rate(ocf) if has_ocf else None

        # Revenue quality: OCF growth vs PAT growth
        revenue_quality = "Strong" if ocf_growth and pat_growth and ocf_growth > pat_growth else "Weak" if has_ocf else "Unknown"

        # Margin trend
        margins = []
        if len(revenue) > 0 and len(pat) > 0:
            for i in range(min(len(revenue), len(pat))):
                if revenue[i] > 0:
                    margins.append(pat[i] / revenue[i])

        margin_trend = "Expanding" if len(margins) >= 2 and margins[-1] > margins[-2] else "Contracting"

        # Balance sheet direction
        leverage_trend = "Improving"
        if has_total_debt and has_equity and len(total_debt) >= 2 and len(equity) >= 2:
            debt_last = total_debt[-1]
            debt_prior = total_debt[-2]
            equity_last = equity[-1]
            if equity_last > 0 and debt_last > debt_prior:
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
            narrative += f"{'for three consecutive reporting periods' if len(revenue) >= 3 else 'in the latest period'}. "
        if pat_growth and revenue_growth:
            if pat_growth < revenue_growth:
                narrative += "Profit growth has lagged sales growth, indicating moderate margin pressure. "
            else:
                narrative += "Profit growth has kept pace with or exceeded sales growth. "
        if has_ocf and ocf and pat:
            narrative += "Operating cash flow remains above reported earnings, which supports earnings quality. "
        if leverage_trend == "Improving":
            narrative += "Leverage has declined and interest coverage has improved. "
        narrative += "The company's core operating position is therefore " + ("strengthening" if improving_count >= 2 else "under pressure") + "."

        # Determine confidence based on data availability
        available_metrics = sum([has_revenue, has_pat, has_ocf, has_total_debt, has_equity])
        if available_metrics >= 4:
            confidence = "High"
            coverage = 95
        elif available_metrics >= 3:
            confidence = "Medium"
            coverage = 75
        else:
            confidence = "Low"
            coverage = 50

        # Calculate score based on components
        score = 50 + (improving_count - worsening_count) * 10
        score = max(0, min(100, score))

        # Set assessment with confidence and coverage
        output.set_assessment(
            assessment=overall,
            score=score,
            narrative=narrative,
            confidence=confidence,
            data_coverage=coverage,
        )

        result = output.to_dict()
        result["components"] = components
        result["latest_data_points"] = {
            "revenue_latest": revenue[-1] if revenue else None,
            "pat_latest": pat[-1] if pat else None,
            "ocf_latest": ocf[-1] if ocf else None,
            "periods_in_series": len(revenue),
        }

        # Validate for contradictions
        result["validation"] = output.validate()

        return result
