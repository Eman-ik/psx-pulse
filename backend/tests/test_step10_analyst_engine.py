"""Step 10: Analyst Engine tests.

Tests analyst engine functionality:
- Recommendation determination
- Entry/exit price calculation
- Position sizing
- Scenario analysis
- Risk management
- Monitoring triggers
- Investment decision generation
"""

import pytest
from datetime import datetime

from app.services.analyst_engine import (
    AnalystEngine,
    InvestmentDecision,
    RecommendationType,
    PositionSizeCategory,
    ScenarioProjection,
    RiskManagementRules,
)
from app.services.llm_client import LLMAnalysisResult
from app.services.evidence_pack_builder import EvidencePack


def create_test_llm_result(**kwargs):
    """Helper to create LLMAnalysisResult."""
    defaults = {
        "ticker": "TEST",
        "overall_thesis": "Neutral",
        "confidence": 50.0,
        "bull_case": "Some upside",
        "bear_case": "Some risks",
        "key_catalysts": [],
        "key_risks": [],
        "price_target_rationale": "",
        "investment_rating": "Hold",
        "time_horizon": "6-12 months",
        "tokens_used": 0,
        "cache_creation_tokens": 0,
        "cache_read_tokens": 0,
    }
    defaults.update(kwargs)
    return LLMAnalysisResult(**defaults)


def create_test_pack(**kwargs):
    """Helper to create EvidencePack with defaults."""
    defaults = {
        "ticker": "TEST",
        "company_name": "Test Company",
        "sector": "Technology",
        "market_cap_bracket": "mid",
        "current_price": 100.0,
        "price_change_pct": 0.0,
        "daily_volume": 1_000_000,
        "free_float_pct": 50.0,
        "trend": "neutral",
        "trend_strength": 50.0,
        "support_level": 80.0,
        "resistance_level": 120.0,
        "distance_to_support_pct": 20.0,
        "distance_to_resistance_pct": -20.0,
        "liquidity_avg_volume": 900_000,
        "revenue_growth_pct": None,
        "earnings_growth_pct": None,
        "net_margin_pct": None,
        "gross_margin_pct": None,
        "return_on_equity_pct": None,
        "return_on_assets_pct": None,
        "debt_to_equity_ratio": None,
        "current_ratio": None,
        "interest_coverage_ratio": None,
        "earnings_quality_ratio": None,
        "periods_analyzed": 0,
        "pe_ratio": None,
        "pb_ratio": None,
        "dividend_yield_pct": None,
        "kse_100_level": 78_000,
        "kse_100_change_pct": 0.0,
        "index_context": "KSE-100 stable",
        "recent_event_count": 0,
        "recent_positive_events": 0,
        "recent_negative_events": 0,
        "latest_event_date": None,
        "latest_event_type": None,
        "data_freshness_days": 0,
        "market_data_confidence": "high",
        "financial_data_confidence": "low",
        "missing_data_fields": [],
        "data_gaps_description": "None",
        "sentiment": "neutral",
        "confidence_score": 50.0,
        "key_strengths": [],
        "key_concerns": [],
    }
    defaults.update(kwargs)
    return EvidencePack(**defaults)


class TestAnalystEngineInitialization:
    """Test engine initialization."""

    def test_engine_instantiation(self):
        """Should create analyst engine."""
        engine = AnalystEngine()
        assert engine is not None
        assert engine.logger is not None


class TestRecommendationDetermination:
    """Test recommendation logic."""

    def test_strong_buy_high_confidence_bullish(self):
        """Should recommend strong buy for bullish high confidence."""
        rec, conviction = AnalystEngine._determine_recommendation(
            thesis="Bullish", confidence=85, catalyst_count=3, risk_count=1
        )

        assert rec == RecommendationType.STRONG_BUY
        assert conviction == "High"

    def test_buy_medium_confidence_bullish(self):
        """Should recommend buy for bullish medium confidence."""
        rec, conviction = AnalystEngine._determine_recommendation(
            thesis="Bullish", confidence=70, catalyst_count=2, risk_count=2
        )

        assert rec == RecommendationType.BUY
        assert conviction == "Medium"

    def test_strong_sell_high_confidence_bearish(self):
        """Should recommend strong sell for bearish high confidence."""
        rec, conviction = AnalystEngine._determine_recommendation(
            thesis="Bearish", confidence=85, catalyst_count=0, risk_count=4
        )

        assert rec == RecommendationType.STRONG_SELL
        assert conviction == "High"

    def test_sell_medium_confidence_bearish(self):
        """Should recommend sell for bearish medium confidence."""
        rec, conviction = AnalystEngine._determine_recommendation(
            thesis="Bearish", confidence=65, catalyst_count=1, risk_count=3
        )

        assert rec == RecommendationType.SELL
        assert conviction == "Medium"

    def test_hold_mixed_thesis(self):
        """Should recommend hold for mixed thesis."""
        rec, conviction = AnalystEngine._determine_recommendation(
            thesis="Mixed", confidence=50, catalyst_count=2, risk_count=2
        )

        assert rec == RecommendationType.HOLD
        assert conviction == "Medium"

    def test_hold_neutral_thesis(self):
        """Should recommend hold for neutral thesis."""
        rec, conviction = AnalystEngine._determine_recommendation(
            thesis="Neutral", confidence=40, catalyst_count=1, risk_count=1
        )

        assert rec == RecommendationType.HOLD
        assert conviction == "Low"


class TestPriceCalculations:
    """Test entry/exit price calculations."""

    def test_entry_price_bullish(self):
        """Should suggest entry above current for bullish thesis."""
        entry = AnalystEngine._calculate_entry_price(100.0, "Bullish")
        assert entry > 100.0
        assert entry == pytest.approx(102.0, rel=0.01)

    def test_entry_price_bearish(self):
        """Should suggest entry at current for bearish thesis."""
        entry = AnalystEngine._calculate_entry_price(100.0, "Bearish")
        assert entry == 100.0

    def test_entry_price_neutral(self):
        """Should suggest entry below current for neutral thesis."""
        entry = AnalystEngine._calculate_entry_price(100.0, "Neutral")
        assert entry < 100.0
        assert entry == pytest.approx(98.0, rel=0.01)

    def test_exit_price_bullish(self):
        """Should calculate 25% upside target for bullish."""
        entry = 100.0
        exit_price = AnalystEngine._calculate_exit_price(entry, "Bullish")
        upside = ((exit_price - entry) / entry) * 100
        assert upside == pytest.approx(25.0, rel=0.01)

    def test_exit_price_bearish(self):
        """Should calculate 20% downside target for bearish."""
        entry = 100.0
        exit_price = AnalystEngine._calculate_exit_price(entry, "Bearish")
        downside = ((entry - exit_price) / entry) * 100
        assert downside == pytest.approx(20.0, rel=0.01)

    def test_stop_loss_high_confidence(self):
        """Should place wider stop for high confidence."""
        entry = 100.0
        stop_high = AnalystEngine._calculate_stop_loss(entry, 85)
        stop_low = AnalystEngine._calculate_stop_loss(entry, 50)

        # Higher confidence = wider stop (willing to take more loss)
        # So stop price is LOWER for high confidence
        assert stop_high < stop_low
        assert stop_high < entry
        assert stop_low < entry

    def test_confidence_band_calculation(self):
        """Should calculate confidence band based on confidence."""
        band_high = AnalystEngine._calculate_confidence_band(100.0, 85)
        band_medium = AnalystEngine._calculate_confidence_band(100.0, 60)
        band_low = AnalystEngine._calculate_confidence_band(100.0, 30)

        assert band_high < band_medium < band_low


class TestPositionSizing:
    """Test position size calculations."""

    def test_full_position_high_conviction_high_confidence(self):
        """Should recommend full position for high conviction + confidence."""
        category, pct = AnalystEngine._calculate_position_size(85, "High")
        assert category == PositionSizeCategory.FULL
        assert pct >= 5

    def test_standard_position_high_conviction_medium_confidence(self):
        """Should recommend standard position for medium confidence."""
        category, pct = AnalystEngine._calculate_position_size(65, "High")
        assert category == PositionSizeCategory.STANDARD
        assert 2 <= pct <= 5

    def test_reduced_position_low_conviction(self):
        """Should recommend reduced position for low conviction."""
        category, pct = AnalystEngine._calculate_position_size(40, "Low")
        assert category == PositionSizeCategory.REDUCED
        assert pct <= 1

    def test_quantity_calculation(self):
        """Should calculate quantity from position size."""
        qty = AnalystEngine._calculate_quantity(
            position_pct=5.0, portfolio_size_thousands=100, entry_price=100.0
        )

        assert qty is not None
        assert qty > 0
        # 5% of 100k = 5k / 100 = 50 shares
        assert qty == 50

    def test_quantity_too_small_returns_none(self):
        """Should return None for very small position."""
        qty = AnalystEngine._calculate_quantity(
            position_pct=0.01, portfolio_size_thousands=100, entry_price=1000.0
        )

        assert qty is None or qty == 0


class TestScenarioAnalysis:
    """Test scenario projection."""

    def test_build_bull_scenario(self):
        """Should build bull case scenario."""
        bull = AnalystEngine._build_scenario(
            name="Bull", base_price=100.0, confidence=80, probability=40, multiplier=1.15
        )

        assert bull.name == "Bull"
        assert bull.target_price == pytest.approx(115.0, rel=0.01)
        assert bull.upside_pct == pytest.approx(15.0, rel=0.01)
        assert bull.probability_pct > 0

    def test_build_base_scenario(self):
        """Should build base case scenario."""
        base = AnalystEngine._build_scenario(
            name="Base", base_price=100.0, confidence=80, probability=35, multiplier=1.05
        )

        assert base.name == "Base"
        assert base.target_price == pytest.approx(105.0, rel=0.01)
        assert base.upside_pct == pytest.approx(5.0, rel=0.01)

    def test_build_bear_scenario(self):
        """Should build bear case scenario."""
        bear = AnalystEngine._build_scenario(
            name="Bear", base_price=100.0, confidence=80, probability=25, multiplier=0.85
        )

        assert bear.name == "Bear"
        assert bear.target_price == pytest.approx(85.0, rel=0.01)
        assert bear.upside_pct == pytest.approx(-15.0, rel=0.01)

    def test_scenario_probability_reduced_low_confidence(self):
        """Should reduce scenario probability for low confidence."""
        scenario_high = AnalystEngine._build_scenario(
            "Bull", 100.0, 85, 40, 1.15
        )
        scenario_low = AnalystEngine._build_scenario(
            "Bull", 100.0, 45, 40, 1.15
        )

        assert scenario_high.probability_pct > scenario_low.probability_pct


class TestRiskManagement:
    """Test risk management rules."""

    def test_stop_loss_percentage(self):
        """Should calculate stop loss percentage correctly."""
        entry = 100.0
        stop = 90.0
        stop_pct = AnalystEngine._calculate_stop_loss_pct(entry, stop)

        assert stop_pct == pytest.approx(10.0, rel=0.01)

    def test_take_profit_percentage(self):
        """Should calculate take profit percentage correctly."""
        entry = 100.0
        exit = 130.0
        tp_pct = AnalystEngine._calculate_take_profit_pct(exit, entry)

        assert tp_pct == pytest.approx(30.0, rel=0.01)


class TestMonitoringTriggers:
    """Test monitoring trigger generation."""

    def test_uptrend_triggers(self):
        """Should generate triggers for uptrend."""
        pack = create_test_pack(trend="uptrend", trend_strength=70)
        llm = create_test_llm_result(overall_thesis="Bullish")

        triggers = AnalystEngine._build_monitoring_triggers(pack, llm)

        assert len(triggers) > 0
        assert any("moving average" in t.lower() for t in triggers)

    def test_catalyst_triggers(self):
        """Should include catalyst-based triggers."""
        pack = create_test_pack()
        llm = create_test_llm_result(
            key_catalysts=["Q4 earnings", "Dividend announcement"]
        )

        triggers = AnalystEngine._build_monitoring_triggers(pack, llm)

        assert len(triggers) > 0


class TestInvalidationEvents:
    """Test invalidation event generation."""

    def test_regulatory_risk_invalidation(self):
        """Should identify regulatory risks as invalidation."""
        pack = create_test_pack(support_level=90)
        llm = create_test_llm_result(
            key_risks=["Regulatory investigation ongoing"]
        )

        invalidations = AnalystEngine._build_invalidation_events(llm, pack)

        assert len(invalidations) > 0
        assert any("regulatory" in i.lower() for i in invalidations)

    def test_support_level_invalidation(self):
        """Should identify support level break as invalidation."""
        pack = create_test_pack(support_level=80.0)
        llm = create_test_llm_result()

        invalidations = AnalystEngine._build_invalidation_events(llm, pack)

        assert len(invalidations) > 0
        assert any("support" in i.lower() for i in invalidations)


class TestInvestmentDecisionGeneration:
    """Test complete decision generation."""

    def test_decide_bullish_high_confidence(self):
        """Should generate strong buy decision for bullish high confidence."""
        llm = create_test_llm_result(
            ticker="FFC",
            overall_thesis="Bullish",
            confidence=85,
            key_catalysts=["Earnings Q4", "Dividend"],
            key_risks=["Market downturn"],
        )
        pack = create_test_pack(
            ticker="FFC",
            company_name="Fauji Fertilizer",
            current_price=305.0,
        )

        engine = AnalystEngine()
        decision = engine.decide(llm, pack, portfolio_size_thousands=100)

        assert decision is not None
        assert decision.ticker == "FFC"
        assert decision.recommendation == RecommendationType.STRONG_BUY
        assert decision.confidence_pct == 85
        assert decision.suggested_entry_price > 300

    def test_decide_bearish_medium_confidence(self):
        """Should generate sell decision for bearish medium confidence."""
        llm = create_test_llm_result(
            ticker="TEST",
            overall_thesis="Bearish",
            confidence=70,
            key_risks=["High leverage", "Earnings miss risk"],
        )
        pack = create_test_pack(ticker="TEST", current_price=100.0)

        engine = AnalystEngine()
        decision = engine.decide(llm, pack)

        assert decision is not None
        assert decision.recommendation == RecommendationType.SELL
        assert decision.conviction_level == "Medium"

    def test_decision_has_all_required_fields(self):
        """Should generate complete decision with all fields."""
        llm = create_test_llm_result(
            ticker="TEST",
            overall_thesis="Bullish",
            confidence=75,
            key_catalysts=["Event 1"],
            key_risks=["Risk 1"],
        )
        pack = create_test_pack()

        engine = AnalystEngine()
        decision = engine.decide(llm, pack)

        assert decision is not None
        assert decision.recommendation is not None
        assert decision.suggested_entry_price > 0
        assert decision.target_exit_price > 0
        assert decision.stop_loss_price > 0
        assert decision.bull_case_projection is not None
        assert decision.base_case_projection is not None
        assert decision.bear_case_projection is not None
        assert decision.expected_return_pct is not None
        assert decision.risk_management is not None

    def test_decision_to_dict(self):
        """Should serialize decision to dictionary."""
        llm = create_test_llm_result(
            ticker="TEST",
            overall_thesis="Neutral",
            confidence=50,
        )
        pack = create_test_pack()

        engine = AnalystEngine()
        decision = engine.decide(llm, pack)

        assert decision is not None
        data = decision.to_dict()

        assert isinstance(data, dict)
        assert data["ticker"] == "TEST"
        assert "recommendation" in data
        assert "confidence_pct" in data
        assert "bull_case" in data
        assert "base_case" in data
        assert "bear_case" in data


class TestIntegrationScenarios:
    """Test complete investment scenarios."""

    def test_high_conviction_buy_scenario(self):
        """Complete high conviction buy scenario."""
        llm = create_test_llm_result(
            ticker="FFC",
            overall_thesis="Bullish",
            confidence=82,
            investment_rating="Strong Buy",
            time_horizon="6-12 months",
            key_catalysts=["Q4 earnings", "Dividend increase"],
            key_risks=["Market correction"],
        )
        pack = create_test_pack(
            ticker="FFC",
            current_price=300.0,
            trend="uptrend",
            trend_strength=68,
            revenue_growth_pct=22,
            sentiment="positive",
        )

        engine = AnalystEngine()
        decision = engine.decide(llm, pack, portfolio_size_thousands=500)

        assert decision.recommendation == RecommendationType.STRONG_BUY
        assert decision.conviction_level == "High"
        assert decision.position_size_pct > 5
        assert decision.suggested_quantity is not None
        assert decision.suggested_quantity > 0

    def test_low_conviction_hold_scenario(self):
        """Complete low conviction hold scenario."""
        llm = create_test_llm_result(
            ticker="TEST",
            overall_thesis="Neutral",
            confidence=45,
        )
        pack = create_test_pack(
            ticker="TEST",
            current_price=100.0,
            sentiment="neutral",
        )

        engine = AnalystEngine()
        decision = engine.decide(llm, pack, portfolio_size_thousands=200)

        assert decision.recommendation == RecommendationType.HOLD
        assert decision.conviction_level == "Low"
        assert decision.position_size_pct <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
