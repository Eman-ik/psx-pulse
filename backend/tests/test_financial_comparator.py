"""Tests for Step 20: FinancialComparator."""

import pytest
from app.services.financial_comparator import (
    FinancialComparator,
    ComparisonType,
)


@pytest.fixture
def comparator():
    """Create financial comparator instance."""
    return FinancialComparator()


def test_period_comparison_yoy(comparator):
    """Test year-over-year comparison."""
    comparison = comparator.compare_periods(
        metric_name="Revenue",
        period_a="Q2 2024",
        value_a=1000.0,
        period_b="Q2 2023",
        value_b=800.0,
        comparison_type=ComparisonType.YOY,
    )

    assert comparison is not None
    assert comparison.absolute_change == 200.0
    assert comparison.change_pct == 25.0  # 200/800 * 100


def test_period_comparison_qoq(comparator):
    """Test quarter-over-quarter comparison."""
    comparison = comparator.compare_periods(
        metric_name="Revenue",
        period_a="Q2 2024",
        value_a=1050.0,
        period_b="Q1 2024",
        value_b=1000.0,
        comparison_type=ComparisonType.QOQ,
    )

    assert comparison is not None
    assert comparison.absolute_change == 50.0
    assert comparison.change_pct == 5.0


def test_period_comparison_to_dict(comparator):
    """Test period comparison dictionary conversion."""
    comparison = comparator.compare_periods(
        metric_name="Revenue",
        period_a="Q2 2024",
        value_a=1000.0,
        period_b="Q1 2024",
        value_b=950.0,
    )

    comp_dict = comparison.to_dict()

    assert "metric_name" in comp_dict
    assert "period_a" in comp_dict
    assert "change_pct" in comp_dict
    assert comp_dict["metric_name"] == "Revenue"


def test_period_comparison_negative_change(comparator):
    """Test comparison with negative change."""
    comparison = comparator.compare_periods(
        metric_name="Expenses",
        period_a="Q2 2024",
        value_a=800.0,
        period_b="Q1 2024",
        value_b=1000.0,
    )

    assert comparison.absolute_change == -200.0
    assert comparison.change_pct == -20.0


def test_period_comparison_none_values(comparator):
    """Test comparison with None values."""
    comparison = comparator.compare_periods(
        metric_name="Revenue",
        period_a="Q2 2024",
        value_a=None,
        period_b="Q1 2024",
        value_b=1000.0,
    )

    assert comparison is None


def test_cagr_calculation(comparator):
    """Test CAGR calculation."""
    # 100 growing to 200 over 5 years = CAGR ~14.87%
    cagr = comparator.calculate_cagr(start_value=100.0, end_value=200.0, years=5.0)

    assert 14.8 < cagr < 15.0


def test_cagr_decline(comparator):
    """Test CAGR with decline."""
    # 200 declining to 100 over 5 years = negative CAGR
    cagr = comparator.calculate_cagr(start_value=200.0, end_value=100.0, years=5.0)

    assert cagr < 0


def test_trend_analysis_basic(comparator):
    """Test basic trend analysis."""
    periods = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
    values = [100.0, 110.0, 120.0, 130.0]

    trend = comparator.analyze_trend(
        metric_name="Revenue",
        periods=periods,
        values=values,
    )

    assert trend is not None
    assert trend.min_value == 100.0
    assert trend.max_value == 130.0
    assert trend.mean_value == 115.0


def test_trend_analysis_volatility(comparator):
    """Test volatility calculation in trend."""
    # Stable trend
    stable_periods = ["Q1", "Q2", "Q3", "Q4"]
    stable_values = [100.0, 100.5, 100.2, 100.8]

    stable_trend = comparator.analyze_trend(
        metric_name="Revenue",
        periods=stable_periods,
        values=stable_values,
    )

    # Volatile trend
    volatile_periods = ["Q1", "Q2", "Q3", "Q4"]
    volatile_values = [100.0, 150.0, 80.0, 140.0]

    volatile_trend = comparator.analyze_trend(
        metric_name="Revenue",
        periods=volatile_periods,
        values=volatile_values,
    )

    # Volatile should have higher volatility
    assert volatile_trend.volatility > stable_trend.volatility


def test_trend_analysis_moving_averages(comparator):
    """Test moving average calculation."""
    periods = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]
    values = [100.0, 105.0, 110.0, 115.0, 120.0, 125.0]

    trend = comparator.analyze_trend(
        metric_name="Revenue",
        periods=periods,
        values=values,
    )

    assert trend.moving_avg_3 is not None
    assert len(trend.moving_avg_3) > 0
    assert trend.moving_avg_5 is not None
    assert len(trend.moving_avg_5) > 0


def test_trend_analysis_with_nones(comparator):
    """Test trend analysis with None values."""
    periods = ["Q1", "Q2", "Q3", "Q4"]
    values = [100.0, None, 110.0, 120.0]

    trend = comparator.analyze_trend(
        metric_name="Revenue",
        periods=periods,
        values=values,
    )

    assert trend is not None
    assert trend.min_value == 100.0
    assert trend.max_value == 120.0


def test_seasonality_detection_q1_q4(comparator):
    """Test seasonality detection between Q1 and Q4."""
    comparison = comparator.compare_periods(
        metric_name="Revenue",
        period_a="Q1 2024",
        value_a=800.0,
        period_b="Q4 2023",
        value_b=900.0,
        comparison_type=ComparisonType.SEQUENTIAL,
    )

    # Q1 typically lower than Q4 due to seasonality
    assert comparison.seasonality_detected is True
    assert comparison.seasonality_adjusted is True


def test_trend_analysis_insufficient_data(comparator):
    """Test trend analysis with insufficient data."""
    trend = comparator.analyze_trend(
        metric_name="Revenue",
        periods=["Q1"],
        values=[100.0],
    )

    assert trend is None


def test_trend_analysis_to_dict(comparator):
    """Test trend analysis dictionary conversion."""
    periods = ["Q1", "Q2", "Q3", "Q4"]
    values = [100.0, 110.0, 120.0, 130.0]

    trend = comparator.analyze_trend(
        metric_name="Revenue",
        periods=periods,
        values=values,
    )

    trend_dict = trend.to_dict()

    assert "metric_name" in trend_dict
    assert "period_count" in trend_dict
    assert trend_dict["period_count"] == 4
    assert "min_value" in trend_dict
    assert "volatility" in trend_dict
