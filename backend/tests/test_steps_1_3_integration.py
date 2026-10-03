"""Integration test for Steps 1-3: PSXClient, MarketDataService, StockSnapshot.

Verifies that the foundational layers connect properly and the schema
is valid.
"""

import pytest
from datetime import date
from app.clients.psx_client import PSXClient
from app.services.market_data_service import MarketDataService
from app.services.snapshot_builder import SnapshotBuilder
from app.schemas.stock_snapshot import (
    StockSnapshot,
    MarketData,
    FinancialMetrics,
    DataQuality,
)


class TestStep1PSXClient:
    """Step 1: PSX API Client with token management."""

    def test_psx_client_instantiation(self):
        """PSXClient should initialize with timeout and retry config."""
        client = PSXClient(timeout_seconds=30, max_retries=3)
        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.token is None  # Lazy initialization

    def test_psx_client_token_validity(self):
        """Token validity check should work even with no token."""
        client = PSXClient()
        assert not client._is_token_valid()

    def test_psx_client_headers(self):
        """Client should have user-agent headers configured."""
        client = PSXClient()
        assert "User-Agent" in client.headers
        assert "Mozilla" in client.headers["User-Agent"]


class TestStep2MarketDataService:
    """Step 2: Unified market data interface."""

    def test_market_data_service_instantiation(self):
        """Service should initialize with PSXClient."""
        service = MarketDataService()
        assert service.psx_client is not None
        assert isinstance(service.psx_client, PSXClient)

    def test_market_data_service_methods_exist(self):
        """Service should have all required methods."""
        service = MarketDataService()
        assert hasattr(service, "get_snapshot")
        assert hasattr(service, "get_history")
        assert hasattr(service, "get_announcements")
        assert hasattr(service, "get_index_snapshot")

    def test_market_data_snapshot_structure(self):
        """MarketData schema should have all required fields."""
        market = MarketData(
            ticker="TEST",
            price=100.0,
            volume=1000,
        )
        assert market.ticker == "TEST"
        assert market.price == 100.0
        assert market.source == "PSX"


class TestStep3StockSnapshot:
    """Step 3: Unified snapshot schema."""

    def test_snapshot_minimal_construction(self):
        """Snapshot should accept minimal market data."""
        market = MarketData(ticker="TEST", price=100.0)
        snapshot = StockSnapshot(
            ticker="TEST",
            market=market,
        )
        assert snapshot.ticker == "TEST"
        assert snapshot.market.price == 100.0

    def test_snapshot_complete_construction(self):
        """Snapshot should support rich data."""
        market = MarketData(
            ticker="TEST",
            price=100.0,
            change_pct=2.5,
            volume=50000,
            market_cap=1000.0,
        )
        financials = FinancialMetrics(
            revenue_growth_pct=15.0,
            pat_growth_pct=20.0,
            net_margin_pct=10.0,
            periods_available=2,
        )
        snapshot = StockSnapshot(
            ticker="TEST",
            company_name="Test Company",
            market=market,
            financials=financials,
        )
        assert snapshot.has_complete_fundamentals()

    def test_snapshot_data_gaps(self):
        """Snapshot should identify missing data."""
        market = MarketData(ticker="TEST", price=None)
        snapshot = StockSnapshot(ticker="TEST", market=market)
        gaps = snapshot.get_data_gaps()
        assert "market_price" in gaps

    def test_snapshot_json_serialization(self):
        """Snapshot should serialize to JSON."""
        market = MarketData(
            ticker="TEST",
            price=100.0,
            price_date=date(2026, 10, 3),
        )
        snapshot = StockSnapshot(ticker="TEST", market=market)
        json_data = snapshot.model_dump_json()
        assert "TEST" in json_data
        assert "100" in json_data

    def test_data_quality_defaults(self):
        """DataQuality should have sensible defaults."""
        quality = DataQuality()
        assert quality.snapshot_time is not None
        assert quality.data_issues == []
        assert quality.missing_data_fields == []


class TestStep4SnapshotBuilder:
    """Step 4: Builder pattern for snapshots."""

    def test_builder_instantiation(self):
        """Builder should initialize with services."""
        builder = SnapshotBuilder()
        assert builder.market_service is not None

    def test_builder_methods_exist(self):
        """Builder should have all required methods."""
        builder = SnapshotBuilder()
        assert hasattr(builder, "build")
        assert hasattr(builder, "_build_financials")
        assert hasattr(builder, "_build_valuation")
        assert hasattr(builder, "_build_technical")

    def test_market_confidence_assessment(self):
        """Confidence assessment should work."""
        builder = SnapshotBuilder()

        # High confidence: price + volume
        high = builder._assess_market_confidence({"price": 100, "volume": 1000})
        assert high == "high"

        # Medium: price only
        medium = builder._assess_market_confidence({"price": 100})
        assert medium == "medium"

        # Low: no data
        low = builder._assess_market_confidence({})
        assert low == "low"


class TestIntegration:
    """Integration: All steps together."""

    def test_client_to_snapshot_flow(self):
        """Data should flow: PSXClient → MarketDataService → SnapshotBuilder."""
        # Create a builder (which uses MarketDataService, which uses PSXClient)
        builder = SnapshotBuilder()

        # Verify the chain exists
        assert builder.market_service is not None
        assert builder.market_service.psx_client is not None
        assert isinstance(builder.market_service.psx_client, PSXClient)

    def test_snapshot_as_api_contract(self):
        """Snapshot should be usable as an API response model."""
        # This would be the HTTP response
        market = MarketData(ticker="TEST", price=100.0)
        snapshot = StockSnapshot(ticker="TEST", market=market)

        # Should serialize for HTTP
        json_str = snapshot.model_dump_json()
        assert '"ticker":"TEST"' in json_str or '"ticker": "TEST"' in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
