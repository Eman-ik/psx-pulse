"""Test suite for corrected data coverage calculations (Phase 1).

CRITICAL: These tests verify that:
1. Complete datasets achieve 100% coverage
2. Missing optional metrics reduce coverage proportionally
3. Immaterial changes still count as "available" (WhatChangedEngine)
4. No hard-coded ceilings prevent 100% coverage
5. Three metrics are properly separated
"""

import pytest
from datetime import datetime, date, timezone, time
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import (
    FinancialFact, Issuer, Security, SourceDocument, Sector,
    IngestionRun, PriceOHLCV
)
from app.analysis.evidence_context import ResearchContext


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def test_db():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def complete_financial_data(test_db: Session):
    """Create issuer with complete 8-comparison data (all 8 comparisons available)."""
    sector = Sector(name="Test Sector")
    test_db.add(sector)
    test_db.flush()

    issuer = Issuer(name="Complete Data Test", sector_id=sector.id)
    test_db.add(issuer)
    test_db.flush()

    source_doc = SourceDocument(
        document_type="financial_statement",
        url="http://example.com/financials.pdf",
        content_hash="test" * 15,
        fetched_at=datetime.now(timezone.utc),
        source_tier="primary",
    )
    test_db.add(source_doc)
    test_db.flush()

    ingest = IngestionRun(source="test", status="ok")
    test_db.add(ingest)
    test_db.flush()

    # Add all 8 required metrics for 2 periods (2024, 2025)
    for year in [2024, 2025]:
        period_end = date(year, 12, 31)
        period_start = date(year - 1, 12, 31)
        metrics = {
            "revenue": 100000000 + (year - 2024) * 5000000,
            "gross_profit": 25000000,
            "finance_cost": 5000000,
            "operating_cash_flow": 20000000,
            "accounts_receivable": 10000000,
            "inventory": 15000000,
            "dividend_per_share": 5.0,
            "total_debt": 50000000,
            "ebitda": 30000000,
        }
        for metric, value in metrics.items():
            fact = FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
                period_start=period_start,
                period_end=period_end,
                period_type="annual",
                scope="standalone",
                unit="PKR",
                value=value,
                source_document_id=source_doc.id,
                published_at=datetime.combine(period_end, time(10, 0), tzinfo=timezone.utc),
            )
            test_db.add(fact)
    test_db.commit()

    # Return context object
    return ResearchContext(test_db, issuer.id)


@pytest.fixture
def complete_evidence(test_db: Session):
    """Create issuer with all 6 earnings quality evidence items."""
    sector = Sector(name="Test Sector")
    test_db.add(sector)
    test_db.flush()

    issuer = Issuer(name="Evidence Test", sector_id=sector.id)
    test_db.add(issuer)
    test_db.flush()

    source_doc = SourceDocument(
        document_type="financial_statement",
        url="http://example.com/evidence.pdf",
        content_hash="test" * 15,
        fetched_at=datetime.now(timezone.utc),
        source_tier="primary",
    )
    test_db.add(source_doc)
    test_db.flush()

    # Add all 6 evidence items
    period_end = date(2025, 12, 31)
    period_start = date(2024, 12, 31)
    evidence_items = {
        "profit_after_tax": 50000000,
        "operating_cash_flow": 45000000,
        "operating_profit": 60000000,
        "other_income": 5000000,
        "finance_cost": 10000000,
        "revenue": 100000000,
    }
    for item, value in evidence_items.items():
        fact = FinancialFact(
            issuer_id=issuer.id,
            line_item=item,
            period_start=period_start,
            period_end=period_end,
            period_type="annual",
            scope="standalone",
            unit="PKR",
            value=value,
            source_document_id=source_doc.id,
            published_at=datetime.combine(period_end, time(10, 0), tzinfo=timezone.utc),
        )
        test_db.add(fact)
    test_db.commit()

    return ResearchContext(test_db, issuer.id)


# ============================================================================
# Phase 1 Tests
# ============================================================================

class TestWhatChangedEngineCorrectedLogic:
    """Verify WhatChangedEngine separates 'available' from 'material change'."""

    def test_all_eight_comparisons_available_equals_100_percent(self, complete_financial_data):
        """With complete data (all 8 comparisons possible), data_coverage = 100%."""
        from app.analysis.what_changed import WhatChangedEngine

        result = WhatChangedEngine.analyze(complete_financial_data)

        # Assertions
        assert result.get("data_coverage_pct") == 100, f"All 8 comparisons available = 100% coverage, got {result.get('data_coverage_pct')}%"
        assert result.get("comparisons_available") == 8, f"Should have 8 comparisons available, got {result.get('comparisons_available')}"


class TestEarningsQualityEngineTransparentCoverage:
    """Verify EarningsQualityEngine uses transparent coverage (no hard-coded 90% ceiling)."""

    def test_all_six_evidence_items_equals_100_percent(self, complete_evidence):
        """With all 6 evidence items, data_coverage = 100%, not hard-coded 90%."""
        from app.analysis.earnings_quality_v2 import EarningsQualityEngine

        result = EarningsQualityEngine.analyze(complete_evidence)

        assert result.get("data_coverage_pct") == 100, f"All 6 evidence items = 100% coverage, got {result.get('data_coverage_pct')}%"
        # Verify it's NOT the old hard-coded 90%
        assert result.get("data_coverage_pct") != 90, "Should NOT use hard-coded 90% ceiling"

    def test_partial_evidence_returns_proportional_coverage(self, test_db: Session):
        """With 3 of 6 evidence items, data_coverage = 50% (not hard-coded value)."""
        from app.analysis.earnings_quality_v2 import EarningsQualityEngine

        sector = Sector(name="Test")
        test_db.add(sector)
        test_db.flush()

        issuer = Issuer(name="Partial Evidence", sector_id=sector.id)
        test_db.add(issuer)
        test_db.flush()

        source_doc = SourceDocument(
            document_type="financial_statement",
            url="http://example.com/partial.pdf",
            content_hash="test" * 15,
            fetched_at=datetime.now(timezone.utc),
            source_tier="primary",
        )
        test_db.add(source_doc)
        test_db.flush()

        # Add only 3 of 6 evidence items
        period_end = date(2025, 12, 31)
        period_start = date(2024, 12, 31)
        for item in ["profit_after_tax", "operating_cash_flow", "revenue"]:
            fact = FinancialFact(
                issuer_id=issuer.id,
                line_item=item,
                period_start=period_start,
                period_end=period_end,
                period_type="annual",
                scope="standalone",
                unit="PKR",
                value=50000000,
                source_document_id=source_doc.id,
                published_at=datetime.combine(period_end, time(10, 0), tzinfo=timezone.utc),
            )
            test_db.add(fact)
        test_db.commit()

        context = ResearchContext(test_db, issuer.id)
        result = EarningsQualityEngine.analyze(context)

        # 3 of 6 = 50%
        assert result.get("data_coverage_pct") == 50, f"3 of 6 items = 50%, got {result.get('data_coverage_pct')}%"


class TestResearchOrchestratorThreeMetrics:
    """Verify ResearchOrchestrator returns three separate metrics."""

    def test_returns_three_separate_metrics(self, complete_evidence):
        """Output should have three separate metrics, not conflated into one."""
        from app.analysis.research_orchestrator import ResearchOrchestrator

        result = ResearchOrchestrator.analyze(complete_evidence.db, complete_evidence.issuer_id)

        # Assertions
        assert "data_coverage_pct" in result, "Should return data_coverage_pct"
        assert "evidence_quality" in result, "Should return evidence_quality"
        assert "analytical_confidence" in result, "Should return analytical_confidence"

        # Verify they are distinct values
        data_cov = result.get("data_coverage_pct")
        evidence_qual = result.get("evidence_quality")
        analytical_conf = result.get("analytical_confidence")

        assert isinstance(data_cov, int), "data_coverage_pct should be an integer (0-100)"
        assert evidence_qual in ["High", "Medium", "Low"], "evidence_quality should be categorical"
        assert analytical_conf in ["High", "Medium", "Low"], "analytical_confidence should be categorical"

    def test_backward_compatibility_deprecated_confidence_score(self, complete_evidence):
        """Old 'confidence_score' still exists for backward compatibility (deprecated)."""
        from app.analysis.research_orchestrator import ResearchOrchestrator

        result = ResearchOrchestrator.analyze(complete_evidence.db, complete_evidence.issuer_id)

        assert "confidence_score" in result, "Backward compatibility: should still have confidence_score"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
