from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import FinancialFact, RatioValue

router = APIRouter(prefix="/financials", tags=["financials"])


@router.get("/{issuer_id}/facts")
def list_facts(issuer_id: int, db: Session = Depends(get_db)) -> list[dict]:
    facts = db.execute(select(FinancialFact).where(FinancialFact.issuer_id == issuer_id)).scalars().all()
    return [
        {
            "line_item": f.line_item,
            "period_end": f.period_end.isoformat(),
            "period_type": f.period_type,
            "scope": f.scope,
            "value": float(f.value),
            "unit": f.unit,
        }
        for f in facts
    ]


@router.get("/{issuer_id}/ratios")
def list_ratios(issuer_id: int, db: Session = Depends(get_db)) -> list[dict]:
    ratios = db.execute(select(RatioValue).where(RatioValue.issuer_id == issuer_id)).scalars().all()
    return [
        {
            "ratio_definition_id": r.ratio_definition_id,
            "period_end": r.period_end.isoformat(),
            "scope": r.scope,
            "value": float(r.value),
        }
        for r in ratios
    ]
