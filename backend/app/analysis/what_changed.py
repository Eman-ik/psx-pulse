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
        """Detect key changes between latest two aligned periods (modular approach)."""
        output = ContextualizedOutput("what_changed", context)
        analyzer = PeriodAlignedAnalyzer(context)

        positive = []
        negative = []
        available_comparisons = 0
        period_type = "Q"
        period_latest_end = None
        period_prior_end = None

        # Comparison 1: Revenue growth (fundamental - required for other ratios)
        revenue_pair = context.get_aligned_values(
            required_metrics=["revenue"],
            period_type="Q",
            limit=2
        )
        if len(revenue_pair) >= 2:
            latest = revenue_pair[0]
            prior = revenue_pair[1]
            period_latest_end = latest.get("period_end")
            period_prior_end = prior.get("period_end")

            rev_latest = latest.get("revenue")
            rev_prior = prior.get("revenue")
            if rev_latest and rev_prior and rev_prior > 0:
                growth_latest = (rev_latest - rev_prior) / rev_prior
                positive.append(f"Revenue growth reached {growth_latest:.1%}.")
                available_comparisons += 1
        else:
            # Cannot do other comparisons without revenue baseline
            return {
                "status": "insufficient_data",
                "positive_changes": [],
                "negative_changes": [],
                "interpretation": "Insufficient aligned Q periods with revenue data.",
                "period_type": "Q",
            }

        # Comparison 2: Gross margin (requires revenue + gross_profit)
        margin_pair = context.get_aligned_values(
            required_metrics=["revenue", "gross_profit"],
            period_type="Q",
            limit=2
        )
        if len(margin_pair) >= 2:
            latest_m = margin_pair[0]
            prior_m = margin_pair[1]
            gm_latest = latest_m.get("gross_profit")
            gm_prior = prior_m.get("gross_profit")
            rev_latest_m = latest_m.get("revenue")
            rev_prior_m = prior_m.get("revenue")
            if gm_latest and gm_prior and rev_latest_m and rev_prior_m:
                gm_bps_latest = (gm_latest / rev_latest_m) * 10000 if rev_latest_m > 0 else 0
                gm_bps_prior = (gm_prior / rev_prior_m) * 10000 if rev_prior_m > 0 else 0
                change_bps = gm_bps_latest - gm_bps_prior
                if change_bps > 50:
                    positive.append(f"Gross margin expanded by {int(change_bps)} bps.")
                    available_comparisons += 1
                elif change_bps < -50:
                    negative.append(f"Gross margin contracted by {int(abs(change_bps))} bps.")
                    available_comparisons += 1

        # Comparison 3: Finance cost (only needs finance_cost)
        fc_pair = context.get_aligned_values(
            required_metrics=["finance_cost"],
            period_type="Q",
            limit=2
        )
        if len(fc_pair) >= 2:
            fc_latest = fc_pair[0].get("finance_cost")
            fc_prior = fc_pair[1].get("finance_cost")
            if fc_latest is not None and fc_prior is not None:
                if fc_latest < fc_prior:
                    positive.append(f"Finance cost declined {((fc_prior - fc_latest) / fc_prior):.1%}.")
                    available_comparisons += 1
                elif fc_latest > fc_prior:
                    negative.append(f"Finance cost increased {((fc_latest - fc_prior) / fc_prior):.1%}.")
                    available_comparisons += 1

        # Comparison 4: Operating cash flow (only needs OCF)
        ocf_pair = context.get_aligned_values(
            required_metrics=["operating_cash_flow"],
            period_type="Q",
            limit=2
        )
        if len(ocf_pair) >= 2:
            ocf_latest = ocf_pair[0].get("operating_cash_flow")
            ocf_prior = ocf_pair[1].get("operating_cash_flow")
            if ocf_latest is not None and ocf_prior is not None:
                if ocf_prior < 0 and ocf_latest > 0:
                    positive.append("Operating cash flow turned positive.")
                    available_comparisons += 1
                elif ocf_latest > ocf_prior and ocf_prior != 0:
                    positive.append(f"Operating cash flow improved {((ocf_latest - ocf_prior) / abs(ocf_prior)):.1%}.")
                    available_comparisons += 1

        # Comparison 5: Receivables (requires AR + revenue)
        ar_pair = context.get_aligned_values(
            required_metrics=["accounts_receivable", "revenue"],
            period_type="Q",
            limit=2
        )
        if len(ar_pair) >= 2:
            ar_latest = ar_pair[0].get("accounts_receivable")
            ar_prior = ar_pair[1].get("accounts_receivable")
            rev_latest_ar = ar_pair[0].get("revenue")
            rev_prior_ar = ar_pair[1].get("revenue")
            if ar_latest and ar_prior and rev_latest_ar and rev_prior_ar:
                ar_days_latest = (ar_latest / rev_latest_ar) * 365 if rev_latest_ar > 0 else 0
                ar_days_prior = (ar_prior / rev_prior_ar) * 365 if rev_prior_ar > 0 else 0
                if ar_days_latest > ar_days_prior + 5:
                    negative.append(f"Receivable days rose from {ar_days_prior:.0f} to {ar_days_latest:.0f}.")
                    available_comparisons += 1

        # Comparison 6: Inventory (requires inventory + revenue)
        inv_pair = context.get_aligned_values(
            required_metrics=["inventory", "revenue"],
            period_type="Q",
            limit=2
        )
        if len(inv_pair) >= 2:
            inv_latest = inv_pair[0].get("inventory")
            inv_prior = inv_pair[1].get("inventory")
            rev_latest_inv = inv_pair[0].get("revenue")
            rev_prior_inv = inv_pair[1].get("revenue")
            if inv_latest and inv_prior and rev_latest_inv and rev_prior_inv:
                inv_growth = (inv_latest - inv_prior) / inv_prior if inv_prior > 0 else 0
                rev_growth = (rev_latest_inv - rev_prior_inv) / rev_prior_inv if rev_prior_inv > 0 else 0
                if inv_growth > rev_growth * 1.2:
                    negative.append("Inventory growth exceeded revenue growth.")
                    available_comparisons += 1

        # Comparison 7: Dividend per share (only needs DPS)
        dps_pair = context.get_aligned_values(
            required_metrics=["dividend_per_share"],
            period_type="Q",
            limit=2
        )
        if len(dps_pair) >= 2:
            dividend_latest = dps_pair[0].get("dividend_per_share")
            dividend_prior = dps_pair[1].get("dividend_per_share")
            if dividend_latest is not None and dividend_prior is not None:
                if dividend_latest > dividend_prior:
                    positive.append(f"Dividend per share increased {((dividend_latest - dividend_prior) / dividend_prior):.1%}.")
                    available_comparisons += 1
                elif dividend_latest < dividend_prior:
                    negative.append(f"Dividend per share fell {((dividend_prior - dividend_latest) / dividend_prior):.1%}.")
                    available_comparisons += 1

        # Comparison 8: Debt/EBITDA (requires both metrics)
        leverage_pair = context.get_aligned_values(
            required_metrics=["total_debt", "ebitda"],
            period_type="Q",
            limit=2
        )
        if len(leverage_pair) >= 2:
            debt_latest = leverage_pair[0].get("total_debt")
            ebitda_latest = leverage_pair[0].get("ebitda")
            debt_prior = leverage_pair[1].get("total_debt")
            ebitda_prior = leverage_pair[1].get("ebitda")
            if all([debt_latest, ebitda_latest, debt_prior, ebitda_prior]):
                leverage_latest = debt_latest / ebitda_latest if ebitda_latest > 0 else None
                leverage_prior = debt_prior / ebitda_prior if ebitda_prior > 0 else None
                if leverage_latest and leverage_prior:
                    if leverage_latest < leverage_prior:
                        positive.append(f"Net debt/EBITDA improved from {leverage_prior:.1f}x to {leverage_latest:.1f}x.")
                        available_comparisons += 1
                    elif leverage_latest > leverage_prior:
                        negative.append(f"Net debt/EBITDA deteriorated from {leverage_prior:.1f}x to {leverage_latest:.1f}x.")
                        available_comparisons += 1

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
        # Coverage based on available comparisons
        coverage = int((available_comparisons / 8) * 100)

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
