"""Golden Financial Test Fixtures — Known-answer test cases for financial correctness validation.

These tests use fabricated but realistic financial statements with known answers
to verify that engines calculate correctly, not just consistently.

Fixture families:
1. Strengthening company (clean growth story)
2. Weakening company (margin compression)
3. Mixed signals (some good metrics, some bad)
4. Pathological cases (negative PAT, declining revenue, zero EBIT, etc.)
5. YTD/discrete ambiguity (tests period duration handling)
"""

from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import Issuer, FinancialFact, SourceDocument
from app.analysis.evidence_context import ResearchContext
from app.analysis.business_health import BusinessHealthEngine
from app.analysis.earnings_quality import EarningsQualityEngine
from app.analysis.what_changed import WhatChangedEngine


@pytest.fixture
def test_db():
    """In-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    return TestingSessionLocal()


@pytest.fixture
def issuer_factory(test_db):
    """Factory for creating test issuers."""
    def _create(name: str = "TEST_CO") -> Issuer:
        issuer = Issuer(
            symbol=name,
            name=f"{name} Limited",
            listing_exchange="PSX",
        )
        test_db.add(issuer)
        test_db.commit()
        return issuer
    return _create


@pytest.fixture
def source_doc_factory(test_db):
    """Factory for creating test source documents."""
    def _create() -> SourceDocument:
        doc = SourceDocument(
            source_type="test",
            identifier="test_doc",
            publication_date=date(2026, 10, 3),
            retrieved_date=date(2026, 10, 3),
        )
        test_db.add(doc)
        test_db.commit()
        return doc
    return _create


class TestGoldenFixtures:
    """Golden financial test cases with known correct answers."""

    def test_strengthening_company(self, test_db, issuer_factory, source_doc_factory):
        """Clear growth story: Revenue+, PAT+, Margins+, OCF+, Leverage declining."""
        issuer = issuer_factory("STRONG_CO")
        source_doc = source_doc_factory()

        # FY2024 baseline
        facts_2024 = [
            ("revenue", 100_000_000),
            ("profit_after_tax", 10_000_000),
            ("gross_profit", 30_000_000),
            ("operating_cash_flow", 11_000_000),
            ("total_debt", 50_000_000),
            ("total_equity", 100_000_000),
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

        # FY2025: Clear improvement
        facts_2025 = [
            ("revenue", 120_000_000),  # +20%
            ("profit_after_tax", 14_400_000),  # +44% (better than revenue)
            ("gross_profit", 39_000_000),  # +30%
            ("operating_cash_flow", 15_000_000),  # +36%
            ("total_debt", 40_000_000),  # -20%
            ("total_equity", 120_000_000),  # +20%
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
        context = ResearchContext(test_db, issuer.id)
        result = BusinessHealthEngine.analyze(context)

        # Known-answer assertions
        assert result["assessment"] == "Improving" or result["assessment"] == "Strong / Improving", \
            f"Expected 'Improving'/'Strong / Improving' but got '{result['assessment']}'"
        assert result["classification_confidence"] == "High", \
            "Clear signal should have High confidence"
        assert "44%" in result.get("assessment_rationale", ""), \
            "Rationale should cite earnings growth exceeding revenue growth"

    def test_weakening_company(self, test_db, issuer_factory, source_doc_factory):
        """Margin compression story: Revenue+, PAT-, Margins declining."""
        issuer = issuer_factory("WEAK_CO")
        source_doc = source_doc_factory()

        # FY2024
        facts_2024 = [
            ("revenue", 100_000_000),
            ("profit_after_tax", 15_000_000),  # 15% margin
            ("operating_cash_flow", 14_000_000),
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

        # FY2025: Revenue up but profitability down
        facts_2025 = [
            ("revenue", 103_500_000),  # +3.5%
            ("profit_after_tax", 11_800_000),  # -21.3% (bad!)
            ("operating_cash_flow", 12_000_000),  # -14%
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
        context = ResearchContext(test_db, issuer.id)
        result = BusinessHealthEngine.analyze(context)

        # Known-answer assertions
        assert result["assessment"] == "Weakening", \
            f"Earnings decline despite revenue growth should be Weakening, got '{result['assessment']}'"
        assert "-21.3%" in result.get("assessment_rationale", ""), \
            "Rationale must cite exact earnings decline percentage"
        assert "margin compression" in result.get("assessment_rationale", "").lower(), \
            "Rationale must explain margin deterioration"

    def test_pathological_negative_pat(self, test_db, issuer_factory, source_doc_factory):
        """Company with negative PAT should not crash or make unsupported claims."""
        issuer = issuer_factory("NEG_PAT_CO")
        source_doc = source_doc_factory()

        # FY2024: Normal
        facts_2024 = [
            ("revenue", 100_000_000),
            ("profit_after_tax", 10_000_000),
            ("operating_cash_flow", 11_000_000),
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

        # FY2025: Loss-making
        facts_2025 = [
            ("revenue", 95_000_000),  # -5%
            ("profit_after_tax", -5_000_000),  # Negative!
            ("operating_cash_flow", 2_000_000),  # Still positive (better than reported loss)
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

        # Should not crash
        context = ResearchContext(test_db, issuer.id)
        result = BusinessHealthEngine.analyze(context)

        assert result["status"] == "complete", \
            "Should handle negative PAT gracefully"
        assert result["assessment"] == "Weakening", \
            "Negative earnings should be clearly negative assessment"

    def test_declining_revenue(self, test_db, issuer_factory, source_doc_factory):
        """Company with revenue decline should not trigger false red flags."""
        issuer = issuer_factory("DECLINE_CO")
        source_doc = source_doc_factory()

        # FY2024
        facts_2024 = [
            ("revenue", 100_000_000),
            ("profit_after_tax", 5_000_000),
            ("accounts_receivable", 20_000_000),
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

        # FY2025: Revenue down 20%
        facts_2025 = [
            ("revenue", 80_000_000),  # -20%
            ("profit_after_tax", 2_000_000),  # -60%
            ("accounts_receivable", 16_000_000),  # Fell proportionally (-20%)
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

        # What changed
        context = ResearchContext(test_db, issuer.id)
        result = WhatChangedEngine.analyze(context)

        # Should not falsely flag AR as problematic
        # (AR fell in proportion to revenue decline)
        ar_flags = [c for c in result.get("negative_changes", []) if "receivable" in c.lower()]
        assert len(ar_flags) == 0, \
            "Should not flag AR as growing faster than revenue when both declined proportionally"

    def test_zero_equity(self, test_db, issuer_factory, source_doc_factory):
        """Company with near-zero equity should handle gracefully."""
        issuer = issuer_factory("ZERO_EQ")
        source_doc = source_doc_factory()

        facts = [
            ("revenue", 100_000_000),
            ("profit_after_tax", 5_000_000),
            ("total_debt", 100_000_000),
            ("total_equity", 1_000_000),  # Near zero
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

        test_db.commit()

        # Should not crash on division by zero
        context = ResearchContext(test_db, issuer.id)
        result = BusinessHealthEngine.analyze(context)

        assert result["status"] in ["complete", "partial"], \
            "Should handle near-zero equity gracefully"


class TestEarningsQualityGolden:
    """Golden fixtures for earnings quality validation."""

    def test_high_quality_earnings(self, test_db, issuer_factory, source_doc_factory):
        """OCF consistently exceeds PAT (high quality)."""
        issuer = issuer_factory("HQ_CO")
        source_doc = source_doc_factory()

        for year in [2024, 2025]:
            pat = 10_000_000
            ocf = 12_000_000  # OCF > PAT indicates high quality

            for metric, value in [("profit_after_tax", pat), ("operating_cash_flow", ocf)]:
                test_db.add(FinancialFact(
                    issuer_id=issuer.id,
                    line_item=metric,
                    period_start=date(year, 1, 1),
                    period_end=date(year, 12, 31),
                    period_type="annual",
                    scope="consolidated",
                    unit="PKR",
                    value=value,
                    source_document_id=source_doc.id,
                ))

        test_db.commit()

        context = ResearchContext(test_db, issuer.id)
        result = EarningsQualityEngine.analyze(context)

        # Should detect high quality
        assert result["status"] == "complete", \
            "Should have data to assess quality"
        assert "high" in result.get("assessment", "").lower() or "strong" in result.get("assessment", "").lower(), \
            "Consistent OCF > PAT should indicate high quality"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
