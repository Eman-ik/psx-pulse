"""Tests for Step 19: TrendVisualizationEngine."""

import pytest
from app.services.trend_visualization_engine import (
    TrendVisualizationEngine,
    ChartType,
    TrendDirection,
)


@pytest.fixture
def engine():
    """Create visualization engine instance."""
    return TrendVisualizationEngine()


@pytest.fixture
def sample_historical_data():
    """Create sample historical data."""
    return [
        ("Q1 2023", 100.0),
        ("Q2 2023", 105.0),
        ("Q3 2023", 110.0),
        ("Q4 2023", 115.0),
        ("Q1 2024", 120.0),
        ("Q2 2024", 125.0),
    ]


@pytest.fixture
def sample_forecast_data():
    """Create sample forecast data."""
    return [
        ("Q3 2024", 130.0),
        ("Q4 2024", 135.0),
    ]


def test_chart_data_creation(engine, sample_historical_data):
    """Test creating chart data from historical values."""
    chart = engine.build_chart_data(
        ticker="APTX",
        metric_name="Revenue",
        historical_values=sample_historical_data,
    )

    assert chart is not None
    assert chart.ticker == "APTX"
    assert chart.metric_name == "Revenue"
    assert len(chart.data_points) == 6


def test_chart_bounds_calculation(engine, sample_historical_data):
    """Test min/max/mean calculation."""
    chart = engine.build_chart_data(
        ticker="APTX",
        metric_name="Revenue",
        historical_values=sample_historical_data,
    )

    assert chart.min_value == 100.0
    assert chart.max_value == 125.0
    assert chart.mean_value == 112.5


def test_trend_direction_uptrend(engine):
    """Test uptrend detection."""
    uptrend_data = [
        ("Q1", 100.0),
        ("Q2", 105.0),
        ("Q3", 110.0),
        ("Q4", 120.0),
    ]

    chart = engine.build_chart_data(
        ticker="APTX",
        metric_name="Revenue",
        historical_values=uptrend_data,
    )

    assert chart.trend_direction == TrendDirection.UPTREND


def test_trend_direction_downtrend(engine):
    """Test downtrend detection."""
    downtrend_data = [
        ("Q1", 150.0),
        ("Q2", 130.0),
        ("Q3", 110.0),
        ("Q4", 100.0),
    ]

    chart = engine.build_chart_data(
        ticker="APTX",
        metric_name="Revenue",
        historical_values=downtrend_data,
    )

    assert chart.trend_direction == TrendDirection.DOWNTREND


def test_trend_direction_stable(engine):
    """Test stable trend detection."""
    stable_data = [
        ("Q1", 100.0),
        ("Q2", 100.5),
        ("Q3", 100.2),
        ("Q4", 100.8),
    ]

    chart = engine.build_chart_data(
        ticker="APTX",
        metric_name="Revenue",
        historical_values=stable_data,
    )

    assert chart.trend_direction == TrendDirection.STABLE


def test_forecast_data_inclusion(engine, sample_historical_data, sample_forecast_data):
    """Test including forecast data in chart."""
    chart = engine.build_chart_data(
        ticker="APTX",
        metric_name="Revenue",
        historical_values=sample_historical_data,
        forecast_values=sample_forecast_data,
    )

    assert chart.has_forecast is True
    assert chart.forecast_confidence > 0
    assert len(chart.data_points) == 8  # 6 historical + 2 forecast


def test_chart_type_selection(engine, sample_historical_data):
    """Test different chart types."""
    for chart_type in [ChartType.LINE, ChartType.AREA, ChartType.BAR]:
        chart = engine.build_chart_data(
            ticker="APTX",
            metric_name="Revenue",
            historical_values=sample_historical_data,
            chart_type=chart_type,
        )

        assert chart.chart_type == chart_type


def test_chart_data_to_dict(engine, sample_historical_data):
    """Test chart data dictionary conversion."""
    chart = engine.build_chart_data(
        ticker="APTX",
        metric_name="Revenue",
        historical_values=sample_historical_data,
    )

    chart_dict = chart.to_dict()

    assert "ticker" in chart_dict
    assert "metric_name" in chart_dict
    assert "data_points" in chart_dict
    assert "bounds" in chart_dict
    assert "trend" in chart_dict
    assert chart_dict["bounds"]["min"] == 100.0
    assert chart_dict["bounds"]["max"] == 125.0


def test_trend_strength_calculation(engine):
    """Test trend strength calculation."""
    # High volatility = weak trend
    volatile_data = [
        ("Q1", 100.0),
        ("Q2", 150.0),
        ("Q3", 80.0),
        ("Q4", 140.0),
    ]

    chart = engine.build_chart_data(
        ticker="APTX",
        metric_name="Revenue",
        historical_values=volatile_data,
    )

    # Strong uptrend data
    strong_data = [
        ("Q1", 100.0),
        ("Q2", 110.0),
        ("Q3", 120.0),
        ("Q4", 130.0),
    ]

    strong_chart = engine.build_chart_data(
        ticker="APTX",
        metric_name="Revenue",
        historical_values=strong_data,
    )

    # Strong trend should have higher strength
    assert strong_chart.trend_strength > chart.trend_strength


def test_empty_historical_data(engine):
    """Test with empty historical data."""
    chart = engine.build_chart_data(
        ticker="APTX",
        metric_name="Revenue",
        historical_values=[],
    )

    assert chart is None


def test_none_values_handling(engine):
    """Test handling of None values in data."""
    data_with_nones = [
        ("Q1", 100.0),
        ("Q2", None),  # Missing value
        ("Q3", 110.0),
    ]

    chart = engine.build_chart_data(
        ticker="APTX",
        metric_name="Revenue",
        historical_values=data_with_nones,
    )

    assert chart is not None
    assert chart.min_value == 100.0
    assert chart.max_value == 110.0
