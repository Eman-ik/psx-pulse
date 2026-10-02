"""Financial Red Flag Engine — automatically detect things traders should investigate.

E.g.: PAT increasing but OCF falling, receivables growing faster than sales,
inventory growing faster than revenue, etc.
"""

from typing import Optional, Dict, List

from app.analysis.evidence_context import ResearchContext, ContextualizedOutput
from app.analysis.period_alignment import PeriodAlignedAnalyzer


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
        """Detect all red flags using period-aligned Evidence Context."""
        output = ContextualizedOutput("red_flags", context)
        analyzer = PeriodAlignedAnalyzer(context)

        flags = []

        # Get aligned Q data (same periods for all metrics)
        q_trend = analyzer.get_q_trend(
            ["revenue", "profit_after_tax", "operating_cash_flow",
             "accounts_receivable", "inventory", "finance_cost", "total_debt", "other_income"],
            limit=3
        )

        # Flag 1: PAT increasing but OCF falling (period-aligned comparison)
        pat_ocf_data = context.get_aligned_values(
            ["profit_after_tax", "operating_cash_flow"],
            period_type="Q",
            limit=2
        )
        if len(pat_ocf_data) >= 2:
            latest = pat_ocf_data[0]
            prior = pat_ocf_data[1]
            if latest.get("profit_after_tax") and prior.get("profit_after_tax") and latest.get("operating_cash_flow") and prior.get("operating_cash_flow"):
                pat_growth = (latest["profit_after_tax"] - prior["profit_after_tax"]) / abs(prior["profit_after_tax"])
                ocf_growth = (latest["operating_cash_flow"] - prior["operating_cash_flow"]) / abs(prior["operating_cash_flow"])
                if pat_growth > 0.10 and ocf_growth < -0.10:
                    flags.append({
                        "severity": "high",
                        "title": "Earnings increasing but cash flow deteriorating",
                        "detail": f"PAT grew {pat_growth:.1%} while OCF fell {abs(ocf_growth):.1%}. Earnings quality is questionable.",
                    })

        # Flag 2: Receivables growing faster than revenue (period-aligned)
        ar_rev_data = context.get_aligned_values(
            ["accounts_receivable", "revenue"],
            period_type="Q",
            limit=2
        )
        if len(ar_rev_data) >= 2:
            latest = ar_rev_data[0]
            prior = ar_rev_data[1]
            if latest.get("accounts_receivable") and prior.get("accounts_receivable") and latest.get("revenue") and prior.get("revenue"):
                ar_growth = (latest["accounts_receivable"] - prior["accounts_receivable"]) / abs(prior["accounts_receivable"])
                rev_growth = (latest["revenue"] - prior["revenue"]) / abs(prior["revenue"])
                if ar_growth > rev_growth * 1.3:
                    flags.append({
                        "severity": "medium",
                        "title": "Receivables growing faster than sales",
                        "detail": f"AR grew {ar_growth:.1%} vs revenue {rev_growth:.1%}. Collection period is lengthening.",
                    })

        # Flag 3: Inventory growing faster than revenue (period-aligned)
        inv_rev_data = context.get_aligned_values(
            ["inventory", "revenue"],
            period_type="Q",
            limit=2
        )
        if len(inv_rev_data) >= 2:
            latest = inv_rev_data[0]
            prior = inv_rev_data[1]
            if latest.get("inventory") and prior.get("inventory") and latest.get("revenue") and prior.get("revenue"):
                inv_growth = (latest["inventory"] - prior["inventory"]) / abs(prior["inventory"])
                rev_growth = (latest["revenue"] - prior["revenue"]) / abs(prior["revenue"])
                if inv_growth > rev_growth * 1.3:
                    flags.append({
                        "severity": "medium",
                        "title": "Inventory accumulation outpacing sales",
                        "detail": f"Inventory grew {inv_growth:.1%} vs revenue {rev_growth:.1%}. Working capital pressure rising.",
                    })

        # Flag 4: Finance expense rising faster than debt (period-aligned)
        fc_debt_data = context.get_aligned_values(
            ["finance_cost", "total_debt"],
            period_type="Q",
            limit=2
        )
        if len(fc_debt_data) >= 2:
            latest = fc_debt_data[0]
            prior = fc_debt_data[1]
            if latest.get("finance_cost") and prior.get("finance_cost") and latest.get("total_debt") and prior.get("total_debt"):
                fc_growth = (latest["finance_cost"] - prior["finance_cost"]) / abs(prior["finance_cost"])
                debt_growth = (latest["total_debt"] - prior["total_debt"]) / abs(prior["total_debt"])
                if fc_growth > debt_growth * 1.5 and fc_growth > 0:
                    flags.append({
                        "severity": "medium",
                        "title": "Finance cost rising faster than debt",
                        "detail": f"Finance costs grew {fc_growth:.1%} vs debt {debt_growth:.1%}. Interest rate or leverage moving against company.",
                    })

        # Flag 5: Other income dominating profit (period-aligned ratio)
        oi_pat_data = context.get_aligned_values(
            ["other_income", "profit_after_tax"],
            period_type="Q",
            limit=1
        )
        if len(oi_pat_data) >= 1:
            latest = oi_pat_data[0]
            if latest.get("other_income") and latest.get("profit_after_tax") and latest["profit_after_tax"] > 0:
                other_income_pct = latest["other_income"] / latest["profit_after_tax"] * 100
                if other_income_pct > 30:
                    flags.append({
                        "severity": "high",
                        "title": "Other income dominating reported profit",
                        "detail": f"Non-operating income is {other_income_pct:.0f}% of reported profit. Core business earnings are weaker.",
                    })

        # Flag 6: Negative or declining OCF despite profits (period-aligned)
        if q_trend and len(q_trend) >= 2:
            latest = q_trend[0]
            prior = q_trend[1]
            if latest.get("operating_cash_flow") and prior.get("operating_cash_flow"):
                if latest["operating_cash_flow"] < 0 or latest["operating_cash_flow"] < prior["operating_cash_flow"] * 0.8:
                    flags.append({
                        "severity": "high",
                        "title": "Operating cash flow weakness despite reported earnings",
                        "detail": "Company may be using accounting techniques or working capital management to inflate earnings.",
                    })

        severity_count = {
            "high": sum(1 for f in flags if f["severity"] == "high"),
            "medium": sum(1 for f in flags if f["severity"] == "medium")
        }

        # Confidence based on period alignment quality
        metrics_available = sum([
            context.has_metric("revenue"),
            context.has_metric("profit_after_tax"),
            context.has_metric("operating_cash_flow"),
            context.has_metric("accounts_receivable"),
            context.has_metric("inventory"),
            context.has_metric("finance_cost"),
        ])
        # Bonus if we have multiple aligned periods for better trend analysis
        alignment_bonus = min(5, (len(q_trend) - 2) * 2) if len(q_trend) >= 2 else 0
        coverage = int((metrics_available / 6) * 100) + alignment_bonus

        confidence = "High" if metrics_available >= 5 else "Medium" if metrics_available >= 3 else "Low"

        # Calculate score (lower is worse)
        score = 90 - (len([f for f in flags if f["severity"] == "high"]) * 15 + len([f for f in flags if f["severity"] == "medium"]) * 5)
        score = max(0, min(100, score))

        output.set_assessment(
            assessment="Complete" if len(flags) > 0 else "No flags",
            score=score,
            narrative=f"Detected {len(flags)} red flags requiring attention." if flags else "No major red flags detected.",
            confidence=confidence,
            data_coverage=int(min(100, coverage)),
        )

        result = output.to_dict()
        result["flags_detected"] = len(flags)
        result["severity_summary"] = severity_count
        result["flags"] = flags
        result["recommendation"] = "Investigate" if len(flags) > 2 else ("Monitor closely" if severity_count["high"] > 0 else "No major concerns")
        result["period_type"] = "Q"  # Explicitly document that analysis uses quarterly periods
        result["periods_analyzed"] = [p.get("period_end").isoformat() if p.get("period_end") else None for p in q_trend]

        # Validate
        result["validation"] = output.validate()

        return result
