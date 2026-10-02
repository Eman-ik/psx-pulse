"""What Should I Watch Engine — converts research into monitoring framework.

Instead of raw analysis, this tells users: Here are the 5 things that will tell you if
the thesis is holding or breaking down. Watch these metrics/signals before buying.
"""

from typing import Dict, List

from app.analysis.evidence_context import ResearchContext, ContextualizedOutput


class WhatToWatchEngine:
    """Generate specific monitoring framework from research."""

    @staticmethod
    def analyze(context: ResearchContext) -> Dict:
        """Create actionable watch list using shared Evidence Context."""
        output = ContextualizedOutput("what_to_watch", context)

        # Get latest values from context
        revenue = context.get_value("revenue")
        gross_profit = context.get_value("gross_profit")
        ocf = context.get_value("operating_cash_flow")
        ar_days = context.get_value("receivable_days")
        debt = context.get_value("total_debt")
        equity = context.get_value("total_equity")

        watch_metrics = []

        # 1. Margin sustainability
        if revenue and gross_profit:
            current_gm = (gross_profit / revenue) * 100
            watch_metrics.append({
                "priority": 1,
                "metric": "Gross margin",
                "current": f"{current_gm:.1f}%",
                "watch_threshold": f"> {current_gm * 0.95:.1f}%",
                "rationale": "Would confirm margin recovery if sustained above this level.",
                "breach_means": "Deterioration suggests input cost pressure or competitive weakness.",
                "frequency": "Quarterly results",
            })

        # 2. Quarterly dispatch/volume growth
        watch_metrics.append({
            "priority": 2,
            "metric": "Quarterly volume/dispatch growth",
            "current": "Need baseline",
            "watch_threshold": "> 8% YoY",
            "rationale": "Needs to remain >8% to support earnings consensus.",
            "breach_means": "Growth below 8% signals demand weakness or market share loss.",
            "frequency": "Quarterly announcements + press release tracking",
        })

        # 3. Receivables quality
        if ar_days:
            watch_metrics.append({
                "priority": 3,
                "metric": "Receivable days",
                "current": f"{ar_days:.0f} days",
                "watch_threshold": f"< {ar_days * 1.15:.0f} days",
                "rationale": f"Currently at {ar_days:.0f}; deterioration above {ar_days * 1.15:.0f} would weaken earnings quality.",
                "breach_means": "Rising receivables signal collection issues or distressed customers.",
                "frequency": "Quarterly balance sheet",
            })

        # 4. Operating cash flow
        watch_metrics.append({
            "priority": 4,
            "metric": "Operating cash flow",
            "current": f"PKR {ocf:,.0f}m" if ocf else "Unknown",
            "watch_threshold": "Maintain above 50% of PAT",
            "rationale": "OCF consistently above reported earnings validates earnings quality.",
            "breach_means": "OCF falling below earnings suggests working capital drain.",
            "frequency": "Quarterly cash flow statement",
        })

        # 5. Leverage trend
        if debt and equity:
            current_leverage = debt / equity
            watch_metrics.append({
                "priority": 5,
                "metric": "Leverage ratio (Debt/Equity)",
                "current": f"{current_leverage:.2f}x",
                "watch_threshold": f"< {current_leverage * 1.10:.2f}x",
                "rationale": "Debt reduction supports the bull thesis and dividend capacity.",
                "breach_means": "Rising leverage constrains financial flexibility.",
                "frequency": "Quarterly balance sheet",
            })

        # 6. Relative strength vs. sector
        watch_metrics.append({
            "priority": 6,
            "metric": "Relative strength vs. sector",
            "current": "TBD",
            "watch_threshold": "Outperforming sector",
            "rationale": "Positive relative momentum confirms thesis support from institutional accumulation.",
            "breach_means": "Underperformance suggests institutional distribution or thesis doubt.",
            "frequency": "Weekly price monitoring",
        })

        # 7. Technical levels
        watch_metrics.append({
            "priority": 7,
            "metric": "Support/resistance",
            "current": "Identify from charts",
            "watch_threshold": "Breakout above primary resistance = trend confirmation",
            "rationale": "High-volume breakout would confirm continuation of bull trend.",
            "breach_means": "Breakdown below support signals thesis invalidation.",
            "frequency": "Daily/weekly technical review",
        })

        # 8. Next results date
        watch_metrics.append({
            "priority": 0,
            "metric": "Next quarterly results",
            "current": "TBD",
            "watch_threshold": "Watch for consensus beat on revenue and margins",
            "rationale": "Critical test for earnings estimates and margin guidance.",
            "breach_means": "Miss on revenues or margins would invalidate bull case.",
            "frequency": "One-time quarterly event",
        })

        # Confidence based on data
        metrics_available = sum([
            context.has_metric("revenue"),
            context.has_metric("gross_profit"),
            context.has_metric("operating_cash_flow"),
            context.has_metric("receivable_days"),
            context.has_metric("total_debt"),
        ])
        confidence = "High" if metrics_available >= 4 else "Medium" if metrics_available >= 3 else "Low"
        coverage = (metrics_available / 5) * 100

        output.set_assessment(
            assessment="Complete",
            score=75,
            narrative="Monitor these 8 metrics to track thesis health.",
            confidence=confidence,
            data_coverage=int(coverage),
        )

        result = output.to_dict()
        result["title"] = "Key Metrics to Watch Before Buying"
        result["introduction"] = "These 8 metrics will tell you if the thesis is holding or breaking down. Monitor them during your holding period."
        result["watch_metrics"] = watch_metrics
        result["monitoring_cadence"] = {
            "daily": ["Relative strength vs. sector", "Support/resistance"],
            "weekly": ["Volume trends", "Technical momentum"],
            "quarterly": ["All fundamental metrics"],
            "real_time": ["Major announcements", "Earnings date"],
        }
        result["thesis_invalidation_triggers"] = [
            "Gross margin compression below 20% for two consecutive quarters",
            "Receivables days rising above 70 days",
            "Operating cash flow turning negative",
            "Leverage rising above 2.0x with no reduction plan",
            "Dividend cut signaling cash generation stress",
            "Technical breakdown below 200-day moving average",
        ]
        result["validation"] = output.validate()

        return result
