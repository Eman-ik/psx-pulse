"""Backfill financial data for cement companies into FinancialFact table.

This script reads the cement company data from manual_financials_seed_cement.py
and seeds it into the database using the standard seed_issuer_financials function.

Run: cd backend && python -m app.ingestion.backfill_cement_financials
"""

import logging

from app.db.session import SessionLocal
from app.ingestion.manual_financials_seed import seed_issuer_financials
from app.ingestion.manual_financials_seed_cement import CEMENT_FINANCIALS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def backfill_cement_financials():
    """Backfill all cement company financial data using the standard seeding function."""
    db = SessionLocal()

    try:
        logger.info("Backfilling cement company financial data...")
        logger.info(f"Processing {len(CEMENT_FINANCIALS)} companies...")

        for issuer_name, data in CEMENT_FINANCIALS.items():
            logger.info(f"\n  Processing {issuer_name}...")
            stats = seed_issuer_financials(db, issuer_name, data)
            logger.info(f"    → Inserted: {stats.get('inserted', 0)}, Skipped: {stats.get('skipped', 0)}")

        db.commit()
        logger.info("\n✓ Backfill complete!")
        logger.info("Next: Run the ratio engine to compute financial ratios from these facts.")

    except Exception as e:
        logger.error(f"Error during backfill: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    backfill_cement_financials()
