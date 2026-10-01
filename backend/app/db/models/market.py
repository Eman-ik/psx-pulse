from datetime import date, datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
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
    """Structured corporate action record; price adjustment must derive from this, not be hardcoded.

    verified distinguishes a row backed by a real source document (source_document_id
    set, verified=True) from one an algorithmic detector produced by noticing a price
    discontinuity that a fresh re-scrape confirms is real -- confirmed real data, but
    not yet cross-checked against an actual PSX announcement. Both kinds are applied by
    price_adjustment.py (an unadjusted chart is a worse default than a best-effort one),
    but the distinction stays visible in every response that surfaces these rows.
    """

    __tablename__ = "corporate_action"

    id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(20))
    announced_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date] = mapped_column(Date, index=True)
    ratio_or_amount: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("source_document.id"), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


INGESTION_RUN_STATUSES = ("running", "ok", "partial", "failed")


class IngestionRun(Base):
    """One execution of a data loader. Fetch failures are recorded here, never papered over
    with generated values: 'partial' means some items failed and got no rows."""

    __tablename__ = "ingestion_run"
    __table_args__ = (
        CheckConstraint("status IN ('running','ok','partial','failed')", name="ck_ingestion_run_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(40))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rows_inserted: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    def add_error(self, message: str) -> None:
        # Reassign so SQLAlchemy sees the JSON change.
        self.errors = [*(self.errors or []), message]


class PriceOHLCV(Base):
    """Daily OHLCV bar. is_delayed defaults True since v1 has no licensed real-time feed.

    source has no default on purpose: every writer must name where the bar came from.
    """

    __tablename__ = "price_ohlcv"
    __table_args__ = (
        UniqueConstraint("security_id", "trade_date", name="uq_price_ohlcv_security_date"),
        CheckConstraint("source <> ''", name="ck_price_ohlcv_source_nonempty"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security.id"), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    source: Mapped[str] = mapped_column(String(40))
    ingestion_run_id: Mapped[int] = mapped_column(ForeignKey("ingestion_run.id"), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
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


class MarketIndex(Base):
    """A PSX benchmark index (e.g. KSE-100). Deliberately separate from Issuer/Security —
    an index is not a company, so it doesn't belong in the identity master.
    """

    __tablename__ = "market_index"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # e.g. "KSE100", psxdata's symbol
    name: Mapped[str] = mapped_column(String(120))


class IndexOHLCV(Base):
    """Daily OHLCV bar for a market index. Same shape as PriceOHLCV; kept as a separate table
    rather than reusing security_id, since an index isn't a Security.
    """

    __tablename__ = "index_ohlcv"
    __table_args__ = (
        UniqueConstraint("market_index_id", "trade_date", name="uq_index_ohlcv_index_date"),
        CheckConstraint("source <> ''", name="ck_index_ohlcv_source_nonempty"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    market_index_id: Mapped[int] = mapped_column(ForeignKey("market_index.id"), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    source: Mapped[str] = mapped_column(String(40))
    ingestion_run_id: Mapped[int] = mapped_column(ForeignKey("ingestion_run.id"), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    open: Mapped[float] = mapped_column(Numeric(14, 4))
    high: Mapped[float] = mapped_column(Numeric(14, 4))
    low: Mapped[float] = mapped_column(Numeric(14, 4))
    close: Mapped[float] = mapped_column(Numeric(14, 4))
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_delayed: Mapped[bool] = mapped_column(Boolean, default=True)
