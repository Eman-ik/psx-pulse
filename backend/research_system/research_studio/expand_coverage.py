"""
Expand Research Studio coverage to include Fertilizer and Cement sectors
Initializes companies for R1-R7 data pipelines
"""

from models import db, Company, Sector, MetricDefinition
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PSX Companies - Fertilizer & Cement sectors
FERTILIZER_COMPANIES = [
    # Fertilizer
    {
        'ticker': 'FFC',
        'legal_name': 'Fauji Fertilizer Company Limited',
        'sector': 'Fertilizer',
        'market_cap': 686_000_000_000,
        'shares_outstanding': 1_420_000_000,
        'free_float': 45,
    },
    {
        'ticker': 'EFERT',
        'legal_name': 'Engro Fertilizers Limited',
        'sector': 'Fertilizer',
        'market_cap': 520_000_000_000,
        'shares_outstanding': 1_200_000_000,
        'free_float': 38,
    },
    {
        'ticker': 'FATIMA',
        'legal_name': 'Fatima Fertilizer Company Limited',
        'sector': 'Fertilizer',
        'market_cap': 380_000_000_000,
        'shares_outstanding': 900_000_000,
        'free_float': 42,
    },
    {
        'ticker': 'IFIC',
        'legal_name': 'Indus Fertilizer Limited',
        'sector': 'Fertilizer',
        'market_cap': 240_000_000_000,
        'shares_outstanding': 720_000_000,
        'free_float': 35,
    },
]

CEMENT_COMPANIES = [
    # Cement
    {
        'ticker': 'DGKC',
        'legal_name': 'Dewan Ghazi Khan Cement Company Limited',
        'sector': 'Cement',
        'market_cap': 195_000_000_000,
        'shares_outstanding': 580_000_000,
        'free_float': 40,
    },
    {
        'ticker': 'LUCK',
        'legal_name': 'Lucky Cement Limited',
        'sector': 'Cement',
        'market_cap': 885_000_000_000,
        'shares_outstanding': 1_050_000_000,
        'free_float': 48,
    },
    {
        'ticker': 'CHCC',
        'legal_name': 'Cherat Cement Company Limited',
        'sector': 'Cement',
        'market_cap': 125_000_000_000,
        'shares_outstanding': 375_000_000,
        'free_float': 32,
    },
    {
        'ticker': 'PCCL',
        'legal_name': 'Pakistan Cement Company Limited',
        'sector': 'Cement',
        'market_cap': 89_000_000_000,
        'shares_outstanding': 267_000_000,
        'free_float': 28,
    },
    {
        'ticker': 'MLCF',
        'legal_name': 'Maple Leaf Cement Factory Limited',
        'sector': 'Cement',
        'market_cap': 42_000_000_000,
        'shares_outstanding': 126_000_000,
        'free_float': 25,
    },
    {
        'ticker': 'PRIM',
        'legal_name': 'Pioneer Cement Limited',
        'sector': 'Cement',
        'market_cap': 67_000_000_000,
        'shares_outstanding': 200_000_000,
        'free_float': 30,
    },
]

def expand_sectors():
    """Ensure all sectors exist"""
    sectors_list = [
        ('Fertilizer', 'Agricultural input and fertilizer manufacturing'),
        ('Cement', 'Cement production and distribution'),
    ]

    for sector_name, description in sectors_list:
        existing = Sector.query.filter_by(sector_name=sector_name).first()
        if not existing:
            sector = Sector(
                sector_name=sector_name,
                description=description,
                created_at=datetime.utcnow()
            )
            db.session.add(sector)
            logger.info(f"Created sector: {sector_name}")
        else:
            logger.info(f"Sector already exists: {sector_name}")

    db.session.commit()

def expand_companies():
    """Add fertilizer and cement companies"""
    all_companies = FERTILIZER_COMPANIES + CEMENT_COMPANIES

    for comp_data in all_companies:
        existing = Company.query.filter_by(ticker=comp_data['ticker']).first()
        if existing:
            logger.info(f"Company already exists: {comp_data['ticker']}")
            continue

        # Get sector
        sector = Sector.query.filter_by(sector_name=comp_data['sector']).first()
        if not sector:
            logger.error(f"Sector not found: {comp_data['sector']}")
            continue

        company = Company(
            ticker=comp_data['ticker'],
            legal_name=comp_data['legal_name'],
            sector_id=sector.sector_id,
            market_cap=comp_data.get('market_cap'),
            shares_outstanding=comp_data.get('shares_outstanding'),
            free_float_percent=comp_data.get('free_float'),
            fiscal_year_end='June',
            status='active',
            created_at=datetime.utcnow()
        )
        db.session.add(company)
        logger.info(f"Created company: {comp_data['ticker']} - {comp_data['legal_name']}")

    db.session.commit()

def expand_metric_definitions():
    """Ensure metric definitions exist for all companies"""
    metric_definitions = [
        # Profitability
        ('REV', 'Total Revenue', 'Revenue', 'Rs. Million'),
        ('EBITDA', 'EBITDA', 'Profitability', 'Rs. Million'),
        ('PAT', 'Profit After Tax', 'Profitability', 'Rs. Million'),
        ('EPS', 'Earnings Per Share', 'Profitability', 'Rs.'),
        ('GROSS_MARGIN', 'Gross Margin %', 'Profitability', '%'),
        ('NET_MARGIN', 'Net Profit Margin %', 'Profitability', '%'),
        ('ROE', 'Return on Equity', 'Profitability', '%'),
        ('ROA', 'Return on Assets', 'Profitability', '%'),

        # Efficiency
        ('ASSET_TURNOVER', 'Asset Turnover Ratio', 'Efficiency', 'x'),
        ('RECEIVABLE_DAYS', 'Days Receivable Outstanding', 'Efficiency', 'days'),
        ('INVENTORY_DAYS', 'Days Inventory Outstanding', 'Efficiency', 'days'),
        ('OPERATING_MARGIN', 'Operating Margin %', 'Efficiency', '%'),

        # Leverage
        ('DEBT_TO_EQUITY', 'Debt to Equity Ratio', 'Leverage', 'x'),
        ('NET_DEBT_TO_EBITDA', 'Net Debt to EBITDA', 'Leverage', 'x'),
        ('INTEREST_COVERAGE', 'Interest Coverage Ratio', 'Leverage', 'x'),
        ('DEBT_RATIO', 'Debt Ratio', 'Leverage', '%'),

        # Liquidity
        ('CURRENT_RATIO', 'Current Ratio', 'Liquidity', 'x'),
        ('QUICK_RATIO', 'Quick Ratio', 'Liquidity', 'x'),

        # Valuation
        ('PE_RATIO', 'Price to Earnings Ratio', 'Valuation', 'x'),
        ('PB_RATIO', 'Price to Book Ratio', 'Valuation', 'x'),
        ('PS_RATIO', 'Price to Sales Ratio', 'Valuation', 'x'),
        ('EV_EBITDA', 'EV/EBITDA Multiple', 'Valuation', 'x'),
        ('DIVIDEND_YIELD', 'Dividend Yield %', 'Valuation', '%'),
        ('PAYOUT_RATIO', 'Dividend Payout Ratio', 'Valuation', '%'),
    ]

    for metric_code, metric_name, category, unit in metric_definitions:
        existing = MetricDefinition.query.filter_by(metric_code=metric_code).first()
        if not existing:
            metric_def = MetricDefinition(
                metric_code=metric_code,
                metric_name=metric_name,
                category=category,
                unit=unit,
                is_calculated=True,
                created_at=datetime.utcnow()
            )
            db.session.add(metric_def)
            logger.info(f"Created metric definition: {metric_code}")
        else:
            logger.info(f"Metric definition already exists: {metric_code}")

    db.session.commit()

def main():
    """Run all expansion tasks"""
    logger.info("=" * 80)
    logger.info("Expanding Research Studio Coverage - Fertilizer & Cement Sectors")
    logger.info("=" * 80)

    logger.info("\n[1/3] Expanding Sectors...")
    expand_sectors()

    logger.info("\n[2/3] Expanding Companies...")
    expand_companies()

    logger.info("\n[3/3] Expanding Metric Definitions...")
    expand_metric_definitions()

    logger.info("\n" + "=" * 80)
    logger.info("✅ Coverage expansion complete!")
    logger.info("=" * 80)

    # Summary
    fertilizer_count = Company.query.join(Sector).filter(
        Sector.sector_name == 'Fertilizer'
    ).count()
    cement_count = Company.query.join(Sector).filter(
        Sector.sector_name == 'Cement'
    ).count()

    logger.info(f"\nCoverage Summary:")
    logger.info(f"  Fertilizer Companies: {fertilizer_count}")
    logger.info(f"  Cement Companies: {cement_count}")
    logger.info(f"  Total: {fertilizer_count + cement_count}")
    logger.info(f"\n  To start ingesting data, run:")
    logger.info(f"    python research_system/research_studio/r2_document_ingestion.py")
    logger.info(f"    python research_system/research_studio/r3_financial_parser.py")
    logger.info(f"    python research_system/research_studio/r4_metrics_engine.py")

if __name__ == '__main__':
    # This should be run from Flask app context
    from app import create_app
    app = create_app()
    with app.app_context():
        main()
