"""How old the data is, where it came from, and whether the last loads worked."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import FinancialFact, IndexOHLCV, IngestionRun, PriceOHLCV
from app.models.financial_fact import FinancialFact as StatementFact

router = APIRouter(prefix="/data", tags=["data"])

# ponytail: calendar days, so a Friday close stays fresh over the weekend; PSX holidays can
# still trip it. Swap in a trading calendar if false alarms matter.
STALE_AFTER_DAYS = 4


def freshness(db: Session, model, *filters) -> dict:
    as_of, retrieved_at = db.execute(
        select(func.max(model.trade_date), func.max(model.retrieved_at)).where(*filters)
    ).one()
    sources = sorted(db.execute(select(model.source).where(*filters).distinct()).scalars())
    return {
        "as_of": as_of.isoformat() if as_of else None,
        "retrieved_at": retrieved_at.isoformat() if retrieved_at else None,
        "sources": sources,
        "stale": as_of is None or (date.today() - as_of).days > STALE_AFTER_DAYS,
    }


def _latest_runs(db: Session) -> list[dict]:
    latest: dict[tuple, IngestionRun] = {}
    for run in db.execute(select(IngestionRun).order_by(IngestionRun.id.desc()).limit(200)).scalars():
        latest.setdefault((run.source, (run.params or {}).get("table")), run)
    return [
        {
            "id": run.id,
            "source": source,
            "table": table,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "rows_inserted": run.rows_inserted,
            "error_count": len(run.errors or []),
            "errors": (run.errors or [])[:5],
        }
        for (source, table), run in latest.items()
    ]


@router.get("/status")
def data_status(db: Session = Depends(get_db)) -> dict:
    return {
        "prices": {
            **freshness(db, PriceOHLCV),
            "bars": db.execute(select(func.count(PriceOHLCV.id))).scalar(),
            "securities": db.execute(select(func.count(func.distinct(PriceOHLCV.security_id)))).scalar(),
        },
        "indices": {
            **freshness(db, IndexOHLCV),
            "bars": db.execute(select(func.count(IndexOHLCV.id))).scalar(),
            "indices": db.execute(select(func.count(func.distinct(IndexOHLCV.market_index_id)))).scalar(),
        },
        "fundamentals": {
            "statement_facts": db.execute(select(func.count(FinancialFact.id))).scalar()
            + db.execute(select(func.count(StatementFact.id))).scalar(),
            "issuers_with_statements": db.execute(select(func.count(func.distinct(FinancialFact.issuer_id)))).scalar()
            + db.execute(select(func.count(func.distinct(StatementFact.company_id)))).scalar(),
        },
        "latest_runs": _latest_runs(db),
    }
