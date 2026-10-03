"""Period Duration Semantics — Distinguish discrete vs cumulative/YTD quarterly data.

CRITICAL: Pakistani financial statements often report:
- Annual: Always discrete (FY2025 = Jan-Dec 2025)
- Quarterly: Can be EITHER discrete (Q3 only) OR cumulative (9M YTD)

This module detects and normalizes the distinction.

Example problem:
  Jun revenue = 55  (6M cumulative)
  Sep revenue = 90  (9M cumulative)
  Naive engine: (90-55)/55 = 63.6% "Q3 growth"
  Actual Q3 discrete: 90-55 = 35

Solution: Tag each fact with duration_basis and normalize during ingestion.
"""

from datetime import date
from typing import Optional, Dict, List, Tuple


class PeriodDurationDetector:
    """Detect whether a quarterly figure is discrete or cumulative/YTD."""

    # PSX-specific heuristics: companies often report 9M/6M/3M cumulative
    # Detected by comparing revenue trends across quarters
    CUMULATIVE_INDICATORS = {
        # If Q1 < Q2 < Q3 (always increasing), likely cumulative
        "monotonic_increase": True,
        # If Q3 > Q2 > Q1 but Q3 < Q1 + Q2 + Q3 potential, might be discrete
        "variance_threshold": 0.15,  # Allow 15% variance
    }

    @staticmethod
    def detect_duration(
        metric: str,
        period_type: str,
        quarters_in_sequence: List[Tuple[date, float]],
    ) -> str:
        """Detect if metric is discrete or cumulative YTD.

        Args:
            metric: Line item name (revenue, pat, etc.)
            period_type: "Q" or "FY"
            quarters_in_sequence: [(date, value), ...] sorted chronologically

        Returns:
            "discrete" | "ytd" | "point_in_time"
        """
        if period_type != "Q" or len(quarters_in_sequence) < 2:
            return "discrete"

        # Point-in-time metrics (balance sheet items) are never cumulative
        if metric in PeriodDurationDetector.POINT_IN_TIME_METRICS:
            return "point_in_time"

        # Flow metrics (income statement, cash flow) can be cumulative
        if metric in PeriodDurationDetector.FLOW_METRICS:
            return PeriodDurationDetector._detect_flow_duration(quarters_in_sequence)

        # Default to discrete
        return "discrete"

    @staticmethod
    def _detect_flow_duration(quarters: List[Tuple[date, float]]) -> str:
        """Detect if flow metric is discrete or cumulative.

        If values always increase (or mostly increase) across quarters,
        likely cumulative. If they vary randomly, likely discrete.
        """
        if len(quarters) < 2:
            return "discrete"

        values = [v for _, v in quarters]

        # Count monotonic increases
        increases = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
        increase_ratio = increases / (len(values) - 1)

        # If 70%+ of comparisons are increases, likely cumulative
        if increase_ratio >= 0.7:
            return "ytd"

        return "discrete"

    # Metrics that are always point-in-time (balance sheet)
    POINT_IN_TIME_METRICS = {
        "total_assets",
        "current_assets",
        "total_liabilities",
        "current_liabilities",
        "total_equity",
        "accounts_receivable",
        "inventory",
        "cash_and_equivalents",
        "total_debt",
        "short_term_debt",
        "long_term_debt",
        "retained_earnings",
    }

    # Metrics that are always flows (income statement / cash flow)
    FLOW_METRICS = {
        "revenue",
        "cost_of_goods_sold",
        "gross_profit",
        "operating_expenses",
        "operating_profit",
        "finance_cost",
        "other_income",
        "profit_before_tax",
        "profit_after_tax",
        "operating_cash_flow",
        "investing_cash_flow",
        "financing_cash_flow",
        "net_cash_flow",
        "dividend_per_share",
        "earnings_per_share",
    }


class PeriodDurationNormalizer:
    """Normalize cumulative figures to discrete equivalent."""

    @staticmethod
    def normalize_to_discrete(
        metric: str,
        period_type: str,
        current_value: float,
        prior_value: Optional[float],
        duration_basis: str,
    ) -> float:
        """Convert YTD cumulative value to discrete equivalent if needed.

        Args:
            metric: Line item name
            period_type: "Q" or "FY"
            current_value: The reported value
            prior_value: Prior period value (if YTD, subtract this)
            duration_basis: "discrete" | "ytd"

        Returns:
            Discrete equivalent of the value
        """
        # Annual and point-in-time are always discrete
        if period_type != "Q" or duration_basis != "ytd":
            return current_value

        # For YTD, discrete value = current - prior (if prior available)
        if prior_value is not None:
            return current_value - prior_value

        # Can't normalize without prior, return as-is
        return current_value

    @staticmethod
    def normalize_comparison(
        current_discrete: float,
        prior_discrete: float,
        current_duration: str,
        prior_duration: str,
    ) -> Tuple[float, float, bool]:
        """Adjust comparison if one value is YTD and other is discrete.

        Args:
            current_discrete: Current period value
            prior_discrete: Prior period value
            current_duration: Current duration basis
            prior_duration: Prior duration basis

        Returns:
            (current_adjusted, prior_adjusted, can_compare)
            can_compare=False if comparison not valid
        """
        # Both same basis: safe to compare
        if current_duration == prior_duration:
            return current_discrete, prior_discrete, True

        # Mixed basis: unsafe to compare directly
        # (would need to reprocess both to same basis)
        return current_discrete, prior_discrete, False


class PeriodAlignmentWithDuration:
    """Period alignment that respects duration basis.

    Ensures comparisons only happen between:
    - Discrete to discrete
    - YTD to YTD (same cumulation point)
    - Never mixed
    """

    @staticmethod
    def get_comparable_periods(
        period_data: Dict[date, Dict],
        duration_basis_map: Dict[date, str],
    ) -> List[Tuple[date, date]]:
        """Get pairs of periods that can be safely compared.

        Only returns pairs with same duration_basis.

        Returns:
            [(current_date, prior_date), ...] that are comparable
        """
        dates = sorted(period_data.keys(), reverse=True)
        comparable = []

        for i in range(1, len(dates)):
            current_date = dates[i-1]
            prior_date = dates[i]

            current_basis = duration_basis_map.get(current_date, "unknown")
            prior_basis = duration_basis_map.get(prior_date, "unknown")

            if current_basis == prior_basis and current_basis != "unknown":
                comparable.append((current_date, prior_date))

        return comparable

    @staticmethod
    def validate_period_comparison(
        metric1: Dict,  # {period: value, duration: basis}
        metric2: Dict,
        metric_name: str,
    ) -> Tuple[bool, str]:
        """Validate that two metrics can be compared.

        Returns:
            (valid, reason)
        """
        if metric1.get("duration") != metric2.get("duration"):
            return False, f"{metric_name}: cannot compare {metric1.get('duration')} to {metric2.get('duration')}"

        if metric1.get("period_type") != metric2.get("period_type"):
            return False, f"{metric_name}: cannot compare {metric1.get('period_type')} to {metric2.get('period_type')}"

        return True, ""


# Expected column in FinancialFact after schema update
DURATION_BASIS_VALUES = ["discrete", "ytd", "point_in_time"]
