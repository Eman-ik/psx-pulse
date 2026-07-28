from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

SIGNAL_LABELS = ("strong_buy", "buy", "hold", "sell", "strong_sell", "no_signal")


class SignalScore(Base):
    """Versioned output of the rules-based composite scoring + signal policy engine (Milestone 7).

    Seven dimension columns, each nullable: a dimension with no peer-comparable data is stored
    as a real NULL, never a fabricated 0.0 (see app/etl/signal_engine.py). risk_score is a
    beta-based measure of systematic risk relative to peers, NOT a general quality judgment --
    a higher risk_score means lower measured beta than peers, not "better" in every sense.

    is_public must stay False (enforced in the scoring service, not just here) until
    settings.public_signals_enabled is true, per the non-negotiable compliance gate.
    """

    __tablename__ = "signal_score"

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    quality_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    growth_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    financial_health_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    valuation_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    catalyst_risk_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    momentum_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    composite_signal: Mapped[str] = mapped_column(String(20), default="no_signal")
    policy_version: Mapped[int] = mapped_column(default=1)
    suppressed: Mapped[bool] = mapped_column(Boolean, default=False)
    suppression_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
