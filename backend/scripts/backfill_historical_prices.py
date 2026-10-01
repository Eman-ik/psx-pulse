#!/usr/bin/env python
"""
Backfill historical PSX price data for the past 90 days
Creates realistic OHLCV data based on current prices
"""

import sys
import io
import random
from datetime import datetime, timedelta

# Fix encoding for Windows console
if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(__file__).rsplit('\\', 2)[0])

from app.db.session import SessionLocal
from app.db.models import Security, PriceOHLCV

class HistoricalPriceBackfiller:
    """Backfill historical price data"""

    def __init__(self):
        self.db = SessionLocal()
        self.today = datetime.now().date()

    def backfill_all(self):
        """Backfill all securities with 365+ days of historical data"""
        try:
            print("\n" + "="*60)
            print("HISTORICAL PRICE BACKFILL - FULL YEAR")
            print("Generating 365+ days of realistic price data for complete momentum analysis")
            print("="*60 + "\n")

            securities = self.db.query(Security).all()
            print(f"[INFO] Found {len(securities)} securities to backfill\n")

            total_prices_created = 0

            for security in securities:
                # Get current price
                current_price_record = self.db.query(PriceOHLCV).filter_by(
                    security_id=security.id
                ).order_by(PriceOHLCV.trade_date.desc()).first()

                if not current_price_record:
                    print(f"  [SKIP] {security.symbol}: No current price found")
                    continue

                current_price = float(current_price_record.close)
                print(f"[BACKFILL] {security.symbol}: Current price = PKR {current_price:.2f}")

                # Generate 365+ days of historical data
                count = 0
                base_price = current_price

                # Start from 366 days ago, work forward (ensure 365-day lookback has data)
                for days_ago in range(365, -1, -1):
                    trade_date = self.today - timedelta(days=days_ago)

                    # Skip weekends (Saturday=5, Sunday=6)
                    if trade_date.weekday() >= 5:
                        continue

                    # Check if price already exists for this date
                    existing = self.db.query(PriceOHLCV).filter_by(
                        security_id=security.id,
                        trade_date=trade_date
                    ).first()

                    if existing:
                        continue

                    # Generate realistic price movement
                    volatility = random.uniform(0.01, 0.04)  # 1-4% daily volatility
                    price_change = random.uniform(-volatility, volatility)
                    close_price = base_price * (1 + price_change)

                    # Generate OHLC
                    open_price = base_price
                    high_price = max(open_price, close_price) * random.uniform(1.002, 1.015)
                    low_price = min(open_price, close_price) * random.uniform(0.985, 0.998)

                    # Generate volume (in thousands)
                    volume = random.randint(500, 5000) * 1000

                    price = PriceOHLCV(
                        security_id=security.id,
                        trade_date=trade_date,
                        open=float(open_price),
                        high=float(high_price),
                        low=float(low_price),
                        close=float(close_price),
                        volume=int(volume),
                        is_delayed=False
                    )
                    self.db.add(price)
                    base_price = close_price
                    count += 1

                if count > 0:
                    self.db.commit()
                    print(f"  [+] {security.symbol}: {count} historical prices added")
                    total_prices_created += count
                else:
                    print(f"  [OK] {security.symbol}: No new prices to add")

            print(f"\n" + "="*60)
            print("SUCCESS: Historical backfill complete!")
            print("="*60)
            print(f"\nTotal prices created: {total_prices_created}")
            print(f"Trading days: ~250-260 (excluding weekends)")
            print(f"Companies: {len(securities)}")
            print(f"\nNow you can use:")
            print(f"  - Technical Screener: Moving averages, RSI")
            print(f"  - Momentum Screener: Multi-period returns")
            print(f"  - Market Analysis: Trend analysis, support/resistance")
            print("="*60 + "\n")

        except Exception as e:
            print(f"\n[ERROR] Backfill failed: {str(e)}\n")
            raise
        finally:
            self.db.close()


def main():
    """Run historical price backfiller"""
    backfiller = HistoricalPriceBackfiller()
    backfiller.backfill_all()


if __name__ == "__main__":
    main()
