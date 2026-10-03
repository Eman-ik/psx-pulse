"""Step 8: Evidence Pack Builder tests.

Tests evidence pack creation:
- Extraction of facts from snapshot
- Sentiment analysis from metrics
- Confidence scoring
- Narrative generation
"""

import pytest
from datetime import date

from app.services.evidence_pack_builder import EvidencePackBuilder, EvidencePack
from app.schemas.stock_snapshot import (
    StockSnapshot,
    MarketData,
    FinancialMetrics,
    TechnicalIndicators,
    MacroContext,
    DataQuality,
)


class TestEvidencePackBuilder:
    """Test evidence pack building."""

    @pytest.fixture
    def builder(self):
        """Create builder instance."""
        return EvidencePackBuilder()

    @pytest.fixture
    def complete_snapshot(self):
        """Create a complete snapshot for testing."""
        return StockSnapshot(
            ticker="TEST",
            company_name="Test Company",
            market=MarketData(
                ticker="TEST",
                price=100.0,
                change_pct=2.5,
                volume=1_000_000,
                market_cap=5_000,
            ),
            technical=TechnicalIndicators(
                trend="uptrend",
                trend_strength=65.0,
                support_52w_low=80.0,
                resistance_52w_high=120.0,
                avg_volume_30d=900_000,
            ),
            financials=FinancialMetrics(
                revenue_growth_pct=20.0,
                pat_growth_pct=25.0,
                net_margin_pct=12.5,
                gross_margin_pct=35.0,
                roe_pct=25.0,
                roa_pct=8.0,
                debt_to_equity=1.0,
                current_ratio=1.5,
                interest_coverage=5.0,
                ocf_to_pat_ratio=1.2,
                periods_available=2,
            ),
            valuation=None,
            macro=MacroContext(
                sector="Technology",
                market_cap_bracket="mid",
                kse_100_level=78_000,
                kse_100_change_pct=1.5,
            ),
            quality=DataQuality(
                market_data_confidence="high",
                financial_data_confidence="high",
                market_data_freshness_days=0,
                financial_data_freshness_days=7,
            ),
        )

    def test_build_complete_snapshot(self, builder, complete_snapshot):
        """Should build pack from complete snapshot."""
        pack = builder.build(complete_snapshot)

        assert pack is not None
        assert pack.ticker == "TEST"
        assert pack.company_name == "Test Company"
        assert pack.current_price == 100.0
        assert pack.revenue_growth_pct == 20.0

    def test_extract_market_facts(self, builder, complete_snapshot):
        """Should extract market facts correctly."""
        pack = builder.build(complete_snapshot)

        assert pack.current_price == 100.0
        assert pack.price_change_pct == 2.5
        assert pack.daily_volume == 1_000_000

    def test_extract_technical_facts(self, builder, complete_snapshot):
        """Should extract technical facts correctly."""
        pack = builder.build(complete_snapshot)

        assert pack.trend == "uptrend"
        assert pack.trend_strength == 65.0
        assert pack.support_level == 80.0
        assert pack.resistance_level == 120.0

    def test_calculate_distance_to_support(self, builder):
        """Should calculate distance to support level."""
        distance = builder._calc_distance_pct(100.0, 80.0, "above")

        assert distance is not None
        assert abs(distance - 25.0) < 0.1  # (100-80)/80 = 25%

    def test_calculate_distance_to_resistance(self, builder):
        """Should calculate distance to resistance level."""
        distance = builder._calc_distance_pct(100.0, 120.0, "below")

        assert distance is not None
        assert abs(distance - 16.67) < 0.1  # (120-100)/120 = 16.67%

    def test_assess_sentiment_positive(self, builder):
        """Should assess positive sentiment."""
        financials = FinancialMetrics(revenue_growth_pct=20.0, roe_pct=25.0)
        technical = TechnicalIndicators(trend="uptrend")
        market = MarketData(ticker="TEST", price=100, change_pct=3.0)

        sentiment = builder._assess_sentiment(financials, technical, market)

        assert sentiment == "positive"

    def test_assess_sentiment_negative(self, builder):
        """Should assess negative sentiment."""
        financials = FinancialMetrics(revenue_growth_pct=-10.0, roe_pct=3.0)
        technical = TechnicalIndicators(trend="downtrend")
        market = MarketData(ticker="TEST", price=100, change_pct=-3.0)

        sentiment = builder._assess_sentiment(financials, technical, market)

        assert sentiment == "negative"

    def test_assess_sentiment_neutral(self, builder):
        """Should assess neutral sentiment."""
        sentiment = builder._assess_sentiment(None, None, None)

        assert sentiment == "neutral"

    def test_confidence_score_high_quality(self, builder):
        """Should score high confidence with recent, complete data."""
        quality = DataQuality(
            market_data_confidence="high",
            financial_data_confidence="high",
            market_data_freshness_days=0,
            missing_data_fields=[],
        )

        score = builder._calc_confidence_score(quality)

        assert score > 80

    def test_confidence_score_low_quality(self, builder):
        """Should score low confidence with stale, incomplete data."""
        quality = DataQuality(
            market_data_confidence="low",
            financial_data_confidence="low",
            market_data_freshness_days=90,
            missing_data_fields=["revenue", "earnings", "assets"],
        )

        score = builder._calc_confidence_score(quality)

        assert score < 40

    def test_identify_strengths(self, builder):
        """Should identify key strengths."""
        financials = FinancialMetrics(
            revenue_growth_pct=20.0,
            roe_pct=25.0,
            ocf_to_pat_ratio=1.3,
        )
        technical = TechnicalIndicators(trend="uptrend", trend_strength=70.0)

        strengths = builder._identify_strengths(financials, technical)

        assert len(strengths) > 0
        assert any("growth" in s.lower() for s in strengths)
        assert any("roe" in s.lower() for s in strengths)

    def test_identify_concerns(self, builder):
        """Should identify key concerns."""
        financials = FinancialMetrics(
            revenue_growth_pct=-10.0,
            debt_to_equity=3.0,
            current_ratio=0.8,
        )
        technical = TechnicalIndicators(trend="downtrend", trend_strength=60.0)

        concerns = builder._identify_concerns(financials, technical)

        assert len(concerns) > 0
        assert any("revenue" in c.lower() for c in concerns)
        assert any("leverage" in c.lower() for c in concerns)

    def test_extract_event_type_earnings(self, builder):
        """Should extract earnings event type."""
        body = "[EARNINGS | POSITIVE | MAJOR]\nTest announcement"
        event_type = builder._extract_event_type(body)

        assert event_type == "EARNINGS"

    def test_extract_event_type_dividend(self, builder):
        """Should extract dividend event type."""
        body = "[DIVIDEND | NEUTRAL | MODERATE]\nTest announcement"
        event_type = builder._extract_event_type(body)

        assert event_type == "DIVIDEND"

    def test_evidence_pack_to_dict(self, builder, complete_snapshot):
        """Should convert pack to dictionary."""
        pack = builder.build(complete_snapshot)

        data = pack.to_dict()

        assert isinstance(data, dict)
        assert data["ticker"] == "TEST"
        assert data["current_price"] == 100.0

    def test_evidence_pack_narrative(self, builder, complete_snapshot):
        """Should generate narrative from pack."""
        pack = builder.build(complete_snapshot)

        narrative = pack.to_narrative()

        assert "TEST" in narrative
        assert "COMPANY PROFILE" in narrative
        assert "TECHNICAL POSITION" in narrative
        assert "FINANCIAL PERFORMANCE" in narrative

    def test_build_minimal_snapshot(self, builder):
        """Should handle minimal snapshot with mostly None values."""
        minimal = StockSnapshot(
            ticker="MIN",
            market=MarketData(ticker="MIN", price=50.0),
        )

        pack = builder.build(minimal)

        assert pack is not None
        assert pack.ticker == "MIN"
        assert pack.current_price == 50.0
        assert pack.revenue_growth_pct is None

    def test_build_returns_none_for_invalid_input(self, builder):
        """Should return None for invalid input."""
        pack = builder.build(None)

        assert pack is None

    def test_confidence_score_range(self, builder):
        """Should keep confidence score in 0-100 range."""
        quality = DataQuality(
            missing_data_fields=["field1", "field2", "field3"] * 10,  # Many missing
        )

        score = builder._calc_confidence_score(quality)

        assert 0 <= score <= 100


class TestIntegrationWithSnapshot:
    """Test evidence pack integration."""

    def test_evidence_pack_is_serializable(self):
        """Evidence pack should be serializable to JSON."""
        from app.services.evidence_pack_builder import EvidencePack
        import json

        pack = EvidencePack(
            ticker="TEST",
            company_name="Test",
            sector="Tech",
            market_cap_bracket="mid",
            current_price=100.0,
            price_change_pct=2.5,
            daily_volume=1_000_000,
            free_float_pct=50.0,
            trend="uptrend",
            trend_strength=60.0,
            support_level=80.0,
            resistance_level=120.0,
            distance_to_support_pct=25.0,
            distance_to_resistance_pct=-16.7,
            liquidity_avg_volume=900_000,
            revenue_growth_pct=20.0,
            earnings_growth_pct=25.0,
            net_margin_pct=12.5,
            gross_margin_pct=35.0,
            return_on_equity_pct=25.0,
            return_on_assets_pct=8.0,
            debt_to_equity_ratio=1.0,
            current_ratio=1.5,
            interest_coverage_ratio=5.0,
            earnings_quality_ratio=1.2,
            periods_analyzed=2,
            pe_ratio=8.0,
            pb_ratio=1.0,
            dividend_yield_pct=4.0,
            kse_100_level=78_000,
            kse_100_change_pct=1.5,
            index_context="KSE-100 up 1.5%",
            recent_event_count=3,
            recent_positive_events=2,
            recent_negative_events=0,
            latest_event_date="2026-10-01",
            latest_event_type="EARNINGS",
            data_freshness_days=0,
            market_data_confidence="high",
            financial_data_confidence="high",
            missing_data_fields=[],
            data_gaps_description="None",
            sentiment="positive",
            confidence_score=90.0,
            key_strengths=["Strong growth", "High ROE"],
            key_concerns=[],
        )

        # Should serialize to JSON without error
        json_str = json.dumps(pack.to_dict())
        assert len(json_str) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
