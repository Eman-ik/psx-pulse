"""
R1: Initialize FFC as first company in Research Studio database
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import os
from pathlib import Path

# Import models
from models import (
    Base, Sector, Company,
    MetricDefinition, MetricCategory
)

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/research_studio"
)

def init_database():
    """Create all tables"""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("[OK] Database tables created")
    return engine

def seed_sectors(session: Session):
    """Create base sectors for PSX"""
    sectors = [
        Sector(sector_name="Fertilizer", sub_sector="Chemicals"),
        Sector(sector_name="Banking", sub_sector="Financial"),
        Sector(sector_name="Cement", sub_sector="Construction"),
        Sector(sector_name="Oil & Gas Exploration", sub_sector="Energy"),
        Sector(sector_name="OMC", sub_sector="Energy"),
        Sector(sector_name="Automobile", sub_sector="Industrial"),
        Sector(sector_name="Technology", sub_sector="IT"),
        Sector(sector_name="Power", sub_sector="Energy"),
    ]

    for sector in sectors:
        existing = session.query(Sector).filter_by(sector_name=sector.sector_name).first()
        if not existing:
            session.add(sector)

    session.commit()
    print(f"[OK] {len(sectors)} sectors created")

def seed_ffc(session: Session):
    """Create FFC company master record"""

    # Get Fertilizer sector
    fertilizer_sector = session.query(Sector).filter_by(sector_name="Fertilizer").first()

    if not fertilizer_sector:
        print("[ERROR] Fertilizer sector not found. Create sectors first.")
        return

    # Check if FFC already exists
    existing = session.query(Company).filter_by(ticker="FFC").first()
    if existing:
        print("[OK] FFC already exists (company_id: %d)" % existing.company_id)
        return

    ffc = Company(
        ticker="FFC",
        legal_name="Fauji Fertilizer Company Limited",
        display_name="FFC",
        sector_id=fertilizer_sector.sector_id,
        fiscal_year_end="December",
        shares_outstanding=1420000000,  # 142 crore shares
        free_float=45.00,  # 45% free float
        website="https://www.ffc.com.pk",
        psx_profile_url="https://www.psx.com.pk/psx/company/FFC",
        psx_company_id="FFC",
        status="active"
    )

    session.add(ffc)
    session.commit()

    print(f"""
[OK] FFC created successfully
     Company ID: {ffc.company_id}
     Ticker: {ffc.ticker}
     Legal Name: {ffc.legal_name}
     Sector: {fertilizer_sector.sector_name}
     Status: {ffc.status}
    """)

    return ffc

def seed_metric_definitions(session: Session):
    """Create metric definitions for calculations"""

    metrics = [
        # Income Statement Metrics
        MetricDefinition(
            metric_code="REV",
            display_name="Revenue",
            unit="PKR",
            category=MetricCategory.PROFITABILITY,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="COGS",
            display_name="Cost of Goods Sold",
            unit="PKR",
            category=MetricCategory.PROFITABILITY,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="GROSS_PROFIT",
            display_name="Gross Profit",
            unit="PKR",
            category=MetricCategory.PROFITABILITY,
            calculation_formula="REV - COGS",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="GROSS_MARGIN",
            display_name="Gross Margin",
            unit="%",
            category=MetricCategory.PROFITABILITY,
            calculation_formula="(GROSS_PROFIT / REV) * 100",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="OPERATING_PROFIT",
            display_name="Operating Profit (EBIT)",
            unit="PKR",
            category=MetricCategory.PROFITABILITY,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="EBITDA",
            display_name="EBITDA",
            unit="PKR",
            category=MetricCategory.PROFITABILITY,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="FINANCE_COST",
            display_name="Finance Cost",
            unit="PKR",
            category=MetricCategory.PROFITABILITY,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="PAT",
            display_name="Profit After Tax",
            unit="PKR",
            category=MetricCategory.PROFITABILITY,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="NET_MARGIN",
            display_name="Net Profit Margin",
            unit="%",
            category=MetricCategory.PROFITABILITY,
            calculation_formula="(PAT / REV) * 100",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="EPS",
            display_name="Earnings Per Share",
            unit="PKR",
            category=MetricCategory.PROFITABILITY,
            calculation_method="reported"
        ),

        # Balance Sheet Metrics
        MetricDefinition(
            metric_code="TOTAL_ASSETS",
            display_name="Total Assets",
            unit="PKR",
            category=MetricCategory.LEVERAGE,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="CURRENT_ASSETS",
            display_name="Current Assets",
            unit="PKR",
            category=MetricCategory.LIQUIDITY,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="CASH",
            display_name="Cash & Equivalents",
            unit="PKR",
            category=MetricCategory.LIQUIDITY,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="RECEIVABLES",
            display_name="Trade Receivables",
            unit="PKR",
            category=MetricCategory.EFFICIENCY,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="INVENTORY",
            display_name="Inventory",
            unit="PKR",
            category=MetricCategory.EFFICIENCY,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="CURRENT_LIABILITIES",
            display_name="Current Liabilities",
            unit="PKR",
            category=MetricCategory.LIQUIDITY,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="TOTAL_DEBT",
            display_name="Total Debt",
            unit="PKR",
            category=MetricCategory.LEVERAGE,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="EQUITY",
            display_name="Shareholders' Equity",
            unit="PKR",
            category=MetricCategory.LEVERAGE,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="NET_DEBT",
            display_name="Net Debt",
            unit="PKR",
            category=MetricCategory.LEVERAGE,
            calculation_formula="TOTAL_DEBT - CASH",
            calculation_method="derived"
        ),

        # Cash Flow Metrics
        MetricDefinition(
            metric_code="CFO",
            display_name="Operating Cash Flow",
            unit="PKR",
            category=MetricCategory.GROWTH,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="CAPEX",
            display_name="Capital Expenditure",
            unit="PKR",
            category=MetricCategory.GROWTH,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="FCF",
            display_name="Free Cash Flow",
            unit="PKR",
            category=MetricCategory.GROWTH,
            calculation_formula="CFO - CAPEX",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="DIVIDEND",
            display_name="Dividend Paid",
            unit="PKR",
            category=MetricCategory.GROWTH,
            calculation_method="reported"
        ),
        MetricDefinition(
            metric_code="DPS",
            display_name="Dividend Per Share",
            unit="PKR",
            category=MetricCategory.GROWTH,
            calculation_method="reported"
        ),

        # Ratios: Profitability
        MetricDefinition(
            metric_code="ROE",
            display_name="Return on Equity",
            unit="%",
            category=MetricCategory.PROFITABILITY,
            calculation_formula="(PAT / EQUITY) * 100",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="ROA",
            display_name="Return on Assets",
            unit="%",
            category=MetricCategory.PROFITABILITY,
            calculation_formula="(PAT / TOTAL_ASSETS) * 100",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="ROIC",
            display_name="Return on Invested Capital",
            unit="%",
            category=MetricCategory.PROFITABILITY,
            calculation_method="derived"
        ),

        # Ratios: Liquidity
        MetricDefinition(
            metric_code="CURRENT_RATIO",
            display_name="Current Ratio",
            unit="ratio",
            category=MetricCategory.LIQUIDITY,
            calculation_formula="CURRENT_ASSETS / CURRENT_LIABILITIES",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="QUICK_RATIO",
            display_name="Quick Ratio",
            unit="ratio",
            category=MetricCategory.LIQUIDITY,
            calculation_method="derived"
        ),

        # Ratios: Leverage
        MetricDefinition(
            metric_code="DEBT_TO_EQUITY",
            display_name="Debt to Equity",
            unit="ratio",
            category=MetricCategory.LEVERAGE,
            calculation_formula="TOTAL_DEBT / EQUITY",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="NET_DEBT_TO_EBITDA",
            display_name="Net Debt to EBITDA",
            unit="ratio",
            category=MetricCategory.LEVERAGE,
            calculation_formula="NET_DEBT / EBITDA",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="INTEREST_COVERAGE",
            display_name="Interest Coverage",
            unit="ratio",
            category=MetricCategory.LEVERAGE,
            calculation_formula="OPERATING_PROFIT / FINANCE_COST",
            calculation_method="derived"
        ),

        # Ratios: Efficiency
        MetricDefinition(
            metric_code="ASSET_TURNOVER",
            display_name="Asset Turnover",
            unit="ratio",
            category=MetricCategory.EFFICIENCY,
            calculation_formula="REV / TOTAL_ASSETS",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="RECEIVABLE_DAYS",
            display_name="Days Sales Outstanding",
            unit="days",
            category=MetricCategory.EFFICIENCY,
            calculation_formula="(RECEIVABLES / REV) * 365",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="INVENTORY_DAYS",
            display_name="Inventory Conversion Days",
            unit="days",
            category=MetricCategory.EFFICIENCY,
            calculation_formula="(INVENTORY / COGS) * 365",
            calculation_method="derived"
        ),

        # Valuation Metrics
        MetricDefinition(
            metric_code="PE_RATIO",
            display_name="Price to Earnings",
            unit="ratio",
            category=MetricCategory.VALUATION,
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="PB_RATIO",
            display_name="Price to Book",
            unit="ratio",
            category=MetricCategory.VALUATION,
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="PS_RATIO",
            display_name="Price to Sales",
            unit="ratio",
            category=MetricCategory.VALUATION,
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="EV_EBITDA",
            display_name="EV / EBITDA",
            unit="ratio",
            category=MetricCategory.VALUATION,
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="DIVIDEND_YIELD",
            display_name="Dividend Yield",
            unit="%",
            category=MetricCategory.VALUATION,
            calculation_formula="(DPS / STOCK_PRICE) * 100",
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="PAYOUT_RATIO",
            display_name="Payout Ratio",
            unit="%",
            category=MetricCategory.VALUATION,
            calculation_formula="(DIVIDEND / PAT) * 100",
            calculation_method="derived"
        ),

        # Growth Metrics
        MetricDefinition(
            metric_code="REV_GROWTH_YOY",
            display_name="Revenue Growth YoY",
            unit="%",
            category=MetricCategory.GROWTH,
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="PAT_GROWTH_YOY",
            display_name="PAT Growth YoY",
            unit="%",
            category=MetricCategory.GROWTH,
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="EPS_GROWTH_YOY",
            display_name="EPS Growth YoY",
            unit="%",
            category=MetricCategory.GROWTH,
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="REV_CAGR_5Y",
            display_name="Revenue 5Y CAGR",
            unit="%",
            category=MetricCategory.GROWTH,
            calculation_method="derived"
        ),
        MetricDefinition(
            metric_code="PAT_CAGR_5Y",
            display_name="PAT 5Y CAGR",
            unit="%",
            category=MetricCategory.GROWTH,
            calculation_method="derived"
        ),
    ]

    for metric in metrics:
        existing = session.query(MetricDefinition).filter_by(metric_code=metric.metric_code).first()
        if not existing:
            session.add(metric)

    session.commit()
    print(f"[OK] {len(metrics)} metric definitions created")

def main():
    """Initialize database"""
    print("\n" + "="*60)
    print("R1: Research Studio - FFC Initialization")
    print("="*60 + "\n")

    # Create tables
    engine = init_database()

    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # Seed data
        seed_sectors(session)
        seed_ffc(session)
        seed_metric_definitions(session)

        print("\n" + "="*60)
        print("✓ FFC Initialization Complete")
        print("="*60)
        print("\nNext Steps:")
        print("1. Download FFC annual reports (5 years)")
        print("2. Download FFC quarterly reports (12 quarters)")
        print("3. Run R2: Document ingestion")
        print("4. Run R3: Financial statement parser")
        print("5. Run R4: Metrics calculation")
        print("="*60 + "\n")

    finally:
        session.close()

if __name__ == "__main__":
    main()
