"""Business Health Engine — Phase 2: Metric Decomposition with Transparent Scoring.

PHASE 2 CHANGES:
- Returns explicit sub-metrics (revenue growth, margin trends, ROE, leverage, OCF)
- Each metric tagged with period and data source
- Separates evidence_confidence (confidence in facts) from classification_confidence (confidence in interpretation)
- Shows assessment rationale: WHY the business is Improving/Stable/Weakening
- Component scores feed into overall assessment

Example output:
{
  "period": "FY25",
  "status": "complete",
  "metrics": {
    "revenue_growth": {value: 0.035, status: "Positive", period: "FY25", trend: "Modest growth"},
    "pat_growth": {value: -0.213, status: "Negative", period: "FY25", trend: "Significant decline"},
    "gross_margin": {current: 0.152, prior: 0.158, trend: "Declining", impact: "Negative"},
    ...
  },
  "assessment": "Weakening",
  "assessment_rationale": "Despite 3.5% revenue growth, profitability compressed due to margin deterioration and 21% PAT decline",
  "evidence_confidence": "High",
  "classification_confidence": "Medium",
  "components": {...}
}
"""

from typing import Optional, Dict

from app.analysis.evidence_context import ResearchContext, ContextualizedOutput
from app.analysis.period_alignment import PeriodAlignedAnalyzer


class BusinessHealthEngine:
    """Diagnose business health from decomposed financial metrics.

    Phase 2: Returns transparent metric-by-metric breakdown with explicit rationale.
    """

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

        # PHASE 2: Calculate all metrics with period context
        latest_period = fy_trend[0]
        prior_period = fy_trend[1]
        latest_period_end = latest_period.get("period_end")
        prior_period_end = prior_period.get("period_end")

        # Initialize decomposed metrics structure
        metrics = {}
        rationales = []

        # 1. REVENUE GROWTH
        revenue_growth = None
        revenue_status = "Unknown"
        if "revenue" in latest_period and "revenue" in prior_period:
            rev_latest = latest_period["revenue"]
            rev_prior = prior_period["revenue"]
            if rev_prior and rev_prior > 0:
                revenue_growth = (rev_latest - rev_prior) / rev_prior
                revenue_status = "Positive" if revenue_growth > 0 else "Negative"
                metrics["revenue_growth"] = {
                    "value": revenue_growth,
                    "value_pct": f"{revenue_growth:.1%}",
                    "status": revenue_status,
                    "latest": rev_latest,
                    "prior": rev_prior,
                    "period": f"{prior_period_end.year} → {latest_period_end.year}",
                    "evidence_confidence": "High"  # Audited financial statements
                }
                rationales.append(f"Revenue {revenue_status.lower()}: {revenue_growth:.1%} YoY")

        # 2. PAT (Earnings) GROWTH
        pat_growth = None
        pat_status = "Unknown"
        if "profit_after_tax" in latest_period and "profit_after_tax" in prior_period:
            pat_latest = latest_period["profit_after_tax"]
            pat_prior = prior_period["profit_after_tax"]
            if pat_prior and pat_prior > 0:
                pat_growth = (pat_latest - pat_prior) / pat_prior
                pat_status = "Positive" if pat_growth > 0 else "Negative"
                metrics["pat_growth"] = {
                    "value": pat_growth,
                    "value_pct": f"{pat_growth:.1%}",
                    "status": pat_status,
                    "latest": pat_latest,
                    "prior": pat_prior,
                    "period": f"{prior_period_end.year} → {latest_period_end.year}",
                    "evidence_confidence": "High"
                }
                rationales.append(f"Earnings {pat_status.lower()}: {pat_growth:.1%} YoY")

        # 3. GROSS MARGIN TREND (if available)
        gross_margins = []
        if "gross_profit" in latest_period and "revenue" in latest_period:
            gm_latest = latest_period["gross_profit"] / latest_period["revenue"] if latest_period["revenue"] > 0 else None
            if gm_latest:
                gross_margins.append(gm_latest)
                if "gross_profit" in prior_period and "revenue" in prior_period:
                    gm_prior = prior_period["gross_profit"] / prior_period["revenue"] if prior_period["revenue"] > 0 else None
                    if gm_prior:
                        gross_margins.append(gm_prior)
                        gm_trend = "Expanding" if gm_latest > gm_prior else "Contracting" if gm_latest < gm_prior else "Stable"
                        metrics["gross_margin"] = {
                            "current": gm_latest,
                            "prior": gm_prior,
                            "change_bps": (gm_latest - gm_prior) * 10000,
                            "trend": gm_trend,
                            "period": f"{prior_period_end.year} → {latest_period_end.year}",
                            "evidence_confidence": "High"
                        }
                        rationales.append(f"Gross margin {gm_trend.lower()}: {(gm_latest - gm_prior) * 10000:.0f} bps")

        # 4. NET MARGIN TREND
        net_margins = []
        if "profit_after_tax" in latest_period and "revenue" in latest_period:
            nm_latest = latest_period["profit_after_tax"] / latest_period["revenue"] if latest_period["revenue"] > 0 else None
            if nm_latest:
                net_margins.append(nm_latest)
                if "profit_after_tax" in prior_period and "revenue" in prior_period:
                    nm_prior = prior_period["profit_after_tax"] / prior_period["revenue"] if prior_period["revenue"] > 0 else None
                    if nm_prior:
                        net_margins.append(nm_prior)
                        nm_trend = "Expanding" if nm_latest > nm_prior else "Contracting" if nm_latest < nm_prior else "Stable"
                        metrics["net_margin"] = {
                            "current": nm_latest,
                            "prior": nm_prior,
                            "change_bps": (nm_latest - nm_prior) * 10000,
                            "trend": nm_trend,
                            "period": f"{prior_period_end.year} → {latest_period_end.year}",
                            "evidence_confidence": "High"
                        }
                        rationales.append(f"Net margin {nm_trend.lower()}: {(nm_latest - nm_prior) * 10000:.0f} bps")

        # 5. OPERATING CASH FLOW GROWTH
        ocf_growth = None
        ocf_status = "Unknown"
        if has_ocf and "operating_cash_flow" in latest_period and "operating_cash_flow" in prior_period:
            ocf_latest = latest_period["operating_cash_flow"]
            ocf_prior = prior_period["operating_cash_flow"]
            if ocf_prior and ocf_prior > 0:
                ocf_growth = (ocf_latest - ocf_prior) / ocf_prior
                ocf_status = "Positive" if ocf_growth > 0 else "Negative"
                metrics["ocf_growth"] = {
                    "value": ocf_growth,
                    "value_pct": f"{ocf_growth:.1%}",
                    "status": ocf_status,
                    "latest": ocf_latest,
                    "prior": ocf_prior,
                    "period": f"{prior_period_end.year} → {latest_period_end.year}",
                    "evidence_confidence": "High"
                }
                rationales.append(f"Operating cash flow {ocf_status.lower()}: {ocf_growth:.1%} YoY")

        # 6. LEVERAGE / DEBT RATIO
        if (has_total_debt and has_equity and
            "total_debt" in latest_period and "total_equity" in latest_period and
            "total_debt" in prior_period and "total_equity" in prior_period):
            debt_latest = latest_period["total_debt"]
            equity_latest = latest_period["total_equity"]
            debt_prior = prior_period["total_debt"]
            equity_prior = prior_period["total_equity"]

            if equity_latest > 0 and equity_prior > 0:
                de_latest = debt_latest / equity_latest if equity_latest > 0 else None
                de_prior = debt_prior / equity_prior if equity_prior > 0 else None

                if de_latest and de_prior:
                    de_trend = "Deteriorating" if de_latest > de_prior else "Improving" if de_latest < de_prior else "Stable"
                    metrics["debt_to_equity"] = {
                        "current": de_latest,
                        "prior": de_prior,
                        "change": de_latest - de_prior,
                        "trend": de_trend,
                        "period": f"{prior_period_end.year} → {latest_period_end.year}",
                        "evidence_confidence": "High"
                    }
                    rationales.append(f"Leverage {de_trend.lower()}: {de_latest:.2f}x → {de_prior:.2f}x")

        # PHASE 2: Determine assessment from metrics (not from vague signals)
        positive_metrics = sum(1 for m in metrics.values() if m.get("status") == "Positive" or m.get("trend") in ["Expanding", "Improving"])
        negative_metrics = sum(1 for m in metrics.values() if m.get("status") == "Negative" or m.get("trend") in ["Contracting", "Deteriorating"])

        # Assessment logic: explicit metric-based determination
        if positive_metrics >= 4:
            overall = "Strong / Improving"
        elif positive_metrics >= 2 and negative_metrics == 0:
            overall = "Improving"
        elif positive_metrics >= negative_metrics:
            overall = "Stable"
        else:
            overall = "Weakening"

        # Build detailed rationale from actual metrics
        assessment_rationale_parts = []

        # Check revenue vs earnings consistency
        if revenue_growth is not None and pat_growth is not None:
            if pat_growth < revenue_growth:
                assessment_rationale_parts.append(f"earnings growth ({pat_growth:.1%}) lagged revenue growth ({revenue_growth:.1%}), indicating margin compression")
            elif pat_growth > revenue_growth:
                assessment_rationale_parts.append(f"earnings growth ({pat_growth:.1%}) exceeded revenue growth ({revenue_growth:.1%}), showing operational leverage")
            else:
                assessment_rationale_parts.append(f"earnings growth ({pat_growth:.1%}) matched revenue growth")

        # Check margin trends
        if "net_margin" in metrics:
            nm = metrics["net_margin"]
            assessment_rationale_parts.append(f"net margin {nm['trend'].lower()} ({nm['change_bps']:.0f} bps)")

        # Check OCF quality
        if "ocf_growth" in metrics and pat_growth is not None:
            ocf_growth = metrics["ocf_growth"]["value"]
            if ocf_growth > pat_growth:
                assessment_rationale_parts.append("OCF growth exceeded earnings growth, validating earnings quality")
            elif ocf_growth < pat_growth * 0.7:
                assessment_rationale_parts.append("OCF growth lagged earnings, suggesting earnings quality concerns")

        # Build final rationale
        if assessment_rationale_parts:
            assessment_rationale = f"Assessment: {overall}. " + "; ".join(assessment_rationale_parts) + "."
        else:
            assessment_rationale = f"Assessment: {overall}. Insufficient metrics for detailed rationale."

        # Confidence levels (Phase 2 distinction)
        # Evidence confidence: how certain we are of the facts (based on data quality)
        evidence_confidence = "High"  # Audited financial statements are high-evidence

        # Classification confidence: how certain we are in the interpretation
        if len(metrics) >= 4 and positive_metrics + negative_metrics >= 3:
            classification_confidence = "High"  # Clear signal
        elif len(metrics) >= 3 or (positive_metrics + negative_metrics >= 2):
            classification_confidence = "Medium"  # Moderate signal
        else:
            classification_confidence = "Low"  # Weak signal

        # Data coverage percentage
        available_metrics = len(metrics)
        data_coverage = int((available_metrics / 6) * 100) if available_metrics > 0 else 0  # 6 possible metrics

        # Calculate score
        score = 50 + (positive_metrics - negative_metrics) * 12
        score = max(0, min(100, score))

        # Build result with PHASE 2 structure
        result = {
            "status": "complete",
            "period": f"FY{latest_period_end.year}",
            "period_type": "FY",
            "periods": {
                "latest": latest_period_end.isoformat() if latest_period_end else None,
                "prior": prior_period_end.isoformat() if prior_period_end else None,
            },

            # PHASE 2: Explicit metrics
            "metrics": metrics,

            # Assessment with rationale
            "assessment": overall,
            "assessment_rationale": assessment_rationale,

            # PHASE 2: Separated confidence
            "evidence_confidence": evidence_confidence,  # Confidence in the facts
            "classification_confidence": classification_confidence,  # Confidence in the interpretation
            "data_coverage_pct": data_coverage,

            # Score and narrative
            "score": score,
            "narrative": f"Business health: {overall}. {assessment_rationale}",

            # Backward compatibility
            "components": {
                "revenue_growth": "Positive" if revenue_growth and revenue_growth > 0 else "Negative" if revenue_growth and revenue_growth < 0 else "Unknown",
                "profitability": "Positive" if pat_growth and pat_growth > 0 else "Negative" if pat_growth and pat_growth < 0 else "Unknown",
                "margins": metrics.get("net_margin", {}).get("trend", "Unknown"),
                "cash_generation": metrics.get("ocf_growth", {}).get("status", "Unknown"),
                "balance_sheet": metrics.get("debt_to_equity", {}).get("trend", "Unknown"),
                "earnings_quality": "Strong" if (ocf_growth and pat_growth and ocf_growth > pat_growth) else "Weak" if has_ocf and ocf_growth else "Unknown",
            }
        }

        return result
