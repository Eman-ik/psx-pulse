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


ML_SIGNAL_LABELS = ("BUY", "HOLD", "NO SIGNAL")


class MlSignalScore(Base):
    """Output of the walk-forward-validated calibrated ML classifier (app/etl/ml_signal_engine.py).

    Deliberately a separate table from SignalScore: this is a genuinely different evidence
    class (a trained/calibrated model's out-of-sample probability estimate) from the rules-based
    peer-relative scoring above, and the two should never be silently conflated in one row.

    Trained pooled across the full PSX universe already in PriceOHLCV (not just the fertilizer
    pilot names) -- a 5-company universe is too thin to validate a classifier honestly, which is
    exactly why app/etl/signal_engine.py stayed rules-based. Pooling across ~250 symbols with
    deep history resolves that objection; this table then simply stores the per-issuer row of
    that pooled model's output, whichever sector the issuer belongs to.

    signal is never "SELL" -- see app/etl/ml_signal_engine.py: the model only estimates the
    probability of clearing a positive-excess-return hurdle, so a low probability is evidence of
    "no edge detected", not evidence of a negative return.

    is_public must stay False (enforced in the scoring service, not just here) until
    settings.ml_signals_enabled is true -- same non-negotiable compliance gate as SignalScore.
    """

    __tablename__ = "ml_signal_score"

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    model_version: Mapped[int] = mapped_column(default=1)
    signal: Mapped[str] = mapped_column(String(20), default="NO SIGNAL")
    outperformance_probability: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)

    # Pooled walk-forward validation metrics for the model run that produced this row -- the
    # same values repeat across every issuer scored in one run (one model, scored for everyone).
    # Denormalized on purpose so each row is a self-contained, auditable record without a join,
    # and so GET /ml-signals/research/evidence can just read the metrics off the latest row.
    validation_observations: Mapped[int | None] = mapped_column(nullable=True)
    validation_accuracy: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    validation_buy_precision: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    validation_sell_precision: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    validation_brier_score: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    validation_roc_auc: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)

    # positive_rate is the base rate of "beat the benchmark" across the pooled walk-forward
    # population -- what a random, size-matched subset would score by construction, with zero
    # skill. beats_naive_baseline (validation_buy_precision > validation_positive_rate) gates
    # BUY the same way signal_qualification.py's beats_naive_baseline gates Kronos: a fixed
    # precision floor means nothing if the population's own base rate already clears it. See
    # app/etl/ml_signal_engine.py's validation_metrics().
    validation_positive_rate: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    beats_naive_baseline: Mapped[bool] = mapped_column(Boolean, default=False)

    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
