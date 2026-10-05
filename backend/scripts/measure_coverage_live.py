#!/usr/bin/env python3
"""Direct coverage measurement script (bypasses pytest, uses app DB directly)."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Issuer, FinancialFact
from app.analysis.research_orchestrator import ResearchOrchestrator


def main():
    db = SessionLocal()

    print("\n" + "="*70)
    print("PHASE 1 COVERAGE RE-MEASUREMENT (Live Database)")
    print("="*70)

    # Find FFC and EFERT
    for ticker_pattern in ["Fauji", "Engro"]:
        issuer_stmt = select(Issuer).where(Issuer.name.ilike(f"%{ticker_pattern}%"))
        issuer = db.execute(issuer_stmt).scalars().first()

        if not issuer:
            print(f"\n{ticker_pattern}: NOT FOUND in database")
            continue

        print(f"\n{'='*70}")
        print(f"COVERAGE: {issuer.name} (ID={issuer.id})")
        print(f"{'='*70}")

        # Run orchestrator
        try:
            result = ResearchOrchestrator.analyze(db, issuer.id)

            # Composite metrics
            composite = result.get("data_coverage_pct")
            evidence = result.get("evidence_quality")
            confidence = result.get("analytical_confidence")

            print(f"\nCOMPOSITE COVERAGE:")
            print(f"  Data Coverage:       {composite}%")
            print(f"  Evidence Quality:    {evidence}")
            print(f"  Analysis Confidence: {confidence}")

            # Per-engine
            print(f"\nPER-ENGINE BREAKDOWN:")
            for engine in ["business_health", "what_changed", "earnings_quality", "valuation_context"]:
                engine_data = result.get(engine, {})
                cov = engine_data.get("data_coverage_pct", "N/A")
                conf = engine_data.get("confidence") or engine_data.get("classification_confidence", "N/A")
                print(f"  {engine:25} {cov:>3}% (confidence: {conf})")

            # Available metrics
            print(f"\nAVAILABLE FINANCIAL INPUTS:")
            metrics_stmt = select(FinancialFact.line_item.distinct()).where(
                FinancialFact.issuer_id == issuer.id
            )
            metrics = sorted(db.execute(metrics_stmt).scalars().all())

            for metric in metrics:
                count_stmt = select(FinancialFact).where(
                    FinancialFact.issuer_id == issuer.id,
                    FinancialFact.line_item == metric
                )
                count = len(db.execute(count_stmt).scalars().all())
                print(f"  {metric:30} {count} periods")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    db.close()

    print("\n" + "="*70)
    print("MEASUREMENT COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
