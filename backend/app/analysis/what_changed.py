"""What Changed Engine — automatically answer what changed since the previous quarter.

Positive changes: Revenue growth accelerated from 8% to 17%, Gross margin expanded by 220 bps
Negative changes: Receivable days rose sharply, Inventory growth exceeded revenue growth
Interpretation: The latest result is operationally stronger but deterioration in working capital
"""

from typing import Optional, Dict

from app.analysis.evidence_context import ResearchContext, ContextualizedOutput
from app.analysis.period_alignment import PeriodAlignedAnalyzer


class WhatChangedEngine:
    """Detect and articulate period-over-period changes."""

    @staticmethod
    def analyze(context: ResearchContext) -> Dict:
        """Detect key changes between latest two aligned periods."""
        output = ContextualizedOutput("what_changed", context)
        analyzer = PeriodAlignedAnalyzer(context)

        # Get aligned Q data for the latest 2 periods (guaranteed same period type)
        aligned_metrics = [
            "revenue", "gross_profit", "finance_cost", "operating_cash_flow",
            "accounts_receivable", "inventory", "dividend_per_share", "total_debt", "ebitda"
        ]
        q_trend = context.get_aligned_values(aligned_metrics, period_type="Q", limit=2)

        if len(q_trend) < 2:
            return {
                "status": "insufficient_data",
                "positive_changes": [],
                "negative_changes": [],
                "interpretation": "Insufficient aligned period data for comparison.",
                "period_type": "Q",
            }

        latest = q_trend[0]
        prior = q_trend[1]
        period_latest_end = latest.get("period_end")
        period_prior_end = prior.get("period_end")

        positive = []
        negative = []

        # Revenue growth
        rev_latest = latest.get("revenue")
        rev_prior = prior.get("revenue")
        if rev_latest and rev_prior and rev_prior > 0:
            growth_latest = (rev_latest - rev_prior) / rev_prior
            positive.append(f"Revenue growth reached {growth_latest:.1%}.")

        # Gross margin
        gm_latest = latest.get("gross_profit")
        gm_prior = prior.get("gross_profit")
        if gm_latest and gm_prior and rev_latest and rev_prior:
            gm_bps_latest = (gm_latest / rev_latest) * 10000 if rev_latest > 0 else 0
            gm_bps_prior = (gm_prior / rev_prior) * 10000 if rev_prior > 0 else 0
            change_bps = gm_bps_latest - gm_bps_prior
            if change_bps > 50:
                positive.append(f"Gross margin expanded by {int(change_bps)} bps.")
            elif change_bps < -50:
                negative.append(f"Gross margin contracted by {int(abs(change_bps))} bps.")

        # Finance cost (period-aligned comparison)
        fc_latest = latest.get("finance_cost")
        fc_prior = prior.get("finance_cost")
        if fc_latest is not None and fc_prior is not None:
            if fc_latest < fc_prior:
                positive.append(f"Finance cost declined {((fc_prior - fc_latest) / fc_prior):.1%}.")
            elif fc_latest > fc_prior:
                negative.append(f"Finance cost increased {((fc_latest - fc_prior) / fc_prior):.1%}.")

        # Operating cash flow (period-aligned comparison)
        ocf_latest = latest.get("operating_cash_flow")
        ocf_prior = prior.get("operating_cash_flow")
        if ocf_latest is not None and ocf_prior is not None:
            if ocf_prior < 0 and ocf_latest > 0:
                positive.append("Operating cash flow turned positive.")
            elif ocf_latest > ocf_prior and ocf_prior != 0:
                positive.append(f"Operating cash flow improved {((ocf_latest - ocf_prior) / abs(ocf_prior)):.1%}.")

        # Receivables (period-aligned comparison)
        ar_latest = latest.get("accounts_receivable")
        ar_prior = prior.get("accounts_receivable")
        if ar_latest and ar_prior and rev_latest and rev_prior:
            ar_days_latest = (ar_latest / rev_latest) * 365 if rev_latest > 0 else 0
            ar_days_prior = (ar_prior / rev_prior) * 365 if rev_prior > 0 else 0
            if ar_days_latest > ar_days_prior + 5:
                negative.append(f"Receivable days rose from {ar_days_prior:.0f} to {ar_days_latest:.0f}.")

        # Inventory (period-aligned comparison)
        inv_latest = latest.get("inventory")
        inv_prior = prior.get("inventory")
        if inv_latest and inv_prior and rev_latest and rev_prior:
            inv_growth = (inv_latest - inv_prior) / inv_prior if inv_prior > 0 else 0
            rev_growth = (rev_latest - rev_prior) / rev_prior if rev_prior > 0 else 0
            if inv_growth > rev_growth * 1.2:
                negative.append("Inventory growth exceeded revenue growth.")

        # Dividend (period-aligned comparison)
        dividend_latest = latest.get("dividend_per_share")
        dividend_prior = prior.get("dividend_per_share")
        if dividend_latest is not None and dividend_prior is not None:
            if dividend_latest > dividend_prior:
                positive.append(f"Dividend per share increased {((dividend_latest - dividend_prior) / dividend_prior):.1%}.")
            elif dividend_latest < dividend_prior:
                negative.append(f"Dividend per share fell {((dividend_prior - dividend_latest) / dividend_prior):.1%}.")

        # Debt/EBITDA (period-aligned comparison)
        debt_latest = latest.get("total_debt")
        ebitda_latest = latest.get("ebitda")
        debt_prior = prior.get("total_debt")
        ebitda_prior = prior.get("ebitda")
        if all([debt_latest, ebitda_latest, debt_prior, ebitda_prior]):
            leverage_latest = debt_latest / ebitda_latest if ebitda_latest > 0 else None
            leverage_prior = debt_prior / ebitda_prior if ebitda_prior > 0 else None
            if leverage_latest and leverage_prior:
                if leverage_latest < leverage_prior:
                    positive.append(f"Net debt/EBITDA improved from {leverage_prior:.1f}x to {leverage_latest:.1f}x.")
                elif leverage_latest > leverage_prior:
                    negative.append(f"Net debt/EBITDA deteriorated from {leverage_prior:.1f}x to {leverage_latest:.1f}x.")

        # Interpretation (WITH BUG FIX: acknowledge receivables as offsetting concern)
        interpretation = ""
        has_receivable_concern = any("receivable" in c.lower() for c in negative)

        if positive and not negative:
            interpretation = "The latest result shows broad operational improvement with no offsetting concerns."
        elif negative and not positive:
            interpretation = "The latest result reveals mixed operational health with deteriorating working capital and leverage metrics."
        elif positive and negative:
            if has_receivable_concern:
                interpretation = "The latest result is operationally stronger, but deterioration in receivable quality and collection efficiency reduces confidence in the improvement."
            else:
                interpretation = "The latest result is operationally stronger but deterioration in working capital and leverage reduces confidence in the improvement."
        else:
            interpretation = "No material changes detected since the prior period."

        # Confidence based on period alignment quality
        metrics_checked = sum([
            context.has_metric("revenue"),
            context.has_metric("gross_profit"),
            context.has_metric("finance_cost"),
            context.has_metric("operating_cash_flow"),
            context.has_metric("accounts_receivable"),
            context.has_metric("inventory"),
        ])
        # Bonus if we have aligned periods
        alignment_bonus = 10 if len(q_trend) >= 2 else 0
        coverage = int((metrics_checked / 6) * 100) + alignment_bonus

        confidence = "High" if metrics_checked >= 5 else "Medium" if metrics_checked >= 3 else "Low"

        # Calculate score based on changes
        score = 50 + len(positive) * 5 - len(negative) * 5
        score = max(0, min(100, score))

        # Set assessment
        output.set_assessment(
            assessment="Complete",
            score=score,
            narrative=interpretation,
            confidence=confidence,
            data_coverage=int(min(100, coverage)),
        )

        result = output.to_dict()
        result["periods"] = {
            "prior": period_prior_end.isoformat() if period_prior_end else None,
            "latest": period_latest_end.isoformat() if period_latest_end else None,
        }
        result["period_type"] = "Q"  # Explicitly document that analysis uses quarterly periods
        result["positive_changes"] = positive
        result["negative_changes"] = negative

        # Validate
        result["validation"] = output.validate()

        return result
