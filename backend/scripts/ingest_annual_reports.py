#!/usr/bin/env python3
"""Complete annual report ingestion workflow.

PHASES:
1. Discovery: Find official annual report URLs
2. Extraction: Download PDFs and extract canonical metrics
3. Validation: Re-measure coverage with new data
4. Report: Show metrics extracted and coverage improvements
"""

import sys
import os
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.ingestion.annual_report_discovery import discover_all_reports
from app.ingestion.annual_report_extraction import extract_and_ingest_reports
from app.analysis.research_orchestrator import ResearchOrchestrator
from sqlalchemy import select
from app.db.models import Issuer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("\n" + "=" * 70)
    print("ANNUAL REPORT INGESTION WORKFLOW")
    print("=" * 70)

    # PHASE 1: Discovery
    print("\n[PHASE 1] Discovering official annual report URLs...")
    reports = discover_all_reports()

    if not any(reports.values()):
        print("ERROR: No reports discovered. Check network and official sources.")
        return False

    # PHASE 2: Extraction
    print("\n[PHASE 2] Extracting metrics from annual reports...")
    with SessionLocal() as db:
        extraction_summary = extract_and_ingest_reports(db, reports)

    print("\nExtraction Summary:")
    for company, years in extraction_summary.items():
        print(f"\n{company}:")
        for year in sorted(years.keys()):
            result = years[year]
            if "error" in result:
                print(f"  FY{year}: ERROR - {result['error']}")
            else:
                print(f"  FY{year}: Extracted {result['extracted']} metrics - {result.get('metrics', [])}")

    # PHASE 3: Validation - Re-measure coverage
    print("\n[PHASE 3] Re-measuring coverage with new data...")
    print("\n" + "=" * 70)
    print("COVERAGE RE-MEASUREMENT (After Ingestion)")
    print("=" * 70)

    with SessionLocal() as db:
        for ticker_pattern, symbol in [("Fauji", "FFC"), ("Engro", "EFERT")]:
            issuer = db.execute(
                select(Issuer).where(Issuer.name.ilike(f"%{ticker_pattern}%"))
            ).scalars().first()

            if not issuer:
                print(f"\n{symbol}: NOT FOUND")
                continue

            print(f"\n{'=' * 70}")
            print(f"{symbol} - {issuer.name}")
            print(f"{'=' * 70}")

            result = ResearchOrchestrator.analyze(db, issuer.id)

            composite = result.get("data_coverage_pct", 0)
            evidence = result.get("evidence_quality", "Unknown")
            confidence = result.get("analytical_confidence", "Unknown")

            print(f"\nComposite Coverage: {composite}%")
            print(f"Evidence Quality:  {evidence}")
            print(f"Confidence:        {confidence}")

            print(f"\nPer-Engine Breakdown:")
            for engine in ["business_health", "what_changed", "earnings_quality", "valuation_context"]:
                engine_data = result.get(engine, {})
                cov = engine_data.get("data_coverage_pct", "N/A")
                conf = engine_data.get("confidence", engine_data.get("classification_confidence", "N/A"))
                print(f"  {engine:25} {cov:>3}% (confidence: {conf})")

            # Available metrics
            from app.db.models import FinancialFact
            metrics = db.execute(
                select(FinancialFact.line_item.distinct()).where(
                    FinancialFact.issuer_id == issuer.id
                )
            ).scalars().all()

            print(f"\nAvailable Metrics ({len(metrics)} total):")
            for metric in sorted(metrics):
                count = len(
                    db.execute(
                        select(FinancialFact).where(
                            FinancialFact.issuer_id == issuer.id,
                            FinancialFact.line_item == metric,
                        )
                    ).scalars().all()
                )
                print(f"  {metric:30} {count} periods")

    print("\n" + "=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review extracted metrics for accuracy")
    print("2. Check coverage improvements above")
    print("3. If metrics are missing, update extraction aliases in annual_report_extraction.py")
    print("4. For valuation data, integrate with stock price API (Phase 3)")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
