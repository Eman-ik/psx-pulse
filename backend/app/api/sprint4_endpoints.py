"""Sprint 4 Frontend MVP API Endpoints

Simple endpoints to support the search, company detail, and financials pages.
Uses SQLAlchemy's new select() API to avoid model registry conflicts.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from pydantic import BaseModel
from datetime import date

from app.db.session import get_db

# Import models directly to access table metadata without registry conflicts
from sqlalchemy import text

router = APIRouter(tags=["sprint4"])


class CompanyResponse(BaseModel):
    id: int
    ticker: str
    name: str
    sector: str
    coverage_tier: str

    class Config:
        from_attributes = True


class PeriodResponse(BaseModel):
    id: int
    company_id: int
    period_type: str  # annual | quarterly
    fiscal_year: int
    quarter: Optional[int] = None

    class Config:
        from_attributes = True


class FinancialFactResponse(BaseModel):
    id: int
    company_id: int
    period_id: int
    metric: str
    value: float
    unit: str
    statement_type: str  # income_statement | balance_sheet | cash_flow
    source_id: int
    source_page: Optional[int] = None
    validation_status: str  # validated | flagged | pending

    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    id: int
    title: str
    document_date: Optional[date] = None
    url: Optional[str] = None
    file_path: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Companies Endpoints
# ============================================================================

@router.get("/companies/search", response_model=List[CompanyResponse])
def search_companies(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Search companies by ticker or name (case-insensitive)."""
    query_lower = f"%{q.lower()}%"
    # Use raw SQL to avoid model registry conflicts
    result = db.execute(text("""
        SELECT id, ticker, name, sector, coverage_tier
        FROM companies
        WHERE LOWER(ticker) LIKE :q OR LOWER(name) LIKE :q
        LIMIT 10
    """), {"q": query_lower})
    companies = []
    for row in result:
        companies.append(CompanyResponse(
            id=row[0], ticker=row[1], name=row[2],
            sector=row[3], coverage_tier=row[4]
        ))
    return companies


@router.get("/companies/{ticker}", response_model=CompanyResponse)
def get_company_by_ticker(
    ticker: str,
    db: Session = Depends(get_db),
):
    """Get company by ticker."""
    result = db.execute(text("""
        SELECT id, ticker, name, sector, coverage_tier
        FROM companies
        WHERE UPPER(ticker) = :ticker
    """), {"ticker": ticker.upper()}).first()

    if not result:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")

    return CompanyResponse(
        id=result[0], ticker=result[1], name=result[2],
        sector=result[3], coverage_tier=result[4]
    )


@router.get("/companies/{company_id}/periods", response_model=List[PeriodResponse])
def list_company_periods(
    company_id: int,
    db: Session = Depends(get_db),
):
    """List all periods for a company."""
    result = db.execute(text("""
        SELECT id, company_id, period_type, fiscal_year, quarter
        FROM periods
        WHERE company_id = :company_id
    """), {"company_id": company_id}).fetchall()

    if not result:
        raise HTTPException(status_code=404, detail=f"No periods found for company {company_id}")

    periods = []
    for row in result:
        periods.append(PeriodResponse(
            id=row[0], company_id=row[1], period_type=row[2],
            fiscal_year=row[3], quarter=row[4]
        ))
    return periods


# ============================================================================
# Periods Endpoints
# ============================================================================

@router.get("/periods/{period_id}", response_model=PeriodResponse)
def get_period(
    period_id: int,
    db: Session = Depends(get_db),
):
    """Get period details."""
    result = db.execute(text("""
        SELECT id, company_id, period_type, fiscal_year, quarter
        FROM periods
        WHERE id = :period_id
    """), {"period_id": period_id}).first()

    if not result:
        raise HTTPException(status_code=404, detail=f"Period {period_id} not found")

    return PeriodResponse(
        id=result[0], company_id=result[1], period_type=result[2],
        fiscal_year=result[3], quarter=result[4]
    )


@router.get("/periods/{period_id}/facts", response_model=List[FinancialFactResponse])
def list_period_facts(
    period_id: int,
    db: Session = Depends(get_db),
):
    """Get all financial facts for a period."""
    result = db.execute(text("""
        SELECT id, company_id, period_id, metric, value, unit, statement_type,
               source_id, source_page, validation_status
        FROM financial_facts
        WHERE period_id = :period_id
    """), {"period_id": period_id}).fetchall()

    facts = []
    for row in result:
        facts.append(FinancialFactResponse(
            id=row[0], company_id=row[1], period_id=row[2], metric=row[3],
            value=float(row[4]), unit=row[5], statement_type=row[6],
            source_id=row[7], source_page=row[8], validation_status=row[9]
        ))
    return facts


# ============================================================================
# Sources Endpoints
# ============================================================================

@router.get("/sources/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
):
    """Get source by ID."""
    result = db.execute(text("""
        SELECT id, title, document_date, url, file_path
        FROM sources
        WHERE id = :source_id
    """), {"source_id": source_id}).first()

    if not result:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    return SourceResponse(
        id=result[0], title=result[1], document_date=result[2],
        url=result[3], file_path=result[4]
    )
