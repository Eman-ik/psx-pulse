"""Backfill: classify sentiment_score for Announcement rows using app/etl/sentiment.py
(new rows get classified at ingestion time in psx_announcements.py going forward).

By default only touches rows where sentiment_score is still NULL, so a routine re-run never
overwrites a value that's already been computed. Pass force=True (or --force on the CLI) to
reclassify every row -- needed after a genuine classifier change, e.g. the "closure"/"closed"
false-positive fix that shipped the same day this script was first run (PSX's "Book Closure"/
"Closed Period" boilerplate was being misread as facility-shutdown news).
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Announcement
from app.etl.sentiment import classify_sentiment

logger = logging.getLogger(__name__)


def backfill_sentiment(db: Session, force: bool = False) -> dict[str, int]:
    stmt = select(Announcement) if force else select(Announcement).where(Announcement.sentiment_score.is_(None))
    rows = db.execute(stmt).scalars().all()
    changed = 0
    for row in rows:
        new_score = classify_sentiment(row.title)
        if row.sentiment_score != new_score:
            row.sentiment_score = new_score
            changed += 1
    db.commit()
    return {"considered": len(rows), "changed": changed}


if __name__ == "__main__":
    import sys

    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)
    force_flag = "--force" in sys.argv
    with SessionLocal() as session:
        stats = backfill_sentiment(session, force=force_flag)
        print(stats)
