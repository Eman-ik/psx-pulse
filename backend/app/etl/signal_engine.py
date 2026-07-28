"""Rules-based composite signal scoring engine (Milestone 7 / plan Phase 3).

Deliberately NOT a trained/calibrated ML model -- the plan's own note on AI/ML honesty (spec
section 7.2/7.5) says to prefer interpretable rules over claiming ML precision, especially with
~5 companies and thin free history, where a "trained model" would be theater. Evidence class:
"predictive_model_output" (see app/db/models/evidence.py) -- an interpretation derived from
real ratios, never presented as a regulated recommendation.

Seven 0-100 dimension scores (matching SignalScore's columns exactly): quality, growth,
financial_health, valuation, catalyst_risk, momentum, risk. Each is a PEER-RELATIVE score --
the same "compare to the mean of the other covered companies" methodology already used for the
Ratios tab's Healthy/Average/Watch badges (see app/api/comparison.py's ratio_benchmarks / the
frontend's RatioGrid.tsx), not an arbitrary absolute threshold nobody could defend. A dimension
with zero available input metrics is left as None (not defaulted to a fake neutral 50) and
excluded from the composite average.

momentum and risk reuse data this project already computes elsewhere -- nothing new is
ingested for them either. momentum is a trailing ~6-month price return computed fresh from
PriceOHLCV.close (no existing module computes this, so the date-tolerance math lives here,
factored into a pure function for unit testing). risk reuses the beta already computed and
stored by app/etl/beta.py (Cov/Var of daily returns vs KSE-100, stored in CapmAssumption) --
lower beta relative to peers scores higher here, meaning "lower measured systematic risk", not
a general quality judgment; a defensive low-beta stock is not "better" in every sense just
because this one dimension scores it higher.

Mandatory suppressors (per the plan's explicit language: "versioned signal policy with
mandatory suppressors") force composite_signal="no_signal", suppressed=True regardless of the
computed score:
  1. Fewer than MIN_DIMENSIONS_FOR_SIGNAL of the 7 dimensions have any real data -- too little
     coverage to mean anything.
  2. The security is delisted (Security.is_active is False) -- a signal for a stock that no
     longer trades is meaningless, not just low-confidence.

is_public always tracks settings.public_signals_enabled at compute time (never hardcoded) --
the non-negotiable compliance gate. That flag defaults False and this module never touches
backend/app/core/config.py, so every row this produces stays non-public unless a human has
already flipped that flag after the compliance review the flag exists to gate.
"""

import logging
from datetime import date, timedelta
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import (
    Announcement,
    CapmAssumption,
    Issuer,
    PriceOHLCV,
    RatioDefinition,
    RatioValue,
    Security,
    SignalScore,
)

logger = logging.getLogger(__name__)

POLICY_VERSION = 2

# dimension -> [(ratio_key, higher_is_better), ...]. Same key set already computed by
# app/etl/ratio_engine.py and app/etl/valuation_engine.py -- nothing new is ingested here.
DIMENSION_METRICS: dict[str, list[tuple[str, bool]]] = {
    "quality": [
        ("roe", True),
        ("roa", True),
        ("gross_profit_margin", True),
        ("operating_profit_margin", True),
    ],
    "growth": [
        ("revenue_growth_yoy", True),
        ("pat_growth_yoy", True),
        ("eps_growth_yoy", True),
    ],
    "financial_health": [
        ("current_ratio", True),
        ("debt_to_equity", False),
        ("debt_to_assets", False),
    ],
    "valuation": [
        ("price_to_earnings", False),
        ("price_to_book", False),
        ("price_to_sales", False),
    ],
}

MIN_DIMENSIONS_FOR_SIGNAL = 2
SENTIMENT_WINDOW_DAYS = 365
MOMENTUM_WINDOW_DAYS = 180
MOMENTUM_TOLERANCE_DAYS = 10

SIGNAL_THRESHOLDS: list[tuple[float, str]] = [
    (75, "strong_buy"),
    (60, "buy"),
    (40, "hold"),
    (25, "sell"),
]


def peer_relative_score(value: float, peer_mean: float, higher_is_better: bool) -> float:
    """0-100, centered at 50 when value equals the peer mean. Deviation is expressed as a
    fraction of the peer mean's magnitude, capped at +/-100% before scaling, so one wild
    outlier metric can't single-handedly peg a dimension at 0 or 100.
    """
    if peer_mean == 0:
        return 50.0
    deviation = (value - peer_mean) / abs(peer_mean)
    deviation = max(-1.0, min(1.0, deviation))
    if not higher_is_better:
        deviation = -deviation
    return 50.0 + deviation * 50.0


def _latest_ratio_values(db: Session, ratio_key: str) -> dict[int, float]:
    """issuer_id -> latest value on file for this ratio key, across ALL issuers (used both to
    get one company's value and to compute the peer mean from the same query).
    """
    rows = db.execute(
        select(RatioValue, RatioDefinition).join(RatioDefinition, RatioDefinition.id == RatioValue.ratio_definition_id).where(
            RatioDefinition.key == ratio_key
        )
    ).all()
    latest: dict[int, tuple] = {}
    for ratio_value, _definition in rows:
        key = (ratio_value.period_end, ratio_value.id)
        if ratio_value.issuer_id not in latest or key > latest[ratio_value.issuer_id][0]:
            latest[ratio_value.issuer_id] = (key, float(ratio_value.value))
    return {issuer_id: v for issuer_id, (_, v) in latest.items()}


def compute_dimension_score(db: Session, issuer_id: int, metrics: list[tuple[str, bool]]) -> float | None:
    sub_scores = []
    for ratio_key, higher_is_better in metrics:
        by_issuer = _latest_ratio_values(db, ratio_key)
        value = by_issuer.get(issuer_id)
        if value is None or len(by_issuer) < 2:  # need at least one peer to compare against
            continue
        peer_mean = sum(by_issuer.values()) / len(by_issuer)
        sub_scores.append(peer_relative_score(value, peer_mean, higher_is_better))
    if not sub_scores:
        return None
    return sum(sub_scores) / len(sub_scores)


def compute_catalyst_risk_score(db: Session, issuer_id: int, as_of: date) -> float | None:
    """Mean sentiment_score (see app/etl/sentiment.py) of this issuer's announcements in the
    trailing SENTIMENT_WINDOW_DAYS, rescaled from [-1, 1] to [0, 100]. Real, keyword-derived
    news flow as the catalyst/risk proxy -- not a count of Thesis bullet points, which would be
    gameable and not really "risk" in any measurable sense.
    """
    window_start = as_of - timedelta(days=SENTIMENT_WINDOW_DAYS)
    rows = db.execute(
        select(Announcement.sentiment_score).where(
            Announcement.issuer_id == issuer_id,
            Announcement.published_at >= window_start,
            Announcement.sentiment_score.is_not(None),
        )
    ).scalars().all()
    scores = [s for s in rows if s is not None]
    if not scores:
        return None
    mean_sentiment = sum(scores) / len(scores)
    return 50.0 + mean_sentiment * 50.0


def compute_momentum_pct(bars: Sequence[tuple[date, float]], as_of: date) -> float | None:
    """Trailing MOMENTUM_WINDOW_DAYS price return: (latest_close - anchor_close) / anchor_close.

    "latest" is the bar closest to as_of, "anchor" is the bar closest to
    as_of - MOMENTUM_WINDOW_DAYS. PSX doesn't trade every calendar day, so both are found within
    MOMENTUM_TOLERANCE_DAYS rather than requiring an exact date match. Returns None (never a
    fabricated 0%) if either anchor has no bar within tolerance, or the anchor close is 0.
    """
    if not bars:
        return None

    def _closest_within_tolerance(target: date) -> float | None:
        closest = min(bars, key=lambda b: abs((b[0] - target).days))
        if abs((closest[0] - target).days) > MOMENTUM_TOLERANCE_DAYS:
            return None
        return closest[1]

    latest_close = _closest_within_tolerance(as_of)
    anchor_close = _closest_within_tolerance(as_of - timedelta(days=MOMENTUM_WINDOW_DAYS))
    if latest_close is None or anchor_close is None or anchor_close == 0:
        return None
    return (latest_close - anchor_close) / anchor_close


def _latest_momentum_values(db: Session, as_of: date) -> dict[int, float]:
    """issuer_id -> trailing momentum, across all issuers with a security and enough price
    history -- same shape/purpose as _latest_ratio_values (one company's value plus the peer mean
    come from this same dict).
    """
    issuers: Sequence[Issuer] = db.execute(select(Issuer).where(Issuer.securities.any())).scalars().all()
    momentum_by_issuer: dict[int, float] = {}
    for issuer in issuers:
        security = issuer.securities[0] if issuer.securities else None
        if security is None:
            continue
        bars = [
            (b.trade_date, float(b.close))
            for b in db.execute(select(PriceOHLCV).where(PriceOHLCV.security_id == security.id)).scalars()
        ]
        momentum = compute_momentum_pct(bars, as_of)
        if momentum is not None:
            momentum_by_issuer[issuer.id] = momentum
    return momentum_by_issuer


def compute_momentum_score(db: Session, issuer_id: int, as_of: date) -> float | None:
    by_issuer = _latest_momentum_values(db, as_of)
    value = by_issuer.get(issuer_id)
    if value is None or len(by_issuer) < 2:  # need at least one peer to compare against
        return None
    peer_mean = sum(by_issuer.values()) / len(by_issuer)
    return peer_relative_score(value, peer_mean, higher_is_better=True)


def _latest_beta_values(db: Session) -> dict[int, float]:
    """issuer_id -> latest beta on file (from app/etl/beta.py's CapmAssumption rows), excluding
    the market-wide issuer_id-is-null default row.
    """
    rows = db.execute(
        select(CapmAssumption).where(CapmAssumption.issuer_id.is_not(None), CapmAssumption.beta.is_not(None))
    ).scalars().all()
    latest: dict[int, tuple[date, float]] = {}
    for row in rows:
        if row.issuer_id not in latest or row.as_of_date > latest[row.issuer_id][0]:
            latest[row.issuer_id] = (row.as_of_date, float(row.beta))
    return {issuer_id: v for issuer_id, (_, v) in latest.items()}


def compute_risk_score(db: Session, issuer_id: int) -> float | None:
    """Peer-relative score on beta -- lower beta than peers scores higher here, i.e. "lower
    measured systematic risk", not a general quality judgment (see module docstring).
    """
    by_issuer = _latest_beta_values(db)
    value = by_issuer.get(issuer_id)
    if value is None or len(by_issuer) < 2:  # need at least one peer to compare against
        return None
    peer_mean = sum(by_issuer.values()) / len(by_issuer)
    return peer_relative_score(value, peer_mean, higher_is_better=False)


def _label_for_score(score: float) -> str:
    for threshold, label in SIGNAL_THRESHOLDS:
        if score >= threshold:
            return label
    return "strong_sell"


def compose_signal(dimension_scores: dict[str, float | None], is_delisted: bool) -> dict:
    """Pure policy step: given the (possibly-missing) dimension scores and whether the
    security is delisted, decides suppression and the composite label. Kept separate from the
    DB-querying functions above so the actual decision logic is unit-testable without a
    database.
    """
    available = {k: v for k, v in dimension_scores.items() if v is not None}
    suppression_reasons: list[str] = []

    if is_delisted:
        suppression_reasons.append("security is delisted or untracked")
    if len(available) < MIN_DIMENSIONS_FOR_SIGNAL:
        suppression_reasons.append(
            f"only {len(available)} of {len(dimension_scores)} score dimensions have data "
            f"(minimum {MIN_DIMENSIONS_FOR_SIGNAL} required)"
        )

    suppressed = len(suppression_reasons) > 0
    composite_score = sum(available.values()) / len(available) if available else 50.0
    composite_signal = "no_signal" if suppressed else _label_for_score(composite_score)

    return {
        "composite_score": composite_score,
        "composite_signal": composite_signal,
        "suppressed": suppressed,
        "suppression_reasons": suppression_reasons,
    }


def compute_signal(db: Session, issuer: Issuer, security: Security | None, as_of: date) -> SignalScore:
    settings = get_settings()

    dimension_scores: dict[str, float | None] = {
        dim: compute_dimension_score(db, issuer.id, metrics) for dim, metrics in DIMENSION_METRICS.items()
    }
    dimension_scores["catalyst_risk"] = compute_catalyst_risk_score(db, issuer.id, as_of)
    dimension_scores["momentum"] = compute_momentum_score(db, issuer.id, as_of)
    dimension_scores["risk"] = compute_risk_score(db, issuer.id)

    policy = compose_signal(dimension_scores, is_delisted=security is None or not security.is_active)

    # All 7 *_score columns are nullable, so a dimension with no peer-comparable data is stored
    # as a real NULL, not a fake 0.0. Still record which dimensions were unavailable as
    # informational notes (independent of whether the row ends up suppressed overall).
    missing_dimension_notes = [f"{dim} dimension: no peer-comparable data available" for dim, v in dimension_scores.items() if v is None]

    return SignalScore(
        issuer_id=issuer.id,
        as_of_date=as_of,
        quality_score=dimension_scores["quality"],
        growth_score=dimension_scores["growth"],
        financial_health_score=dimension_scores["financial_health"],
        valuation_score=dimension_scores["valuation"],
        catalyst_risk_score=dimension_scores["catalyst_risk"],
        momentum_score=dimension_scores["momentum"],
        risk_score=dimension_scores["risk"],
        composite_signal=policy["composite_signal"],
        policy_version=POLICY_VERSION,
        suppressed=policy["suppressed"],
        suppression_reasons=[*policy["suppression_reasons"], *missing_dimension_notes],
        is_public=settings.public_signals_enabled,
    )


def run_for_all_issuers(db: Session, as_of: date | None = None) -> dict[str, dict]:
    as_of = as_of or date.today()
    issuers: Sequence[Issuer] = db.execute(select(Issuer).where(Issuer.securities.any())).scalars().all()

    results = {}
    for issuer in issuers:
        security = issuer.securities[0] if issuer.securities else None
        score = compute_signal(db, issuer, security, as_of)

        existing = db.execute(
            select(SignalScore).where(SignalScore.issuer_id == issuer.id, SignalScore.as_of_date == as_of)
        ).scalar_one_or_none()
        if existing is not None:
            db.delete(existing)
            db.flush()
        db.add(score)

        def _round_or_none(v: float | None) -> float | None:
            return round(v, 1) if v is not None else None

        results[issuer.name] = {
            "composite_signal": score.composite_signal,
            "suppressed": score.suppressed,
            "suppression_reasons": score.suppression_reasons,
            "quality": _round_or_none(score.quality_score),
            "growth": _round_or_none(score.growth_score),
            "financial_health": _round_or_none(score.financial_health_score),
            "valuation": _round_or_none(score.valuation_score),
            "catalyst_risk": _round_or_none(score.catalyst_risk_score),
            "momentum": _round_or_none(score.momentum_score),
            "risk": _round_or_none(score.risk_score),
            "is_public": score.is_public,
        }

    db.commit()
    return results


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    settings = get_settings()
    if settings.public_signals_enabled:
        logger.warning(
            "PUBLIC_SIGNALS_ENABLED is true -- rows computed now will be marked is_public=True. "
            "Only proceed if the compliance review documented in docs/rights_matrix.template.md "
            "has actually happened."
        )

    with SessionLocal() as session:
        for name, result in run_for_all_issuers(session).items():
            print(f"{name}: {result}")
