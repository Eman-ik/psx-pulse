"""Sprint 2: Lucky Cement data setup.

Create LUCK company and financial periods in database.
Data foundation for extraction pipeline.
"""
from datetime import date
from sqlalchemy.orm import Session

from app.models import Company, Period


def create_lucky_cement(db: Session) -> Company:
    """Create Lucky Cement Limited company record.

    Ticker: LUCK
    Sector: Materials
    Industry: Cement
    Listed: PSX
    Fiscal year end: March 31 (month 3)
    Currency: PKR
    """
    existing = db.query(Company).filter(Company.ticker == "LUCK").first()
    if existing:
        return existing

    company = Company(
        ticker="LUCK",
        name="Lucky Cement Limited",
        sector="Materials",
        industry="Cement",
        listed_date=date(1980, 1, 1),  # Approximate listing date
        fiscal_year_end=3,  # March 31
        currency="PKR",
        status="active",
        coverage_tier="partial",  # Will be "full" after extraction complete
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def create_luck_periods(db: Session, company_id: int) -> dict:
    """Create financial periods for LUCK.

    Creates:
    - 3 annual periods (FY2024, FY2025, FY2026)
    - 8 quarterly periods (Q1-Q4 for FY2026)

    Returns dict: {period_type: {fiscal_year: Period}}
    """
    periods = {}

    # Annual periods (3 years)
    annual_configs = [
        (2024, date(2023, 4, 1), date(2024, 3, 31)),
        (2025, date(2024, 4, 1), date(2025, 3, 31)),
        (2026, date(2025, 4, 1), date(2026, 3, 31)),
    ]

    for fiscal_year, start_date, end_date in annual_configs:
        existing = db.query(Period).filter(
            Period.company_id == company_id,
            Period.period_type == "annual",
            Period.fiscal_year == fiscal_year,
        ).first()

        if not existing:
            period = Period(
                company_id=company_id,
                period_type="annual",
                fiscal_year=fiscal_year,
                quarter=None,
                start_date=start_date,
                end_date=end_date,
            )
            db.add(period)
            db.commit()
            db.refresh(period)
        else:
            period = existing

        if "annual" not in periods:
            periods["annual"] = {}
        periods["annual"][fiscal_year] = period

    # Quarterly periods (FY2026 only)
    quarterly_configs = [
        (1, date(2025, 4, 1), date(2025, 6, 30)),
        (2, date(2025, 7, 1), date(2025, 9, 30)),
        (3, date(2025, 10, 1), date(2025, 12, 31)),
        (4, date(2026, 1, 1), date(2026, 3, 31)),
    ]

    for quarter, start_date, end_date in quarterly_configs:
        existing = db.query(Period).filter(
            Period.company_id == company_id,
            Period.period_type == f"q{quarter}",
            Period.fiscal_year == 2026,
        ).first()

        if not existing:
            period = Period(
                company_id=company_id,
                period_type=f"q{quarter}",
                fiscal_year=2026,
                quarter=quarter,
                start_date=start_date,
                end_date=end_date,
            )
            db.add(period)
            db.commit()
            db.refresh(period)
        else:
            period = existing

        if "quarterly" not in periods:
            periods["quarterly"] = {}
        periods["quarterly"][quarter] = period

    return periods


def setup_lucky_cement_data(db: Session) -> dict:
    """Complete LUCK setup: company + periods.

    Returns: {
        'company': Company,
        'periods': {period_type: {fiscal_year: Period}}
    }
    """
    company = create_lucky_cement(db)
    periods = create_luck_periods(db, company.id)

    return {
        "company": company,
        "periods": periods,
    }
