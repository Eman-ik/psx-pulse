from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FinancialFact(Base):
    """A single canonical-taxonomy line item for one issuer/period/scope, tied to its source.

    The "critical formula rule" from the spec: never store a bare number. This row always
    carries period_type, scope and unit so downstream ratios can't silently mix incompatible bases.
    """

    __tablename__ = "financial_fact"

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    line_item: Mapped[str] = mapped_column(String(80), index=True)  # canonical taxonomy key
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date, index=True)
    period_type: Mapped[str] = mapped_column(String(20))  # annual | half_year | quarterly | ttm
    scope: Mapped[str] = mapped_column(String(20))  # standalone | consolidated
    unit: Mapped[str] = mapped_column(String(20), default="PKR")
    value: Mapped[float] = mapped_column(Numeric(20, 2))
    source_document_id: Mapped[int] = mapped_column(ForeignKey("source_document.id"))
    extraction_id: Mapped[int | None] = mapped_column(ForeignKey("extraction.id"), nullable=True)
    is_restated: Mapped[bool] = mapped_column(Boolean, default=False)
    superseded_by_id: Mapped[int | None] = mapped_column(ForeignKey("financial_fact.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RatioDefinition(Base):
    """A versioned formula. Changing the formula creates a new version, never mutates history."""

    __tablename__ = "ratio_definition"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(60), index=True)  # e.g. "roe"
    formula_version: Mapped[int] = mapped_column(default=1)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(30))
    # profitability | growth | liquidity | leverage | efficiency | cash_flow | per_share | valuation
    formula_description: Mapped[str] = mapped_column(String(500))
    unit: Mapped[str] = mapped_column(String(20), default="ratio")


class RatioValue(Base):
    """A computed ratio, retaining exactly which facts and formula version produced it."""

    __tablename__ = "ratio_value"

    id: Mapped[int] = mapped_column(primary_key=True)
    ratio_definition_id: Mapped[int] = mapped_column(ForeignKey("ratio_definition.id"), index=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    period_end: Mapped[date] = mapped_column(Date, index=True)
    period_type: Mapped[str] = mapped_column(String(20))
    scope: Mapped[str] = mapped_column(String(20))
    value: Mapped[float] = mapped_column(Numeric(20, 6))
    input_fact_ids: Mapped[list[int]] = mapped_column(JSON)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
