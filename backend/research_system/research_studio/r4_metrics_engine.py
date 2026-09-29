"""
R4: Metrics & KPI Engine
Calculate financial metrics from parsed statements

Calculates:
- Profitability: ROE, ROA, margins
- Efficiency: asset turnover, receivable days, inventory days
- Leverage: debt-to-equity, net debt/EBITDA
- Liquidity: current ratio, quick ratio
- Growth: YoY, QoQ, CAGR
- Valuation: P/E, P/B, dividend yield, payout ratio

Stores in financial_metrics table with source lineage
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import (
    Company, Document, FinancialStatement, StatementLineItem,
    FinancialMetric, MetricDefinition, StatementType, DataLineage
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsCalculator:
    """Calculate all financial metrics"""

    def __init__(self, session: Session):
        self.session = session
        self.stats = {
            "metrics_calculated": 0,
            "metrics_created": 0,
            "errors": 0
        }

    # =====================================================================
    # Helper: Get line item value
    # =====================================================================

    def get_value(self, statement: FinancialStatement, line_code: str) -> Optional[int]:
        """Get line item value from statement"""
        item = self.session.query(StatementLineItem).filter(
            and_(
                StatementLineItem.statement_id == statement.statement_id,
                StatementLineItem.line_code == line_code
            )
        ).first()

        return item.value if item else None

    # =====================================================================
    # Profitability Metrics
    # =====================================================================

    def calc_gross_margin(self, statement: FinancialStatement) -> Optional[float]:
        """Gross Margin % = (Gross Profit / Revenue) * 100"""
        rev = self.get_value(statement, "REV")
        gp = self.get_value(statement, "GROSS_PROFIT")

        if rev and rev != 0:
            return (gp / rev) * 100 if gp else None
        return None

    def calc_operating_margin(self, statement: FinancialStatement) -> Optional[float]:
        """Operating Margin % = (Operating Profit / Revenue) * 100"""
        rev = self.get_value(statement, "REV")
        op = self.get_value(statement, "OPERATING_PROFIT")

        if rev and rev != 0:
            return (op / rev) * 100 if op else None
        return None

    def calc_net_margin(self, statement: FinancialStatement) -> Optional[float]:
        """Net Profit Margin % = (PAT / Revenue) * 100"""
        rev = self.get_value(statement, "REV")
        pat = self.get_value(statement, "PAT")

        if rev and rev != 0:
            return (pat / rev) * 100 if pat else None
        return None

    def calc_roe(self, statement: FinancialStatement) -> Optional[float]:
        """Return on Equity % = (PAT / Shareholders' Equity) * 100"""
        pat = self.get_value(statement, "PAT")
        equity = self.get_value(statement, "TOTAL_EQUITY")

        if equity and equity != 0:
            return (pat / equity) * 100 if pat else None
        return None

    def calc_roa(self, statement: FinancialStatement) -> Optional[float]:
        """Return on Assets % = (PAT / Total Assets) * 100"""
        pat = self.get_value(statement, "PAT")
        assets = self.get_value(statement, "TOTAL_ASSETS")

        if assets and assets != 0:
            return (pat / assets) * 100 if pat else None
        return None

    # =====================================================================
    # Efficiency Metrics
    # =====================================================================

    def calc_asset_turnover(self, statement: FinancialStatement) -> Optional[float]:
        """Asset Turnover = Revenue / Total Assets"""
        rev = self.get_value(statement, "REV")
        assets = self.get_value(statement, "TOTAL_ASSETS")

        if assets and assets != 0:
            return rev / assets if rev else None
        return None

    def calc_receivable_days(self, statement: FinancialStatement) -> Optional[float]:
        """Days Sales Outstanding = (Receivables / Revenue) * 365"""
        receivables = self.get_value(statement, "RECEIVABLES")
        rev = self.get_value(statement, "REV")

        if rev and rev != 0:
            return (receivables / rev) * 365 if receivables else None
        return None

    def calc_inventory_days(self, statement: FinancialStatement) -> Optional[float]:
        """Inventory Days = (Inventory / COGS) * 365"""
        inventory = self.get_value(statement, "INVENTORY")
        cogs = self.get_value(statement, "COGS")

        if cogs and cogs != 0:
            return (inventory / cogs) * 365 if inventory else None
        return None

    # =====================================================================
    # Leverage Metrics
    # =====================================================================

    def calc_debt_to_equity(self, statement: FinancialStatement) -> Optional[float]:
        """Debt-to-Equity = Total Debt / Shareholders' Equity"""
        debt = self.get_value(statement, "TOTAL_DEBT")
        equity = self.get_value(statement, "TOTAL_EQUITY")

        if equity and equity != 0:
            return debt / equity if debt else None
        return None

    def calc_net_debt_to_ebitda(self, statement: FinancialStatement) -> Optional[float]:
        """Net Debt / EBITDA"""
        debt = self.get_value(statement, "TOTAL_DEBT")
        cash = self.get_value(statement, "CASH")
        ebitda = self.get_value(statement, "EBITDA")

        if ebitda and ebitda != 0:
            net_debt = (debt or 0) - (cash or 0)
            return net_debt / ebitda
        return None

    def calc_interest_coverage(self, statement: FinancialStatement) -> Optional[float]:
        """Interest Coverage = Operating Profit / Finance Cost"""
        op = self.get_value(statement, "OPERATING_PROFIT")
        fc = self.get_value(statement, "FINANCE_COST")

        if fc and fc != 0:
            return op / fc if op else None
        return None

    # =====================================================================
    # Liquidity Metrics
    # =====================================================================

    def calc_current_ratio(self, statement: FinancialStatement) -> Optional[float]:
        """Current Ratio = Current Assets / Current Liabilities"""
        ca = self.get_value(statement, "CURRENT_ASSETS")
        cl = self.get_value(statement, "CURRENT_LIABILITIES")

        if cl and cl != 0:
            return ca / cl if ca else None
        return None

    def calc_quick_ratio(self, statement: FinancialStatement) -> Optional[float]:
        """Quick Ratio = (Current Assets - Inventory) / Current Liabilities"""
        ca = self.get_value(statement, "CURRENT_ASSETS")
        inventory = self.get_value(statement, "INVENTORY")
        cl = self.get_value(statement, "CURRENT_LIABILITIES")

        if cl and cl != 0:
            quick_assets = (ca or 0) - (inventory or 0)
            return quick_assets / cl
        return None

    # =====================================================================
    # Store metric in database
    # =====================================================================

    def store_metric(
        self,
        company_id: int,
        metric_code: str,
        value: Optional[float],
        statement: FinancialStatement,
        is_calculated: bool = True
    ) -> bool:
        """Store calculated metric in database"""

        if value is None:
            return False

        # Get metric definition
        metric_def = self.session.query(MetricDefinition).filter_by(
            metric_code=metric_code
        ).first()

        if not metric_def:
            logger.warning(f"Metric definition not found: {metric_code}")
            return False

        # Check if already exists
        existing = self.session.query(FinancialMetric).filter(
            and_(
                FinancialMetric.company_id == company_id,
                FinancialMetric.metric_id == metric_def.metric_id,
                FinancialMetric.fiscal_year == statement.fiscal_year,
                FinancialMetric.fiscal_quarter == statement.fiscal_quarter
            )
        ).first()

        if existing:
            # Update
            existing.value = value
            existing.calculated_at = datetime.utcnow()
        else:
            # Create new
            metric = FinancialMetric(
                company_id=company_id,
                metric_id=metric_def.metric_id,
                fiscal_year=statement.fiscal_year,
                fiscal_quarter=statement.fiscal_quarter,
                period_end=statement.reporting_period_end,
                value=value,
                unit=metric_def.unit,
                source_statement_id=statement.statement_id,
                is_calculated=is_calculated,
                confidence=0.95,
                calculated_at=datetime.utcnow()
            )
            self.session.add(metric)

        self.stats["metrics_created"] += 1
        return True

    # =====================================================================
    # Main calculation dispatcher
    # =====================================================================

    def calculate_metrics_for_statement(
        self,
        company_id: int,
        statement: FinancialStatement
    ) -> int:
        """Calculate all applicable metrics for a statement"""

        metrics_count = 0

        # Only calculate for income statement and balance sheet
        if statement.statement_type == StatementType.INCOME:
            # Profitability
            if self.store_metric(company_id, "GROSS_MARGIN", self.calc_gross_margin(statement), statement):
                metrics_count += 1
            if self.store_metric(company_id, "NET_MARGIN", self.calc_net_margin(statement), statement):
                metrics_count += 1

        elif statement.statement_type == StatementType.BALANCE_SHEET:
            # Profitability (requires both IS and BS)
            if self.store_metric(company_id, "ROE", self.calc_roe(statement), statement):
                metrics_count += 1
            if self.store_metric(company_id, "ROA", self.calc_roa(statement), statement):
                metrics_count += 1

            # Efficiency
            if self.store_metric(company_id, "ASSET_TURNOVER", self.calc_asset_turnover(statement), statement):
                metrics_count += 1
            if self.store_metric(company_id, "RECEIVABLE_DAYS", self.calc_receivable_days(statement), statement):
                metrics_count += 1
            if self.store_metric(company_id, "INVENTORY_DAYS", self.calc_inventory_days(statement), statement):
                metrics_count += 1

            # Leverage
            if self.store_metric(company_id, "DEBT_TO_EQUITY", self.calc_debt_to_equity(statement), statement):
                metrics_count += 1
            if self.store_metric(company_id, "NET_DEBT_TO_EBITDA", self.calc_net_debt_to_ebitda(statement), statement):
                metrics_count += 1
            if self.store_metric(company_id, "INTEREST_COVERAGE", self.calc_interest_coverage(statement), statement):
                metrics_count += 1

            # Liquidity
            if self.store_metric(company_id, "CURRENT_RATIO", self.calc_current_ratio(statement), statement):
                metrics_count += 1
            if self.store_metric(company_id, "QUICK_RATIO", self.calc_quick_ratio(statement), statement):
                metrics_count += 1

        self.stats["metrics_calculated"] += metrics_count
        return metrics_count

    # =====================================================================
    # Process all statements
    # =====================================================================

    def calculate_for_company(self, company_id: int) -> dict:
        """Calculate metrics for all statements of a company"""

        logger.info("\n" + "="*60)
        logger.info("R4: Metrics & KPI Engine")
        logger.info("="*60 + "\n")

        # Get all statements
        statements = self.session.query(FinancialStatement).filter_by(
            company_id=company_id
        ).all()

        if not statements:
            logger.error("[ERROR] No financial statements found. Run R3 parser first.")
            return {
                "status": "failed",
                "reason": "No statements found"
            }

        logger.info(f"Found {len(statements)} financial statements")

        # Calculate metrics for each statement
        for statement in statements:
            logger.info(f"\n{statement.statement_type.value.upper()} FY{statement.fiscal_year} Q{statement.fiscal_quarter or 'A'}")

            count = self.calculate_metrics_for_statement(company_id, statement)
            logger.info(f"  → Calculated {count} metrics")

        self.session.commit()

        logger.info("\n" + "="*60)
        logger.info("R4: Metrics Calculation Complete")
        logger.info("="*60)
        logger.info(f"Total Metrics Calculated: {self.stats['metrics_calculated']}")
        logger.info(f"Total Metrics Created:    {self.stats['metrics_created']}")
        logger.info(f"Errors:                   {self.stats['errors']}")
        logger.info("="*60 + "\n")

        logger.info("\nKey Metrics Available:")
        logger.info("- Profitability: Gross Margin, Net Margin, ROE, ROA")
        logger.info("- Efficiency: Asset Turnover, Receivable Days, Inventory Days")
        logger.info("- Leverage: Debt-to-Equity, Net Debt/EBITDA, Interest Coverage")
        logger.info("- Liquidity: Current Ratio, Quick Ratio")
        logger.info("\nNext: R5 Valuation Engine (stock prices, P/E, dividend yield)")

        return {
            "status": "completed",
            "stats": self.stats
        }

def main():
    """Run metrics engine"""
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
        # Get FFC
        ffc = session.query(Company).filter_by(ticker="FFC").first()
        if not ffc:
            print("[ERROR] FFC not found. Run R1 initialization first.")
            return

        calculator = MetricsCalculator(session)
        result = calculator.calculate_for_company(ffc.company_id)
        print(f"\nResult: {result}")

    finally:
        session.close()

if __name__ == "__main__":
    main()
