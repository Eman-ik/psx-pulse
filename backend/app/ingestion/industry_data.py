"""Validated ingestion contract for Stage 2 industry data.

Collectors may parse APCMA/NFDC/PBS/regulator files in different ways, but all writes pass
through these functions so units, dates, source lineage and verification are consistent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import IndustryAssessment, IndustryObservation, Issuer, Sector, SourceDocument


ALLOWED_METRICS = {
    "installed_capacity", "effective_capacity", "production", "domestic_demand",
    "domestic_dispatches", "export_dispatches", "imports", "exports", "inventory",
    "realized_price", "retention_price", "input_cost", "market_share",
    "capacity_utilization", "new_capacity", "sector_revenue", "sector_ebit",
    "sector_invested_capital", "sector_roic", "cost_of_capital",
}
ALLOWED_FREQUENCIES = {"monthly", "quarterly", "half_year", "annual"}
ALLOWED_DIMENSIONS = {"pricing_power", "entry_barriers", "regulation", "substitutes"}


@dataclass(frozen=True)
class IndustryObservationInput:
    sector: str
    metric_key: str
    period_start: date
    period_end: date
    frequency: str
    value: float
    unit: str
    source_document_id: int
    company_symbol: str | None = None
    product: str | None = None
    source_page: int | None = None
    confidence: float = 1.0
    is_verified: bool = False


def upsert_observation(db: Session, item: IndustryObservationInput) -> IndustryObservation:
    key = item.metric_key.strip().lower()
    if key not in ALLOWED_METRICS:
        raise ValueError(f"Unsupported industry metric: {item.metric_key}")
    if item.frequency not in ALLOWED_FREQUENCIES:
        raise ValueError(f"Unsupported frequency: {item.frequency}")
    if item.period_start > item.period_end:
        raise ValueError("period_start must be on or before period_end")
    if not 0 <= item.confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if not item.unit.strip():
        raise ValueError("unit is required")

    sector = db.execute(select(Sector).where(Sector.name.ilike(item.sector.strip()))).scalar_one_or_none()
    if sector is None:
        raise ValueError(f"Unknown sector: {item.sector}")
    source = db.get(SourceDocument, item.source_document_id)
    if source is None:
        raise ValueError(f"Unknown source document: {item.source_document_id}")

    issuer_id = None
    if item.company_symbol:
        from app.db.models import Security
        security = db.execute(select(Security).where(Security.symbol == item.company_symbol.strip().upper())).scalar_one_or_none()
        if security is None:
            raise ValueError(f"Unknown company symbol: {item.company_symbol}")
        issuer = db.get(Issuer, security.issuer_id)
        if issuer is None or issuer.sector_id != sector.id:
            raise ValueError("company_symbol does not belong to the selected sector")
        issuer_id = issuer.id

    existing = db.execute(
        select(IndustryObservation).where(
            IndustryObservation.sector_id == sector.id,
            IndustryObservation.metric_key == key,
            IndustryObservation.company_issuer_id == issuer_id,
            IndustryObservation.product == item.product,
            IndustryObservation.period_end == item.period_end,
        )
    ).scalar_one_or_none()
    row = existing or IndustryObservation(
        sector_id=sector.id, metric_key=key, company_issuer_id=issuer_id,
        product=item.product, period_start=item.period_start, period_end=item.period_end,
        frequency=item.frequency, value=item.value, unit=item.unit.strip(),
        source_document_id=item.source_document_id,
    )
    row.period_start = item.period_start
    row.frequency = item.frequency
    row.value = item.value
    row.unit = item.unit.strip()
    row.source_document_id = item.source_document_id
    row.source_page = item.source_page
    row.confidence = item.confidence
    row.is_verified = item.is_verified
    db.add(row)
    db.flush()
    return row


def create_assessment(
    db: Session, *, sector_name: str, dimension: str, rating: str, assessment: str,
    as_of_date: date, source_document_id: int, analyst: str, source_page: int | None = None,
    confidence: float = 1.0, review_date: date | None = None,
) -> IndustryAssessment:
    dimension = dimension.strip().lower()
    if dimension not in ALLOWED_DIMENSIONS:
        raise ValueError(f"Unsupported industry dimension: {dimension}")
    if not assessment.strip() or not analyst.strip():
        raise ValueError("assessment and analyst are required")
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    sector = db.execute(select(Sector).where(Sector.name.ilike(sector_name.strip()))).scalar_one_or_none()
    if sector is None:
        raise ValueError(f"Unknown sector: {sector_name}")
    if db.get(SourceDocument, source_document_id) is None:
        raise ValueError(f"Unknown source document: {source_document_id}")
    row = IndustryAssessment(
        sector_id=sector.id, dimension=dimension, rating=rating.strip().lower(),
        assessment=assessment.strip(), as_of_date=as_of_date,
        source_document_id=source_document_id, source_page=source_page,
        confidence=confidence, analyst=analyst.strip(), review_date=review_date,
    )
    db.add(row)
    db.flush()
    return row
