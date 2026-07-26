from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

CORPORATE_ACTION_TYPES = (
    "dividend",
    "bonus",
    "rights",
    "split",
    "consolidation",
    "merger",
    "ticker_change",
    "suspension",
    "delisting",
    "ipo",
)


class CorporateAction(Base):
    """Structured corporate action record; price adjustment must derive from this, not be hardcoded."""

    __tablename__ = "corporate_action"

    id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(20))
    announced_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date] = mapped_column(Date, index=True)
    ratio_or_amount: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("source_document.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PriceOHLCV(Base):
    """Daily OHLCV bar. is_delayed defaults True since v1 has no licensed real-time feed."""

    __tablename__ = "price_ohlcv"

    id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security.id"), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    open: Mapped[float] = mapped_column(Numeric(14, 4))
    high: Mapped[float] = mapped_column(Numeric(14, 4))
    low: Mapped[float] = mapped_column(Numeric(14, 4))
    close: Mapped[float] = mapped_column(Numeric(14, 4))
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    value: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    trades: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adjusted: Mapped[bool] = mapped_column(Boolean, default=False)
    adjustment_method: Mapped[str | None] = mapped_column(String(60), nullable=True)
    circuit_upper: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    circuit_lower: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    is_delayed: Mapped[bool] = mapped_column(Boolean, default=True)
