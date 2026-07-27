from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.db.models import SignalScore

router = APIRouter(prefix="/signals", tags=["signals"])


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
    return {
        "as_of_date": row.as_of_date.isoformat(),
        "quality_score": float(row.quality_score),
        "growth_score": float(row.growth_score),
        "financial_health_score": float(row.financial_health_score),
        "valuation_score": float(row.valuation_score),
        "catalyst_risk_score": float(row.catalyst_risk_score),
        "composite_signal": row.composite_signal,
        "policy_version": row.policy_version,
        "suppression_reasons": row.suppression_reasons,
    }
