from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Evidence classes shown to the user (spec section 3.1)
EVIDENCE_CLASSES = (
    "reported_fact",
    "calculated_metric",
    "third_party_estimate",
    "analyst_interpretation",
    "predictive_model_output",
)

SOURCE_TIERS = ("primary", "licensed_secondary", "prohibited")


class SourceDocument(Base):
    """An immutable original document (filing, announcement, report) with lineage metadata."""

    __tablename__ = "source_document"
    __table_args__ = (
        CheckConstraint("url IS NOT NULL OR local_path IS NOT NULL", name="ck_source_document_locator"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int | None] = mapped_column(ForeignKey("issuer.id"), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    document_type: Mapped[str] = mapped_column(String(60))
    source_tier: Mapped[str] = mapped_column(String(30), default="primary")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    extractions: Mapped[list["Extraction"]] = relationship(back_populates="source_document")


class Extraction(Base):
    """A parse/extraction pass over a source document (manual entry counts as a method)."""

    __tablename__ = "extraction"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_document_id: Mapped[int] = mapped_column(ForeignKey("source_document.id"), index=True)
    method: Mapped[str] = mapped_column(String(20), default="manual")  # manual | ocr | parsed
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    source_document: Mapped[SourceDocument] = relationship(back_populates="extractions")


class EvidenceLink(Base):
    """Ties any displayed fact/metric/interpretation to its evidence class and source lineage.

    target_table/target_id is a generic pointer (e.g. "financial_fact", 42) rather than a
    polymorphic FK, since the evidence model must cover many unrelated target tables.
    """

    __tablename__ = "evidence_link"

    id: Mapped[int] = mapped_column(primary_key=True)
    evidence_class: Mapped[str] = mapped_column(String(30))
    target_table: Mapped[str] = mapped_column(String(60))
    target_id: Mapped[int] = mapped_column()
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("source_document.id"), nullable=True)
    extraction_id: Mapped[int | None] = mapped_column(ForeignKey("extraction.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
