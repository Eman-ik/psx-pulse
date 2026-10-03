"""Step 20: Financial Comparator — Compare financials across periods.

Period-over-period financial analysis:
- Absolute change and percentage change
- YoY, QoQ, and trend comparisons
- Seasonality detection and adjustment
- Moving average trends

Input: Multiple periods of financial data
Output: PeriodComparison (comparative metrics with context)
"""

import logging
import statistics
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ComparisonType(str, Enum):
    """Types of period comparisons."""

    YOY = "Year-over-Year"  # Same period, different year
    QOQ = "Quarter-over-Quarter"  # Consecutive quarters
    SEQUENTIAL = "Sequential"  # Any consecutive periods
    TREND = "Trend"  # Multiple periods


@dataclass
class PeriodComparison:
    """Comparison between two periods."""

    metric_name: str
    period_a: str  # Label for first period (e.g., "Q1 2024")
    period_b: str  # Label for second period (e.g., "Q4 2023")
    comparison_type: ComparisonType

    value_a: Optional[float]
    value_b: Optional[float]

    # Change metrics
    absolute_change: Optional[float] = None  # value_a - value_b
    change_pct: Optional[float] = None  # (value_a - value_b) / value_b * 100
    cagr: Optional[float] = None  # Compound annual growth rate

    # Context
    seasonality_detected: bool = False
    seasonality_adjusted: bool = False
    adjusted_value_a: Optional[float] = None  # Seasonality-adjusted value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "period_a": self.period_a,
            "period_b": self.period_b,
            "comparison_type": self.comparison_type.value,
            "value_a": round(self.value_a, 2) if self.value_a else None,
            "value_b": round(self.value_b, 2) if self.value_b else None,
            "absolute_change": round(self.absolute_change, 2) if self.absolute_change else None,
            "change_pct": round(self.change_pct, 1) if self.change_pct else None,
            "seasonality_adjusted": self.seasonality_adjusted,
        }


@dataclass
class TrendAnalysisResult:
    """Multi-period trend analysis."""

    metric_name: str
    periods: List[str]  # Chronologically ordered period labels
    values: List[Optional[float]]  # Values for each period

    # Trend metrics
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    volatility: float = 0.0  # Coefficient of variation

    # Moving averages
    moving_avg_3: Optional[List[float]] = None  # 3-period MA
    moving_avg_5: Optional[List[float]] = None  # 5-period MA

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "period_count": len(self.periods),
            "min_value": round(self.min_value, 2) if self.min_value else None,
            "max_value": round(self.max_value, 2) if self.max_value else None,
            "mean_value": round(self.mean_value, 2) if self.mean_value else None,
            "volatility": round(self.volatility, 2),
        }


class FinancialComparator:
    """Compares financial metrics across multiple periods."""

    def __init__(self):
        """Initialize comparator."""
        self.logger = logging.getLogger(__name__)

    def compare_periods(
        self,
        metric_name: str,
        period_a: str,
        value_a: Optional[float],
        period_b: str,
        value_b: Optional[float],
        comparison_type: ComparisonType = ComparisonType.SEQUENTIAL,
    ) -> Optional[PeriodComparison]:
        """Compare metric between two periods.

        Args:
            metric_name: Name of metric (e.g., "Revenue")
            period_a: Label for current/later period
            value_a: Value in period A
            period_b: Label for prior/earlier period
            value_b: Value in period B
            comparison_type: Type of comparison (YoY, QoQ, etc.)

        Returns:
            PeriodComparison with change metrics
        """
        try:
            if value_a is None or value_b is None:
                return None

            comparison = PeriodComparison(
                metric_name=metric_name,
                period_a=period_a,
                period_b=period_b,
                comparison_type=comparison_type,
                value_a=value_a,
                value_b=value_b,
            )

            # Calculate changes
            comparison.absolute_change = value_a - value_b
            if value_b != 0:
                comparison.change_pct = (comparison.absolute_change / value_b) * 100

            # Detect seasonality
            seasonality = self._detect_seasonality(period_a, period_b)
            if seasonality:
                comparison.seasonality_detected = True
                comparison.adjusted_value_a = self._adjust_for_seasonality(
                    value_a, seasonality
                )
                comparison.seasonality_adjusted = True

            self.logger.info(
                f"Compared {metric_name}: {period_a} ({value_a}) vs "
                f"{period_b} ({value_b}), change: {comparison.change_pct:.1f}%"
            )
            return comparison

        except Exception as e:
            self.logger.error(f"Error comparing periods: {e}")
            return None

    def analyze_trend(
        self,
        metric_name: str,
        periods: List[str],  # Chronologically ordered
        values: List[Optional[float]],
    ) -> Optional[TrendAnalysisResult]:
        """Analyze metric trend across multiple periods.

        Args:
            metric_name: Name of metric
            periods: List of period labels (chronologically ordered)
            values: Values for each period

        Returns:
            TrendAnalysisResult with statistics
        """
        try:
            if len(periods) != len(values) or len(periods) < 2:
                return None

            valid_values = [v for v in values if v is not None]
            if not valid_values:
                return None

            result = TrendAnalysisResult(
                metric_name=metric_name,
                periods=periods,
                values=values,
            )

            # Calculate statistics
            result.min_value = min(valid_values)
            result.max_value = max(valid_values)
            result.mean_value = statistics.mean(valid_values)

            # Calculate volatility
            if len(valid_values) > 1:
                stdev = statistics.stdev(valid_values)
                mean = result.mean_value
                if mean != 0:
                    result.volatility = (stdev / mean) * 100

            # Calculate moving averages
            result.moving_avg_3 = self._calculate_moving_average(valid_values, 3)
            result.moving_avg_5 = self._calculate_moving_average(valid_values, 5)

            self.logger.info(
                f"Analyzed trend for {metric_name} over {len(periods)} periods: "
                f"mean={result.mean_value:.2f}, volatility={result.volatility:.1f}%"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing trend: {e}")
            return None

    def calculate_cagr(
        self,
        start_value: float,
        end_value: float,
        years: float,
    ) -> float:
        """Calculate Compound Annual Growth Rate.

        Args:
            start_value: Value at start
            end_value: Value at end
            years: Number of years between start and end

        Returns:
            CAGR as percentage
        """
        if start_value <= 0 or years <= 0:
            return 0.0

        try:
            cagr = ((end_value / start_value) ** (1 / years) - 1) * 100
            return max(-100, cagr)  # Cap at -100% (total loss)
        except Exception as e:
            self.logger.error(f"Error calculating CAGR: {e}")
            return 0.0

    @staticmethod
    def _detect_seasonality(period_a: str, period_b: str) -> Optional[float]:
        """Detect if periods have seasonal patterns.

        Returns seasonality factor (1.0-1.3) or None if not detected.
        """
        # Extract quarters/months from period labels
        a_q = None
        b_q = None

        for quarter in ["Q1", "Q2", "Q3", "Q4"]:
            if quarter in period_a:
                a_q = int(quarter[1])
            if quarter in period_b:
                b_q = int(quarter[1])

        if a_q and b_q:
            # Q1 typically 10-15% lower than Q4 (seasonal)
            if a_q == 1 and b_q == 4:
                return 1.12  # Average seasonality factor
            elif a_q == 4 and b_q == 1:
                return 0.89

        return None

    @staticmethod
    def _adjust_for_seasonality(value: float, seasonality_factor: float) -> float:
        """Adjust value for seasonality."""
        return value / seasonality_factor if seasonality_factor else value

    @staticmethod
    def _calculate_moving_average(
        values: List[float],
        period: int,
    ) -> List[float]:
        """Calculate moving average for given period."""
        if len(values) < period:
            return []

        moving_avg = []
        for i in range(period - 1, len(values)):
            window = values[i - period + 1 : i + 1]
            moving_avg.append(statistics.mean(window))

        return moving_avg
