"""Tests for Steps 26-30: ML, Signals, Optimization, Monitoring."""

import pytest
from app.services.ml_screener import MLScreener
from app.services.signal_generator import SignalGenerator, SignalType
from app.services.portfolio_optimizer import PortfolioOptimizer
from app.services.enterprise_monitor import EnterpriseMonitor


@pytest.fixture
def ml_screener():
    return MLScreener()


@pytest.fixture
def signal_gen():
    return SignalGenerator()


@pytest.fixture
def optimizer():
    return PortfolioOptimizer()


@pytest.fixture
def monitor():
    return EnterpriseMonitor()


# ============== Step 26: ML Screener ==============

def test_ml_screener_basic(ml_screener):
    """Test basic ML scoring."""
    company = {
        "revenue_growth": 15.0,
        "profit_growth": 18.0,
        "roe": 22.0,
        "pe_multiple": 12.5,
        "net_margin": 8.5,
        "momentum": 65.0,
    }

    score = ml_screener.score_company("APTX", company)

    assert score is not None
    assert 0 <= score.ml_score <= 100
    assert score.recommendation in ["Strong Buy", "Buy", "Hold", "Sell"]


def test_ml_screener_high_score(ml_screener):
    """Test high ML score."""
    strong_company = {
        "revenue_growth": 40.0,  # High
        "profit_growth": 45.0,   # High
        "roe": 45.0,             # High
        "pe_multiple": 8.0,      # Low (good)
        "net_margin": 18.0,      # High
        "momentum": 95.0,        # High
        "debt_to_equity": 0.5,   # Low (good)
    }

    score = ml_screener.score_company("STRONG", strong_company)

    assert score.ml_score > 70
    assert score.recommendation in ["Strong Buy", "Buy"]


def test_ml_screener_to_dict(ml_screener):
    """Test ML score dictionary conversion."""
    company = {"revenue_growth": 15.0, "roe": 20.0}

    score = ml_screener.score_company("APTX", company)
    score_dict = score.to_dict()

    assert "ticker" in score_dict
    assert "ml_score" in score_dict
    assert "recommendation" in score_dict


# ============== Step 27: Signal Generator ==============

def test_signal_generation_entry(signal_gen):
    """Test entry signal generation."""
    signals = signal_gen.generate_signals(
        ticker="APTX",
        technical_score=75.0,
        fundamental_score=80.0,
        momentum_pct=8.0,
        current_price=100.0,
    )

    entry_signals = [s for s in signals if s.signal_type == SignalType.ENTRY]
    assert len(entry_signals) > 0
    assert entry_signals[0].strength > 0


def test_signal_generation_exit(signal_gen):
    """Test exit signal generation."""
    signals = signal_gen.generate_signals(
        ticker="APTX",
        technical_score=25.0,
        fundamental_score=30.0,
        momentum_pct=-5.0,
        current_price=100.0,
    )

    exit_signals = [s for s in signals if s.signal_type == SignalType.EXIT]
    assert len(exit_signals) > 0


def test_signal_stop_loss(signal_gen):
    """Test stop loss signal."""
    signals = signal_gen.generate_signals(
        ticker="APTX",
        technical_score=50.0,
        fundamental_score=50.0,
        momentum_pct=0.0,
        current_price=95.0,
        support_level=100.0,
    )

    stop_signals = [
        s for s in signals if s.signal_type == SignalType.STOP_LOSS
    ]
    assert len(stop_signals) > 0


# ============== Step 28: Portfolio Optimizer ==============

def test_portfolio_optimization(optimizer):
    """Test portfolio allocation."""
    candidates = [
        {
            "ticker": "APTX",
            "ml_score": 85,
            "risk_score": 30,
            "current_price": 100.0,
            "expected_return_pct": 15.0,
        },
        {
            "ticker": "CRWR",
            "ml_score": 70,
            "risk_score": 50,
            "current_price": 50.0,
            "expected_return_pct": 10.0,
        },
    ]

    allocation = optimizer.optimize_allocation(
        candidates=candidates,
        portfolio_value=100000.0,
        max_positions=2,
    )

    assert allocation is not None
    assert len(allocation.positions) > 0
    assert allocation.total_weight > 0


def test_allocation_to_dict(optimizer):
    """Test allocation dictionary conversion."""
    candidates = [
        {
            "ticker": "APTX",
            "ml_score": 85,
            "risk_score": 30,
            "current_price": 100.0,
        }
    ]

    allocation = optimizer.optimize_allocation(
        candidates=candidates,
        portfolio_value=50000.0,
    )

    alloc_dict = allocation.to_dict()

    assert "positions" in alloc_dict
    assert "cash_weight" in alloc_dict
    assert len(alloc_dict["positions"]) > 0


# ============== Steps 29-30: Enterprise Monitor ==============

def test_health_report_generation(monitor):
    """Test health report generation."""
    services = {
        "PSXClient": {"status": "Healthy", "uptime_pct": 99.5, "error_count": 2},
        "LLMClient": {"status": "Healthy", "uptime_pct": 98.0, "error_count": 5},
        "Database": {"status": "Healthy", "uptime_pct": 100.0, "error_count": 0},
    }

    api_metrics = {
        "calls_total": 1000,
        "errors": 10,
        "cache_hit_rate": 75.0,
    }

    report = monitor.generate_health_report(services, api_metrics)

    assert report is not None
    assert len(report.services) == 3
    assert report.overall_status == "Healthy"


def test_health_report_degraded(monitor):
    """Test degraded health status."""
    services = {
        "PSXClient": {"status": "Degraded", "uptime_pct": 90.0, "error_count": 50},
        "Database": {"status": "Healthy", "uptime_pct": 100.0, "error_count": 0},
    }

    api_metrics = {
        "calls_total": 1000,
        "errors": 100,
        "cache_hit_rate": 20.0,
    }

    report = monitor.generate_health_report(services, api_metrics)

    assert report.overall_status in ["Degraded", "Down"]
    assert len(report.alerts) > 0


def test_health_to_dict(monitor):
    """Test health report dictionary conversion."""
    services = {
        "PSXClient": {"status": "Healthy", "uptime_pct": 99.5, "error_count": 0}
    }

    api_metrics = {
        "calls_total": 100,
        "errors": 1,
        "cache_hit_rate": 80.0,
    }

    report = monitor.generate_health_report(services, api_metrics)
    report_dict = report.to_dict()

    assert "status" in report_dict
    assert "services" in report_dict
    assert "api_health" in report_dict
    assert "cache_hit_rate" in report_dict
