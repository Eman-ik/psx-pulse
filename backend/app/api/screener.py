from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Issuer, Sector

router = APIRouter(prefix="/screener", tags=["screener"])


@router.get("")
def screen(sector: str | None = "Fertilizer", db: Session = Depends(get_db)) -> list[dict]:
    """v1 screener is Fertilizer-sector-scoped only; a sector filter outside the pilot returns empty."""
    stmt = select(Issuer).join(Sector, Issuer.sector_id == Sector.id).where(Sector.name == sector)
    issuers = db.execute(stmt).scalars().all()
    return [{"id": i.id, "name": i.name} for i in issuers]
