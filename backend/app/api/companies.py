from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Issuer

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("")
def list_companies(db: Session = Depends(get_db)) -> list[dict]:
    issuers = db.execute(select(Issuer)).scalars().all()
    return [
        {"id": i.id, "name": i.name, "short_name": i.short_name, "sector_id": i.sector_id}
        for i in issuers
    ]


@router.get("/{issuer_id}")
def get_company(issuer_id: int, db: Session = Depends(get_db)) -> dict | None:
    issuer = db.get(Issuer, issuer_id)
    if issuer is None:
        return None
    return {"id": issuer.id, "name": issuer.name, "short_name": issuer.short_name}
