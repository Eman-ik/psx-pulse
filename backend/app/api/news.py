from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Announcement

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/announcements")
def list_announcements(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(Announcement).order_by(Announcement.published_at.desc())).scalars().all()
    return [
        {
            "id": a.id,
            "issuer_id": a.issuer_id,
            "title": a.title,
            "category": a.category,
            "published_at": a.published_at.isoformat(),
            "sentiment_score": a.sentiment_score,
        }
        for a in rows
    ]
