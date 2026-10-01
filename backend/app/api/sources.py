"""Source registry API endpoints.

Manages company data sources (documents, reports, announcements).
Validates before storage: extract → normalize → validate → store or flag.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Company, Source, Period
from pydantic import BaseModel
from datetime import date, datetime

router = APIRouter(prefix="/api/sources", tags=["sources"])


class SourceCreate(BaseModel):
    company_id: int
    source_type: str  # annual_report, quarterly_results, announcement, etc
    publisher: Optional[str] = None
    title: Optional[str] = None
    document_type: Optional[str] = None
    period_id: Optional[int] = None
    url: Optional[str] = None
    file_path: Optional[str] = None
    document_date: Optional[date] = None
    publication_date: Optional[date] = None
    retrieved_date: Optional[date] = None
    document_hash: Optional[str] = None


class SourceResponse(BaseModel):
    id: int
    company_id: int
    source_type: str
    title: Optional[str]
    status: str
    document_date: Optional[date]
    publication_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=SourceResponse)
def create_source(
    source: SourceCreate,
    db: Session = Depends(get_db),
) -> SourceResponse:
    """Create a new data source.

    Verifies company exists before storage.
    """
    # Verify company exists
    company = db.query(Company).filter(Company.id == source.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {source.company_id} not found")

    # Verify period exists if provided
    if source.period_id:
        period = db.query(Period).filter(Period.id == source.period_id).first()
        if not period:
            raise HTTPException(status_code=404, detail=f"Period {source.period_id} not found")

    # Create source
    new_source = Source(
        company_id=source.company_id,
        source_type=source.source_type,
        publisher=source.publisher,
        title=source.title,
        document_type=source.document_type,
        period_id=source.period_id,
        url=source.url,
        file_path=source.file_path,
        document_date=source.document_date,
        publication_date=source.publication_date,
        retrieved_date=source.retrieved_date,
        document_hash=source.document_hash,
        status="pending",
    )
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    return new_source


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
) -> SourceResponse:
    """Get source by ID."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return source


@router.get("/company/{company_id}", response_model=List[SourceResponse])
def list_sources_by_company(
    company_id: int,
    source_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> List[SourceResponse]:
    """List sources for a company.

    Optional filters: source_type, status
    """
    query = db.query(Source).filter(Source.company_id == company_id)

    if source_type:
        query = query.filter(Source.source_type == source_type)
    if status:
        query = query.filter(Source.status == status)

    sources = query.order_by(Source.created_at.desc()).all()
    return sources


@router.patch("/{source_id}/status")
def update_source_status(
    source_id: int,
    new_status: str,
    db: Session = Depends(get_db),
) -> SourceResponse:
    """Update source extraction/validation status.

    Status: pending → extracted → validated → stored, or flagged for review
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    valid_statuses = {"pending", "extracted", "validated", "stored", "flagged"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    source.status = new_status
    db.commit()
    db.refresh(source)
    return source
