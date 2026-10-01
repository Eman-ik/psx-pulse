"""Records every loader execution in ingestion_run, including what failed to load."""

import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from sqlalchemy.orm import Session

from app.db.models import IngestionRun

logger = logging.getLogger(__name__)


@contextmanager
def ingestion_run(db: Session, source: str, **params) -> Iterator[IngestionRun]:
    """Writers call run.add_error() for any item they could not fetch and bump
    run.rows_inserted for what they stored; status is derived on exit."""
    run = IngestionRun(source=source, params=params, status="running", rows_inserted=0, errors=[])
    db.add(run)
    db.commit()
    try:
        yield run
    except Exception as exc:
        db.rollback()
        run.add_error(f"{type(exc).__name__}: {exc}")
        run.status = "failed"
        raise
    else:
        if not run.errors:
            run.status = "ok"
        else:
            run.status = "partial" if run.rows_inserted else "failed"
    finally:
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(
            "ingestion_run %s [%s] %s: %d rows, %d errors",
            run.id, source, run.status, run.rows_inserted, len(run.errors or []),
        )
