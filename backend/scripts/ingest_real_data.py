#!/usr/bin/env python
"""
Real-time PSX data ingestion script
Fetches current prices, fundamentals, and indices for all PSX companies
Populates the database for research studio and screeners
"""

import sys
from datetime import datetime, timedelta
from typing import Optional
import logging

from sqlalchemy import select
from psxdata import PSXClient

# Add backend to path
sys.path.insert(0, str(__file__).rsplit('\\', 2)[0])

from app.db.session import SessionLocal
from app.db.models import (
    Security, Issuer, Sector, PriceOHLCV, MarketIndex, IndexOHLCV,
    FinancialFact, RatioValue
)

logging.basicConfig(level=logging.INFO)
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

            logger.info("✅ Data ingestion complete!")

        except Exception as e:
            logger.error(f"❌ Ingestion failed: {str(e)}")
            raise
        finally:
            self.db.close()

    def ingest_symbols(self):
        """Fetch all PSX symbols and create Security records"""
        logger.info("📥 Fetching PSX symbols...")

        try:
            symbols_data = self.client.symbols()
            logger.info(f"Found {len(symbols_data)} securities")

            for symbol, details in symbols_data.items():
                # Check if security already exists
                existing = self.db.execute(
                    select(Security).where(Security.symbol == symbol)
                ).scalar_one_or_none()

                if existing:
                    logger.debug(f"  {symbol} already exists")
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
                logger.info(f"  ✅ Added {symbol} ({sector_name})")

            self.db.commit()
            logger.info("✅ Symbols ingestion complete")

        except Exception as e:
            logger.error(f"Error ingesting symbols: {str(e)}")
            self.db.rollback()
            raise

    def ingest_quotes(self):
        """Fetch current quotes and populate PriceOHLCV"""
        logger.info("📥 Fetching current quotes...")

        try:
            # Get all active securities
            securities = self.db.execute(
                select(Security).where(Security.is_active == True)
            ).scalars().all()

            logger.info(f"Fetching quotes for {len(securities)} securities")

            for security in securities:
                try:
                    # Get quote for this symbol
                    quote = self.client.quote(security.symbol)

                    if not quote:
                        logger.warning(f"  ⚠️ No quote for {security.symbol}")
                        continue

                    # Check if price record exists for today
                    existing = self.db.execute(
                        select(PriceOHLCV).where(
                            PriceOHLCV.security_id == security.id,
                            PriceOHLCV.trade_date == self.today
                        )
                    ).scalar_one_or_none()

                    if existing:
                        logger.debug(f"  {security.symbol} quote already exists for today")
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
                    logger.info(f"  ✅ {security.symbol}: {quote.get('last_price')} PKR")

                except Exception as e:
                    logger.warning(f"  Error fetching quote for {security.symbol}: {str(e)}")
                    continue

            self.db.commit()
            logger.info("✅ Quotes ingestion complete")

        except Exception as e:
            logger.error(f"Error ingesting quotes: {str(e)}")
            self.db.rollback()
            raise

    def ingest_fundamentals(self):
        """Fetch fundamental data and populate FinancialFact"""
        logger.info("📥 Fetching fundamental data...")

        try:
            # Get all active securities
            securities = self.db.execute(
                select(Security).where(Security.is_active == True)
            ).scalars().all()

            logger.info(f"Fetching fundamentals for {len(securities)} securities")

            for security in securities:
                try:
                    # Get fundamentals for this symbol
                    fundamentals = self.client.fundamentals(security.symbol)

                    if not fundamentals:
                        logger.warning(f"  ⚠️ No fundamentals for {security.symbol}")
                        continue

                    # Check if financial data exists for this security
                    existing = self.db.execute(
                        select(FinancialFact).where(
                            FinancialFact.security_id == security.id,
                            FinancialFact.fiscal_year == self.today.year
                        )
                    ).scalar_one_or_none()

                    if existing:
                        logger.debug(f"  {security.symbol} fundamentals already exist")
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
                    logger.info(f"  ✅ {security.symbol}: EPS {fundamentals.get('eps', 'N/A')}")

                except Exception as e:
                    logger.warning(f"  Error fetching fundamentals for {security.symbol}: {str(e)}")
                    continue

            self.db.commit()
            logger.info("✅ Fundamentals ingestion complete")

        except Exception as e:
            logger.error(f"Error ingesting fundamentals: {str(e)}")
            self.db.rollback()
            raise

    def ingest_indices(self):
        """Fetch index data and populate IndexOHLCV"""
        logger.info("📥 Fetching index data...")

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
                        logger.warning(f"  ⚠️ No data for {code}")
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
                        logger.debug(f"  {code} quote already exists for today")
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
                    logger.info(f"  ✅ {code}: {index_info.get('last_close')} points")

                except Exception as e:
                    logger.warning(f"  Error fetching {code}: {str(e)}")
                    continue

            self.db.commit()
            logger.info("✅ Indices ingestion complete")

        except Exception as e:
            logger.error(f"Error ingesting indices: {str(e)}")
            self.db.rollback()
            raise


def main():
    """Run data ingestion"""
    print("""
    ╔════════════════════════════════════════╗
    ║  PSX Real-Time Data Ingestion Script   ║
    ║  Populate database with live PSX data  ║
    ╚════════════════════════════════════════╝
    """)

    ingester = PSXDataIngester()
    ingester.ingest_all()

    print("""
    ✅ Data ingestion successful!

    Research Studio and Screeners now have real PSX data:
    • Current prices for all listed companies
    • Fundamental metrics (EPS, P/E, Book Value, etc.)
    • Index levels (KSE-100, KSE-30, KMI-30)
    • Market breadth and movers

    Visit: http://localhost:3000
      - Market Overview: /market
      - Fundamental Screener: /screening
      - Technical Screener: /technical
      - Momentum Screener: /momentum
      - Research Studio: /research
    """)


if __name__ == "__main__":
    main()
