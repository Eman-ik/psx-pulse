from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ANNOUNCEMENT_CATEGORIES = (
    "results",
    "dividend",
    "board",
    "contract",
    "production",
    "regulatory",
    "litigation",
    "capex",
    "financing",
    "rating",
    "m_and_a",
    "other",
)


class Announcement(Base):
    """A classified corporate announcement/event, always traceable to its raw source document."""

    __tablename__ = "announcement"

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int | None] = mapped_column(ForeignKey("issuer.id"), nullable=True, index=True)
    source_document_id: Mapped[int] = mapped_column(ForeignKey("source_document.id"))
    title: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(30), default="other")
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # Sentiment kept separate from price impact/causality per spec section 6.4.
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class EntityLink(Base):
    """Resolves an announcement/document to the issuer/sector it concerns, with a confidence score."""

    __tablename__ = "entity_link"

    id: Mapped[int] = mapped_column(primary_key=True)
    announcement_id: Mapped[int | None] = mapped_column(ForeignKey("announcement.id"), nullable=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sector.id"), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    resolved_by: Mapped[str] = mapped_column(String(20), default="analyst")  # auto | analyst
