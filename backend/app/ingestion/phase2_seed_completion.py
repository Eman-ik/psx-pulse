"""Phase 2: Complete the seed ingestion with missing metrics.

KEY DISCOVERY: The seed data ALREADY DEFINES all missing metrics!
- FFC: 14 metrics defined in seed, only 5 in database
- EFERT: 10 metrics defined in seed, only 5 in database

This script completes the ingestion of already-prepared seed data,
rather than requiring new data extraction from annual reports.

Missing metrics from FFC (already in seed):
- gross_profit (2020-2023)
- finance_cost (2020-2023)
- inventory (2020-2023)
- accounts_receivable equivalent: trade_debts (2020-2023)
- cost_of_sales (2020-2023)
- current_assets (2020-2023)
- current_liabilities (2020-2023)
- short_term_investments (2020-2023)
- total_liabilities (2020-2023)

Missing metrics from EFERT (already in seed):
- inventory (2023-2025)
- cost_of_sales (2023-2025)
- current_assets (2024-2025)
- current_liabilities (2024-2025)

NOT in seed (truly missing):
- operating_profit / EBIT
- other_income
- tax_expense
- dividend_per_share
- ebitda
- eps (except FATIMA)
"""

from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Issuer, SourceDocument, FinancialFact
from app.ingestion.manual_financials_seed import FFC_DATA, EFERT_DATA, seed_issuer_financials


def ingest_phase2_seed_completion(db: Session) -> dict:
    """Complete seed ingestion by loading all defined metrics.

    The seed data has been prepared with full financial statements,
    but only a subset was loaded into the database. This completes it.

    Returns:
        Summary of ingestion results
    """
    results = {}

    # Ingest FFC with full seed data
    print("Phase 2: Completing FFC ingestion...")
    ffc_result = seed_issuer_financials(db, "Fauji Fertilizer Company Limited", FFC_DATA)
    results["FFC"] = ffc_result
    print(f"  FFC: {ffc_result}")

    # Ingest EFERT with full seed data
    print("Phase 2: Completing EFERT ingestion...")
    efert_result = seed_issuer_financials(db, "Engro Fertilizers Limited", EFERT_DATA)
    results["EFERT"] = efert_result
    print(f"  EFERT: {efert_result}")

    return results


if __name__ == "__main__":
    from app.db.session import SessionLocal
    import logging

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        results = ingest_phase2_seed_completion(session)
        print("\n" + "="*70)
        print("PHASE 2 SEED COMPLETION SUMMARY")
        print("="*70)
        for issuer, result in results.items():
            print(f"\n{issuer}:")
            print(f"  Inserted: {result['inserted']}")
            print(f"  Skipped:  {result['skipped']}")
            print(f"  Superseded: {result.get('superseded', 0)}")
