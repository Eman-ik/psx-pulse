from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import SectorRiskSnapshot

router = APIRouter(prefix="/macro", tags=["macro"])


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
