"""Period Alignment Utilities — ensure FY/Q/TTM comparisons are explicit and correct.

Problem: Engines comparing revenue[-1] and pat[-1] may be mixing FY and Q periods.
Solution: Use aligned_values() to ensure all metrics from same period.

Example:
    # BEFORE (potentially wrong)
    revenue = context.get_series("revenue")
    pat = context.get_series("profit_after_tax")
    if revenue[-1] and pat[-1]:
        margin = pat[-1] / revenue[-1]  # Are these from same period?

    # AFTER (explicitly correct)
    aligned = context.get_aligned_values(
        ["revenue", "profit_after_tax"],
        period_type="FY",
        limit=3
    )
    for period_data in aligned:
        margin = period_data["profit_after_tax"] / period_data["revenue"]
        # Now guaranteed same period
"""

from typing import Dict, List, Optional
from datetime import date
from app.analysis.evidence_context import ResearchContext


class PeriodAlignedAnalyzer:
    """Helper for period-aligned financial analysis."""

    def __init__(self, context: ResearchContext):
        self.context = context

    def calculate_growth_aligned(
        self,
        metric: str,
        period_type: str = "FY",
        periods: int = 1,
    ) -> Optional[float]:
        """Calculate growth rate using aligned periods (not just latest values).

        Args:
            metric: Metric name (e.g., "revenue")
            period_type: "FY" or "Q"
            periods: Number of periods back to compare (1 = YoY for FY)

        Returns:
            Growth rate as decimal (0.15 = +15%), or None if insufficient data
        """
        series = self.context.get_aligned_series([metric], period_type)
        values = series.get(metric, [])

        if len(values) < periods + 1:
            return None

        current = values[-1]
        prior = values[-(periods + 1)]

        if prior == 0:
            return None

        return (current - prior) / abs(prior)

    def compare_metrics_aligned(
        self,
        metric1: str,
        metric2: str,
        period_type: str = "FY",
    ) -> Optional[Dict]:
        """Compare two metrics from the same period.

        Returns:
            {
                "period_end": date,
                "metric1": value,
                "metric2": value,
                "ratio": metric1 / metric2,
                "period_type": "FY" | "Q"
            }
            or None if metrics not aligned
        """
        aligned = self.context.get_aligned_values(
            [metric1, metric2],
            period_type=period_type,
            limit=1,
        )

        if not aligned:
            return None

        latest = aligned[0]
        m1_val = latest.get(metric1)
        m2_val = latest.get(metric2)

        if m1_val is None or m2_val is None or m2_val == 0:
            return None

        return {
            "period_end": latest["period_end"],
            "metric1": metric1,
            "metric1_value": m1_val,
            "metric2": metric2,
            "metric2_value": m2_val,
            "ratio": m1_val / m2_val,
            "period_type": self.context.get_period_type(latest["period_end"]),
        }

    def get_fy_trend(
        self,
        metrics: List[str],
        limit: int = 5,
    ) -> List[Dict]:
        """Get FY trend for multiple metrics over time.

        Returns:
            [{
                "period_end": date,
                "metric1": value,
                "metric2": value,
                ...
            }, ...]
        """
        return self.context.get_aligned_values(metrics, period_type="FY", limit=limit)

    def get_q_trend(
        self,
        metrics: List[str],
        limit: int = 8,
    ) -> List[Dict]:
        """Get quarterly trend for multiple metrics over time.

        Returns:
            [{
                "period_end": date,
                "metric1": value,
                "metric2": value,
                ...
            }, ...]
        """
        return self.context.get_aligned_values(metrics, period_type="Q", limit=limit)


# Example usage in an engine:
"""
class RatioAnalysisEngine:
    @staticmethod
    def analyze(context: ResearchContext) -> Dict:
        analyzer = PeriodAlignedAnalyzer(context)

        # GOOD: Explicitly aligned comparison
        roe_comparison = analyzer.compare_metrics_aligned(
            "profit_after_tax",
            "total_equity",
            period_type="FY"
        )

        # GOOD: Explicit growth rate using aligned periods
        revenue_growth = analyzer.calculate_growth_aligned(
            "revenue",
            period_type="FY",
            periods=1  # YoY
        )

        # GOOD: Trend analysis with guaranteed alignment
        fy_trend = analyzer.get_fy_trend(
            ["revenue", "profit_after_tax", "operating_cash_flow"],
            limit=5  # 5 year trend
        )

        return {
            "roe": roe_comparison,
            "revenue_growth": revenue_growth,
            "trend": fy_trend,
        }
"""
