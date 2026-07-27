from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint, func
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
