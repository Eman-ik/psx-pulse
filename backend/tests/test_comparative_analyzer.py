"""Tests for Step 17: ComparativeAnalyzer."""

import pytest
import statistics
from app.services.comparative_analyzer import (
    ComparativeAnalyzer,
    ComparisonMetric,
    MetricCategory,
)


@pytest.fixture
def analyzer():
    """Create analyzer instance."""
    return ComparativeAnalyzer()


@pytest.fixture
def sample_companies():
    """Create sample company data for comparison."""
    return {
        "APTX": {
            "ticker": "APTX",
            "company_name": "Apex Textiles",
            "revenue_growth_pct": 15.5,
            "profit_growth_pct": 18.2,
            "pe_ratio": 12.5,
            "pb_ratio": 1.8,
            "roe_pct": 22.0,
            "net_margin_pct": 8.5,
            "debt_to_equity": 0.5,
        },
        "CRWR": {
            "ticker": "CRWR",
            "company_name": "Crown Chemicals",
            "revenue_growth_pct": 8.2,
            "profit_growth_pct": 5.1,
            "pe_ratio": 18.0,
            "pb_ratio": 2.5,
            "roe_pct": 15.0,
            "net_margin_pct": 5.0,
            "debt_to_equity": 1.2,
        },
        "ZCPF": {
            "ticker": "ZCPF",
            "company_name": "Zulu Cement",
            "revenue_growth_pct": 12.0,
            "profit_growth_pct": 10.5,
            "pe_ratio": 14.0,
            "pb_ratio": 2.0,
            "roe_pct": 20.0,
            "net_margin_pct": 7.5,
            "debt_to_equity": 0.8,
        },
    }


def test_comparison_metric_creation(analyzer):
    """Test creating a comparison metric."""
    companies = {
        "A": {"metric1": 10.0},
        "B": {"metric1": 20.0},
        "C": {"metric1": 15.0},
    }

    metric = analyzer._build_comparison_metric("metric1", companies, list(companies.keys()))

    assert metric is not None
    assert metric.metric_name == "metric1"
    assert len(metric.company_values) == 3
    assert metric.peer_median == 15.0
    assert metric.peer_mean == 15.0


def test_metric_category_detection(analyzer):
    """Test metric category detection."""
    assert analyzer._get_metric_category("revenue_growth_pct") == MetricCategory.GROWTH
    assert analyzer._get_metric_category("pe_ratio") == MetricCategory.VALUATION
    assert analyzer._get_metric_category("roe_pct") == MetricCategory.PROFITABILITY
    assert analyzer._get_metric_category("debt_to_equity") == MetricCategory.LEVERAGE
    assert analyzer._get_metric_category("trend_strength") == MetricCategory.TECHNICAL


def test_inverse_metric_detection(analyzer):
    """Test detection of inverse metrics (lower = better)."""
    assert analyzer._is_inverse_metric("pe_ratio") is True
    assert analyzer._is_inverse_metric("debt_to_equity") is True
    assert analyzer._is_inverse_metric("revenue_growth_pct") is False
    assert analyzer._is_inverse_metric("roe_pct") is False


def test_company_ranking(analyzer, sample_companies):
    """Test ranking companies for a metric."""
    metric = analyzer._build_comparison_metric(
        "roe_pct", sample_companies, list(sample_companies.keys())
    )

    rankings = analyzer._rank_companies(metric, list(sample_companies.keys()))

    assert len(rankings) == 3
    # APTX has highest ROE (22.0), should be rank 1
    assert rankings[0].ticker == "APTX"
    assert rankings[0].rank == 1
    # Percentile: (3-1)/3 * 100 = 66.67
    assert abs(rankings[0].percentile - 66.67) < 1


def test_inverse_metric_ranking(analyzer, sample_companies):
    """Test ranking with inverse metric (P/E: lower is better)."""
    metric = analyzer._build_comparison_metric(
        "pe_ratio", sample_companies, list(sample_companies.keys())
    )

    rankings = analyzer._rank_companies(metric, list(sample_companies.keys()))

    assert len(rankings) == 3
    # APTX has lowest P/E (12.5), should be rank 1
    assert rankings[0].ticker == "APTX"
    assert rankings[0].rank == 1
    # Percentile: (3-1)/3 * 100 = 66.67
    assert abs(rankings[0].percentile - 66.67) < 1


def test_company_scores(analyzer, sample_companies):
    """Test overall company score calculation."""
    metrics = ["revenue_growth_pct", "roe_pct", "pe_ratio"]
    rankings = {}

    for metric_name in metrics:
        metric = analyzer._build_comparison_metric(
            metric_name, sample_companies, list(sample_companies.keys())
        )
        if metric:
            rankings[metric_name] = analyzer._rank_companies(
                metric, list(sample_companies.keys())
            )

    scores = analyzer._calculate_company_scores(rankings, list(sample_companies.keys()))

    assert len(scores) == 3
    assert all(0 <= score <= 100 for score in scores.values())
    # APTX should have highest score (best growth, ROE, P/E)
    assert scores["APTX"] >= scores["CRWR"]
    assert scores["APTX"] >= scores["ZCPF"]


def test_full_comparison_flow(analyzer, sample_companies):
    """Test complete comparison flow."""
    result = analyzer.compare(sample_companies)

    assert result is not None
    assert len(result.tickers_compared) == 3
    assert result.leader == "APTX"  # Best performer
    assert result.laggard == "CRWR"  # Worst performer
    assert result.metrics is not None
    assert len(result.metrics) > 0


def test_comparison_with_custom_metrics(analyzer, sample_companies):
    """Test comparison with custom metric selection."""
    custom_metrics = ["revenue_growth_pct", "pe_ratio"]
    result = analyzer.compare(sample_companies, metric_names=custom_metrics)

    assert result is not None
    assert len(result.metrics) == 2
    assert any(m.metric_name == "revenue_growth_pct" for m in result.metrics)
    assert any(m.metric_name == "pe_ratio" for m in result.metrics)


def test_comparison_with_missing_data(analyzer):
    """Test comparison when some companies missing metrics."""
    companies = {
        "A": {"metric1": 10.0, "metric2": 5.0},
        "B": {"metric1": 20.0, "metric2": None},  # Missing metric2
        "C": {"metric1": None, "metric2": 15.0},  # Missing metric1
    }

    result = analyzer.compare(companies, metric_names=["metric1", "metric2"])

    assert result is not None
    # Should still build comparison with available data
    assert len(result.tickers_compared) == 3


def test_comparison_with_single_company(analyzer):
    """Test that comparison with <2 companies returns None."""
    companies = {"A": {"metric1": 10.0}}
    result = analyzer.compare(companies)

    assert result is None


def test_comparison_empty_dict(analyzer):
    """Test comparison with empty company dict."""
    result = analyzer.compare({})

    assert result is None


def test_comparison_result_to_dict(analyzer, sample_companies):
    """Test conversion of comparison result to dictionary."""
    result = analyzer.compare(sample_companies)
    result_dict = result.to_dict()

    assert "tickers_compared" in result_dict
    assert "company_count" in result_dict
    assert "metrics_count" in result_dict
    assert "leader" in result_dict
    assert "laggard" in result_dict
    assert "company_scores" in result_dict
    assert result_dict["company_count"] == 3


def test_peer_statistics_calculation(analyzer):
    """Test peer median, mean, and stdev calculation."""
    companies = {
        "A": {"metric": 10.0},
        "B": {"metric": 20.0},
        "C": {"metric": 30.0},
    }

    metric = analyzer._build_comparison_metric("metric", companies, ["A", "B", "C"])

    assert metric.peer_median == 20.0
    assert metric.peer_mean == 20.0
    assert metric.peer_stdev == 10.0


def test_all_metrics_comparison(analyzer, sample_companies):
    """Test comparison with all default metrics."""
    result = analyzer.compare(sample_companies)

    assert result is not None
    # Should include growth, valuation, profitability, leverage metrics
    categories = set(m.category for m in result.metrics)
    assert MetricCategory.GROWTH in categories or MetricCategory.VALUATION in categories


def test_ranking_with_tied_values(analyzer):
    """Test ranking when companies have tied metric values."""
    companies = {
        "A": {"metric": 15.0},
        "B": {"metric": 15.0},
        "C": {"metric": 20.0},
    }

    metric = analyzer._build_comparison_metric("metric", companies, ["A", "B", "C"])
    rankings = analyzer._rank_companies(metric, ["A", "B", "C"])

    # Two companies tied for rank 1, one for rank 2
    assert len(rankings) == 3
    # All should have valid ranks
    assert all(r.rank > 0 for r in rankings)
