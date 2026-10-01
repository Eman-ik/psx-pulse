#!/usr/bin/env python
"""
Mock PSX data ingestion script
Populates database with realistic mock PSX data for screeners and research studio
Useful when real PSX API is unavailable
"""

import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, str(__file__).rsplit('\\', 2)[0])

from app.db.session import SessionLocal
from app.db.models import (
    Security, Issuer, Sector, PriceOHLCV, MarketIndex, IndexOHLCV, FinancialFact
)

# Mock companies (13 PSX companies - Fertilizer & Cement sectors)
MOCK_COMPANIES = {
    'FFC': {'name': 'Fauji Fertilizer Company', 'sector': 'Fertilizer', 'base_price': 18.5},
    'FFCL': {'name': 'Fauji Fertilizer Crescent Limited', 'sector': 'Fertilizer', 'base_price': 28.0},
    'ENGRO': {'name': 'Engro Fertilizers Limited', 'sector': 'Fertilizer', 'base_price': 92.5},
    'EFERT': {'name': 'Engro Fertilizers Limited', 'sector': 'Fertilizer', 'base_price': 45.0},
    'UFERT': {'name': 'Unimaster Fertilizer Ltd', 'sector': 'Fertilizer', 'base_price': 12.5},
    'ACFL': {'name': 'Adamjee Fertilizers Limited', 'sector': 'Fertilizer', 'base_price': 14.2},
    'DCC': {'name': 'Dewan Cement Company', 'sector': 'Cement', 'base_price': 18.8},
    'LUCK': {'name': 'Lucky Cement Limited', 'sector': 'Cement', 'base_price': 550.0},
    'CHCC': {'name': 'Cherat Cement Company', 'sector': 'Cement', 'base_price': 28.5},
    'PCCW': {'name': 'Pioneer Cement Company', 'sector': 'Cement', 'base_price': 65.0},
    'SKCH': {'name': 'Sikandar Cement Limited', 'sector': 'Cement', 'base_price': 28.0},
    'PKLC': {'name': 'Pakistan Knitwear Limited', 'sector': 'Textile', 'base_price': 25.0},
    'INDU': {'name': 'Indus Motor Company', 'sector': 'Automobile', 'base_price': 1450.0},
}

class MockDataIngester:
    """Ingest mock PSX data into the database"""

    def __init__(self):
        self.db = SessionLocal()
        self.today = datetime.now().date()

    def ingest_all(self):
        """Run complete mock data ingestion"""
        try:
            print("\n[INGEST] Loading mock PSX data...\n")

            self.ingest_sectors()
            self.ingest_companies()
            self.ingest_prices()
            self.ingest_fundamentals()
            self.ingest_indices()

            print("\n[SUCCESS] Mock data ingestion complete!\n")

        except Exception as e:
            print(f"\n[ERROR] Ingestion failed: {str(e)}\n")
            raise
        finally:
            self.db.close()

    def ingest_sectors(self):
        """Create sector records"""
        print("[SECTORS] Creating sectors...")

        sectors_list = ['Fertilizer', 'Cement', 'Textile', 'Automobile']

        for sector_name in sectors_list:
            existing = self.db.query(Sector).filter_by(name=sector_name).first()
            if not existing:
                sector = Sector(name=sector_name, description=f"{sector_name} sector")
                self.db.add(sector)

        self.db.commit()
        print(f"  [+] {len(sectors_list)} sectors created\n")

    def ingest_companies(self):
        """Create company and security records"""
        print("[COMPANIES] Creating companies and securities...")

        count = 0
        for symbol, data in MOCK_COMPANIES.items():
            existing = self.db.query(Security).filter_by(symbol=symbol).first()
            if existing:
                continue

            # Create issuer
            issuer = self.db.query(Issuer).filter_by(name=data['name']).first()
            if not issuer:
                issuer = Issuer(name=data['name'], status='active')
                self.db.add(issuer)
                self.db.flush()

            # Create sector
            sector = self.db.query(Sector).filter_by(name=data['sector']).first()

            # Create security
            security = Security(
                symbol=symbol,
                name=data['name'],
                issuer_id=issuer.id,
                sector_id=sector.id if sector else None,
                is_active=True,
                market_cap=random.uniform(5000000000, 100000000000)
            )
            self.db.add(security)
            count += 1
            print(f"  [+] {symbol}: {data['name']}")

        self.db.commit()
        print(f"\n  Total: {count} companies created\n")

    def ingest_prices(self):
        """Generate and ingest realistic price data"""
        print("[PRICES] Generating price data for last 90 days...")

        securities = self.db.query(Security).all()
        count = 0

        for security in securities:
            # Generate prices for last 90 days
            base_price = MOCK_COMPANIES.get(security.symbol, {}).get('base_price', 100)

            for days_ago in range(90, -1, -1):
                trade_date = self.today - timedelta(days=days_ago)

                # Check if already exists
                existing = self.db.query(PriceOHLCV).filter_by(
                    security_id=security.id,
                    trade_date=trade_date
                ).first()

                if existing:
                    continue

                # Generate realistic OHLCV
                volatility = random.uniform(0.01, 0.05)
                price_change = random.uniform(-volatility, volatility)
                close = base_price * (1 + price_change)

                price = PriceOHLCV(
                    security_id=security.id,
                    trade_date=trade_date,
                    open=close * random.uniform(0.98, 1.02),
                    high=close * random.uniform(1.01, 1.05),
                    low=close * random.uniform(0.95, 0.99),
                    close=close,
                    volume=random.randint(100000, 10000000),
                    is_delayed=False
                )
                self.db.add(price)
                base_price = close
                count += 1

            print(f"  [+] {security.symbol}: 90 days of price data")

        self.db.commit()
        print(f"\n  Total: {count} price records created\n")

    def ingest_fundamentals(self):
        """Generate and ingest fundamental data"""
        print("[FUNDAMENTALS] Generating fundamental metrics...")

        securities = self.db.query(Security).all()
        count = 0

        for security in securities:
            existing = self.db.query(FinancialFact).filter_by(
                security_id=security.id,
                fiscal_year=self.today.year
            ).first()

            if existing:
                continue

            # Generate realistic fundamentals
            market_cap = random.uniform(1000000000, 50000000000)
            revenue = random.uniform(market_cap * 0.5, market_cap * 2)
            eps = random.uniform(0.5, 25)

            financial = FinancialFact(
                security_id=security.id,
                fiscal_year=self.today.year,
                fiscal_period='FY',
                revenue=revenue,
                eps=eps,
                pe_ratio=random.uniform(5, 25),
                pb_ratio=random.uniform(0.8, 3),
                dividend_yield=random.uniform(0, 8),
                market_cap=market_cap,
                book_value=market_cap / random.uniform(1, 3)
            )
            self.db.add(financial)
            count += 1
            print(f"  [+] {security.symbol}: EPS={eps:.2f}, P/E={financial.pe_ratio:.1f}")

        self.db.commit()
        print(f"\n  Total: {count} fundamental records created\n")

    def ingest_indices(self):
        """Generate and ingest index data"""
        print("[INDICES] Generating index data...")

        index_specs = [
            ('KSE-100', 'KSE-100 Index', 79000),
            ('KSE-30', 'KSE-30 Index', 52000),
            ('KMI-30', 'KMI-30 Index', 7000),
        ]

        for code, name, base_level in index_specs:
            # Get or create index
            index = self.db.query(MarketIndex).filter_by(code=code).first()
            if not index:
                index = MarketIndex(
                    code=code,
                    name=name,
                    description=f"Pakistan Stock Exchange {code} Index"
                )
                self.db.add(index)
                self.db.flush()

            # Generate prices for last 90 days
            level = base_level
            for days_ago in range(90, -1, -1):
                trade_date = self.today - timedelta(days=days_ago)

                existing = self.db.query(IndexOHLCV).filter_by(
                    market_index_id=index.id,
                    trade_date=trade_date
                ).first()

                if existing:
                    continue

                # Generate realistic movement
                change = random.uniform(-0.02, 0.02)
                close = level * (1 + change)

                index_price = IndexOHLCV(
                    market_index_id=index.id,
                    trade_date=trade_date,
                    open=close * random.uniform(0.99, 1.01),
                    high=close * random.uniform(1.001, 1.02),
                    low=close * random.uniform(0.98, 0.999),
                    close=close,
                    volume=random.randint(1000000, 100000000),
                    is_delayed=False
                )
                self.db.add(index_price)
                level = close

            print(f"  [+] {code}: Current level={level:.0f}")

        self.db.commit()
        print(f"\n  Total: 3 indices with 90 days of data\n")


def main():
    """Run mock data ingestion"""
    print("\n" + "="*60)
    print("PSX MOCK DATA INGESTION")
    print("Loading realistic PSX data for screeners & research studio")
    print("="*60)

    ingester = MockDataIngester()
    ingester.ingest_all()

    print("="*60)
    print("MOCK DATA LOADED SUCCESSFULLY!")
    print("="*60)
    print("\nSystem now has:")
    print("  [+] 13 PSX companies (Fertilizer & Cement sectors)")
    print("  [+] 90 days of realistic price history")
    print("  [+] Current fundamental metrics")
    print("  [+] KSE-100, KSE-30, KMI-30 index data")
    print("\nAccess at: http://localhost:3000")
    print("  - Market Overview: /market")
    print("  - Fundamental Screener: /screening")
    print("  - Technical Screener: /technical")
    print("  - Momentum Screener: /momentum")
    print("  - Research Studio: /research")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
