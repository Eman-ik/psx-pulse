"""Step 4: Technical Calculator tests.

Tests technical indicator calculation:
- Support/resistance (52-week high/low)
- Trend detection (uptrend/downtrend/consolidation)
- Trend strength (0-100%)
- Average volume
"""

import pytest
from app.services.technical_calculator import TechnicalCalculator
from app.schemas.stock_snapshot import TechnicalIndicators


class TestTechnicalCalculator:
    """Test technical indicator calculations."""

    @pytest.fixture
    def uptrend_history(self):
        """Create mock price history with clear uptrend."""
        return [
            {"date": "2025-01-01", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 1000},
            {"date": "2025-01-02", "open": 101, "high": 103, "low": 100, "close": 102, "volume": 1100},
            {"date": "2025-01-03", "open": 102, "high": 105, "low": 101, "close": 104, "volume": 1200},
            {"date": "2025-01-04", "open": 104, "high": 107, "low": 103, "close": 106, "volume": 1300},
            {"date": "2025-01-05", "open": 106, "high": 110, "low": 105, "close": 109, "volume": 1400},
            {"date": "2025-01-06", "open": 109, "high": 112, "low": 108, "close": 111, "volume": 1500},
            {"date": "2025-01-07", "open": 111, "high": 115, "low": 110, "close": 114, "volume": 1600},
            {"date": "2025-01-08", "open": 114, "high": 118, "low": 113, "close": 117, "volume": 1700},
        ]

    @pytest.fixture
    def downtrend_history(self):
        """Create mock price history with clear downtrend."""
        return [
            {"date": "2025-01-01", "open": 150, "high": 152, "low": 148, "close": 150, "volume": 2000},
            {"date": "2025-01-02", "open": 150, "high": 151, "low": 148, "close": 148, "volume": 2100},
            {"date": "2025-01-03", "open": 148, "high": 149, "low": 145, "close": 146, "volume": 2200},
            {"date": "2025-01-04", "open": 146, "high": 147, "low": 143, "close": 144, "volume": 2300},
            {"date": "2025-01-05", "open": 144, "high": 145, "low": 140, "close": 141, "volume": 2400},
            {"date": "2025-01-06", "open": 141, "high": 142, "low": 138, "close": 139, "volume": 2500},
            {"date": "2025-01-07", "open": 139, "high": 140, "low": 135, "close": 137, "volume": 2600},
            {"date": "2025-01-08", "open": 137, "high": 138, "low": 133, "close": 135, "volume": 2700},
        ]

    @pytest.fixture
    def consolidation_history(self):
        """Create mock price history with consolidation (no trend)."""
        return [
            {"date": "2025-01-01", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 1000},
            {"date": "2025-01-02", "open": 101, "high": 103, "low": 100, "close": 100, "volume": 1000},
            {"date": "2025-01-03", "open": 100, "high": 101, "low": 99, "close": 101, "volume": 1000},
            {"date": "2025-01-04", "open": 101, "high": 102, "low": 100, "close": 100, "volume": 1000},
            {"date": "2025-01-05", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 1000},
            {"date": "2025-01-06", "open": 101, "high": 103, "low": 100, "close": 100, "volume": 1000},
            {"date": "2025-01-07", "open": 100, "high": 101, "low": 99, "close": 101, "volume": 1000},
            {"date": "2025-01-08", "open": 101, "high": 102, "low": 100, "close": 100, "volume": 1000},
        ]

    def test_calculate_uptrend(self, uptrend_history):
        """Should detect uptrend with rising prices."""
        indicators = TechnicalCalculator.calculate("TEST_UP", uptrend_history)

        assert indicators is not None
        assert indicators.trend == "uptrend"
        assert indicators.trend_strength is not None
        assert indicators.trend_strength > 0
        assert indicators.current_price == 117  # Last close
        assert indicators.support_52w_low == 99  # Lowest point
        assert indicators.resistance_52w_high == 118  # Highest point

    def test_calculate_downtrend(self, downtrend_history):
        """Should detect downtrend with falling prices."""
        indicators = TechnicalCalculator.calculate("TEST_DOWN", downtrend_history)

        assert indicators is not None
        assert indicators.trend == "downtrend"
        assert indicators.trend_strength is not None
        assert indicators.trend_strength > 0
        assert indicators.current_price == 135  # Last close
        assert indicators.support_52w_low == 133  # Lowest point
        assert indicators.resistance_52w_high == 152  # Highest point

    def test_calculate_consolidation(self, consolidation_history):
        """Should detect consolidation (sideways movement)."""
        indicators = TechnicalCalculator.calculate("TEST_CONS", consolidation_history)

        assert indicators is not None
        assert indicators.trend == "consolidation"
        # Strength should be low for consolidation
        assert indicators.trend_strength is not None
        assert indicators.trend_strength < 20

    def test_average_volume(self, uptrend_history):
        """Should calculate average volume correctly."""
        indicators = TechnicalCalculator.calculate("TEST", uptrend_history)

        assert indicators.avg_volume_30d is not None
        # Average of 1000-1700 should be around 1350
        assert 1200 < indicators.avg_volume_30d < 1600

    def test_insufficient_data(self):
        """Should handle insufficient price data gracefully."""
        # Only 1 record
        history = [{"close": 100, "high": 102, "low": 99, "volume": 1000}]
        indicators = TechnicalCalculator.calculate("TEST", history)

        assert indicators is None

    def test_empty_history(self):
        """Should handle empty history."""
        indicators = TechnicalCalculator.calculate("TEST", [])
        assert indicators is None

    def test_missing_prices(self):
        """Should handle missing price data."""
        history = [
            {"date": "2025-01-01", "volume": 1000},  # Missing prices
            {"date": "2025-01-02", "volume": 1000},
        ]
        indicators = TechnicalCalculator.calculate("TEST", history)

        assert indicators is None

    def test_distance_from_support(self):
        """Should calculate distance from support correctly."""
        distance = TechnicalCalculator.distance_from_support(current=105, support=100)

        assert distance is not None
        assert abs(distance - 5.0) < 0.1  # 5% above support

    def test_distance_from_resistance(self):
        """Should calculate distance from resistance correctly."""
        distance = TechnicalCalculator.distance_from_resistance(current=95, resistance=100)

        assert distance is not None
        assert abs(distance - 5.0) < 0.1  # 5% below resistance

    def test_distance_from_support_edge_case(self):
        """Should return None if price below support."""
        distance = TechnicalCalculator.distance_from_support(current=95, support=100)
        assert distance is None

    def test_distance_from_resistance_edge_case(self):
        """Should return None if price above resistance."""
        distance = TechnicalCalculator.distance_from_resistance(current=105, resistance=100)
        assert distance is None


class TestIntegrationWithSnapshot:
    """Test technical calculator integration with SnapshotBuilder."""

    def test_snapshot_with_technical_indicators(self):
        """Technical indicators should integrate into snapshot."""
        from app.services.snapshot_builder import SnapshotBuilder
        from app.schemas.stock_snapshot import StockSnapshot, MarketData

        # Create uptrend history
        uptrend_history = [
            {"date": "2025-01-01", "open": 100, "high": 102, "low": 99, "close": 101, "volume": 1000},
            {"date": "2025-01-02", "open": 101, "high": 103, "low": 100, "close": 102, "volume": 1100},
            {"date": "2025-01-03", "open": 102, "high": 105, "low": 101, "close": 104, "volume": 1200},
            {"date": "2025-01-04", "open": 104, "high": 107, "low": 103, "close": 106, "volume": 1300},
            {"date": "2025-01-05", "open": 106, "high": 110, "low": 105, "close": 109, "volume": 1400},
            {"date": "2025-01-06", "open": 109, "high": 112, "low": 108, "close": 111, "volume": 1500},
            {"date": "2025-01-07", "open": 111, "high": 115, "low": 110, "close": 114, "volume": 1600},
            {"date": "2025-01-08", "open": 114, "high": 118, "low": 113, "close": 117, "volume": 1700},
        ]

        # Build minimal snapshot
        market = MarketData(ticker="TEST", price=117)
        snapshot = StockSnapshot(ticker="TEST", market=market)

        # Should have no technical data initially
        assert snapshot.technical is None

        # Now build with calculator
        technical = TechnicalCalculator.calculate("TEST", uptrend_history)
        snapshot.technical = technical

        # Should have technical data after calculation
        assert snapshot.technical is not None
        assert snapshot.technical.trend == "uptrend"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
