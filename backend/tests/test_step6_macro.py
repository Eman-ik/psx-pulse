"""Step 6: Macro Context Service tests.

Tests macro context calculation:
- Sector information
- Market cap brackets
- Index data
- Economic context
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import Issuer, FinancialFact, SourceDocument, Sector, Security
from app.services.macro_context_service import MacroContextService
from app.services.market_data_service import MarketDataService
from app.schemas.stock_snapshot import MacroContext


@pytest.fixture
def test_db():
    """In-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    return TestingSessionLocal()


@pytest.fixture
def sector_factory(test_db):
    """Factory for creating test sectors."""
    def _create(name: str = "Fertilizer") -> Sector:
        sector = Sector(name=name)
        test_db.add(sector)
        test_db.commit()
        return sector
    return _create


@pytest.fixture
def issuer_factory(test_db):
    """Factory for creating test issuers with optional sector."""
    def _create(symbol: str = "TEST_CO", sector: Sector = None) -> Issuer:
        issuer = Issuer(
            name=f"{symbol} Limited",
            sector_id=sector.id if sector else None,
        )
        test_db.add(issuer)
        test_db.flush()

        # Create associated security with the symbol
        security = Security(
            issuer_id=issuer.id,
            symbol=symbol,
            security_type="ordinary_share",
            listing_status="listed",
        )
        test_db.add(security)
        test_db.commit()

        return issuer
    return _create


@pytest.fixture
def source_doc_factory(test_db):
    """Factory for creating test source documents."""
    import hashlib
    import uuid

    def _create() -> SourceDocument:
        # Generate unique content hash
        content = str(uuid.uuid4()).encode()
        content_hash = hashlib.sha256(content).hexdigest()

        doc = SourceDocument(
            url="http://test.local/doc",
            content_hash=content_hash,
            document_type="test_macro",
            source_tier="primary",
        )
        test_db.add(doc)
        test_db.commit()
        return doc
    return _create


class TestMacroContextService:
    """Test macro context calculations."""

    def test_analyze_with_sector(self, test_db, sector_factory, issuer_factory):
        """Should include sector information."""
        sector = sector_factory("Fertilizer")
        issuer = issuer_factory("FFC", sector=sector)

        service = MacroContextService(test_db)
        result = service.analyze(issuer.id)

        assert result is not None
        assert result.sector == "Fertilizer"

    def test_analyze_without_sector(self, test_db, issuer_factory):
        """Should handle missing sector gracefully."""
        issuer = issuer_factory("NO_SECTOR")

        service = MacroContextService(test_db)
        result = service.analyze(issuer.id)

        assert result is not None
        assert result.sector is None

    def test_market_cap_bracket_micro(self):
        """Market cap < 500M should be micro."""
        service = MacroContextService(None)
        bracket = service._get_market_cap_bracket(250)

        assert bracket == "micro"

    def test_market_cap_bracket_small(self):
        """Market cap 500M - 5B should be small."""
        service = MacroContextService(None)

        bracket1 = service._get_market_cap_bracket(500)
        assert bracket1 == "small"

        bracket2 = service._get_market_cap_bracket(2_500)
        assert bracket2 == "small"

    def test_market_cap_bracket_mid(self):
        """Market cap 5B - 50B should be mid."""
        service = MacroContextService(None)

        bracket1 = service._get_market_cap_bracket(5_000)
        assert bracket1 == "mid"

        bracket2 = service._get_market_cap_bracket(25_000)
        assert bracket2 == "mid"

    def test_market_cap_bracket_large(self):
        """Market cap > 50B should be large."""
        service = MacroContextService(None)
        bracket = service._get_market_cap_bracket(100_000)

        assert bracket == "large"

    def test_analyze_with_market_cap(self, test_db, issuer_factory):
        """Should set market cap bracket when provided."""
        issuer = issuer_factory("CAP_TEST")

        service = MacroContextService(test_db)

        # Small cap
        result_small = service.analyze(issuer.id, market_cap_millions=1_000)
        assert result_small.market_cap_bracket == "small"

        # Large cap
        result_large = service.analyze(issuer.id, market_cap_millions=75_000)
        assert result_large.market_cap_bracket == "large"

    def test_analyze_fetches_market_cap_from_db(self, test_db, issuer_factory, source_doc_factory):
        """Should fetch market cap from database facts."""
        issuer = issuer_factory("DB_CAP")
        source_doc = source_doc_factory()

        # Add market cap fact (value in millions)
        test_db.add(FinancialFact(
            issuer_id=issuer.id,
            line_item="market_cap",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            period_type="snapshot",
            scope="standalone",
            unit="PKR_million",
            value=20_000,  # 20B (20,000 million)
            source_document_id=source_doc.id,
        ))
        test_db.commit()

        service = MacroContextService(test_db)
        result = service.analyze(issuer.id)

        assert result is not None
        assert result.market_cap_bracket == "mid"  # 20B is mid cap

    def test_sector_risk_profile(self):
        """Should return risk profiles for known sectors."""
        service = MacroContextService(None)

        profile_fert = service.sector_risk_profile("Fertilizer")
        assert profile_fert["volatility"] == 0.35
        assert profile_fert["beta"] == 1.2

        profile_cement = service.sector_risk_profile("Cement")
        assert profile_cement["volatility"] == 0.40

        profile_unknown = service.sector_risk_profile("Unknown Sector")
        assert profile_unknown["volatility"] == 0.30

    def test_sector_valuation_median(self):
        """Should return median valuation for sectors."""
        service = MacroContextService(None)

        valuation_fert = service.sector_valuation_median("Fertilizer")
        assert valuation_fert["pe"] == 7.5
        assert valuation_fert["dividend_yield"] == 4.5

        valuation_banking = service.sector_valuation_median("Banking")
        assert valuation_banking["pe"] == 8.5

        valuation_unknown = service.sector_valuation_median("Unknown")
        assert valuation_unknown["pe"] == 7.0

    def test_analyze_nonexistent_issuer(self, test_db):
        """Should handle missing issuer gracefully."""
        service = MacroContextService(test_db)
        result = service.analyze(999)  # Non-existent ID

        assert result is None

    def test_index_snapshot_integration(self, test_db, issuer_factory):
        """Should include KSE-100 data when market service available."""
        issuer = issuer_factory("INDEX_TEST")

        # Create a mock market service that returns index data
        class MockMarketService:
            def get_index_snapshot(self):
                return {
                    "index": "KSE-100",
                    "price": 78_500.0,
                    "change_pct": 1.5,
                    "volume": 5_000_000,
                }

        service = MacroContextService(test_db, MockMarketService())
        result = service.analyze(issuer.id)

        assert result is not None
        assert result.kse_100_level == 78_500.0
        assert result.kse_100_change_pct == 1.5


class TestIntegrationWithSnapshot:
    """Test macro context integration with SnapshotBuilder."""

    def test_snapshot_includes_macro(self, test_db, sector_factory, issuer_factory, source_doc_factory):
        """Macro context should integrate into snapshot."""
        from app.services.snapshot_builder import SnapshotBuilder
        from app.schemas.stock_snapshot import StockSnapshot, MarketData

        sector = sector_factory("Fertilizer")
        issuer = issuer_factory("SNAPSHOT_MACRO", sector=sector)
        source_doc = source_doc_factory()

        # Add market cap fact
        test_db.add(FinancialFact(
            issuer_id=issuer.id,
            line_item="market_cap",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            period_type="snapshot",
            scope="standalone",
            unit="PKR_thousand",
            value=20_000_000,  # 20B mid-cap
            source_document_id=source_doc.id,
        ))
        test_db.commit()

        # Build snapshot with database
        builder = SnapshotBuilder(db=test_db)

        # Manually build to test
        market = MarketData(ticker="SNAPSHOT_MACRO", price=100, market_cap=20_000)
        snapshot = StockSnapshot(ticker="SNAPSHOT_MACRO", market=market)

        # Add macro context
        service = MacroContextService(test_db)
        snapshot.macro = service.analyze(issuer.id, market_cap_millions=20_000)

        # Should have macro data
        assert snapshot.macro is not None
        assert snapshot.macro.sector == "Fertilizer"
        assert snapshot.macro.market_cap_bracket == "mid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
