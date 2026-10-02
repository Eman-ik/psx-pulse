"""Financial Red Flag Engine — automatically detect things traders should investigate.

E.g.: PAT increasing but OCF falling, receivables growing faster than sales,
inventory growing faster than revenue, etc.
"""

from typing import Optional, Dict, List

from app.analysis.evidence_context import ResearchContext, ContextualizedOutput


class RedFlagEngine:
    """Detect financial red flags requiring investigation."""

    @staticmethod
    def growth_rate(values: list[float]) -> Optional[float]:
        """Period-over-period growth rate as decimal."""
        if len(values) < 2 or values[-2] == 0:
            return None
        return (values[-1] - values[-2]) / abs(values[-2])

    @staticmethod
    def detect(context: ResearchContext) -> Dict:
        """Detect all red flags using shared Evidence Context."""
        output = ContextualizedOutput("red_flags", context)

        flags = []

        revenue = context.get_series("revenue", periods=3)
        pat = context.get_series("profit_after_tax", periods=3)
        ocf = context.get_series("operating_cash_flow", periods=3)
        ar = context.get_series("accounts_receivable", periods=3)
        inventory = context.get_series("inventory", periods=3)
        finance_cost = context.get_series("finance_cost", periods=3)
        total_debt = context.get_series("total_debt", periods=3)
        other_income = context.get_series("other_income", periods=3)

        # Flag 1: PAT increasing but OCF falling (only if OCF data exists)
        if context.has_metric("operating_cash_flow") and pat and ocf:
            pat_growth = RedFlagEngine.growth_rate(pat)
            ocf_growth = RedFlagEngine.growth_rate(ocf)
            if (pat_growth and pat_growth > 0.10) and (ocf_growth and ocf_growth < -0.10):
                flags.append({
                    "severity": "high",
                    "title": "Earnings increasing but cash flow deteriorating",
                    "detail": f"PAT grew {pat_growth:.1%} while OCF fell {abs(ocf_growth):.1%}. Earnings quality is questionable.",
                })

        # Flag 2: Receivables growing faster than revenue
        if context.has_metric("accounts_receivable") and ar and revenue:
            ar_growth = RedFlagEngine.growth_rate(ar)
            rev_growth = RedFlagEngine.growth_rate(revenue)
            if ar_growth and rev_growth and ar_growth > rev_growth * 1.3:
                flags.append({
                    "severity": "medium",
                    "title": "Receivables growing faster than sales",
                    "detail": f"AR grew {ar_growth:.1%} vs revenue {rev_growth:.1%}. Collection period is lengthening.",
                })

        # Flag 3: Inventory growing faster than revenue
        if context.has_metric("inventory") and inventory and revenue:
            inv_growth = RedFlagEngine.growth_rate(inventory)
            rev_growth = RedFlagEngine.growth_rate(revenue)
            if inv_growth and rev_growth and inv_growth > rev_growth * 1.3:
                flags.append({
                    "severity": "medium",
                    "title": "Inventory accumulation outpacing sales",
                    "detail": f"Inventory grew {inv_growth:.1%} vs revenue {rev_growth:.1%}. Working capital pressure rising.",
                })

        # Flag 4: Finance expense rising faster than debt
        if context.has_metric("finance_cost") and finance_cost and total_debt:
            fc_growth = RedFlagEngine.growth_rate(finance_cost)
            debt_growth = RedFlagEngine.growth_rate(total_debt)
            if fc_growth and debt_growth and fc_growth > debt_growth * 1.5 and fc_growth > 0:
                flags.append({
                    "severity": "medium",
                    "title": "Finance cost rising faster than debt",
                    "detail": f"Finance costs grew {fc_growth:.1%} vs debt {debt_growth:.1%}. Interest rate or leverage moving against company.",
                })

        # Flag 5: Other income dominating profit
        if context.has_metric("other_income") and pat and other_income:
            if len(pat) > 0 and len(other_income) > 0:
                other_income_pct = other_income[-1] / pat[-1] * 100 if pat[-1] > 0 else 0
                if other_income_pct > 30:
                    flags.append({
                        "severity": "high",
                        "title": "Other income dominating reported profit",
                        "detail": f"Non-operating income is {other_income_pct:.0f}% of reported profit. Core business earnings are weaker.",
                    })

        # Flag 6: Negative or declining OCF despite profits (only if OCF exists)
        if context.has_metric("operating_cash_flow") and pat and ocf:
            if ocf[-1] < 0 or (len(ocf) >= 2 and ocf[-1] < ocf[-2] * 0.8):
                flags.append({
                    "severity": "high",
                    "title": "Operating cash flow weakness despite reported earnings",
                    "detail": "Company may be using accounting techniques or working capital management to inflate earnings.",
                })

        severity_count = {
            "high": sum(1 for f in flags if f["severity"] == "high"),
            "medium": sum(1 for f in flags if f["severity"] == "medium")
        }

        # Confidence based on data
        metrics_available = sum([
            context.has_metric("revenue"),
            context.has_metric("profit_after_tax"),
            context.has_metric("operating_cash_flow"),
            context.has_metric("accounts_receivable"),
            context.has_metric("inventory"),
            context.has_metric("finance_cost"),
        ])
        confidence = "High" if metrics_available >= 5 else "Medium" if metrics_available >= 3 else "Low"
        coverage = (metrics_available / 6) * 100

        # Calculate score (lower is worse)
        score = 90 - (len([f for f in flags if f["severity"] == "high"]) * 15 + len([f for f in flags if f["severity"] == "medium"]) * 5)
        score = max(0, min(100, score))

        output.set_assessment(
            assessment="Complete" if len(flags) > 0 else "No flags",
            score=score,
            narrative=f"Detected {len(flags)} red flags requiring attention." if flags else "No major red flags detected.",
            confidence=confidence,
            data_coverage=int(coverage),
        )

        result = output.to_dict()
        result["flags_detected"] = len(flags)
        result["severity_summary"] = severity_count
        result["flags"] = flags
        result["recommendation"] = "Investigate" if len(flags) > 2 else ("Monitor closely" if severity_count["high"] > 0 else "No major concerns")

        # Validate
        result["validation"] = output.validate()

        return result
