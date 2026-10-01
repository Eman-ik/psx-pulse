"""Sprint 2: Load sample LUCK data into database.

Demonstrates extraction pipeline in action:
1. Setup LUCK company and periods
2. Create data source record
3. Load sample financial facts
4. Validate and store in database

Usage:
    python -c "from app.etl.load_sample_luck import load_sample_luck_data; load_sample_luck_data()"
"""
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Source
from app.etl.lucky_cement_setup import setup_lucky_cement_data
from app.etl.extraction_pipeline import ExtractionPipeline
from app.etl.sample_luck_data import get_sample_data_by_year


def load_sample_luck_data(db: Session = None) -> dict:
    """Load sample LUCK financial data into database.

    Returns: {
        'company': Company,
        'periods': {period_type: {fiscal_year: Period}},
        'sources': {fiscal_year: Source},
        'results': {fiscal_year: pipeline_result}
    }
    """
    if db is None:
        db = SessionLocal()

    # Setup LUCK company and periods
    print("Creating LUCK company and periods...")
    luck_data = setup_lucky_cement_data(db)
    company = luck_data["company"]
    periods = luck_data["periods"]
    print(f"[OK] Created company: {company.ticker} - {company.name}")
    print(f"[OK] Created {len(periods['annual'])} annual periods + {len(periods['quarterly'])} quarterly periods")

    # Load data for each fiscal year
    sources = {}
    results = {}

    for fiscal_year in [2024, 2025, 2026]:
        print(f"\nLoading FY{fiscal_year} data...")

        # Create source record
        source = Source(
            company_id=company.id,
            source_type="annual_report",
            title=f"Lucky Cement Limited - Annual Report FY{fiscal_year}",
            document_type="annual_report",
            document_date=None,  # Real date would be 31-Mar-FY
            status="pending",
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        sources[fiscal_year] = source
        print(f"[OK] Created source: {source.title} (ID: {source.id})")

        # Get sample facts for this year
        raw_facts = get_sample_data_by_year(fiscal_year)
        print(f"  Extracted {len(raw_facts)} raw facts from annual report")

        # Process through pipeline
        period = periods["annual"][fiscal_year]
        result = ExtractionPipeline.process_raw_facts(
            db, company.id, period.id, source.id, raw_facts
        )
        results[fiscal_year] = result

        # Report results
        stats = result["stats"]
        print(f"  Pipeline results:")
        print(f"    [OK] Stored: {stats['stored']}")
        print(f"    [WARN] Flagged: {stats['flagged']}")
        print(f"    [ERR] Skipped: {stats['skipped']}")

        if stats["flagged"] > 0:
            print(f"  Flagged items (require manual review):")
            for item in result["flagged"]:
                print(f"    - {item['fact'].metric}: {item['reason']}")

        if stats["skipped"] > 0:
            print(f"  Skipped items (errors):")
            for item in result["skipped"]:
                print(f"    - {item['raw_fact'].metric}: {item['error']}")

    # Update company coverage tier
    company.coverage_tier = "full"
    db.commit()
    print(f"\n[OK] Updated company coverage tier to 'full'")

    # Summary
    print("\n" + "=" * 60)
    print("LOAD SUMMARY")
    print("=" * 60)
    total_stored = sum(r["stats"]["stored"] for r in results.values())
    total_flagged = sum(r["stats"]["flagged"] for r in results.values())
    total_skipped = sum(r["stats"]["skipped"] for r in results.values())

    print(f"Company: {company.ticker} ({company.name})")
    print(f"Total financial facts loaded:")
    print(f"  [OK] Stored (validated): {total_stored}")
    print(f"  [WARN] Flagged (review): {total_flagged}")
    print(f"  [ERR] Skipped (errors): {total_skipped}")
    print(f"  Total: {total_stored + total_flagged + total_skipped}")
    print("\nNext steps:")
    print("  1. Review flagged items for data quality")
    print("  2. Verify extracted values match source PDFs")
    print("  3. Calculate derived metrics (ROE, FCF, margins, etc)")
    print("  4. Generate peer comparison and insights")

    return {
        "company": company,
        "periods": periods,
        "sources": sources,
        "results": results,
    }


if __name__ == "__main__":
    db = SessionLocal()
    try:
        result = load_sample_luck_data(db)
        print("\nData load complete!")
    finally:
        db.close()
