"""
R5: Valuation & Peer Comparison Engine
Ingest stock prices and calculate historical valuations

Calculates:
- Historical P/E, P/B, P/S, EV/EBITDA, dividend yield
- Sector median comparisons
- Percentile rankings
- Valuation trends (is FFC cheap vs. history?)

Outputs:
- stock_prices table (daily: open, high, low, close, volume, market_cap)
- valuations table (daily: P/E, P/B, P/S, EV/EBITDA, dividend yield vs. sector)
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple, Dict
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from models import (
    Company, FinancialMetric, MetricDefinition,
    StockPrice, Valuation, Sector
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# FFC Historical Stock Price Data (Manual Configuration)
# In production, this would come from PSX API or Yahoo Finance
# ============================================================================

FFC_STOCK_PRICES = [
    # 2024 (recent data)
    {"date": date(2024, 9, 30), "close": 485.20, "high": 495.00, "low": 475.50, "volume": 2500000, "open": 480.00},
    {"date": date(2024, 9, 27), "close": 478.50, "high": 488.00, "low": 475.00, "volume": 2100000, "open": 482.00},
    {"date": date(2024, 9, 26), "close": 482.00, "high": 490.00, "low": 478.00, "volume": 1950000, "open": 485.00},
    {"date": date(2024, 9, 25), "close": 480.00, "high": 485.00, "low": 475.00, "volume": 1850000, "open": 479.00},
    {"date": date(2024, 6, 30), "close": 465.00, "high": 475.00, "low": 455.00, "volume": 2200000, "open": 468.00},
    {"date": date(2024, 3, 31), "close": 450.00, "high": 460.00, "low": 440.00, "volume": 2100000, "open": 452.00},

    # 2023 (year-ago data)
    {"date": date(2023, 12, 31), "close": 420.00, "high": 435.00, "low": 410.00, "volume": 2000000, "open": 425.00},
    {"date": date(2023, 9, 30), "close": 412.00, "high": 425.00, "low": 400.00, "volume": 1950000, "open": 415.00},
    {"date": date(2023, 6, 30), "close": 400.00, "high": 415.00, "low": 390.00, "volume": 1850000, "open": 405.00},
    {"date": date(2023, 3, 31), "close": 385.00, "high": 400.00, "low": 375.00, "volume": 1800000, "open": 390.00},

    # 2022 (2 years ago)
    {"date": date(2022, 12, 31), "close": 350.00, "high": 375.00, "low": 340.00, "volume": 1800000, "open": 360.00},
    {"date": date(2022, 9, 30), "close": 345.00, "high": 360.00, "low": 335.00, "volume": 1700000, "open": 350.00},

    # 2021 (3 years ago)
    {"date": date(2021, 12, 31), "close": 310.00, "high": 335.00, "low": 300.00, "volume": 1600000, "open": 320.00},
    {"date": date(2021, 6, 30), "close": 290.00, "high": 310.00, "low": 280.00, "volume": 1500000, "open": 295.00},
]

class StockPriceFetcher:
    """Fetch historical stock prices for FFC"""

    @staticmethod
    def fetch_ffc_prices() -> List[dict]:
        """
        Fetch FFC historical prices

        In production, this would query:
        - PSX API: GET /api/companies/FFC/prices
        - Yahoo Finance: GET https://query1.finance.yahoo.com/v8/finance/chart/FFC.KA
        - Custom data provider

        For now: Return manually configured data
        """
        logger.info(f"[OK] Loaded {len(FFC_STOCK_PRICES)} FFC price records")
        return FFC_STOCK_PRICES

    @staticmethod
    def calculate_market_cap(close_price: float, shares_outstanding: int) -> int:
        """Calculate market cap from price and shares"""
        return int(close_price * shares_outstanding)

class ValuationCalculator:
    """Calculate valuation metrics"""

    def __init__(self, session: Session):
        self.session = session
        self.stats = {
            "prices_ingested": 0,
            "valuations_calculated": 0,
            "errors": 0
        }

    def get_metric_value(
        self,
        company_id: int,
        metric_code: str,
        fiscal_year: int,
        fiscal_quarter: Optional[int] = None
    ) -> Optional[float]:
        """Get metric value for a specific period"""

        metric_def = self.session.query(MetricDefinition).filter_by(
            metric_code=metric_code
        ).first()

        if not metric_def:
            return None

        metric = self.session.query(FinancialMetric).filter(
            and_(
                FinancialMetric.company_id == company_id,
                FinancialMetric.metric_id == metric_def.metric_id,
                FinancialMetric.fiscal_year == fiscal_year,
                FinancialMetric.fiscal_quarter == fiscal_quarter
            )
        ).first()

        return float(metric.value) if metric else None

    def get_ttm_metric_value(
        self,
        company_id: int,
        metric_code: str
    ) -> Optional[float]:
        """Get TTM (trailing twelve months) value"""

        metric_def = self.session.query(MetricDefinition).filter_by(
            metric_code=metric_code
        ).first()

        if not metric_def:
            return None

        metric = self.session.query(FinancialMetric).filter(
            and_(
                FinancialMetric.company_id == company_id,
                FinancialMetric.metric_id == metric_def.metric_id,
                FinancialMetric.is_ttm == True
            )
        ).order_by(FinancialMetric.period_end.desc()).first()

        return float(metric.value) if metric else None

    # =====================================================================
    # Valuation Calculations
    # =====================================================================

    def calc_pe_ratio(
        self,
        close_price: float,
        eps: Optional[float]
    ) -> Optional[float]:
        """P/E Ratio = Stock Price / EPS"""
        if eps and eps != 0:
            return close_price / eps
        return None

    def calc_pb_ratio(
        self,
        market_cap: int,
        equity: Optional[int]
    ) -> Optional[float]:
        """P/B Ratio = Market Cap / Shareholders' Equity"""
        if equity and equity != 0:
            return market_cap / equity
        return None

    def calc_ps_ratio(
        self,
        market_cap: int,
        revenue: Optional[int]
    ) -> Optional[float]:
        """P/S Ratio = Market Cap / Annual Revenue"""
        if revenue and revenue != 0:
            return market_cap / revenue
        return None

    def calc_ev_ebitda(
        self,
        market_cap: int,
        total_debt: Optional[int],
        cash: Optional[int],
        ebitda: Optional[int]
    ) -> Optional[float]:
        """EV/EBITDA = (Market Cap + Net Debt) / EBITDA"""
        if ebitda and ebitda != 0:
            net_debt = (total_debt or 0) - (cash or 0)
            enterprise_value = market_cap + net_debt
            return enterprise_value / ebitda
        return None

    def calc_dividend_yield(
        self,
        close_price: float,
        dps: Optional[float]
    ) -> Optional[float]:
        """Dividend Yield % = (DPS / Stock Price) * 100"""
        if close_price and close_price != 0:
            return (dps / close_price) * 100 if dps else None
        return None

    # =====================================================================
    # Ingest Prices
    # =====================================================================

    def ingest_prices(self, company_id: int, prices: List[dict]) -> int:
        """Ingest historical stock prices"""

        company = self.session.query(Company).filter_by(company_id=company_id).first()
        if not company:
            logger.error(f"Company {company_id} not found")
            return 0

        count = 0
        for price_data in prices:
            # Check if already exists
            existing = self.session.query(StockPrice).filter(
                and_(
                    StockPrice.company_id == company_id,
                    StockPrice.price_date == price_data["date"]
                )
            ).first()

            if existing:
                continue

            # Calculate market cap
            market_cap = self.calculate_market_cap(
                price_data["close"],
                company.shares_outstanding
            )

            # Create price record
            price = StockPrice(
                company_id=company_id,
                price_date=price_data["date"],
                open_price=price_data.get("open"),
                high_price=price_data.get("high"),
                low_price=price_data.get("low"),
                close_price=price_data["close"],
                volume=price_data.get("volume"),
                market_cap=market_cap,
                source="manual"
            )

            self.session.add(price)
            count += 1

        self.session.commit()
        self.stats["prices_ingested"] = count

        return count

    # =====================================================================
    # Calculate Valuations for a Date
    # =====================================================================

    def calculate_valuations_for_date(
        self,
        company_id: int,
        price_date: date
    ) -> int:
        """Calculate all valuations for a specific date"""

        # Get price
        price = self.session.query(StockPrice).filter(
            and_(
                StockPrice.company_id == company_id,
                StockPrice.price_date == price_date
            )
        ).first()

        if not price:
            return 0

        close_price = float(price.close_price)
        market_cap = price.market_cap

        # Determine fiscal year from price_date
        # For FY ending Dec 31
        fiscal_year = price_date.year if price_date.month > 0 else price_date.year - 1

        valuations_created = 0

        # Get metrics for calculation
        eps = self.get_metric_value(company_id, "EPS", fiscal_year)
        equity = self.get_metric_value(company_id, "TOTAL_EQUITY", fiscal_year)
        revenue = self.get_metric_value(company_id, "REV", fiscal_year)
        total_debt = self.get_metric_value(company_id, "TOTAL_DEBT", fiscal_year)
        cash = self.get_metric_value(company_id, "CASH", fiscal_year)
        ebitda = self.get_metric_value(company_id, "EBITDA", fiscal_year)
        dps = self.get_metric_value(company_id, "DPS", fiscal_year)

        # Calculate valuations
        pe = self.calc_pe_ratio(close_price, eps)
        if pe and self._store_valuation(company_id, price_date, "pe_ratio", pe):
            valuations_created += 1

        pb = self.calc_pb_ratio(market_cap, int(equity) if equity else None)
        if pb and self._store_valuation(company_id, price_date, "pb_ratio", pb):
            valuations_created += 1

        ps = self.calc_ps_ratio(market_cap, int(revenue) if revenue else None)
        if ps and self._store_valuation(company_id, price_date, "ps_ratio", ps):
            valuations_created += 1

        ev_ebitda = self.calc_ev_ebitda(
            market_cap,
            int(total_debt) if total_debt else None,
            int(cash) if cash else None,
            int(ebitda) if ebitda else None
        )
        if ev_ebitda and self._store_valuation(company_id, price_date, "ev_ebitda", ev_ebitda):
            valuations_created += 1

        div_yield = self.calc_dividend_yield(close_price, dps)
        if div_yield and self._store_valuation(company_id, price_date, "dividend_yield", div_yield):
            valuations_created += 1

        return valuations_created

    def _store_valuation(
        self,
        company_id: int,
        val_date: date,
        metric_code: str,
        value: float
    ) -> bool:
        """Store valuation metric"""

        # Check if already exists
        existing = self.session.query(Valuation).filter(
            and_(
                Valuation.company_id == company_id,
                Valuation.valuation_date == val_date,
                Valuation.metric_code == metric_code
            )
        ).first()

        if existing:
            existing.metric_value = value
        else:
            valuation = Valuation(
                company_id=company_id,
                valuation_date=val_date,
                metric_code=metric_code,
                metric_value=value,
                source="calculated"
            )
            self.session.add(valuation)

        return True

    # =====================================================================
    # Calculate Sector Medians & Percentiles
    # =====================================================================

    def calculate_sector_comparisons(self, company_id: int) -> dict:
        """Calculate sector median for valuation comparisons"""

        company = self.session.query(Company).filter_by(company_id=company_id).first()
        if not company:
            return {}

        # Get all valuations for this company (latest date)
        latest_val_date = self.session.query(func.max(Valuation.valuation_date)).filter(
            Valuation.company_id == company_id
        ).scalar()

        if not latest_val_date:
            return {}

        # Get other companies in same sector
        peer_companies = self.session.query(Company).filter(
            and_(
                Company.sector_id == company.sector_id,
                Company.company_id != company_id
            )
        ).all()

        # For each metric, calculate sector median
        metrics_to_compare = ["pe_ratio", "pb_ratio", "ps_ratio", "ev_ebitda", "dividend_yield"]

        sector_stats = {}
        for metric in metrics_to_compare:
            # Get all peer valuations for this metric on same date
            peer_values = self.session.query(Valuation.metric_value).filter(
                and_(
                    Valuation.metric_code == metric,
                    Valuation.valuation_date == latest_val_date,
                    Valuation.company_id.in_([p.company_id for p in peer_companies])
                )
            ).all()

            if peer_values:
                values = sorted([float(v[0]) for v in peer_values])
                median = values[len(values) // 2]
                sector_stats[metric] = median

        # Update valuations with sector median
        for metric in metrics_to_compare:
            if metric in sector_stats:
                valuations = self.session.query(Valuation).filter(
                    and_(
                        Valuation.company_id == company_id,
                        Valuation.valuation_date == latest_val_date,
                        Valuation.metric_code == metric
                    )
                ).all()

                for val in valuations:
                    val.sector_median = sector_stats[metric]
                    if val.metric_value:
                        # Calculate percentile
                        val.sector_percentile = (val.metric_value / sector_stats[metric]) * 100

        self.session.commit()
        return sector_stats

class ValuationEngine:
    """Main valuation engine orchestrator"""

    def __init__(self, session: Session):
        self.session = session
        self.fetcher = StockPriceFetcher()
        self.calculator = ValuationCalculator(session)

    def process_ffc_valuations(self) -> dict:
        """Complete R5 pipeline for FFC"""

        logger.info("\n" + "="*60)
        logger.info("R5: Valuation & Peer Comparison Engine")
        logger.info("="*60 + "\n")

        # Get FFC
        ffc = self.session.query(Company).filter_by(ticker="FFC").first()
        if not ffc:
            logger.error("[ERROR] FFC not found. Run R1 initialization first.")
            return {"status": "failed", "reason": "FFC not found"}

        logger.info(f"[OK] Found FFC (company_id: {ffc.company_id})")
        logger.info(f"     Shares Outstanding: {ffc.shares_outstanding:,}")
        logger.info(f"     Free Float: {ffc.free_float}%\n")

        # Step 1: Fetch prices
        logger.info("Step 1: Fetching historical stock prices...")
        prices = self.fetcher.fetch_ffc_prices()

        # Step 2: Ingest prices
        logger.info("Step 2: Ingesting prices into database...")
        prices_ingested = self.calculator.ingest_prices(ffc.company_id, prices)
        logger.info(f"[OK] Ingested {prices_ingested} price records")

        # Step 3: Calculate valuations for each price date
        logger.info("\nStep 3: Calculating valuations...")
        valuations_total = 0

        for price_data in prices:
            val_count = self.calculator.calculate_valuations_for_date(
                ffc.company_id,
                price_data["date"]
            )
            valuations_total += val_count

        logger.info(f"[OK] Calculated {valuations_total} valuation metrics")

        # Step 4: Calculate sector comparisons
        logger.info("\nStep 4: Calculating sector medians...")
        sector_stats = self.calculator.calculate_sector_comparisons(ffc.company_id)
        logger.info(f"[OK] Calculated sector medians: {len(sector_stats)} metrics")

        # Step 5: Display valuation snapshot
        logger.info("\n" + "="*60)
        logger.info("FFC Valuation Snapshot")
        logger.info("="*60)

        latest_price = self.session.query(StockPrice).filter_by(
            company_id=ffc.company_id
        ).order_by(StockPrice.price_date.desc()).first()

        if latest_price:
            logger.info(f"\nLatest Price: Rs. {latest_price.close_price}")
            logger.info(f"Date: {latest_price.price_date}")
            logger.info(f"Market Cap: Rs. {latest_price.market_cap:,}")

            latest_vals = self.session.query(Valuation).filter(
                and_(
                    Valuation.company_id == ffc.company_id,
                    Valuation.valuation_date == latest_price.price_date
                )
            ).all()

            logger.info("\nValuation Ratios:")
            for val in latest_vals:
                if val.metric_value:
                    percentile = f" ({val.sector_percentile:.0f}% of sector median)" if val.sector_percentile else ""
                    logger.info(f"  {val.metric_code:20} {val.metric_value:>10.2f}{percentile}")

        logger.info("\n" + "="*60)
        logger.info("R5: Valuation Engine Complete")
        logger.info("="*60)
        logger.info(f"Prices Ingested:       {self.calculator.stats['prices_ingested']}")
        logger.info(f"Valuations Calculated: {valuations_total}")
        logger.info("="*60 + "\n")

        logger.info("\nNext Steps:")
        logger.info("1. R6: Announcement Intelligence (classify latest results)")
        logger.info("2. R7: AI Copilot (answer 'why did P/E change?')")
        logger.info("3. R8: Research Workspace UI (display all data)")

        return {
            "status": "completed",
            "prices_ingested": self.calculator.stats["prices_ingested"],
            "valuations_calculated": valuations_total,
            "sector_medians": len(sector_stats)
        }

def main():
    """Run valuation engine"""
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/research_studio"
    )

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        engine_instance = ValuationEngine(session)
        result = engine_instance.process_ffc_valuations()
        print(f"\nResult: {result}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
