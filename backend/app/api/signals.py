from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.db.models import SignalScore

router = APIRouter(prefix="/signals", tags=["signals"])


def _signal_row_to_dict(row: SignalScore) -> dict:
    def _f(v) -> float | None:
        return float(v) if v is not None else None
    return {
        "as_of_date": row.as_of_date.isoformat(),
        "quality_score": _f(row.quality_score),
        "growth_score": _f(row.growth_score),
        "financial_health_score": _f(row.financial_health_score),
        "valuation_score": _f(row.valuation_score),
        "catalyst_risk_score": _f(row.catalyst_risk_score),
        "momentum_score": _f(row.momentum_score),
        "risk_score": _f(row.risk_score),
        "composite_signal": row.composite_signal,
        "policy_version": row.policy_version,
        "suppressed": row.suppressed,
        "suppression_reasons": row.suppression_reasons,
    }


@router.get("/research/{issuer_id}")
def get_signal_research(issuer_id: int, db: Session = Depends(get_db)) -> dict:
    """Internal research view — returns the latest signal score without the public gate.

    This endpoint is explicitly NOT the same as the public signal output:
    - No PUBLIC_SIGNALS_ENABLED gate (this is for the researcher's own tool, not SECP distribution)
    - Reads the most recent SignalScore row regardless of is_public flag
    - Response includes is_research_only=True and a disclaimer to prevent misuse

    The SECP compliance gate (PUBLIC_SIGNALS_ENABLED) still applies to the /signals/{id}
    endpoint and to any external distribution. This endpoint is for the platform's own UI only.
    """
    row = db.execute(
        select(SignalScore)
        .where(SignalScore.issuer_id == issuer_id)
        .order_by(SignalScore.as_of_date.desc())
    ).scalars().first()
    if row is None:
        return {
            "composite_signal": "no_signal",
            "reason": "no signal score computed yet — run app/etl/signal_engine.py",
            "is_research_only": True,
        }
    result = _signal_row_to_dict(row)
    result["is_research_only"] = True
    result["disclaimer"] = (
        "Experimental rules-based output for internal research only. "
        "Not a regulated investment recommendation. "
        "See docs/research_disclaimer.md."
    )
    return result


@router.get("/{issuer_id}")
def get_signal(issuer_id: int, db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    if not settings.public_signals_enabled:
        raise HTTPException(
            status_code=403,
            detail=(
                "AI signal output is disabled pending PSX data-licensing and SECP research-"
                "regulation review (see docs/rights_matrix.template.md). Set "
                "PUBLIC_SIGNALS_ENABLED=true only after that review is documented."
            ),
        )
    row = db.execute(
        select(SignalScore)
        .where(SignalScore.issuer_id == issuer_id, SignalScore.is_public.is_(True))
        .order_by(SignalScore.as_of_date.desc())
    ).scalars().first()
    if row is None or row.suppressed:
        return {"composite_signal": "no_signal", "reason": "no eligible score for this issuer"}
    return _signal_row_to_dict(row)
