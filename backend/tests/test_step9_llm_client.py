"""Step 9: LLM Client tests.

Tests LLM client functionality:
- Analysis modes (quick, deep, forecast)
- Prompt construction
- Response parsing
- Token tracking
- Cost estimation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import date

from app.services.llm_client import LLMClient, LLMAnalysisResult
from app.services.evidence_pack_builder import EvidencePack


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


class TestLLMAnalysisResult:
    """Test LLMAnalysisResult dataclass."""

    def test_create_analysis_result(self):
        """Should create analysis result with all fields."""
        result = LLMAnalysisResult(
            ticker="FFC",
            overall_thesis="Bullish",
            confidence=75.0,
            bull_case="Strong revenue growth",
            bear_case="High debt levels",
            key_catalysts=["Earnings Q4", "Dividend announcement"],
            key_risks=["Market downturn", "Interest rate rise"],
            price_target_rationale="12-month historical average P/E of 8x on FY2025E earnings",
            investment_rating="Buy",
            time_horizon="6-12 months",
            tokens_used=2500,
            cache_creation_tokens=1500,
            cache_read_tokens=400,
        )

        assert result.ticker == "FFC"
        assert result.overall_thesis == "Bullish"
        assert result.confidence == 75.0
        assert result.tokens_used == 2500

    def test_analysis_result_to_dict(self):
        """Should convert result to dictionary."""
        result = LLMAnalysisResult(
            ticker="TEST",
            overall_thesis="Neutral",
            confidence=50.0,
            bull_case="Some growth",
            bear_case="Some risks",
            key_catalysts=[],
            key_risks=[],
            price_target_rationale="",
            investment_rating="Hold",
            time_horizon="3-6 months",
            tokens_used=1000,
            cache_creation_tokens=0,
            cache_read_tokens=0,
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert data["ticker"] == "TEST"
        assert data["overall_thesis"] == "Neutral"
        assert data["confidence"] == 50.0


class TestLLMClientInitialization:
    """Test LLMClient initialization."""

    def test_client_initialization_default(self):
        """Should initialize with default settings."""
        with patch("anthropic.Anthropic"):
            client = LLMClient(api_key="test-key")

            assert client.api_key == "test-key"
            assert client.model == "claude-opus-5"

    def test_client_initialization_custom_model(self):
        """Should initialize with custom model."""
        with patch("anthropic.Anthropic"):
            client = LLMClient(api_key="test-key", model="claude-sonnet-4")

            assert client.model == "claude-sonnet-4"

    def test_client_uses_env_api_key(self):
        """Should use ANTHROPIC_API_KEY from environment."""
        with patch("anthropic.Anthropic"), patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}):
            client = LLMClient()

            assert client.api_key == "env-key"


class TestPromptConstruction:
    """Test prompt building."""

    def test_build_system_prompt_quick(self):
        """Should build quick analysis system prompt."""
        prompt = LLMClient._build_system_prompt("quick")

        assert "expert investment analyst" in prompt
        assert "QUICK ANALYSIS" in prompt
        assert "3-5 key signals" in prompt.lower()

    def test_build_system_prompt_deep(self):
        """Should build deep analysis system prompt."""
        prompt = LLMClient._build_system_prompt("deep")

        assert "expert investment analyst" in prompt
        assert "DEEP ANALYSIS" in prompt
        assert "multiple angles" in prompt.lower()

    def test_build_system_prompt_forecast(self):
        """Should build forecast analysis system prompt."""
        prompt = LLMClient._build_system_prompt("forecast")

        assert "expert investment analyst" in prompt
        assert "FORECAST ANALYSIS" in prompt
        assert "price targets" in prompt.lower()

    def test_build_user_prompt_includes_narrative(self):
        """Should include evidence pack narrative in user prompt."""
        pack = create_test_pack(
            ticker="FFC",
            company_name="Fauji Fertilizer",
            sector="Chemicals",
            current_price=305.0,
        )

        prompt = LLMClient._build_user_prompt(pack, "quick")

        assert "FFC" in prompt
        assert "Fauji Fertilizer" in prompt
        assert "investment purposes" in prompt

    def test_build_user_prompt_with_context(self):
        """Should include additional context in user prompt."""
        pack = create_test_pack(
            ticker="TEST",
            company_name="Test Company",
            current_price=100.0,
        )

        prompt = LLMClient._build_user_prompt(pack, "forecast", context="12-month horizon")

        assert "12-month horizon" in prompt


class TestResponseParsing:
    """Test response parsing."""

    def test_parse_json_response(self):
        """Should parse JSON response."""
        response = """{
            "overall_thesis": "Bullish",
            "confidence": 75,
            "bull_case": "Strong growth",
            "bear_case": "High leverage",
            "key_catalysts": ["Earnings"],
            "key_risks": ["Market downturn"],
            "investment_rating": "Buy",
            "time_horizon": "6-12 months"
        }"""

        result = LLMClient._parse_analysis("FFC", response)

        assert result.ticker == "FFC"
        assert result.overall_thesis == "Bullish"
        assert result.confidence == 75
        assert result.investment_rating == "Buy"

    def test_parse_text_response(self):
        """Should parse text response with key-value pairs."""
        response = """Investment Analysis:
        Overall Thesis: Bearish
        Confidence: 45%
        Bull Case: Some upside potential
        """

        result = LLMClient._parse_analysis("TEST", response)

        assert result.ticker == "TEST"
        assert result.overall_thesis == "Bearish"
        assert result.confidence == 45.0

    def test_parse_malformed_response(self):
        """Should handle malformed response gracefully."""
        response = "This is not valid JSON or structured format xyz"

        result = LLMClient._parse_analysis("TEST", response)

        assert result.ticker == "TEST"
        assert result.overall_thesis == "Mixed"  # Default when parsing fails
        assert result.confidence >= 0

    def test_parse_response_sets_defaults(self):
        """Should set defaults for missing fields."""
        response = '{"overall_thesis": "Neutral"}'

        result = LLMClient._parse_analysis("TEST", response)

        assert result.overall_thesis == "Neutral"
        assert result.confidence >= 0
        assert result.investment_rating is not None
        assert isinstance(result.key_catalysts, list)
        assert isinstance(result.key_risks, list)


class TestAnalysisMethods:
    """Test analysis method calls."""

    def test_analyze_quick(self):
        """Should call analyze with quick mode."""
        pack = create_test_pack(
            ticker="FFC",
            company_name="Fauji Fertilizer",
            current_price=305.0,
        )

        with patch("anthropic.Anthropic"):
            client = LLMClient(api_key="test-key")

            with patch.object(client, "_analyze") as mock_analyze:
                mock_analyze.return_value = LLMAnalysisResult(
                    ticker="FFC",
                    overall_thesis="Bullish",
                    confidence=80.0,
                    bull_case="Growth",
                    bear_case="Risks",
                    key_catalysts=[],
                    key_risks=[],
                    price_target_rationale="",
                    investment_rating="Buy",
                    time_horizon="6-12 months",
                    tokens_used=0,
                    cache_creation_tokens=0,
                    cache_read_tokens=0,
                )

                result = client.analyze_quick(pack)

                mock_analyze.assert_called_once()
                assert result.overall_thesis == "Bullish"

    def test_analyze_deep(self):
        """Should call analyze with deep mode."""
        pack = create_test_pack(
            ticker="TEST",
            company_name="Test Company",
            current_price=100.0,
        )

        with patch("anthropic.Anthropic"):
            client = LLMClient(api_key="test-key")

            with patch.object(client, "_analyze") as mock_analyze:
                mock_analyze.return_value = LLMAnalysisResult(
                    ticker="TEST",
                    overall_thesis="Bearish",
                    confidence=70.0,
                    bull_case="",
                    bear_case="",
                    key_catalysts=[],
                    key_risks=[],
                    price_target_rationale="",
                    investment_rating="Sell",
                    time_horizon="3-6 months",
                    tokens_used=0,
                    cache_creation_tokens=0,
                    cache_read_tokens=0,
                )

                result = client.analyze_deep(pack)

                assert result.overall_thesis == "Bearish"

    def test_analyze_forecast(self):
        """Should call analyze with forecast mode."""
        pack = create_test_pack(
            ticker="TEST",
            company_name="Test Company",
            current_price=100.0,
        )

        with patch("anthropic.Anthropic"):
            client = LLMClient(api_key="test-key")

            with patch.object(client, "_analyze") as mock_analyze:
                mock_analyze.return_value = LLMAnalysisResult(
                    ticker="TEST",
                    overall_thesis="Mixed",
                    confidence=60.0,
                    bull_case="",
                    bear_case="",
                    key_catalysts=[],
                    key_risks=[],
                    price_target_rationale="Target: 120 PKR",
                    investment_rating="Hold",
                    time_horizon="12-month horizon",
                    tokens_used=0,
                    cache_creation_tokens=0,
                    cache_read_tokens=0,
                )

                result = client.analyze_forecast(pack, months=12)

                assert result.price_target_rationale == "Target: 120 PKR"


class TestCostEstimation:
    """Test cost estimation."""

    def test_estimate_cost_single_analysis(self):
        """Should estimate cost for single analysis."""
        with patch("anthropic.Anthropic"):
            client = LLMClient(api_key="test-key")

            cost = client.estimate_cost(evidence_pack_count=1)

            assert "first_analysis_cost" in cost
            assert "subsequent_analysis_cost" in cost
            assert "total_estimated_cost" in cost
            assert cost["analyses_counted"] == 1

    def test_estimate_cost_multiple_analyses(self):
        """Should estimate cost for multiple analyses."""
        with patch("anthropic.Anthropic"):
            client = LLMClient(api_key="test-key")

            cost = client.estimate_cost(evidence_pack_count=10)

            assert cost["analyses_counted"] == 10
            # Total cost should be first run + 9 subsequent
            expected_total = cost["first_analysis_cost"] + (9 * cost["subsequent_analysis_cost"])
            assert abs(cost["total_estimated_cost"] - expected_total) < 0.0001

    def test_estimate_cost_uses_caching(self):
        """Should show cost savings from caching."""
        with patch("anthropic.Anthropic"):
            client = LLMClient(api_key="test-key")

            cost = client.estimate_cost(evidence_pack_count=100)

            # Subsequent analyses should be cheaper due to cache hits
            assert cost["subsequent_analysis_cost"] < cost["first_analysis_cost"]

    def test_estimate_cost_returns_dict(self):
        """Should return dictionary with cost breakdown."""
        with patch("anthropic.Anthropic"):
            client = LLMClient(api_key="test-key")

            cost = client.estimate_cost(evidence_pack_count=5)

            assert isinstance(cost, dict)
            assert all(isinstance(v, (int, float)) for v in cost.values())


class TestIntegrationWithEvidencePack:
    """Test integration with evidence pack."""

    def test_analysis_accepts_evidence_pack(self):
        """Should accept complete evidence pack."""
        pack = create_test_pack(
            ticker="FFC",
            company_name="Fauji Fertilizer",
            sector="Chemicals",
            current_price=305.50,
            price_change_pct=2.5,
            daily_volume=1_200_000,
            trend="uptrend",
            trend_strength=65.0,
            revenue_growth_pct=20.0,
            earnings_growth_pct=25.0,
            sentiment="positive",
            confidence_score=85.0,
            key_strengths=["Strong revenue growth", "High ROE"],
        )

        with patch("anthropic.Anthropic"):
            client = LLMClient(api_key="test-key")

            # Should not raise error
            prompt = LLMClient._build_user_prompt(pack, "quick")
            assert "FFC" in prompt
            assert "Fauji Fertilizer" in prompt

    def test_analysis_handles_sparse_pack(self):
        """Should handle minimal evidence pack."""
        pack = create_test_pack(
            ticker="MIN",
            company_name="Minimal Corp",
            current_price=50.0,
        )

        with patch("anthropic.Anthropic"):
            client = LLMClient(api_key="test-key")

            prompt = LLMClient._build_user_prompt(pack, "deep")
            assert "MIN" in prompt
            assert "Minimal Corp" in prompt


class TestTokenTracking:
    """Test token usage tracking."""

    def test_track_token_usage(self):
        """Should track token usage from API response."""
        result = LLMAnalysisResult(
            ticker="FFC",
            overall_thesis="Bullish",
            confidence=75.0,
            bull_case="Growth",
            bear_case="Risks",
            key_catalysts=[],
            key_risks=[],
            price_target_rationale="",
            investment_rating="Buy",
            time_horizon="6-12 months",
            tokens_used=2500,
            cache_creation_tokens=1500,
            cache_read_tokens=400,
        )

        assert result.tokens_used == 2500
        assert result.cache_creation_tokens == 1500
        assert result.cache_read_tokens == 400

    def test_default_token_values(self):
        """Should default to zero for token values."""
        result = LLMAnalysisResult(
            ticker="TEST",
            overall_thesis="Neutral",
            confidence=50.0,
            bull_case="",
            bear_case="",
            key_catalysts=[],
            key_risks=[],
            price_target_rationale="",
            investment_rating="Hold",
            time_horizon="6-12 months",
            tokens_used=0,
            cache_creation_tokens=0,
            cache_read_tokens=0,
        )

        assert result.tokens_used == 0
        assert result.cache_creation_tokens == 0
        assert result.cache_read_tokens == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
