"""Step 19: Trend Visualization Engine — Format trends for frontend charting.

Converts analytical data into chart-ready JSON:
- Time-series data with historical and forecast values
- Technical indicators (moving averages, trend lines)
- Min/max bounds for scaling
- Multiple chart types (line, area, bar)

Input: Historical data + forecasts
Output: TrendChartData (frontend-ready JSON)
"""

import logging
import statistics
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ChartType(str, Enum):
    """Chart rendering types."""

    LINE = "line"
    AREA = "area"
    BAR = "bar"
    CANDLESTICK = "candlestick"


class TrendDirection(str, Enum):
    """Trend direction classification."""

    UPTREND = "Uptrend"
    DOWNTREND = "Downtrend"
    STABLE = "Stable"
    VOLATILE = "Volatile"


@dataclass
class ChartDataPoint:
    """Single data point for chart."""

    label: str  # Period label: "Q1 2024", "Jan 2024", etc.
    actual_value: Optional[float] = None  # Historical/current value
    forecast_value: Optional[float] = None  # Projected value
    moving_avg_20: Optional[float] = None  # 20-period moving average
    moving_avg_50: Optional[float] = None  # 50-period moving average


@dataclass
class TrendChartData:
    """Complete chart data ready for frontend rendering."""

    ticker: str
    metric_name: str
    chart_type: ChartType

    data_points: List[ChartDataPoint] = field(default_factory=list)

    # Bounds and statistics
    min_value: float = 0.0
    max_value: float = 100.0
    mean_value: float = 50.0
    median_value: float = 50.0

    # Trend info
    trend_direction: TrendDirection = TrendDirection.STABLE
    trend_strength: float = 0.0  # 0-100%

    # Forecast info
    has_forecast: bool = False
    forecast_confidence: float = 50.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ticker": self.ticker,
            "metric_name": self.metric_name,
            "chart_type": self.chart_type.value,
            "data_points": [
                {
                    "label": p.label,
                    "actual": round(p.actual_value, 2) if p.actual_value else None,
                    "forecast": round(p.forecast_value, 2) if p.forecast_value else None,
                    "ma20": round(p.moving_avg_20, 2) if p.moving_avg_20 else None,
                    "ma50": round(p.moving_avg_50, 2) if p.moving_avg_50 else None,
                }
                for p in self.data_points
            ],
            "bounds": {
                "min": round(self.min_value, 2),
                "max": round(self.max_value, 2),
                "mean": round(self.mean_value, 2),
                "median": round(self.median_value, 2),
            },
            "trend": {
                "direction": self.trend_direction.value,
                "strength_pct": round(self.trend_strength, 1),
            },
            "forecast": {
                "has_forecast": self.has_forecast,
                "confidence": round(self.forecast_confidence, 1),
            },
        }


class TrendVisualizationEngine:
    """Formats trends into chart-ready JSON for frontend."""

    def __init__(self):
        """Initialize visualization engine."""
        self.logger = logging.getLogger(__name__)

    def build_chart_data(
        self,
        ticker: str,
        metric_name: str,
        historical_values: List[tuple],  # [(label, value), ...]
        forecast_values: Optional[List[tuple]] = None,  # [(label, value), ...]
        chart_type: ChartType = ChartType.LINE,
    ) -> Optional[TrendChartData]:
        """Build chart-ready data from historical and forecast values.

        Args:
            ticker: Company ticker
            metric_name: Metric being charted (e.g., "Revenue", "Profit")
            historical_values: List of (label, value) tuples for history
            forecast_values: List of (label, value) tuples for forecast
            chart_type: Type of chart to render

        Returns:
            TrendChartData or None on error
        """
        try:
            if not historical_values:
                return None

            # Extract values for calculations
            hist_vals = [v for _, v in historical_values if v is not None]
            if not hist_vals:
                return None

            # Build data points
            data_points = []

            # Add historical data
            for label, value in historical_values:
                if value is not None:
                    data_points.append(
                        ChartDataPoint(label=label, actual_value=value)
                    )

            # Add forecast data
            has_forecast = False
            forecast_conf = 50.0
            if forecast_values:
                has_forecast = True
                for label, value in forecast_values:
                    if value is not None:
                        data_points.append(
                            ChartDataPoint(label=label, forecast_value=value)
                        )
                forecast_conf = self._calculate_forecast_confidence(
                    hist_vals, forecast_values
                )

            # Calculate moving averages
            data_points = self._add_moving_averages(data_points)

            # Calculate statistics
            min_val = min(hist_vals)
            max_val = max(hist_vals)
            mean_val = statistics.mean(hist_vals)
            median_val = statistics.median(hist_vals)

            # Determine trend
            trend_dir = self._determine_trend_direction(hist_vals)
            trend_str = self._calculate_trend_strength(hist_vals)

            chart_data = TrendChartData(
                ticker=ticker,
                metric_name=metric_name,
                chart_type=chart_type,
                data_points=data_points,
                min_value=min_val,
                max_value=max_val,
                mean_value=mean_val,
                median_value=median_val,
                trend_direction=trend_dir,
                trend_strength=trend_str,
                has_forecast=has_forecast,
                forecast_confidence=forecast_conf,
            )

            self.logger.info(
                f"Built chart data for {ticker} {metric_name}: "
                f"{len(data_points)} points, trend {trend_dir.value}"
            )
            return chart_data

        except Exception as e:
            self.logger.error(f"Error building chart data: {e}")
            return None

    @staticmethod
    def _add_moving_averages(data_points: List[ChartDataPoint]) -> List[ChartDataPoint]:
        """Add moving averages to data points."""
        # Extract actual values for MA calculation
        actual_vals = [p.actual_value for p in data_points if p.actual_value is not None]

        if len(actual_vals) < 20:
            return data_points

        # Calculate 20-period and 50-period moving averages
        for i, point in enumerate(data_points):
            if point.actual_value is not None:
                # 20-period MA
                if i >= 19:
                    ma20_vals = actual_vals[max(0, i - 19) : i + 1]
                    point.moving_avg_20 = statistics.mean(ma20_vals)

                # 50-period MA
                if i >= 49:
                    ma50_vals = actual_vals[max(0, i - 49) : i + 1]
                    point.moving_avg_50 = statistics.mean(ma50_vals)

        return data_points

    @staticmethod
    def _determine_trend_direction(values: List[float]) -> TrendDirection:
        """Determine overall trend direction."""
        if len(values) < 2:
            return TrendDirection.STABLE

        # Compare recent vs historical
        recent_avg = statistics.mean(values[-3:]) if len(values) >= 3 else values[-1]
        historical_avg = statistics.mean(values[:-3]) if len(values) > 3 else values[0]

        if historical_avg == 0:
            return TrendDirection.STABLE

        change_pct = ((recent_avg - historical_avg) / historical_avg) * 100

        if change_pct > 10:
            return TrendDirection.UPTREND
        elif change_pct < -10:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.STABLE

    @staticmethod
    def _calculate_trend_strength(values: List[float]) -> float:
        """Calculate trend strength as percentage (0-100%)."""
        if len(values) < 2:
            return 0.0

        # Calculate volatility (inverse indicates strength)
        mean = statistics.mean(values)
        if mean == 0:
            return 0.0

        variance = statistics.variance(values) if len(values) > 1 else 0
        stdev = (variance ** 0.5) if variance > 0 else 0

        # Coefficient of variation
        cv = (stdev / mean) * 100 if mean != 0 else 0

        # Strength: inverse of CV (low volatility = strong trend)
        strength = max(0, 100 - cv)

        return strength

    @staticmethod
    def _calculate_forecast_confidence(
        historical_values: List[float],
        forecast_values: List[tuple],
    ) -> float:
        """Calculate confidence in forecast."""
        confidence = 60.0

        # More historical data = higher confidence
        confidence += min(20, len(historical_values) / 5)

        # Fewer anomalies = higher confidence
        if len(historical_values) > 2:
            volatility = (
                statistics.stdev(historical_values) / statistics.mean(historical_values)
                if statistics.mean(historical_values) != 0
                else 1.0
            )
            confidence -= min(10, volatility * 10)

        return max(0, min(100, confidence))
