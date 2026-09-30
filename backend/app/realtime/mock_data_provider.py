"""Mock price data provider for live market simulation."""

import asyncio
import random
from datetime import datetime
from typing import Dict

import logging

logger = logging.getLogger(__name__)


class MockPriceProvider:
    """Generates realistic mock price data for demonstration."""

    def __init__(self):
        # Initial index levels (realistic PSX values)
        self.indices = {
            "KSE-100": {"level": 79500, "volatility": 0.15},
            "KSE-30": {"level": 52300, "volatility": 0.18},
            "KMI-30": {"level": 7200, "volatility": 0.20},
        }

        # Sample securities with initial prices
        self.securities = {
            "FFC": {"price": 165, "volatility": 0.25},
            "FATIMA": {"price": 85, "volatility": 0.28},
            "EFERT": {"price": 72, "volatility": 0.30},
            "LUCK": {"price": 52, "volatility": 0.22},
            "MLCF": {"price": 68, "volatility": 0.24},
            "DGKC": {"price": 121, "volatility": 0.20},
            "CHCC": {"price": 94, "volatility": 0.26},
            "BWCL": {"price": 145, "volatility": 0.19},
            "ACPL": {"price": 55, "volatility": 0.23},
            "FCCL": {"price": 38, "volatility": 0.27},
            "KOHC": {"price": 42, "volatility": 0.25},
            "DCL": {"price": 98, "volatility": 0.21},
            "GWLC": {"price": 75, "volatility": 0.23},
            "HBL": {"price": 185, "volatility": 0.15},
            "MCB": {"price": 445, "volatility": 0.16},
            "UBL": {"price": 8200, "volatility": 0.12},
            "PAEL": {"price": 625, "volatility": 0.17},
            "OGDC": {"price": 95, "volatility": 0.24},
            "PPL": {"price": 445, "volatility": 0.18},
            "MARI": {"price": 480, "volatility": 0.21},
        }

        # Previous prices for change calculation
        self.prev_prices = {k: v["price"] for k, v in self.securities.items()}
        self.prev_indices = {k: v["level"] for k, v in self.indices.items()}

    async def update_prices(self) -> Dict:
        """Generate updated prices with realistic movements."""
        updates = {
            "indices": {},
            "securities": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Update indices
        for code, data in self.indices.items():
            # Random walk with mean reversion
            change = random.gauss(0, data["volatility"] * data["level"] * 0.01)
            new_level = data["level"] + change
            change_pct = (new_level - self.prev_indices[code]) / self.prev_indices[code] * 100

            updates["indices"][code] = {
                "level": round(new_level, 2),
                "change": round(new_level - self.prev_indices[code], 2),
                "change_pct": round(change_pct, 2),
            }

            self.prev_indices[code] = new_level
            self.indices[code]["level"] = new_level

        # Update individual securities
        for symbol, data in self.securities.items():
            # Random walk
            change = random.gauss(0, data["volatility"] * data["price"] * 0.01)
            new_price = max(data["price"] + change, data["price"] * 0.01)  # Prevent negative prices
            change_pct = (new_price - self.prev_prices[symbol]) / self.prev_prices[symbol] * 100
            volume = random.randint(10000, 1000000)

            updates["securities"].append({
                "symbol": symbol,
                "price": round(new_price, 2),
                "change": round(new_price - self.prev_prices[symbol], 2),
                "change_pct": round(change_pct, 2),
                "volume": volume,
            })

            self.prev_prices[symbol] = new_price
            self.securities[symbol]["price"] = new_price

        return updates

    async def get_market_snapshot(self) -> Dict:
        """Get current market snapshot."""
        # Count gainers/decliners
        gainers = sum(
            1 for symbol, price in self.prev_prices.items()
            if price > self.securities[symbol]["price"]
        )
        decliners = sum(
            1 for symbol, price in self.prev_prices.items()
            if price < self.securities[symbol]["price"]
        )
        unchanged = len(self.securities) - gainers - decliners

        # Get top gainers/losers
        price_changes = [
            (
                symbol,
                (self.securities[symbol]["price"] - self.prev_prices[symbol])
                / self.prev_prices[symbol]
                * 100,
            )
            for symbol in self.securities.keys()
        ]
        price_changes.sort(key=lambda x: x[1], reverse=True)

        gainers_list = [
            {
                "symbol": symbol,
                "price": round(self.securities[symbol]["price"], 2),
                "change_pct": round(change_pct, 2),
            }
            for symbol, change_pct in price_changes[:5]
        ]

        losers_list = [
            {
                "symbol": symbol,
                "price": round(self.securities[symbol]["price"], 2),
                "change_pct": round(change_pct, 2),
            }
            for symbol, change_pct in price_changes[-5:]
        ]

        return {
            "indices": {
                code: {
                    "level": round(data["level"], 2),
                    "prev": round(self.prev_indices[code], 2),
                }
                for code, data in self.indices.items()
            },
            "breadth": {
                "gainers": gainers,
                "decliners": decliners,
                "unchanged": unchanged,
                "total": len(self.securities),
            },
            "gainers": gainers_list,
            "losers": losers_list,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global provider instance
provider = MockPriceProvider()
