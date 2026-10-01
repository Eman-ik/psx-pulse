"""Sprint 4 Frontend MVP API Endpoints

Simple endpoints to support the search, company detail, and financials pages.
Wraps the data model from Sprint 1-3.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models import Company, Period, FinancialFact, Source
from pydantic import BaseModel
from datetime import date

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

@router.get("/companies/search")
def search_companies(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> List[CompanyResponse]:
    """Search companies by ticker or name (case-insensitive)."""
    query_lower = q.lower()
    companies = db.query(Company).filter(
        (Company.ticker.ilike(f"%{query_lower}%")) |
        (Company.name.ilike(f"%{query_lower}%"))
    ).limit(10).all()
    return companies


@router.get("/companies/{ticker}")
def get_company_by_ticker(
    ticker: str,
    db: Session = Depends(get_db),
) -> CompanyResponse:
    """Get company by ticker."""
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")
    return company


@router.get("/companies/{company_id}/periods")
def list_company_periods(
    company_id: int,
    db: Session = Depends(get_db),
) -> List[PeriodResponse]:
    """List all periods for a company."""
    periods = db.query(Period).filter(Period.company_id == company_id).all()
    if not periods:
        raise HTTPException(status_code=404, detail=f"No periods found for company {company_id}")
    return periods


# ============================================================================
# Periods Endpoints
# ============================================================================

@router.get("/periods/{period_id}")
def get_period(
    period_id: int,
    db: Session = Depends(get_db),
) -> PeriodResponse:
    """Get period details."""
    period = db.query(Period).filter(Period.id == period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail=f"Period {period_id} not found")
    return period


@router.get("/periods/{period_id}/facts")
def list_period_facts(
    period_id: int,
    db: Session = Depends(get_db),
) -> List[FinancialFactResponse]:
    """Get all financial facts for a period."""
    facts = db.query(FinancialFact).filter(FinancialFact.period_id == period_id).all()
    return facts


# ============================================================================
# Sources Endpoints
# ============================================================================

@router.get("/sources/{source_id}")
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
) -> SourceResponse:
    """Get source by ID."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return source
