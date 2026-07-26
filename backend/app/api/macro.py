from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import MacroObservation, MacroSeries, SectorRiskSnapshot

router = APIRouter(prefix="/macro", tags=["macro"])


@router.get("/series")
def list_series(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(MacroSeries)).scalars().all()
    return [
        {"code": s.code, "name": s.name, "source": s.source, "frequency": s.frequency, "unit": s.unit}
        for s in rows
    ]


@router.get("/series/{code}")
def get_series(code: str, db: Session = Depends(get_db)) -> dict | None:
    series = db.execute(select(MacroSeries).where(MacroSeries.code == code)).scalar_one_or_none()
    if series is None:
        return None
    observations = db.execute(
        select(MacroObservation)
        .where(MacroObservation.macro_series_id == series.id)
        .order_by(MacroObservation.period)
    ).scalars().all()
    return {
        "code": series.code,
        "name": series.name,
        "source": series.source,
        "unit": series.unit,
        "observations": [{"period": o.period.isoformat(), "value": float(o.value)} for o in observations],
    }


@router.get("/risk-snapshot")
def latest_risk_snapshot(db: Session = Depends(get_db)) -> dict | None:
    row = db.execute(
        select(SectorRiskSnapshot).order_by(SectorRiskSnapshot.as_of_date.desc())
    ).scalars().first()
    if row is None:
        return None
    return {
        "as_of_date": row.as_of_date.isoformat(),
        "overall_risk": row.overall_risk,
        "geopolitical": row.geopolitical,
        "economy": row.economy,
        "imf_program": row.imf_program,
        "currency_pkr": row.currency_pkr,
        "key_positives": row.key_positives,
        "key_negatives": row.key_negatives,
    }
