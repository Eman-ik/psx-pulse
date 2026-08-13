from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.db.models import MlSignalScore

router = APIRouter(prefix="/ml-signals", tags=["ml-signals"])

_DISCLAIMER = (
    "Experimental output of a walk-forward-validated calibrated classifier, for internal "
    "research only. Not a regulated investment recommendation. See docs/research_disclaimer.md."
)


def _row_to_dict(row: MlSignalScore) -> dict:
    def _f(v) -> float | None:
        return float(v) if v is not None else None

    return {
        "as_of_date": row.as_of_date.isoformat(),
        "model_version": row.model_version,
        "signal": row.signal,
        "outperformance_probability": _f(row.outperformance_probability),
        "validation_observations": row.validation_observations,
        "validation_accuracy": _f(row.validation_accuracy),
        "validation_buy_precision": _f(row.validation_buy_precision),
        "validation_sell_precision": _f(row.validation_sell_precision),
        "validation_brier_score": _f(row.validation_brier_score),
        "validation_roc_auc": _f(row.validation_roc_auc),
        "is_public": row.is_public,
    }


@router.get("/research/evidence")
def get_ml_signal_evidence(db: Session = Depends(get_db)) -> dict:
    """Pooled walk-forward validation metrics from the most recent scoring run, for the
    platform-wide "Model Evidence" page. The same metrics are denormalized onto every row of a
    run (see MlSignalScore docstring), so any single latest row carries the full picture.
    """
    row = db.execute(
        select(MlSignalScore).order_by(MlSignalScore.calculated_at.desc())
    ).scalars().first()
    if row is None:
        return {
            "is_research_only": True,
            "reason": "no ML signal scoring run has completed yet -- run app/etl/ml_signal_engine.py",
        }
    return {
        "as_of_date": row.as_of_date.isoformat(),
        "calculated_at": row.calculated_at.isoformat(),
        "model_version": row.model_version,
        "observations": row.validation_observations,
        "accuracy": float(row.validation_accuracy) if row.validation_accuracy is not None else None,
        "buy_precision": float(row.validation_buy_precision) if row.validation_buy_precision is not None else None,
        "sell_precision": float(row.validation_sell_precision) if row.validation_sell_precision is not None else None,
        "brier_score": float(row.validation_brier_score) if row.validation_brier_score is not None else None,
        "roc_auc": float(row.validation_roc_auc) if row.validation_roc_auc is not None else None,
        "is_research_only": True,
        "disclaimer": _DISCLAIMER,
    }


@router.get("/research/{issuer_id}")
def get_ml_signal_research(issuer_id: int, db: Session = Depends(get_db)) -> dict:
    """Internal research view -- returns the latest MlSignalScore row without the public gate.

    Same pattern as GET /signals/research/{issuer_id}: no ML_SIGNALS_ENABLED gate (this is for
    the platform's own UI, not SECP distribution), reads the most recent row regardless of
    is_public, and always includes is_research_only=True + a disclaimer.

    Registered AFTER /research/evidence on purpose -- FastAPI/Starlette matches routes in
    registration order and does not fall through to a later route when an already-matched
    route's path-parameter validation fails, so this literal-suffix route must come first or it
    would 422 instead of ever reaching /research/evidence.
    """
    row = db.execute(
        select(MlSignalScore)
        .where(MlSignalScore.issuer_id == issuer_id)
        .order_by(MlSignalScore.as_of_date.desc())
    ).scalars().first()
    if row is None:
        return {
            "signal": "NO SIGNAL",
            "reason": "no ML signal score computed yet -- run app/etl/ml_signal_engine.py",
            "is_research_only": True,
        }
    result = _row_to_dict(row)
    result["is_research_only"] = True
    result["disclaimer"] = _DISCLAIMER
    return result


@router.get("/{issuer_id}")
def get_ml_signal(issuer_id: int, db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    if not settings.ml_signals_enabled:
        raise HTTPException(
            status_code=403,
            detail=(
                "ML signal output is disabled pending PSX data-licensing and SECP research-"
                "regulation review (see docs/rights_matrix.template.md). Set "
                "ML_SIGNALS_ENABLED=true only after that review is documented."
            ),
        )
    row = db.execute(
        select(MlSignalScore)
        .where(MlSignalScore.issuer_id == issuer_id, MlSignalScore.is_public.is_(True))
        .order_by(MlSignalScore.as_of_date.desc())
    ).scalars().first()
    if row is None:
        return {"signal": "NO SIGNAL", "reason": "no eligible score for this issuer"}
    return _row_to_dict(row)
