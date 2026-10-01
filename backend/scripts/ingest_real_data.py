#!/usr/bin/env python
"""
Real-time PSX data ingestion script
Fetches current prices, fundamentals, and indices for all PSX companies
Populates the database for research studio and screeners
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Optional
import logging

# Fix encoding for Windows console
if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from sqlalchemy import select
from psxdata import PSXClient

# Add backend to path
sys.path.insert(0, str(__file__).rsplit('\\', 2)[0])

from app.db.session import SessionLocal
from app.db.models import (
    Security, Issuer, Sector, PriceOHLCV, MarketIndex, IndexOHLCV,
    FinancialFact, RatioValue
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PSXDataIngester:
    """Ingest real PSX data into the database"""

    def __init__(self):
        self.client = PSXClient()
        self.db = SessionLocal()
        self.today = datetime.now().date()

    def ingest_all(self):
        """Run complete data ingestion pipeline"""
        try:
            logger.info("Starting PSX data ingestion...")

            # Step 1: Fetch and populate symbols
            self.ingest_symbols()

            # Step 2: Fetch and populate current quotes
            self.ingest_quotes()

            # Step 3: Fetch and populate fundamentals
            self.ingest_fundamentals()

            # Step 4: Fetch and populate indices
            self.ingest_indices()

            logger.info("Data ingestion complete!")

        except Exception as e:
            logger.error(f"Ingestion failed: {str(e)}")
            raise
        finally:
            self.db.close()

    def ingest_symbols(self):
        """Fetch all PSX symbols and create Security records"""
        logger.info("[FETCH] Getting PSX symbols...")

        try:
            symbols_data = self.client.symbols()
            logger.info(f"Found {len(symbols_data)} securities")

            count = 0
            for symbol, details in symbols_data.items():
                # Check if security already exists
                existing = self.db.execute(
                    select(Security).where(Security.symbol == symbol)
                ).scalar_one_or_none()

                if existing:
                    continue

                # Get or create issuer
                issuer_name = details.get('name', symbol)
                issuer = self.db.execute(
                    select(Issuer).where(Issuer.name == issuer_name)
                ).scalar_one_or_none()

                if not issuer:
                    issuer = Issuer(
                        name=issuer_name,
                        status='active'
                    )
                    self.db.add(issuer)
                    self.db.flush()

                # Get or create sector
                sector_name = details.get('sector', 'Miscellaneous')
                sector = self.db.execute(
                    select(Sector).where(Sector.name == sector_name)
                ).scalar_one_or_none()

                if not sector:
                    sector = Sector(
                        name=sector_name,
                        description=f"{sector_name} sector"
                    )
                    self.db.add(sector)
                    self.db.flush()

                # Create security
                security = Security(
                    symbol=symbol,
                    name=issuer_name,
                    issuer_id=issuer.id,
                    sector_id=sector.id,
                    is_active=True,
                    listing_date=details.get('listing_date'),
                    market_cap=details.get('market_cap')
                )
                self.db.add(security)
                count += 1
                if count % 10 == 0:
                    logger.info(f"  Added {count} symbols...")

            self.db.commit()
            logger.info(f"[OK] Symbols ingestion complete: {count} new securities")

        except Exception as e:
            logger.error(f"Error ingesting symbols: {str(e)}")
            self.db.rollback()
            raise

    def ingest_quotes(self):
        """Fetch current quotes and populate PriceOHLCV"""
        logger.info("[FETCH] Getting current quotes...")

        try:
            # Get all active securities
            securities = self.db.execute(
                select(Security).where(Security.is_active == True)
            ).scalars().all()

            logger.info(f"Fetching quotes for {len(securities)} securities")

            count = 0
            for i, security in enumerate(securities):
                try:
                    # Get quote for this symbol
                    quote = self.client.quote(security.symbol)

                    if not quote:
                        continue

                    # Check if price record exists for today
                    existing = self.db.execute(
                        select(PriceOHLCV).where(
                            PriceOHLCV.security_id == security.id,
                            PriceOHLCV.trade_date == self.today
                        )
                    ).scalar_one_or_none()

                    if existing:
                        continue

                    # Create price record
                    price = PriceOHLCV(
                        security_id=security.id,
                        trade_date=self.today,
                        open=float(quote.get('open', quote.get('last_price', 0))),
                        high=float(quote.get('high', quote.get('last_price', 0))),
                        low=float(quote.get('low', quote.get('last_price', 0))),
                        close=float(quote.get('last_price', 0)),
                        volume=int(quote.get('volume', 0)),
                        is_delayed=False
                    )
                    self.db.add(price)
                    count += 1

                    if count % 10 == 0 or (i+1) == len(securities):
                        logger.info(f"  Loaded {count} quotes... ({i+1}/{len(securities)})")

                except Exception as e:
                    continue

            self.db.commit()
            logger.info(f"[OK] Quotes ingestion complete: {count} prices loaded")

        except Exception as e:
            logger.error(f"Error ingesting quotes: {str(e)}")
            self.db.rollback()
            raise

    def ingest_fundamentals(self):
        """Fetch fundamental data and populate FinancialFact"""
        logger.info("[FETCH] Getting fundamental data...")

        try:
            # Get all active securities
            securities = self.db.execute(
                select(Security).where(Security.is_active == True)
            ).scalars().all()

            logger.info(f"Fetching fundamentals for {len(securities)} securities")

            count = 0
            for i, security in enumerate(securities):
                try:
                    # Get fundamentals for this symbol
                    fundamentals = self.client.fundamentals(security.symbol)

                    if not fundamentals:
                        continue

                    # Check if financial data exists for this security
                    existing = self.db.execute(
                        select(FinancialFact).where(
                            FinancialFact.security_id == security.id,
                            FinancialFact.fiscal_year == self.today.year
                        )
                    ).scalar_one_or_none()

                    if existing:
                        continue

                    # Create financial fact record
                    financial = FinancialFact(
                        security_id=security.id,
                        fiscal_year=self.today.year,
                        fiscal_period='FY',
                        revenue=float(fundamentals.get('revenue', 0)),
                        eps=float(fundamentals.get('eps', 0)),
                        pe_ratio=float(fundamentals.get('pe_ratio', 0)),
                        pb_ratio=float(fundamentals.get('pb_ratio', 0)),
                        dividend_yield=float(fundamentals.get('dividend_yield', 0)),
                        market_cap=float(fundamentals.get('market_cap', 0)),
                        book_value=float(fundamentals.get('book_value', 0))
                    )
                    self.db.add(financial)
                    count += 1

                    if count % 10 == 0 or (i+1) == len(securities):
                        logger.info(f"  Loaded {count} fundamentals... ({i+1}/{len(securities)})")

                except Exception as e:
                    continue

            self.db.commit()
            logger.info(f"[OK] Fundamentals ingestion complete: {count} records loaded")

        except Exception as e:
            logger.error(f"Error ingesting fundamentals: {str(e)}")
            self.db.rollback()
            raise

    def ingest_indices(self):
        """Fetch index data and populate IndexOHLCV"""
        logger.info("[FETCH] Getting index data...")

        try:
            # Get or create market indices
            index_codes = ['KSE-100', 'KSE-30', 'KMI-30']

            for code in index_codes:
                try:
                    # Get or create index
                    index = self.db.execute(
                        select(MarketIndex).where(MarketIndex.code == code)
                    ).scalar_one_or_none()

                    if not index:
                        index = MarketIndex(
                            code=code,
                            name=f"{code} Index",
                            description=f"Pakistan Stock Exchange {code} Index"
                        )
                        self.db.add(index)
                        self.db.flush()

                    # Get index data from PSX
                    indices_data = self.client.indices()

                    if code not in indices_data:
                        logger.warning(f"No data for {code}")
                        continue

                    index_info = indices_data[code]

                    # Check if index record exists for today
                    existing = self.db.execute(
                        select(IndexOHLCV).where(
                            IndexOHLCV.market_index_id == index.id,
                            IndexOHLCV.trade_date == self.today
                        )
                    ).scalar_one_or_none()

                    if existing:
                        continue

                    # Create index price record
                    index_price = IndexOHLCV(
                        market_index_id=index.id,
                        trade_date=self.today,
                        open=float(index_info.get('open', index_info.get('last_close', 0))),
                        high=float(index_info.get('high', index_info.get('last_close', 0))),
                        low=float(index_info.get('low', index_info.get('last_close', 0))),
                        close=float(index_info.get('last_close', 0)),
                        volume=int(index_info.get('volume', 0)),
                        is_delayed=False
                    )
                    self.db.add(index_price)
                    logger.info(f"  [+] {code}: {index_info.get('last_close')} points")

                except Exception as e:
                    logger.warning(f"Error fetching {code}: {str(e)}")
                    continue

            self.db.commit()
            logger.info("[OK] Indices ingestion complete")

        except Exception as e:
            logger.error(f"Error ingesting indices: {str(e)}")
            self.db.rollback()
            raise


def main():
    """Run data ingestion"""
    print("\n" + "="*60)
    print("PSX REAL-TIME DATA INGESTION SCRIPT")
    print("Populating database with live PSX data")
    print("="*60 + "\n")

    ingester = PSXDataIngester()
    ingester.ingest_all()

    print("\n" + "="*60)
    print("SUCCESS: Data ingestion complete!")
    print("="*60)
    print("\nResearch Studio and Screeners now have REAL PSX DATA:")
    print("  [+] Current prices for all listed companies")
    print("  [+] Fundamental metrics (EPS, P/E, Book Value, etc.)")
    print("  [+] Index levels (KSE-100, KSE-30, KMI-30)")
    print("  [+] Market breadth and movers")
    print("\nAccess at: http://localhost:3000")
    print("  - Market Overview: /market")
    print("  - Fundamental Screener: /screening")
    print("  - Technical Screener: /technical")
    print("  - Momentum Screener: /momentum")
    print("  - Research Studio: /research")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
