"""Step 5: Financial Context Service tests.

Tests financial metric calculation:
- Growth (revenue, PAT)
- Profitability (margins, ROA, ROE)
- Leverage (debt-to-equity, current ratio)
- Cash flow quality (OCF/PAT)
"""

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import Issuer, FinancialFact, SourceDocument, Security
from app.services.financial_context_service import FinancialContextService
from app.schemas.stock_snapshot import FinancialMetrics


@pytest.fixture
def test_db():
    """In-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    return TestingSessionLocal()


@pytest.fixture
def issuer_factory(test_db):
    """Factory for creating test issuers with security."""
    def _create(symbol: str = "TEST_CO") -> Issuer:
        issuer = Issuer(
            name=f"{symbol} Limited",
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

    def _create() -> SourceDocument:
        # Generate unique content hash
        import uuid
        content = str(uuid.uuid4()).encode()
        content_hash = hashlib.sha256(content).hexdigest()

        doc = SourceDocument(
            url="http://test.local/doc",
            content_hash=content_hash,
            document_type="test_financial",
            source_tier="primary",
        )
        test_db.add(doc)
        test_db.commit()
        return doc
    return _create


class TestFinancialContextService:
    """Test financial metric calculations."""

    def test_analyze_growth_company(self, test_db, issuer_factory, source_doc_factory):
        """Should calculate growth metrics for improving company."""
        issuer = issuer_factory("GROWTH_CO")
        source_doc = source_doc_factory()

        # FY2024: Baseline
        facts_2024 = [
            ("revenue", 100_000_000),
            ("profit_after_tax", 10_000_000),
            ("gross_profit", 30_000_000),
            ("total_assets", 500_000_000),
            ("total_equity", 250_000_000),
            ("total_debt", 100_000_000),
            ("operating_cash_flow", 12_000_000),
            ("ebit", 15_000_000),
            ("interest_expense", 5_000_000),
        ]

        for metric, value in facts_2024:
            test_db.add(FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 12, 31),
                period_type="annual",
                scope="consolidated",
                unit="PKR",
                value=value,
                source_document_id=source_doc.id,
            ))

        # FY2025: Growth
        facts_2025 = [
            ("revenue", 130_000_000),  # +30%
            ("profit_after_tax", 14_300_000),  # +43%
            ("gross_profit", 39_000_000),
            ("total_assets", 550_000_000),
            ("total_equity", 280_000_000),
            ("total_debt", 80_000_000),
            ("operating_cash_flow", 15_000_000),
            ("ebit", 20_000_000),
            ("interest_expense", 4_000_000),
        ]

        for metric, value in facts_2025:
            test_db.add(FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
                period_type="annual",
                scope="consolidated",
                unit="PKR",
                value=value,
                source_document_id=source_doc.id,
            ))

        test_db.commit()

        # Analyze
        service = FinancialContextService(test_db)
        result = service.analyze(issuer.id)

        # Assertions
        assert result is not None
        assert result.revenue_growth_pct is not None
        assert abs(result.revenue_growth_pct - 30.0) < 1.0
        assert result.pat_growth_pct is not None
        assert abs(result.pat_growth_pct - 43.0) < 1.0
        assert result.net_margin_pct is not None
        assert 10 < result.net_margin_pct < 12  # 14.3M / 130M ≈ 11%
        assert result.roe_pct is not None
        assert result.periods_available == 2

    def test_analyze_margin_compression(self, test_db, issuer_factory, source_doc_factory):
        """Should detect margin compression."""
        issuer = issuer_factory("MARGIN_CO")
        source_doc = source_doc_factory()

        # FY2024: 15% net margin
        facts_2024 = [
            ("revenue", 100_000_000),
            ("profit_after_tax", 15_000_000),
            ("gross_profit", 40_000_000),
        ]

        for metric, value in facts_2024:
            test_db.add(FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 12, 31),
                period_type="annual",
                scope="consolidated",
                unit="PKR",
                value=value,
                source_document_id=source_doc.id,
            ))

        # FY2025: 10% net margin (compression)
        facts_2025 = [
            ("revenue", 105_000_000),  # +5% revenue
            ("profit_after_tax", 10_500_000),  # -30% PAT
            ("gross_profit", 31_500_000),
        ]

        for metric, value in facts_2025:
            test_db.add(FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
                period_type="annual",
                scope="consolidated",
                unit="PKR",
                value=value,
                source_document_id=source_doc.id,
            ))

        test_db.commit()

        service = FinancialContextService(test_db)
        result = service.analyze(issuer.id)

        assert result is not None
        assert result.net_margin_pct is not None
        assert abs(result.net_margin_pct - 10.0) < 1.0  # 10.5M / 105M

    def test_analyze_leverage(self, test_db, issuer_factory, source_doc_factory):
        """Should calculate leverage ratios."""
        issuer = issuer_factory("LEVERAGE_CO")
        source_doc = source_doc_factory()

        facts = [
            ("revenue", 100_000_000),
            ("profit_after_tax", 10_000_000),
            ("total_debt", 200_000_000),
            ("total_equity", 100_000_000),
            ("current_assets", 50_000_000),
            ("current_liabilities", 25_000_000),
        ]

        for metric, value in facts:
            test_db.add(FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
                period_type="annual",
                scope="consolidated",
                unit="PKR",
                value=value,
                source_document_id=source_doc.id,
            ))

        # Need prior year for growth calculation
        for metric, value in [("revenue", 100_000_000)]:
            test_db.add(FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 12, 31),
                period_type="annual",
                scope="consolidated",
                unit="PKR",
                value=value,
                source_document_id=source_doc.id,
            ))

        test_db.commit()

        service = FinancialContextService(test_db)
        result = service.analyze(issuer.id)

        assert result is not None
        assert result.debt_to_equity is not None
        assert abs(result.debt_to_equity - 2.0) < 0.1  # 200M / 100M
        assert result.current_ratio is not None
        assert abs(result.current_ratio - 2.0) < 0.1  # 50M / 25M

    def test_analyze_earnings_quality(self, test_db, issuer_factory, source_doc_factory):
        """Should detect high-quality earnings (OCF > PAT)."""
        issuer = issuer_factory("QUALITY_CO")
        source_doc = source_doc_factory()

        facts = [
            ("profit_after_tax", 10_000_000),
            ("operating_cash_flow", 12_000_000),  # OCF > PAT = quality
        ]

        for metric, value in facts:
            test_db.add(FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
                period_type="annual",
                scope="consolidated",
                unit="PKR",
                value=value,
                source_document_id=source_doc.id,
            ))

        # Prior year
        test_db.add(FinancialFact(
            issuer_id=issuer.id,
            line_item="profit_after_tax",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            period_type="annual",
            scope="consolidated",
            unit="PKR",
            value=10_000_000,
            source_document_id=source_doc.id,
        ))

        test_db.commit()

        service = FinancialContextService(test_db)
        result = service.analyze(issuer.id)

        assert result is not None
        assert result.ocf_to_pat_ratio is not None
        assert result.ocf_to_pat_ratio > 1.0  # OCF exceeds PAT

    def test_insufficient_data(self, test_db, issuer_factory, source_doc_factory):
        """Should return None with insufficient data."""
        issuer = issuer_factory("EMPTY_CO")
        source_doc = source_doc_factory()

        # Only one period
        test_db.add(FinancialFact(
            issuer_id=issuer.id,
            line_item="revenue",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            period_type="annual",
            scope="consolidated",
            unit="PKR",
            value=100_000_000,
            source_document_id=source_doc.id,
        ))

        test_db.commit()

        service = FinancialContextService(test_db)
        result = service.analyze(issuer.id)

        # Should return None (need at least 2 periods for growth)
        assert result is None

    def test_no_data(self, test_db, issuer_factory):
        """Should return None with no data."""
        issuer = issuer_factory("NO_DATA_CO")

        service = FinancialContextService(test_db)
        result = service.analyze(issuer.id)

        assert result is None

    def test_zero_division_safety(self, test_db, issuer_factory, source_doc_factory):
        """Should handle zero-division gracefully."""
        issuer = issuer_factory("ZERO_DIV_CO")
        source_doc = source_doc_factory()

        facts = [
            ("revenue", 0),  # Zero revenue
            ("profit_after_tax", 0),
            ("total_equity", 0),  # Zero equity
        ]

        for metric, value in facts:
            test_db.add(FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
                period_type="annual",
                scope="consolidated",
                unit="PKR",
                value=value,
                source_document_id=source_doc.id,
            ))

        # Prior year with non-zero
        test_db.add(FinancialFact(
            issuer_id=issuer.id,
            line_item="revenue",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            period_type="annual",
            scope="consolidated",
            unit="PKR",
            value=100_000_000,
            source_document_id=source_doc.id,
        ))

        test_db.commit()

        service = FinancialContextService(test_db)
        result = service.analyze(issuer.id)

        # Should not crash; metrics with zero denominators should be None
        assert result is not None
        # ROE with zero equity should be None
        assert result.roe_pct is None


class TestIntegrationWithSnapshot:
    """Test financial metrics integration with SnapshotBuilder."""

    def test_snapshot_includes_financials(self, test_db, issuer_factory, source_doc_factory):
        """Financial metrics should integrate into snapshot."""
        from app.services.snapshot_builder import SnapshotBuilder
        from app.schemas.stock_snapshot import StockSnapshot, MarketData

        issuer = issuer_factory("SNAPSHOT_CO")
        source_doc = source_doc_factory()

        # Add financial facts
        facts_2024 = [
            ("revenue", 100_000_000),
            ("profit_after_tax", 10_000_000),
        ]
        for metric, value in facts_2024:
            test_db.add(FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 12, 31),
                period_type="annual",
                scope="consolidated",
                unit="PKR",
                value=value,
                source_document_id=source_doc.id,
            ))

        facts_2025 = [
            ("revenue", 120_000_000),
            ("profit_after_tax", 12_000_000),
        ]
        for metric, value in facts_2025:
            test_db.add(FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
                period_type="annual",
                scope="consolidated",
                unit="PKR",
                value=value,
                source_document_id=source_doc.id,
            ))

        test_db.commit()

        # Build snapshot with database
        builder = SnapshotBuilder(db=test_db)

        # Manually build to test
        market = MarketData(ticker="SNAPSHOT_CO", price=100)
        snapshot = StockSnapshot(ticker="SNAPSHOT_CO", market=market)

        # Add financial metrics
        service = FinancialContextService(test_db)
        snapshot.financials = service.analyze(issuer.id)

        # Should have financial data
        assert snapshot.financials is not None
        assert snapshot.financials.revenue_growth_pct is not None
        assert abs(snapshot.financials.revenue_growth_pct - 20.0) < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
