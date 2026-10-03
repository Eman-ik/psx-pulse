"""Step 11: API Integration tests.

Tests research API routes:
- GET /api/research/{ticker}/snapshot
- POST /api/research/{ticker}/analyze
- POST /api/research/{ticker}/decide
- POST /api/research/{ticker}/unified-flow
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Should return healthy status."""
        response = client.get("/api/research/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestSnapshotEndpoint:
    """Test snapshot endpoint."""

    def test_snapshot_success(self, client):
        """Should return snapshot for valid ticker."""
        with patch("app.services.snapshot_builder.SnapshotBuilder.build") as mock_build:
            with patch("app.services.evidence_pack_builder.EvidencePackBuilder.build") as mock_pack:
                # Mock snapshot
                mock_snapshot = Mock()
                mock_snapshot.market = Mock(ticker="TEST", price=100.0)
                mock_build.return_value = mock_snapshot

                # Mock evidence pack
                from app.services.evidence_pack_builder import EvidencePack
                mock_evidence = Mock(spec=EvidencePack)
                mock_evidence.ticker = "TEST"
                mock_evidence.company_name = "Test Company"
                mock_evidence.current_price = 100.0
                mock_evidence.market_cap_bracket = "mid"
                mock_evidence.sentiment = "neutral"
                mock_evidence.confidence_score = 50.0
                mock_evidence.data_freshness_days = 0
                mock_evidence.to_dict.return_value = {"ticker": "TEST"}
                mock_pack.return_value = mock_evidence

                response = client.get("/api/research/TEST/snapshot")

                assert response.status_code == 200
                data = response.json()
                assert data["ticker"] == "TEST"
                assert "data" in data

    def test_snapshot_not_found(self, client):
        """Should return 404 for missing ticker."""
        with patch("app.services.snapshot_builder.SnapshotBuilder.build") as mock_build:
            mock_build.return_value = None

            response = client.get("/api/research/INVALID/snapshot")

            assert response.status_code == 404


class TestAnalyzeEndpoint:
    """Test analyze endpoint."""

    def test_analyze_quick_mode(self, client):
        """Should run quick analysis."""
        with patch("app.services.snapshot_builder.SnapshotBuilder.build") as mock_build:
            with patch("app.services.evidence_pack_builder.EvidencePackBuilder.build") as mock_pack:
                with patch("app.services.llm_client.LLMClient.analyze_quick") as mock_analyze:
                    # Mock snapshot and pack
                    mock_snapshot = Mock()
                    mock_build.return_value = mock_snapshot

                    mock_evidence = Mock()
                    mock_pack.return_value = mock_evidence

                    # Mock LLM result
                    from app.services.llm_client import LLMAnalysisResult
                    mock_result = LLMAnalysisResult(
                        ticker="TEST",
                        overall_thesis="Bullish",
                        confidence=75.0,
                        bull_case="Growth",
                        bear_case="Risks",
                        key_catalysts=["Event"],
                        key_risks=["Risk"],
                        price_target_rationale="",
                        investment_rating="Buy",
                        time_horizon="6-12 months",
                        tokens_used=1000,
                        cache_creation_tokens=0,
                        cache_read_tokens=0,
                    )
                    mock_analyze.return_value = mock_result

                    response = client.post(
                        "/api/research/TEST/analyze?mode=quick"
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["ticker"] == "TEST"
                    assert data["overall_thesis"] == "Bullish"

    def test_analyze_deep_mode(self, client):
        """Should run deep analysis."""
        with patch("app.services.snapshot_builder.SnapshotBuilder.build") as mock_build:
            with patch("app.services.evidence_pack_builder.EvidencePackBuilder.build") as mock_pack:
                with patch("app.services.llm_client.LLMClient.analyze_deep") as mock_analyze:
                    mock_snapshot = Mock()
                    mock_build.return_value = mock_snapshot

                    mock_evidence = Mock()
                    mock_pack.return_value = mock_evidence

                    from app.services.llm_client import LLMAnalysisResult
                    mock_result = LLMAnalysisResult(
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
                        tokens_used=2000,
                        cache_creation_tokens=1500,
                        cache_read_tokens=0,
                    )
                    mock_analyze.return_value = mock_result

                    response = client.post(
                        "/api/research/TEST/analyze?mode=deep"
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["tokens_used"] == 2000

    def test_analyze_invalid_mode(self, client):
        """Should reject invalid analysis mode."""
        with patch("app.services.snapshot_builder.SnapshotBuilder.build") as mock_build:
            with patch("app.services.evidence_pack_builder.EvidencePackBuilder.build") as mock_pack:
                mock_snapshot = Mock()
                mock_build.return_value = mock_snapshot
                mock_evidence = Mock()
                mock_pack.return_value = mock_evidence

                response = client.post(
                    "/api/research/TEST/analyze?mode=invalid"
                )

                assert response.status_code == 400


class TestDecideEndpoint:
    """Test decision endpoint."""

    def test_decide_generates_decision(self, client):
        """Should generate investment decision."""
        with patch("app.services.snapshot_builder.SnapshotBuilder.build") as mock_build:
            with patch("app.services.evidence_pack_builder.EvidencePackBuilder.build") as mock_pack:
                with patch("app.services.llm_client.LLMClient.analyze_quick") as mock_analyze:
                    with patch("app.services.analyst_engine.AnalystEngine.decide") as mock_decide:
                        # Mock snapshot and pack
                        mock_snapshot = Mock()
                        mock_build.return_value = mock_snapshot
                        mock_evidence = Mock()
                        mock_pack.return_value = mock_evidence

                        # Mock LLM result
                        from app.services.llm_client import LLMAnalysisResult
                        mock_result = LLMAnalysisResult(
                            ticker="TEST",
                            overall_thesis="Bullish",
                            confidence=80.0,
                            bull_case="Growth",
                            bear_case="",
                            key_catalysts=["Earnings"],
                            key_risks=[],
                            price_target_rationale="",
                            investment_rating="Buy",
                            time_horizon="6-12 months",
                            tokens_used=0,
                            cache_creation_tokens=0,
                            cache_read_tokens=0,
                        )
                        mock_analyze.return_value = mock_result

                        # Mock decision
                        from app.services.analyst_engine import (
                            InvestmentDecision,
                            RecommendationType,
                            PositionSizeCategory,
                            ScenarioProjection,
                            RiskManagementRules,
                        )
                        mock_decision = InvestmentDecision(
                            ticker="TEST",
                            recommendation=RecommendationType.STRONG_BUY,
                            confidence_pct=80.0,
                            conviction_level="High",
                            suggested_entry_price=102.0,
                            entry_confidence_band_pct=2.0,
                            target_exit_price=127.5,
                            stop_loss_price=91.8,
                            position_size_category=PositionSizeCategory.FULL,
                            position_size_pct=7.5,
                            suggested_quantity=750,
                            bull_case_projection=ScenarioProjection(
                                name="Bull",
                                target_price=127.5,
                                probability_pct=40,
                                upside_pct=25.0,
                                reasoning="Growth",
                            ),
                            base_case_projection=ScenarioProjection(
                                name="Base",
                                target_price=107.1,
                                probability_pct=35,
                                upside_pct=5.0,
                                reasoning="Stable",
                            ),
                            bear_case_projection=ScenarioProjection(
                                name="Bear",
                                target_price=86.7,
                                probability_pct=25,
                                upside_pct=-15.0,
                                reasoning="Downturn",
                            ),
                            expected_return_pct=8.5,
                            risk_management=RiskManagementRules(
                                stop_loss_pct=10.0,
                                take_profit_pct=25.0,
                                position_size_pct=7.5,
                                max_drawdown_pct=20.0,
                                monitoring_interval_days=7,
                            ),
                            key_upside_catalysts=["Earnings"],
                            key_downside_risks=[],
                            monitoring_triggers=[],
                            analysis_timestamp="2026-10-03T00:00:00",
                            time_horizon="6-12 months",
                            invalidation_events=[],
                        )
                        mock_decide.return_value = mock_decision

                        response = client.post(
                            "/api/research/TEST/decide?portfolio_size_thousands=100"
                        )

                        assert response.status_code == 200
                        data = response.json()
                        assert data["ticker"] == "TEST"
                        assert data["recommendation"] == "Strong Buy"
                        assert data["position_size_pct"] == 7.5


class TestUnifiedFlowEndpoint:
    """Test unified flow endpoint."""

    def test_unified_flow_complete(self, client):
        """Should complete full research flow."""
        with patch("app.services.snapshot_builder.SnapshotBuilder.build") as mock_build:
            with patch("app.services.evidence_pack_builder.EvidencePackBuilder.build") as mock_pack:
                with patch("app.services.llm_client.LLMClient.analyze_quick") as mock_analyze:
                    with patch("app.services.analyst_engine.AnalystEngine.decide") as mock_decide:
                        # Mock snapshot
                        mock_snapshot = Mock()
                        mock_build.return_value = mock_snapshot

                        # Mock evidence pack
                        mock_evidence = Mock()
                        mock_evidence.to_dict.return_value = {"ticker": "TEST", "price": 100}
                        mock_pack.return_value = mock_evidence

                        # Mock LLM result
                        from app.services.llm_client import LLMAnalysisResult
                        mock_result = LLMAnalysisResult(
                            ticker="TEST",
                            overall_thesis="Bullish",
                            confidence=75.0,
                            bull_case="Growth",
                            bear_case="Risks",
                            key_catalysts=["Event"],
                            key_risks=["Risk"],
                            price_target_rationale="",
                            investment_rating="Buy",
                            time_horizon="6-12 months",
                            tokens_used=1000,
                            cache_creation_tokens=0,
                            cache_read_tokens=0,
                        )
                        mock_result_dict = {
                            "ticker": "TEST",
                            "overall_thesis": "Bullish",
                            "confidence": 75.0,
                        }
                        mock_result.to_dict = Mock(return_value=mock_result_dict)
                        mock_analyze.return_value = mock_result

                        # Mock decision
                        from app.services.analyst_engine import (
                            InvestmentDecision,
                            RecommendationType,
                            PositionSizeCategory,
                            ScenarioProjection,
                            RiskManagementRules,
                        )
                        mock_decision = InvestmentDecision(
                            ticker="TEST",
                            recommendation=RecommendationType.BUY,
                            confidence_pct=75.0,
                            conviction_level="Medium",
                            suggested_entry_price=102.0,
                            entry_confidence_band_pct=3.5,
                            target_exit_price=127.5,
                            stop_loss_price=93.8,
                            position_size_category=PositionSizeCategory.STANDARD,
                            position_size_pct=4.0,
                            suggested_quantity=400,
                            bull_case_projection=ScenarioProjection(
                                "Bull", 127.5, 40, 25.0, "Growth"
                            ),
                            base_case_projection=ScenarioProjection(
                                "Base", 107.1, 35, 5.0, "Stable"
                            ),
                            bear_case_projection=ScenarioProjection(
                                "Bear", 86.7, 25, -15.0, "Downturn"
                            ),
                            expected_return_pct=8.5,
                            risk_management=RiskManagementRules(
                                stop_loss_pct=8.0,
                                take_profit_pct=25.0,
                                position_size_pct=4.0,
                                max_drawdown_pct=20.0,
                                monitoring_interval_days=7,
                            ),
                            key_upside_catalysts=["Event"],
                            key_downside_risks=["Risk"],
                            monitoring_triggers=[],
                            analysis_timestamp="2026-10-03T00:00:00",
                            time_horizon="6-12 months",
                            invalidation_events=[],
                        )
                        mock_decision.to_dict = Mock(
                            return_value={"recommendation": "Buy", "ticker": "TEST"}
                        )
                        mock_decide.return_value = mock_decision

                        response = client.post(
                            "/api/research/TEST/unified-flow?analysis_mode=quick&portfolio_size_thousands=100"
                        )

                        assert response.status_code == 200
                        data = response.json()
                        assert data["ticker"] == "TEST"
                        assert data["flow_status"] in ["complete", "partial"]
                        assert "snapshot" in data
                        assert "analysis" in data
                        assert "decision" in data

    def test_unified_flow_partial_failure(self, client):
        """Should handle partial failure gracefully."""
        with patch("app.services.snapshot_builder.SnapshotBuilder.build") as mock_build:
            with patch("app.services.evidence_pack_builder.EvidencePackBuilder.build") as mock_pack:
                # Snapshot succeeds
                mock_snapshot = Mock()
                mock_build.return_value = mock_snapshot

                # Pack fails
                mock_pack.return_value = None

                response = client.post(
                    "/api/research/TEST/unified-flow?analysis_mode=quick"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["flow_status"] == "partial"
                assert "error" in data["snapshot"] or "error" in data["analysis"]


class TestAPIDataStructures:
    """Test API response structures."""

    def test_snapshot_response_structure(self):
        """Snapshot response should have correct structure."""
        from app.api.research_routes import SnapshotResponse

        response = SnapshotResponse(
            ticker="TEST",
            company_name="Test Company",
            current_price=100.0,
            market_cap_bracket="mid",
            sentiment="positive",
            confidence_score=85.0,
            data_freshness_days=0,
            data={"test": "data"},
        )

        assert response.ticker == "TEST"
        assert response.current_price == 100.0

    def test_analysis_response_structure(self):
        """Analysis response should have correct structure."""
        from app.api.research_routes import AnalysisResponse

        response = AnalysisResponse(
            ticker="TEST",
            overall_thesis="Bullish",
            confidence=75.0,
            investment_rating="Buy",
            bull_case="Growth potential",
            bear_case="Market risk",
            key_catalysts=["Event 1"],
            key_risks=["Risk 1"],
            tokens_used=1500,
            time_horizon="6-12 months",
        )

        assert response.overall_thesis == "Bullish"
        assert response.tokens_used == 1500

    def test_decision_response_structure(self):
        """Decision response should have correct structure."""
        from app.api.research_routes import DecisionResponse

        response = DecisionResponse(
            ticker="TEST",
            recommendation="Buy",
            confidence_pct=75.0,
            conviction_level="Medium",
            suggested_entry_price=102.0,
            target_exit_price=127.5,
            stop_loss_price=91.8,
            position_size_pct=4.0,
            position_size_category="Standard",
            suggested_quantity=400,
            bull_case={"target_price": 127.5, "upside_pct": 25.0, "probability_pct": 40},
            base_case={"target_price": 107.1, "upside_pct": 5.0, "probability_pct": 35},
            bear_case={"target_price": 86.7, "upside_pct": -15.0, "probability_pct": 25},
            expected_return_pct=8.5,
            key_upside_catalysts=["Event"],
            key_downside_risks=["Risk"],
            time_horizon="6-12 months",
        )

        assert response.recommendation == "Buy"
        assert response.position_size_pct == 4.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
