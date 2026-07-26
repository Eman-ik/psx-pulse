from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

SIGNAL_LABELS = ("strong_buy", "buy", "hold", "sell", "strong_sell", "no_signal")


class SignalScore(Base):
    """Versioned output of the rules-based composite scoring + signal policy engine (Milestone 7).

    is_public must stay False (enforced in the scoring service, not just here) until
    settings.public_signals_enabled is true, per the non-negotiable compliance gate.
    """

    __tablename__ = "signal_score"

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    quality_score: Mapped[float] = mapped_column(Numeric(5, 2))
    growth_score: Mapped[float] = mapped_column(Numeric(5, 2))
    financial_health_score: Mapped[float] = mapped_column(Numeric(5, 2))
    valuation_score: Mapped[float] = mapped_column(Numeric(5, 2))
    catalyst_risk_score: Mapped[float] = mapped_column(Numeric(5, 2))
    composite_signal: Mapped[str] = mapped_column(String(20), default="no_signal")
    policy_version: Mapped[int] = mapped_column(default=1)
    suppressed: Mapped[bool] = mapped_column(Boolean, default=False)
    suppression_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
