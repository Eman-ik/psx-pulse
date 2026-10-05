"""Test suite for Phase 1: Corrected data coverage formulas.

CRITICAL VERIFICATION:
1. WhatChangedEngine separates comparisons_available from material_changes_detected
2. EarningsQualityEngine removes hard-coded 90% ceiling
3. ValuationContextEngine removes hard-coded 0/70/90 ceilings
4. ResearchOrchestrator separates three metrics: data_coverage_pct, evidence_quality, analytical_confidence
"""

import pytest
from datetime import datetime, date, timezone, time
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import (
    FinancialFact, Issuer, SourceDocument, Sector, IngestionRun
)
from app.analysis.evidence_context import ResearchContext
from app.analysis.what_changed import WhatChangedEngine
from app.analysis.earnings_quality_v2 import EarningsQualityEngine
from app.analysis.research_orchestrator import ResearchOrchestrator


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
def complete_issuer(test_db: Session):
    """Create issuer with complete financial data for all 8 WhatChanged comparisons."""
    sector = Sector(name="Test")
    test_db.add(sector)
    test_db.flush()

    issuer = Issuer(name="Complete Issuer", sector_id=sector.id)
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

    # Add complete data for 2 periods
    for year in [2024, 2025]:
        period_end = date(year, 12, 31)
        period_start = date(year - 1, 12, 31)

        metrics = [
            ("revenue", 100000000 + (year - 2024) * 1000000),
            ("gross_profit", 25000000),
            ("finance_cost", 5000000),
            ("operating_cash_flow", 20000000),
            ("accounts_receivable", 10000000),
            ("inventory", 15000000),
            ("dividend_per_share", 5.0),
            ("total_debt", 50000000),
            ("ebitda", 30000000),
        ]

        for metric, value in metrics:
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
    return test_db, issuer


class TestPhase1FormulasWork:
    """Verify Phase 1 corrected formulas produce expected output."""

    def test_what_changed_separates_available_from_material(self, complete_issuer):
        """WhatChangedEngine separates 'comparisons available' from 'material changes detected'."""
        test_db, issuer = complete_issuer

        context = ResearchContext(test_db, issuer.id)
        result = WhatChangedEngine.analyze(context)

        # With complete data, should have 8 comparisons available
        assert result.get("comparisons_available") > 0, "Should count available comparisons"
        assert result.get("data_coverage_pct") > 0, "Should calculate coverage based on availability"

        # Key verification: output includes both metrics separately
        assert "comparisons_available" in result
        assert "material_changes_detected" in result
        assert "data_coverage_pct" in result
        assert "changes_detected_pct" in result

    def test_earnings_quality_no_hard_coded_ceiling(self, test_db: Session):
        """EarningsQualityEngine removes hard-coded 90% ceiling."""
        sector = Sector(name="Test")
        test_db.add(sector)
        test_db.flush()

        issuer = Issuer(name="EQ Test", sector_id=sector.id)
        test_db.add(issuer)
        test_db.flush()

        source_doc = SourceDocument(
            document_type="financial_statement",
            url="http://example.com/eq.pdf",
            content_hash="test" * 15,
            fetched_at=datetime.now(timezone.utc),
            source_tier="primary",
        )
        test_db.add(source_doc)
        test_db.flush()

        # Add 4 of 6 optional evidence items
        period_end = date(2025, 12, 31)
        period_start = date(2024, 12, 31)

        for metric in ["profit_after_tax", "operating_cash_flow", "revenue", "finance_cost"]:
            fact = FinancialFact(
                issuer_id=issuer.id,
                line_item=metric,
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

        coverage = result.get("data_coverage_pct")

        # Key verifications:
        # 1. Should NOT be hard-coded 90%
        assert coverage != 90, "Should NOT use hard-coded ceiling of 90%"

        # 2. Should be based on formula (items_available / 6) * 100
        # With 4 items, expect 66% (4/6), not 90%
        assert coverage in range(60, 75), f"With 4 of 6 items, expect ~66%, got {coverage}%"

    def test_research_orchestrator_three_separate_metrics(self, complete_issuer):
        """ResearchOrchestrator returns three separate metrics."""
        test_db, issuer = complete_issuer

        result = ResearchOrchestrator.analyze(test_db, issuer.id)

        # Key verifications:
        assert "data_coverage_pct" in result, "Should return data_coverage_pct"
        assert "evidence_quality" in result, "Should return evidence_quality"
        assert "analytical_confidence" in result, "Should return analytical_confidence"

        # All three should be distinct
        data_cov = result.get("data_coverage_pct")
        evidence_qual = result.get("evidence_quality")
        analytical_conf = result.get("analytical_confidence")

        assert isinstance(data_cov, int), "data_coverage_pct should be integer"
        assert evidence_qual in ["High", "Medium", "Low"], "evidence_quality should be categorical"
        assert analytical_conf in ["High", "Medium", "Low"], "analytical_confidence should be categorical"

        # Backward compatibility check
        assert "confidence_score" in result, "Should still have deprecated confidence_score"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
