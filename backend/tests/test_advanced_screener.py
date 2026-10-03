"""Tests for Step 16: AdvancedScreener."""

import pytest
from app.services.advanced_screener import (
    AdvancedScreener,
    ScreeningCriteria,
    ScreeningStage,
    FilterResult,
)


@pytest.fixture
def screener():
    """Create screener instance."""
    return AdvancedScreener()


@pytest.fixture
def sample_companies():
    """Create sample company data."""
    return [
        {
            "ticker": "APTX",
            "company_name": "Apex Textiles",
            "market_cap_millions": 2500,
            "revenue_growth_pct": 15.5,
            "profit_growth_pct": 18.2,
            "pe_ratio": 12.5,
            "pb_ratio": 1.8,
            "roe_pct": 22.0,
            "net_margin_pct": 8.5,
            "debt_to_equity": 0.5,
            "trend": "uptrend",
            "trend_strength_pct": 65.0,
        },
        {
            "ticker": "CRWR",
            "company_name": "Crown Chemicals",
            "market_cap_millions": 450,  # Below 500M
            "revenue_growth_pct": 8.2,
            "profit_growth_pct": 5.1,
            "pe_ratio": 18.0,
            "pb_ratio": 2.5,
            "roe_pct": 15.0,
            "net_margin_pct": 5.0,
            "debt_to_equity": 1.2,
            "trend": "downtrend",
            "trend_strength_pct": 35.0,
        },
        {
            "ticker": "ZCPF",
            "company_name": "Zulu Cement",
            "market_cap_millions": 7500,
            "revenue_growth_pct": 12.0,
            "profit_growth_pct": 10.5,
            "pe_ratio": 14.0,
            "pb_ratio": 2.0,
            "roe_pct": 20.0,
            "net_margin_pct": 7.5,
            "debt_to_equity": 0.8,
            "trend": "uptrend",
            "trend_strength_pct": 58.0,
        },
    ]


def test_market_cap_filter_pass(screener):
    """Test market cap filter passes when in range."""
    company = {"market_cap_millions": 5000}
    criteria = ScreeningCriteria(min_market_cap_millions=1000, max_market_cap_millions=10000)
    result = screener._filter_market_cap(company, criteria)
    assert result == FilterResult.PASS


def test_market_cap_filter_fail_below_min(screener):
    """Test market cap filter fails when below minimum."""
    company = {"market_cap_millions": 500}
    criteria = ScreeningCriteria(min_market_cap_millions=1000)
    result = screener._filter_market_cap(company, criteria)
    assert result == FilterResult.FAIL


def test_market_cap_filter_fail_above_max(screener):
    """Test market cap filter fails when above maximum."""
    company = {"market_cap_millions": 100000}
    criteria = ScreeningCriteria(max_market_cap_millions=50000)
    result = screener._filter_market_cap(company, criteria)
    assert result == FilterResult.FAIL


def test_market_cap_filter_insufficient_data(screener):
    """Test market cap filter returns insufficient data when missing."""
    company = {"market_cap_millions": None}
    criteria = ScreeningCriteria(min_market_cap_millions=1000)
    result = screener._filter_market_cap(company, criteria)
    assert result == FilterResult.INSUFFICIENT_DATA


def test_growth_filter_pass(screener):
    """Test growth filter passes when meets criteria."""
    company = {"revenue_growth_pct": 15.0, "profit_growth_pct": 12.0}
    criteria = ScreeningCriteria(min_revenue_growth_pct=10.0, min_profit_growth_pct=10.0)
    result = screener._filter_growth(company, criteria)
    assert result == FilterResult.PASS


def test_growth_filter_fail_revenue(screener):
    """Test growth filter fails when revenue below threshold."""
    company = {"revenue_growth_pct": 8.0, "profit_growth_pct": 12.0}
    criteria = ScreeningCriteria(min_revenue_growth_pct=10.0)
    result = screener._filter_growth(company, criteria)
    assert result == FilterResult.FAIL


def test_valuation_filter_pass(screener):
    """Test valuation filter passes when meets criteria."""
    company = {"pe_ratio": 14.0, "pb_ratio": 2.0}
    criteria = ScreeningCriteria(max_pe_ratio=15.0, max_pb_ratio=2.5)
    result = screener._filter_valuation(company, criteria)
    assert result == FilterResult.PASS


def test_valuation_filter_fail_pe(screener):
    """Test valuation filter fails when P/E too high."""
    company = {"pe_ratio": 20.0, "pb_ratio": 2.0}
    criteria = ScreeningCriteria(max_pe_ratio=15.0)
    result = screener._filter_valuation(company, criteria)
    assert result == FilterResult.FAIL


def test_quality_filter_pass(screener):
    """Test quality filter passes when meets criteria."""
    company = {"roe_pct": 22.0, "net_margin_pct": 8.5, "debt_to_equity": 0.5}
    criteria = ScreeningCriteria(min_roe_pct=20.0, min_net_margin_pct=7.0, max_debt_to_equity=1.0)
    result = screener._filter_quality(company, criteria)
    assert result == FilterResult.PASS


def test_quality_filter_fail_debt(screener):
    """Test quality filter fails when debt too high."""
    company = {"roe_pct": 22.0, "net_margin_pct": 8.5, "debt_to_equity": 2.0}
    criteria = ScreeningCriteria(max_debt_to_equity=1.0)
    result = screener._filter_quality(company, criteria)
    assert result == FilterResult.FAIL


def test_technical_filter_pass(screener):
    """Test technical filter passes when meets criteria."""
    company = {"trend": "uptrend", "trend_strength_pct": 65.0}
    criteria = ScreeningCriteria(required_trend="uptrend", min_trend_strength_pct=60.0)
    result = screener._filter_technical(company, criteria)
    assert result == FilterResult.PASS


def test_technical_filter_fail_trend(screener):
    """Test technical filter fails when trend doesn't match."""
    company = {"trend": "downtrend", "trend_strength_pct": 65.0}
    criteria = ScreeningCriteria(required_trend="uptrend")
    result = screener._filter_technical(company, criteria)
    assert result == FilterResult.FAIL


def test_screening_score_calculation(screener):
    """Test screening score calculation."""
    company = {"revenue_growth_pct": 15.0, "roe_pct": 22.0, "pe_ratio": 14.0}
    criteria = ScreeningCriteria(
        min_revenue_growth_pct=10.0,
        min_roe_pct=20.0,
        max_pe_ratio=15.0,
    )
    score = screener._calculate_screening_score(company, criteria)
    # Base 50 + 10 (growth) + 10 (roe) + 10 (pe) = 80
    assert score == 80.0


def test_full_screening_flow(screener, sample_companies):
    """Test complete screening flow with multiple companies."""
    criteria = ScreeningCriteria(
        min_market_cap_millions=1000,  # Filters out CRWR
        min_revenue_growth_pct=12.0,  # Filters out CRWR
        max_pe_ratio=15.0,  # Filters out CRWR
        min_roe_pct=20.0,  # Filters out CRWR
        required_trend="uptrend",  # Filters out CRWR (downtrend)
    )

    result = screener.screen(sample_companies, criteria)

    assert result is not None
    assert result.total_companies == 3
    assert result.passed_companies >= 1  # APTX and ZCPF should pass
    assert result.failed_companies > 0  # CRWR should fail
    assert len(result.company_results) == 3
    assert len(result.top_scorers) <= 10


def test_screening_result_to_dict(screener, sample_companies):
    """Test screening result dictionary conversion."""
    criteria = ScreeningCriteria(
        min_market_cap_millions=500,
        min_revenue_growth_pct=5.0,
    )

    result = screener.screen(sample_companies, criteria)
    result_dict = result.to_dict()

    assert "total_companies" in result_dict
    assert "passed_companies" in result_dict
    assert "failed_companies" in result_dict
    assert "pass_rate_pct" in result_dict
    assert "stage_results" in result_dict
    assert result_dict["total_companies"] == 3


def test_empty_company_list(screener):
    """Test screening with empty company list."""
    criteria = ScreeningCriteria(min_market_cap_millions=1000)
    result = screener.screen([], criteria)
    assert result is None


def test_all_companies_pass(screener):
    """Test when all companies pass screening."""
    companies = [
        {
            "ticker": "APTX",
            "company_name": "Apex",
            "market_cap_millions": 5000,
            "revenue_growth_pct": 15.0,
            "profit_growth_pct": 12.0,
            "pe_ratio": 12.0,
            "pb_ratio": 1.5,
            "roe_pct": 25.0,
            "net_margin_pct": 10.0,
            "debt_to_equity": 0.3,
            "trend": "uptrend",
            "trend_strength_pct": 75.0,
        },
    ]
    criteria = ScreeningCriteria(
        min_market_cap_millions=1000,
        min_revenue_growth_pct=10.0,
    )
    result = screener.screen(companies, criteria)
    assert result.passed_companies == 1
    assert result.failed_companies == 0


def test_all_companies_fail(screener):
    """Test when all companies fail screening."""
    companies = [
        {
            "ticker": "POOR",
            "company_name": "Poor Company",
            "market_cap_millions": 100,  # Below minimum
            "revenue_growth_pct": 2.0,  # Below minimum
            "profit_growth_pct": 1.0,
            "pe_ratio": 50.0,  # Above maximum
            "pb_ratio": 5.0,
            "roe_pct": 5.0,  # Below minimum
            "net_margin_pct": 1.0,
            "debt_to_equity": 5.0,  # Above maximum
            "trend": "downtrend",
            "trend_strength_pct": 20.0,
        },
    ]
    criteria = ScreeningCriteria(
        min_market_cap_millions=1000,
        min_revenue_growth_pct=10.0,
        max_pe_ratio=20.0,
        min_roe_pct=15.0,
        max_debt_to_equity=1.0,
    )
    result = screener.screen(companies, criteria)
    assert result.passed_companies == 0
    assert result.failed_companies == 1
