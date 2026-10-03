"""Step 14: Multi-Period Analyzer — Compare financial trends across periods.

Analyzes financial changes over time:
- Growth rates (YoY, QoQ)
- Trend direction (improving, declining, stable)
- Volatility and consistency
- Seasonality patterns
- Anomaly detection (unusual changes)
- Projection of future trends

Input: Multiple periods of financial data
Output: TrendAnalysis (growth rates, patterns, forecasts)
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    """Trend direction indicators."""

    IMPROVING = "Improving"
    DECLINING = "Declining"
    STABLE = "Stable"
    VOLATILE = "Volatile"
    UNKNOWN = "Unknown"


@dataclass
class PeriodData:
    """Financial data for a single period."""

    period_label: str  # "Q1 2024", "FY 2023", etc.
    date: str
    revenue: Optional[float]
    profit: Optional[float]
    assets: Optional[float]
    liabilities: Optional[float]
    equity: Optional[float]
    cash_flow: Optional[float]


@dataclass
class GrowthMetrics:
    """Growth rate calculations."""

    metric_name: str
    yoy_growth_pct: Optional[float]  # Year-over-year
    qoq_growth_pct: Optional[float]  # Quarter-over-quarter
    cagr_pct: Optional[float]  # Compound annual growth rate
    avg_growth_pct: Optional[float]  # Average growth


@dataclass
class TrendAnalysis:
    """Complete trend analysis across periods."""

    ticker: str
    company_name: str
    periods_analyzed: int

    # Growth metrics
    revenue_growth: GrowthMetrics
    profit_growth: GrowthMetrics
    asset_growth: GrowthMetrics
    equity_growth: GrowthMetrics

    # Trend directions
    revenue_trend: TrendDirection
    profit_trend: TrendDirection
    margin_trend: TrendDirection
    roe_trend: TrendDirection

    # Consistency metrics
    revenue_volatility: float  # Coefficient of variation
    profit_volatility: float
    consistency_score: float  # 0-100%, how consistent is growth

    # Anomalies
    anomalies_detected: List[str]
    unusual_periods: List[str]

    # Forecasts
    revenue_forecast_next_period: Optional[float]
    profit_forecast_next_period: Optional[float]
    confidence_in_forecast: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "periods_analyzed": self.periods_analyzed,
            "revenue_trend": self.revenue_trend.value,
            "profit_trend": self.profit_trend.value,
            "margin_trend": self.margin_trend.value,
            "roe_trend": self.roe_trend.value,
            "revenue_volatility": round(self.revenue_volatility, 2),
            "profit_volatility": round(self.profit_volatility, 2),
            "consistency_score": round(self.consistency_score, 1),
            "anomalies_detected": self.anomalies_detected,
            "revenue_forecast_next_period": round(self.revenue_forecast_next_period, 2) if self.revenue_forecast_next_period else None,
            "profit_forecast_next_period": round(self.profit_forecast_next_period, 2) if self.profit_forecast_next_period else None,
            "confidence_in_forecast": round(self.confidence_in_forecast, 1),
        }


class MultiPeriodAnalyzer:
    """Analyzes financial trends across multiple periods."""

    def __init__(self):
        """Initialize analyzer."""
        self.logger = logging.getLogger(__name__)

    def analyze(
        self, ticker: str, company_name: str, periods: List[PeriodData]
    ) -> Optional[TrendAnalysis]:
        """Analyze trends across periods.

        Args:
            ticker: Company ticker
            company_name: Company name
            periods: List of period data (chronologically sorted)

        Returns:
            TrendAnalysis or None on error
        """
        try:
            if len(periods) < 2:
                self.logger.warning(f"Need at least 2 periods for analysis, got {len(periods)}")
                return None

            # Calculate growth metrics
            revenue_growth = self._calculate_growth_metrics(
                [p.revenue for p in periods], "Revenue"
            )
            profit_growth = self._calculate_growth_metrics(
                [p.profit for p in periods], "Profit"
            )
            asset_growth = self._calculate_growth_metrics(
                [p.assets for p in periods], "Assets"
            )
            equity_growth = self._calculate_growth_metrics(
                [p.equity for p in periods], "Equity"
            )

            # Determine trends
            revenue_trend = self._determine_trend(
                [p.revenue for p in periods if p.revenue is not None]
            )
            profit_trend = self._determine_trend(
                [p.profit for p in periods if p.profit is not None]
            )
            margin_trend = self._determine_margin_trend(periods)
            roe_trend = self._determine_roe_trend(periods)

            # Calculate volatility
            revenue_volatility = self._calculate_volatility(
                [p.revenue for p in periods if p.revenue is not None]
            )
            profit_volatility = self._calculate_volatility(
                [p.profit for p in periods if p.profit is not None]
            )

            # Consistency score (inverse of volatility)
            consistency_score = max(0, 100 - (revenue_volatility + profit_volatility) / 2)

            # Detect anomalies
            anomalies = self._detect_anomalies(periods)

            # Forecast next period
            revenue_forecast = self._forecast_next_value(
                [p.revenue for p in periods if p.revenue is not None]
            )
            profit_forecast = self._forecast_next_value(
                [p.profit for p in periods if p.profit is not None]
            )
            forecast_confidence = self._calculate_forecast_confidence(periods, anomalies)

            analysis = TrendAnalysis(
                ticker=ticker,
                company_name=company_name,
                periods_analyzed=len(periods),
                revenue_growth=revenue_growth,
                profit_growth=profit_growth,
                asset_growth=asset_growth,
                equity_growth=equity_growth,
                revenue_trend=revenue_trend,
                profit_trend=profit_trend,
                margin_trend=margin_trend,
                roe_trend=roe_trend,
                revenue_volatility=revenue_volatility,
                profit_volatility=profit_volatility,
                consistency_score=consistency_score,
                anomalies_detected=anomalies,
                unusual_periods=[],
                revenue_forecast_next_period=revenue_forecast,
                profit_forecast_next_period=profit_forecast,
                confidence_in_forecast=forecast_confidence,
            )

            self.logger.info(
                f"Analyzed {len(periods)} periods for {ticker}: "
                f"Revenue {revenue_trend.value}, Profit {profit_trend.value}"
            )
            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return None

    @staticmethod
    def _calculate_growth_metrics(values: List[Optional[float]], metric_name: str) -> GrowthMetrics:
        """Calculate growth metrics."""
        valid_values = [v for v in values if v is not None and v > 0]

        yoy = None
        qoq = None
        cagr = None
        avg = None

        if len(valid_values) >= 2:
            # YoY growth (last value vs first value)
            yoy = ((valid_values[-1] - valid_values[-2]) / valid_values[-2] * 100)

            # QoQ growth (consecutive quarters)
            if len(valid_values) >= 2:
                qoq = ((valid_values[-1] - valid_values[-2]) / valid_values[-2] * 100)

            # Average growth
            if len(valid_values) > 1:
                period_growth = [
                    (valid_values[i] - valid_values[i - 1]) / valid_values[i - 1] * 100
                    for i in range(1, len(valid_values))
                ]
                avg = statistics.mean(period_growth)

            # CAGR (simplified)
            if len(valid_values) >= 2:
                cagr = ((valid_values[-1] / valid_values[0]) ** (1 / (len(valid_values) - 1)) - 1) * 100

        return GrowthMetrics(
            metric_name=metric_name,
            yoy_growth_pct=yoy,
            qoq_growth_pct=qoq,
            cagr_pct=cagr,
            avg_growth_pct=avg,
        )

    @staticmethod
    def _determine_trend(values: List[float]) -> TrendDirection:
        """Determine trend direction."""
        if len(values) < 2:
            return TrendDirection.UNKNOWN

        valid_values = [v for v in values if v is not None]
        if len(valid_values) < 2:
            return TrendDirection.UNKNOWN

        # Compare recent vs historical
        recent_avg = statistics.mean(valid_values[-2:])
        historical_avg = statistics.mean(valid_values[:-2]) if len(valid_values) > 2 else valid_values[0]

        change_pct = ((recent_avg - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0

        if change_pct > 10:
            return TrendDirection.IMPROVING
        elif change_pct < -10:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE

    @staticmethod
    def _determine_margin_trend(periods: List[PeriodData]) -> TrendDirection:
        """Determine profit margin trend."""
        margins = []
        for p in periods:
            if p.revenue and p.profit and p.revenue > 0:
                margin = (p.profit / p.revenue) * 100
                margins.append(margin)

        if len(margins) < 2:
            return TrendDirection.UNKNOWN

        if margins[-1] > margins[0]:
            return TrendDirection.IMPROVING
        elif margins[-1] < margins[0]:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE

    @staticmethod
    def _determine_roe_trend(periods: List[PeriodData]) -> TrendDirection:
        """Determine ROE (Return on Equity) trend."""
        roes = []
        for p in periods:
            if p.profit and p.equity and p.equity > 0:
                roe = (p.profit / p.equity) * 100
                roes.append(roe)

        if len(roes) < 2:
            return TrendDirection.UNKNOWN

        if roes[-1] > roes[0]:
            return TrendDirection.IMPROVING
        elif roes[-1] < roes[0]:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE

    @staticmethod
    def _calculate_volatility(values: List[float]) -> float:
        """Calculate volatility (coefficient of variation)."""
        valid_values = [v for v in values if v is not None and v > 0]

        if len(valid_values) < 2:
            return 0.0

        mean = statistics.mean(valid_values)
        variance = statistics.variance(valid_values)
        stdev = statistics.stdev(valid_values)

        if mean > 0:
            return (stdev / mean) * 100
        return 0.0

    @staticmethod
    def _detect_anomalies(periods: List[PeriodData]) -> List[str]:
        """Detect anomalies in financial data."""
        anomalies = []

        # Check for unusual changes
        revenues = [p.revenue for p in periods if p.revenue is not None and p.revenue > 0]
        if len(revenues) >= 2:
            for i in range(1, len(revenues)):
                change_pct = abs((revenues[i] - revenues[i - 1]) / revenues[i - 1] * 100)
                if change_pct > 50:  # >50% change is unusual
                    anomalies.append(f"Unusual revenue change: {change_pct:.1f}%")

        # Check for negative profit with positive revenue
        for p in periods:
            if p.revenue and p.revenue > 0 and p.profit and p.profit < 0:
                anomalies.append(f"Loss in {p.period_label} despite revenue")

        # Check for decreasing equity
        equities = [p.equity for p in periods if p.equity is not None]
        if len(equities) >= 2 and equities[-1] < equities[0]:
            anomalies.append("Decreasing equity over period")

        return anomalies[:3]  # Top 3 anomalies

    @staticmethod
    def _forecast_next_value(values: List[float]) -> Optional[float]:
        """Forecast next period value using simple trend."""
        valid_values = [v for v in values if v is not None and v > 0]

        if len(valid_values) < 2:
            return None

        # Simple linear extrapolation
        recent = valid_values[-1]
        previous = valid_values[-2]
        change = recent - previous
        forecast = recent + change

        return max(0, forecast)  # Don't forecast negative values

    @staticmethod
    def _calculate_forecast_confidence(periods: List[PeriodData], anomalies: List[str]) -> float:
        """Calculate confidence in forecast."""
        # Base confidence
        confidence = 70.0

        # More periods = higher confidence
        confidence += min(10, len(periods))

        # Anomalies reduce confidence
        confidence -= len(anomalies) * 10

        return max(0, min(100, confidence))
