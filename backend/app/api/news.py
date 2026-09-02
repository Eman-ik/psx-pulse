from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Announcement, SourceDocument

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/announcements")
def list_announcements(
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, ge=1, le=2000),
    issuer_id: int | None = None,
) -> list[dict]:
    """`limit`/`issuer_id` are optional and unset by default, preserving the existing
    unbounded full-list response the frontend's client-side news feed filtering relies on
    today -- this just gives future/bulk callers a way to bound the query instead of always
    pulling every Announcement row in the DB, which has no cap otherwise.
    """
    query = (
        select(Announcement, SourceDocument)
        .join(SourceDocument, SourceDocument.id == Announcement.source_document_id)
        .order_by(Announcement.published_at.desc())
    )
    if issuer_id is not None:
        query = query.where(Announcement.issuer_id == issuer_id)
    if limit is not None:
        query = query.limit(limit)
    rows = db.execute(query).all()
    return [
        {
            "id": a.id,
            "issuer_id": a.issuer_id,
            "title": a.title,
            "category": a.category,
            "published_at": a.published_at.isoformat(),
            "summary": a.summary,
            "sentiment_score": a.sentiment_score,
            "source_url": sd.url,
        }
        for a, sd in rows
    ]
