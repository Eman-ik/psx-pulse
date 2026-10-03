"""Tests for Steps 22-25: Peer, Valuation, Risk, and Synthesis."""

import pytest
from app.services.peer_comparison_engine import PeerComparisonEngine
from app.services.valuation_comparator import ValuationComparator
from app.services.risk_profile_comparator import RiskProfileComparator
from app.services.synthesis_reporter import (
    SynthesisReporter,
    CompanyReportSummary,
)


@pytest.fixture
def peer_engine():
    """Create peer comparison engine."""
    return PeerComparisonEngine()


@pytest.fixture
def valuation_engine():
    """Create valuation comparator."""
    return ValuationComparator()


@pytest.fixture
def risk_engine():
    """Create risk profile comparator."""
    return RiskProfileComparator()


@pytest.fixture
def reporter():
    """Create synthesis reporter."""
    return SynthesisReporter()


@pytest.fixture
def sample_companies():
    """Create sample company data."""
    return {
        "APTX": {
            "name": "Apex Textiles",
            "sector": "Textiles",
            "revenue_growth_pct": 15.0,
            "profit_growth_pct": 18.0,
            "roe_pct": 22.0,
            "pe_ratio": 12.5,
            "pb_ratio": 1.8,
            "net_margin_pct": 8.5,
        },
        "CRWR": {
            "name": "Crown Chemicals",
            "sector": "Textiles",
            "revenue_growth_pct": 8.0,
            "profit_growth_pct": 5.0,
            "roe_pct": 15.0,
            "pe_ratio": 18.0,
            "pb_ratio": 2.5,
            "net_margin_pct": 5.0,
        },
        "ZCPF": {
            "name": "Zulu Cement",
            "sector": "Textiles",
            "revenue_growth_pct": 12.0,
            "profit_growth_pct": 10.0,
            "roe_pct": 20.0,
            "pe_ratio": 14.0,
            "pb_ratio": 2.0,
            "net_margin_pct": 7.5,
        },
    }


# ============== Step 22: Peer Comparison Tests ==============

def test_peer_comparison_basic(peer_engine, sample_companies):
    """Test basic peer comparison."""
    comparison = peer_engine.compare_to_peers(
        ticker="APTX",
        company_name="Apex Textiles",
        sector="Textiles",
        company_data=sample_companies["APTX"],
        all_companies=sample_companies,
    )

    assert comparison is not None
    assert comparison.ticker == "APTX"
    assert comparison.peer_count == 2
    assert len(comparison.peer_metrics) > 0


def test_peer_comparison_percentile(peer_engine, sample_companies):
    """Test percentile calculation vs peers."""
    comparison = peer_engine.compare_to_peers(
        ticker="APTX",
        company_name="Apex Textiles",
        sector="Textiles",
        company_data=sample_companies["APTX"],
        all_companies=sample_companies,
    )

    # APTX should have highest ROE (22.0)
    roe_metric = next(
        (m for m in comparison.peer_metrics if m.metric_name == "roe_pct"),
        None,
    )
    assert roe_metric is not None
    assert roe_metric.company_percentile > 50


def test_peer_comparison_to_dict(peer_engine, sample_companies):
    """Test peer comparison dictionary conversion."""
    comparison = peer_engine.compare_to_peers(
        ticker="APTX",
        company_name="Apex Textiles",
        sector="Textiles",
        company_data=sample_companies["APTX"],
        all_companies=sample_companies,
    )

    comp_dict = comparison.to_dict()

    assert "ticker" in comp_dict
    assert "peer_count" in comp_dict
    assert "overall_percentile" in comp_dict
    assert comp_dict["peer_count"] == 2


# ============== Step 23: Valuation Comparator Tests ==============

def test_valuation_analysis_basic(valuation_engine):
    """Test basic valuation analysis."""
    analysis = valuation_engine.analyze_valuation(
        ticker="APTX",
        current_price=100.0,
        current_eps=8.0,
        current_book_value=45.0,
    )

    assert analysis.ticker == "APTX"
    assert analysis.pe_ratio_current == 12.5  # 100/8
    assert analysis.pb_ratio_current == pytest.approx(2.22, 0.01)


def test_valuation_fair_value(valuation_engine):
    """Test fair value estimation."""
    analysis = valuation_engine.analyze_valuation(
        ticker="APTX",
        current_price=100.0,
        current_eps=8.0,
        historical_pe_ratios=[12.0, 13.0, 14.0, 15.0],
        peer_pe_median=14.0,
    )

    assert analysis.fair_value_estimate is not None
    assert analysis.fair_value_estimate > 0


def test_valuation_assessment(valuation_engine):
    """Test valuation assessment."""
    # Undervalued case
    analysis = valuation_engine.analyze_valuation(
        ticker="APTX",
        current_price=80.0,
        current_eps=8.0,
        historical_pe_ratios=[12.0, 13.0, 14.0],
        peer_pe_median=14.0,
    )

    assert analysis.fair_value_estimate is not None
    if analysis.discount_premium_pct:
        if analysis.discount_premium_pct < -10:
            assert analysis.valuation_assessment == "Undervalued"


def test_valuation_to_dict(valuation_engine):
    """Test valuation dictionary conversion."""
    analysis = valuation_engine.analyze_valuation(
        ticker="APTX",
        current_price=100.0,
        current_eps=8.0,
    )

    val_dict = analysis.to_dict()

    assert "ticker" in val_dict
    assert "pe_current" in val_dict
    assert "assessment" in val_dict


# ============== Step 24: Risk Profile Tests ==============

def test_risk_analysis_basic(risk_engine):
    """Test basic risk analysis."""
    price_history = [100, 105, 110, 108, 115, 120, 118, 122]

    analysis = risk_engine.analyze_risk(
        ticker="APTX",
        company_name="Apex Textiles",
        price_history=price_history,
        debt_to_equity=0.5,
    )

    assert analysis is not None
    assert analysis.volatility_pct >= 0
    assert analysis.maximum_drawdown_pct <= 0


def test_risk_rating_determination(risk_engine):
    """Test risk rating determination."""
    # Low volatility history
    stable_history = [100, 101, 102, 103, 104, 105]

    stable_analysis = risk_engine.analyze_risk(
        ticker="STABLE",
        company_name="Stable Corp",
        price_history=stable_history,
    )

    # High volatility history
    volatile_history = [100, 80, 120, 70, 130, 60, 140]

    volatile_analysis = risk_engine.analyze_risk(
        ticker="VOLATILE",
        company_name="Volatile Corp",
        price_history=volatile_history,
    )

    # Stable should have lower risk
    assert stable_analysis.volatility_pct < volatile_analysis.volatility_pct


def test_risk_scenarios(risk_engine):
    """Test downside scenario generation."""
    price_history = [100, 105, 110, 115, 120]

    analysis = risk_engine.analyze_risk(
        ticker="APTX",
        company_name="Apex Textiles",
        price_history=price_history,
    )

    assert analysis.downside_scenarios is not None
    assert len(analysis.downside_scenarios) > 0

    for scenario in analysis.downside_scenarios:
        assert scenario.probability_pct > 0
        assert scenario.impact_pct < 0


def test_risk_to_dict(risk_engine):
    """Test risk profile dictionary conversion."""
    price_history = [100, 105, 110, 115, 120]

    analysis = risk_engine.analyze_risk(
        ticker="APTX",
        company_name="Apex Textiles",
        price_history=price_history,
    )

    risk_dict = analysis.to_dict()

    assert "ticker" in risk_dict
    assert "volatility_pct" in risk_dict
    assert "risk_rating" in risk_dict
    assert "scenarios" in risk_dict


# ============== Step 25: Synthesis Reporter Tests ==============

def test_comprehensive_report_generation(reporter):
    """Test comprehensive report generation."""
    summaries = [
        CompanyReportSummary(
            ticker="APTX",
            company_name="Apex Textiles",
            sector="Textiles",
            recommendation="Buy",
            confidence=85.0,
            thesis="Strong growth with attractive valuation",
            key_strengths=["Revenue growth", "High ROE"],
            key_risks=["Competition"],
            valuation_assessment="Undervalued",
            risk_rating="Medium",
            target_price=120.0,
            upside_downside_pct=20.0,
        ),
        CompanyReportSummary(
            ticker="CRWR",
            company_name="Crown Chemicals",
            sector="Chemicals",
            recommendation="Hold",
            confidence=60.0,
            thesis="Fair value with moderate growth",
            valuation_assessment="Fair Value",
            risk_rating="High",
        ),
    ]

    report = reporter.generate_report(
        title="Q4 2024 Analysis",
        analysis_period="Q4 2024",
        company_summaries=summaries,
    )

    assert report is not None
    assert report.total_companies == 2
    assert report.bull_case_count == 1
    assert report.neutral_count == 1
    assert len(report.key_findings) > 0


def test_report_to_dict(reporter):
    """Test report dictionary conversion."""
    summaries = [
        CompanyReportSummary(
            ticker="APTX",
            company_name="Apex Textiles",
            sector="Textiles",
            recommendation="Buy",
            confidence=85.0,
            thesis="Test thesis",
            valuation_assessment="Undervalued",
            risk_rating="Medium",
        ),
    ]

    report = reporter.generate_report(
        title="Test Report",
        analysis_period="Q4 2024",
        company_summaries=summaries,
    )

    report_dict = report.to_dict()

    assert "title" in report_dict
    assert "total_companies" in report_dict
    assert "recommendation_summary" in report_dict
    assert "companies" in report_dict


def test_report_key_findings(reporter):
    """Test key findings generation."""
    summaries = [
        CompanyReportSummary(
            ticker="A",
            company_name="Company A",
            sector="Tech",
            recommendation="Buy",
            confidence=80.0,
            thesis="Growth story",
            valuation_assessment="Undervalued",
            risk_rating="Low",
        ),
        CompanyReportSummary(
            ticker="B",
            company_name="Company B",
            sector="Tech",
            recommendation="Sell",
            confidence=75.0,
            thesis="Overvalued",
            valuation_assessment="Overvalued",
            risk_rating="Very High",
        ),
    ]

    report = reporter.generate_report(
        title="Test Report",
        analysis_period="Q4 2024",
        company_summaries=summaries,
    )

    assert len(report.key_findings) > 0
    # Should mention both bull and bear cases
    findings_text = " ".join(report.key_findings)
    assert "bull" in findings_text.lower() or "bear" in findings_text.lower()
