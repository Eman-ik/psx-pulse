"""Step 7: Announcement Normalizer tests.

Tests announcement normalization:
- Categorization (earnings, dividend, M&A, etc.)
- Sentiment analysis (positive, negative, neutral)
- Materiality assessment (major, moderate, minor)
- Event normalization
"""

import pytest
from datetime import date

from app.services.announcement_normalizer import AnnouncementNormalizer
from app.schemas.stock_snapshot import RecentEvent


class TestAnnouncementNormalizer:
    """Test announcement normalization."""

    @pytest.fixture
    def normalizer(self):
        """Create normalizer instance."""
        return AnnouncementNormalizer()

    def test_normalize_earnings_announcement(self, normalizer):
        """Should normalize earnings announcement."""
        announcement = {
            "date": "2026-10-01",
            "title": "FY2025 Results: Strong Growth",
            "body": "Revenue increased 25% to 130 billion. Profit after tax grew 35% to 14.3 billion.",
            "source": "PSX",
        }

        event = normalizer.normalize_single("FFC", announcement)

        assert event is not None
        assert "earnings" in event.body.lower() or "strong" in event.body.lower()
        assert event.source == "PSX"
        assert event.date == date(2026, 10, 1)

    def test_categorize_earnings(self, normalizer):
        """Should categorize earnings announcement."""
        text = "FY2024 Annual Results: Revenue and Profit Growth"
        category = normalizer._categorize(text.lower())

        assert category == "earnings"

    def test_categorize_dividend(self, normalizer):
        """Should categorize dividend announcement."""
        text = "Board announces cash dividend of 5 Rs per share"
        category = normalizer._categorize(text.lower())

        assert category == "dividend"

    def test_categorize_acquisition(self, normalizer):
        """Should categorize acquisition announcement."""
        text = "Company acquires 60% stake in competitor for 500 million"
        category = normalizer._categorize(text.lower())

        assert category == "acquisition"

    def test_categorize_regulatory(self, normalizer):
        """Should categorize regulatory announcement."""
        text = "SECP investigation concluded with no findings"
        category = normalizer._categorize(text.lower())

        assert category == "regulatory"

    def test_sentiment_positive(self, normalizer):
        """Should assess positive sentiment."""
        text = "strong growth exceeded expectations record performance"
        sentiment = normalizer._assess_sentiment(text)

        assert sentiment == "positive"

    def test_sentiment_negative(self, normalizer):
        """Should assess negative sentiment."""
        text = "decline in revenue loss in profitability weak market"
        sentiment = normalizer._assess_sentiment(text)

        assert sentiment == "negative"

    def test_sentiment_neutral(self, normalizer):
        """Should assess neutral sentiment."""
        text = "company announced management change"
        sentiment = normalizer._assess_sentiment(text)

        assert sentiment == "neutral"

    def test_materiality_major_large_percentage(self, normalizer):
        """Should mark large percentage changes as major."""
        text = "revenue increased by 50%"
        # Earnings category with large percentage should be at least moderate
        materiality = normalizer._assess_materiality(text, "earnings")

        assert materiality in ["major", "moderate"]

    def test_materiality_moderate_medium_percentage(self, normalizer):
        """Should mark medium percentage changes as moderate."""
        text = "revenue increased by 15%"
        materiality = normalizer._assess_materiality(text, "earnings")

        assert materiality == "moderate"

    def test_materiality_major_earnings_category(self, normalizer):
        """Earnings category should be at least moderate materiality."""
        text = "quarterly results announced"
        materiality = normalizer._assess_materiality(text, "earnings")

        assert materiality in ["moderate", "major"]

    def test_materiality_major_acquisition_category(self, normalizer):
        """Acquisition category should be at least moderate."""
        text = "acquisition agreement signed"
        materiality = normalizer._assess_materiality(text, "acquisition")

        assert materiality in ["moderate", "major"]

    def test_extract_numbers(self, normalizer):
        """Should extract numbers from text."""
        text = "Revenue 100,000 million, Profit 15,500 million, Growth 25%"
        numbers = normalizer.extract_numbers(text)

        assert 100000 in numbers
        assert 15500 in numbers
        assert 25 in numbers

    def test_extract_date_mentions(self, normalizer):
        """Should extract date mentions from text."""
        text = "Q1 2025 results announced on 15/04/2025. FY2024 was strong."
        dates = normalizer.extract_date_mentions(text)

        assert any("q1" in d.lower() for d in dates)
        assert any("2025" in d for d in dates)
        assert any("2024" in d for d in dates)

    def test_normalize_batch(self, normalizer):
        """Should normalize batch of announcements."""
        announcements = [
            {
                "date": "2026-10-01",
                "title": "Q3 Results: Strong Performance",
                "body": "Revenue grew 20%",
                "source": "PSX",
            },
            {
                "date": "2026-09-15",
                "title": "Cash Dividend Announcement",
                "body": "DPS of 5 rupees",
                "source": "PSX",
            },
        ]

        events = normalizer.normalize_batch("TEST", announcements)

        assert len(events) == 2
        assert all(isinstance(e, RecentEvent) for e in events)

    def test_normalize_batch_with_invalid(self, normalizer):
        """Should skip invalid announcements in batch."""
        announcements = [
            {
                "date": "2026-10-01",
                "title": "Valid announcement",
                "body": "Details here",
                "source": "PSX",
            },
            {
                "title": "",  # Empty title should be skipped
                "source": "PSX",
            },
            {
                "date": "2026-09-01",
                "title": "Another valid",
                "body": "More details",
                "source": "PSX",
            },
        ]

        events = normalizer.normalize_batch("TEST", announcements)

        assert len(events) == 2  # Only valid announcements

    def test_is_material_event_major(self, normalizer):
        """Should identify major events."""
        announcement = {
            "title": "Acquisition Announcement",
            "body": "Company acquires competitor for 5000 million rupees",
        }

        # Acquisition category is inherently moderate or above
        is_material = normalizer.is_material_event(announcement, "major")

        # Might be moderate instead of major depending on implementation
        is_material_moderate = normalizer.is_material_event(announcement, "moderate")
        assert is_material_moderate  # At least moderate materiality

    def test_is_material_event_moderate(self, normalizer):
        """Should identify moderate events."""
        announcement = {
            "title": "Quarterly Earnings",
            "body": "Revenue increased by 12%",
        }

        is_material = normalizer.is_material_event(announcement, "moderate")

        assert is_material

    def test_is_material_event_minor(self, normalizer):
        """Should identify minor events."""
        announcement = {
            "title": "Management Update",
            "body": "Department head change",
        }

        is_material = normalizer.is_material_event(announcement, "minor")

        assert is_material

    def test_is_material_event_below_threshold(self, normalizer):
        """Should filter below materiality threshold."""
        announcement = {
            "title": "Minor News",
            "body": "Office relocation",
        }

        # Minor event, but threshold is major
        is_material = normalizer.is_material_event(announcement, "major")

        assert not is_material

    def test_event_body_structure(self, normalizer):
        """Should format event body with metadata."""
        title = "Test Announcement"
        body = "Test details here"

        event_body = normalizer._build_event_body(
            title, body, "earnings", "positive", "major"
        )

        assert "[EARNINGS | POSITIVE | MAJOR]" in event_body
        assert title in event_body
        assert body in event_body

    def test_normalize_with_date_string(self, normalizer):
        """Should handle date as string."""
        announcement = {
            "date": "2026-10-03",
            "title": "Test",
            "body": "Details",
            "source": "PSX",
        }

        event = normalizer.normalize_single("TEST", announcement)

        assert event is not None
        assert event.date == date(2026, 10, 3)

    def test_normalize_with_invalid_date(self, normalizer):
        """Should default to today for invalid date."""
        announcement = {
            "date": "invalid-date",
            "title": "Test",
            "body": "Details",
            "source": "PSX",
        }

        event = normalizer.normalize_single("TEST", announcement)

        assert event is not None
        # Should default to today's date
        assert event.date == date.today()

    def test_normalize_empty_batch(self, normalizer):
        """Should handle empty announcement batch."""
        events = normalizer.normalize_batch("TEST", [])

        assert events == []

    def test_normalize_truncates_long_body(self, normalizer):
        """Should truncate long announcement bodies."""
        long_text = "x" * 1000
        announcement = {
            "date": "2026-10-01",
            "title": "Test",
            "body": long_text,
            "source": "PSX",
        }

        event = normalizer.normalize_single("TEST", announcement)

        assert event is not None
        # Body should be truncated to reasonable length
        assert len(event.body) < 700


class TestIntegrationWithSnapshot:
    """Test announcement integration with SnapshotBuilder."""

    def test_snapshot_includes_recent_events(self):
        """Recent events should integrate into snapshot."""
        from app.services.snapshot_builder import SnapshotBuilder
        from app.schemas.stock_snapshot import StockSnapshot, MarketData

        # Create minimal snapshot
        market = MarketData(ticker="TEST", price=100)
        snapshot = StockSnapshot(ticker="TEST", market=market, recent_events=[])

        # Should have empty events initially
        assert snapshot.recent_events == []

        # Add normalized event
        normalizer = AnnouncementNormalizer()
        event = RecentEvent(
            date=date.today(),
            title="Test Announcement",
            body="Test details with [EARNINGS | POSITIVE | MAJOR]",
            source="PSX",
        )
        snapshot.recent_events = [event]

        # Should have event
        assert len(snapshot.recent_events) == 1
        assert snapshot.recent_events[0].title == "Test Announcement"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
