from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OperationalMetric(Base):
    """Physical operating KPIs (production, capacity, offtake, market share) — the "Operations
    and production" section of the company IA. Distinct from financial_fact because these are
    volumes/percentages tied to a product line, not currency line items from a financial statement.
    """

    __tablename__ = "operational_metric"
    __table_args__ = (
        UniqueConstraint(
            "issuer_id", "metric_key", "product", "period_end", name="uq_operational_metric_issuer_key_product_period"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    metric_key: Mapped[str] = mapped_column(String(60), index=True)
    product: Mapped[str | None] = mapped_column(String(40), nullable=True)  # e.g. urea, DAP, NP, CAN; null = company-wide
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date, index=True)
    period_type: Mapped[str] = mapped_column(String(20), default="annual")
    value: Mapped[float] = mapped_column(Numeric(18, 4))
    unit: Mapped[str] = mapped_column(String(20))  # KT | percent | million_MT
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("source_document.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndustryObservation(Base):
    """A sourced numeric observation describing an industry rather than one issuer.

    Examples include installed capacity, production, dispatches, imports, exports,
    realized prices and input costs.  The source document is mandatory so Stage 2 can
    never turn a spreadsheet entry into an unattributed industry fact.
    """

    __tablename__ = "industry_observation"
    __table_args__ = (
        UniqueConstraint(
            "sector_id", "metric_key", "company_issuer_id", "product", "period_end",
            name="uq_industry_observation_dimension_period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sector.id"), index=True)
    company_issuer_id: Mapped[int | None] = mapped_column(ForeignKey("issuer.id"), nullable=True, index=True)
    metric_key: Mapped[str] = mapped_column(String(60), index=True)
    product: Mapped[str | None] = mapped_column(String(50), nullable=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date, index=True)
    frequency: Mapped[str] = mapped_column(String(20))
    value: Mapped[float] = mapped_column(Numeric(20, 4))
    unit: Mapped[str] = mapped_column(String(30))
    source_document_id: Mapped[int] = mapped_column(ForeignKey("source_document.id"), index=True)
    source_page: Mapped[int | None] = mapped_column(nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndustryAssessment(Base):
    """Source-grounded qualitative assessment for non-numeric industry dimensions."""

    __tablename__ = "industry_assessment"
    __table_args__ = (
        UniqueConstraint("sector_id", "dimension", "as_of_date", name="uq_industry_assessment_dimension_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sector.id"), index=True)
    dimension: Mapped[str] = mapped_column(String(50), index=True)
    rating: Mapped[str] = mapped_column(String(30))
    assessment: Mapped[str] = mapped_column(Text)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    source_document_id: Mapped[int] = mapped_column(ForeignKey("source_document.id"), index=True)
    source_page: Mapped[int | None] = mapped_column(nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    analyst: Mapped[str] = mapped_column(String(120))
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CapmAssumption(Base):
    """CAPM inputs for cost-of-equity, per the plan's valuation-methodology guidance
    (5.6: "show every assumption in a visible base/bull/bear table"). issuer_id is nullable
    for market-wide defaults (risk-free rate, equity risk premiums apply to every issuer);
    beta is issuer-specific where known.
    """

    __tablename__ = "capm_assumption"

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int | None] = mapped_column(ForeignKey("issuer.id"), nullable=True, index=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    risk_free_rate_pct: Mapped[float] = mapped_column(Numeric(6, 3))
    beta: Mapped[float] = mapped_column(Numeric(6, 3))
    base_equity_risk_premium_pct: Mapped[float] = mapped_column(Numeric(6, 3))
    country_risk_premium_pct: Mapped[float] = mapped_column(Numeric(6, 3))
    source_note: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Thesis(Base):
    """Analyst-authored bull/base/bear thesis (evidence class: analyst_interpretation).
    A correction/update creates a new row (as_of_date changes); history is never overwritten,
    matching the evidence model's versioning philosophy elsewhere in this schema.
    """

    __tablename__ = "thesis"

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    bull_case: Mapped[str] = mapped_column(Text)
    base_case: Mapped[str] = mapped_column(Text)
    bear_case: Mapped[str] = mapped_column(Text)
    key_catalysts: Mapped[list[str]] = mapped_column(JSON, default=list)
    key_risks: Mapped[list[str]] = mapped_column(JSON, default=list)
    author: Mapped[str] = mapped_column(String(200))
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("source_document.id"), nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
