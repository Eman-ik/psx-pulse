"""Valuation Context Engine — never just say "P/E = 8.3x", but interpret it.

The stock trades 22% below its historical median despite above-peer profitability.
The discount may therefore reflect concern over X rather than weak current fundamentals.
"""

from typing import Optional, Dict

from app.analysis.period_alignment import PeriodAlignedAnalyzer
from app.analysis.evidence_context import ResearchContext, ContextualizedOutput


class ValuationContextEngine:
    """Interpret valuation relative to history and peers."""

    @staticmethod
    def analyze(context: ResearchContext, sector_median_pe: Optional[float] = None) -> Dict:
        """Assess valuation using shared Evidence Context."""
        output = ContextualizedOutput("valuation_context", context)

        # Get data from context
        current_pe = context.get_value("pe_ratio")
        roe = context.get_value("roe")
        rev_growth = context.get_value("revenue_growth")
        pb_ratio = context.get_value("pb_ratio")

        assessment = "Valuation: "
        interpretation = ""
        discount_premium = None

        # P/E Assessment — if PE data missing, return insufficient
        if not context.has_metric("pe_ratio") or current_pe is None:
            assessment += "Unavailable"
            output.set_assessment(
                assessment=assessment,
                score=0,
                narrative="Valuation analysis requires P/E ratio data, which is unavailable.",
                confidence="None",
                data_coverage=0,
            )
            result = output.to_dict()
            result["status"] = "insufficient_data"
            result["multiples"] = {"current_pe": None, "historical_median_pe": None, "pb_ratio": pb_ratio}
            result["fundamentals"] = {"roe": roe, "revenue_growth": rev_growth}
            result["validation"] = output.validate()
            return result

        # Get historical median from series
        pe_series = context.get_series("pe_ratio", periods=5)
        historical_median_pe = sorted(pe_series)[len(pe_series) // 2] if pe_series and len(pe_series) > 0 else None

        if historical_median_pe:
            discount_premium = (current_pe - historical_median_pe) / historical_median_pe
            if discount_premium < -0.20:
                assessment += "Significantly undervalued"
            elif discount_premium < -0.05:
                assessment += "Modestly undervalued"
            elif discount_premium < 0.05:
                assessment += "Fair value"
            elif discount_premium < 0.20:
                assessment += "Modestly expensive"
            else:
                assessment += "Significantly overvalued"

            discount_pct = abs(discount_premium) * 100
            if discount_premium < 0:
                interpretation = f"The stock trades {discount_pct:.0f}% below its 5-year median P/E of {historical_median_pe:.1f}x. "
            else:
                interpretation = f"The stock trades {discount_pct:.0f}% above its 5-year median P/E of {historical_median_pe:.1f}x. "

        # Context check: profitability vs. valuation
        if roe and current_pe:
            if roe > 0.15:
                if current_pe < 10:
                    interpretation += "Despite above-peer profitability (ROE > 15%), valuation is compressed. "
                    interpretation += "The discount may reflect concern over earnings sustainability rather than weak fundamentals."
                elif current_pe > 12:
                    interpretation += "Strong ROE justifies a premium multiple. Market is paying up for quality."
            else:
                if current_pe > (historical_median_pe if historical_median_pe else 8):
                    interpretation += "The stock trades at a premium despite below-historical profitability. "
                    interpretation += "An earnings inflection would be required to justify the valuation."

        # Growth-to-multiple check
        if rev_growth and current_pe:
            peg = current_pe / (rev_growth * 100) if rev_growth > 0 else None
            if peg and peg < 1.0:
                interpretation += "The PEG ratio is below 1.0, suggesting reasonable valuation relative to growth."
            elif peg and peg > 2.0:
                interpretation += "The PEG ratio exceeds 2.0, indicating expensive valuation relative to growth prospects."

        # Book value
        if pb_ratio:
            if pb_ratio < 1.0:
                interpretation += "The stock trades below book value, suggesting potential value."
            elif pb_ratio > 2.0:
                interpretation += "The stock trades at 2x+ book value, reflecting either growth expectations or intangible premiums."

        if not interpretation:
            interpretation = "Current valuation reflects market consensus on earnings and growth prospects."

        # Score: 50 = fair, lower = undervalued, higher = overvalued
        score = 50
        if discount_premium:
            score += discount_premium * 100

        output.set_assessment(
            assessment=assessment,
            score=max(0, min(100, score)),
            narrative=interpretation,
            confidence="High" if historical_median_pe else "Medium",
            data_coverage=90 if historical_median_pe else 70,
        )

        result = output.to_dict()
        result["multiples"] = {
            "current_pe": current_pe,
            "historical_median_pe": historical_median_pe,
            "sector_median_pe": sector_median_pe,
            "pb_ratio": pb_ratio,
            "discount_premium_pct": discount_premium * 100 if discount_premium else None,
        }
        result["fundamentals"] = {
            "roe": roe,
            "revenue_growth": rev_growth,
        }
        result["period_type"] = "Point"  # Valuation multiples are point-in-time values
        result["validation"] = output.validate()

        return result
