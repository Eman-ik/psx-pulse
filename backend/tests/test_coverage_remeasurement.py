"""Re-measure actual FFC/EFERT coverage with Phase 1 corrected formulas.

This test runs the corrected orchestrator on real data from the database
and reports the actual coverage numbers to verify the semantic fixes work.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Issuer
from app.analysis.evidence_context import ResearchContext
from app.analysis.research_orchestrator import ResearchOrchestrator


@pytest.mark.requires_seeded_data
class TestCoverageRemeasurement:
    """Measure actual coverage with corrected formulas."""

    def test_ffc_coverage_with_corrected_formulas(self, db: Session):
        """Measure FFC coverage using corrected Phase 1 formulas."""
        # Get FFC from database
        ffc_stmt = select(Issuer).where(Issuer.name.like("%Fauji%"))
        ffc = db.execute(ffc_stmt).scalars().first()

        if not ffc:
            pytest.skip("FFC not found in database")

        print(f"\n{'='*70}")
        print(f"COVERAGE RE-MEASUREMENT: FFC (issuer_id={ffc.id})")
        print(f"{'='*70}")

        # Run corrected orchestrator
        result = ResearchOrchestrator.analyze(db, ffc.id)

        # Report composite coverage
        composite_coverage = result.get("data_coverage_pct")
        evidence_quality = result.get("evidence_quality")
        analytical_conf = result.get("analytical_confidence")

        print(f"\nCOMPOSITE COVERAGE (after Phase 1 formula fixes):")
        print(f"  Data Coverage:       {composite_coverage}%")
        print(f"  Evidence Quality:    {evidence_quality}")
        print(f"  Analysis Confidence: {analytical_conf}")

        # Per-engine breakdown
        print(f"\nPER-ENGINE BREAKDOWN:")
        for engine in ["business_health", "what_changed", "earnings_quality", "valuation_context"]:
            engine_data = result.get(engine, {})
            coverage = engine_data.get("data_coverage_pct", "N/A")
            confidence = engine_data.get("confidence", engine_data.get("classification_confidence", "N/A"))
            print(f"  {engine:25} {coverage:>3}% (confidence: {confidence})")

        # Assertions: verify no hard-coded ceilings
        assert composite_coverage is not None, "Should calculate coverage"
        assert 0 <= composite_coverage <= 100, "Coverage should be 0-100%"
        assert composite_coverage != 90, "Should NOT have hard-coded 90% ceiling"
        assert evidence_quality in ["High", "Medium", "Low"], "Evidence quality should be categorical"
        assert analytical_conf in ["High", "Medium", "Low"], "Analytical confidence should be categorical"

    def test_efert_coverage_with_corrected_formulas(self, db: Session):
        """Measure EFERT coverage using corrected Phase 1 formulas."""
        # Get EFERT from database
        efert_stmt = select(Issuer).where(Issuer.name.like("%Engro%"))
        efert = db.execute(efert_stmt).scalars().first()

        if not efert:
            pytest.skip("EFERT not found in database")

        print(f"\n{'='*70}")
        print(f"COVERAGE RE-MEASUREMENT: EFERT (issuer_id={efert.id})")
        print(f"{'='*70}")

        # Run corrected orchestrator
        result = ResearchOrchestrator.analyze(db, efert.id)

        # Report composite coverage
        composite_coverage = result.get("data_coverage_pct")
        evidence_quality = result.get("evidence_quality")
        analytical_conf = result.get("analytical_confidence")

        print(f"\nCOMPOSITE COVERAGE (after Phase 1 formula fixes):")
        print(f"  Data Coverage:       {composite_coverage}%")
        print(f"  Evidence Quality:    {evidence_quality}")
        print(f"  Analysis Confidence: {analytical_conf}")

        # Per-engine breakdown
        print(f"\nPER-ENGINE BREAKDOWN:")
        for engine in ["business_health", "what_changed", "earnings_quality", "valuation_context"]:
            engine_data = result.get(engine, {})
            coverage = engine_data.get("data_coverage_pct", "N/A")
            confidence = engine_data.get("confidence", engine_data.get("classification_confidence", "N/A"))
            print(f"  {engine:25} {coverage:>3}% (confidence: {confidence})")

        # Assertions: verify no hard-coded ceilings
        assert composite_coverage is not None, "Should calculate coverage"
        assert 0 <= composite_coverage <= 100, "Coverage should be 0-100%"
        assert composite_coverage != 90, "Should NOT have hard-coded 90% ceiling"
        assert evidence_quality in ["High", "Medium", "Low"], "Evidence quality should be categorical"
        assert analytical_conf in ["High", "Medium", "Low"], "Analytical confidence should be categorical"

    def test_available_metrics_in_database(self, db: Session):
        """Identify which financial metrics are available for FFC and EFERT."""
        from app.db.models import FinancialFact

        print(f"\n{'='*70}")
        print(f"AVAILABLE METRICS IN DATABASE")
        print(f"{'='*70}")

        # Get FFC
        ffc_stmt = select(Issuer).where(Issuer.name.like("%Fauji%"))
        ffc = db.execute(ffc_stmt).scalars().first()

        if ffc:
            print(f"\nFFC (issuer_id={ffc.id}):")
            metrics_stmt = select(FinancialFact.line_item.distinct()).where(
                FinancialFact.issuer_id == ffc.id
            )
            metrics = sorted(db.execute(metrics_stmt).scalars().all())
            for metric in metrics:
                count_stmt = select(FinancialFact).where(
                    FinancialFact.issuer_id == ffc.id,
                    FinancialFact.line_item == metric
                )
                count = len(db.execute(count_stmt).scalars().all())
                print(f"  {metric:30} {count} periods")

        # Get EFERT
        efert_stmt = select(Issuer).where(Issuer.name.like("%Engro%"))
        efert = db.execute(efert_stmt).scalars().first()

        if efert:
            print(f"\nEFERT (issuer_id={efert.id}):")
            metrics_stmt = select(FinancialFact.line_item.distinct()).where(
                FinancialFact.issuer_id == efert.id
            )
            metrics = sorted(db.execute(metrics_stmt).scalars().all())
            for metric in metrics:
                count_stmt = select(FinancialFact).where(
                    FinancialFact.issuer_id == efert.id,
                    FinancialFact.line_item == metric
                )
                count = len(db.execute(count_stmt).scalars().all())
                print(f"  {metric:30} {count} periods")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
