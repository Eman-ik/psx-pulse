"""Source-linked financial statements and the ratios computed from them, per ticker."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import FinancialFact, RatioDefinition, RatioValue, Security, SourceDocument
from app.etl.ratio_engine import reconcile_balance_sheet

router = APIRouter(prefix="/fundamentals", tags=["fundamentals"])


@router.get("/{symbol}")
def fundamentals(symbol: str, db: Session = Depends(get_db)) -> dict:
    security = db.execute(select(Security).where(Security.symbol == symbol.upper())).scalar_one_or_none()
    if security is None:
        raise HTTPException(status_code=404, detail=f"Unknown symbol {symbol}")
    issuer = security.issuer

    facts = db.execute(
        select(FinancialFact)
        .where(FinancialFact.issuer_id == issuer.id, FinancialFact.superseded_by_id.is_(None))
        .order_by(FinancialFact.line_item, FinancialFact.period_end)
    ).scalars().all()
    fact_ids = {f.id for f in facts}
    documents = db.execute(
        select(SourceDocument).where(SourceDocument.id.in_({f.source_document_id for f in facts}))
    ).scalars().all()

    # Only ratios whose every input is a current, source-linked fact on this page.
    rows = db.execute(
        select(RatioValue, RatioDefinition)
        .join(RatioDefinition, RatioDefinition.id == RatioValue.ratio_definition_id)
        .where(RatioValue.issuer_id == issuer.id)
        .order_by(RatioDefinition.category, RatioDefinition.key, RatioValue.period_end)
    ).all()
    ratios = [
        {
            "key": d.key,
            "name": d.name,
            "category": d.category,
            "unit": d.unit,
            "formula": d.formula_description,
            "period_end": v.period_end.isoformat(),
            "value": float(v.value),
            "input_fact_ids": v.input_fact_ids,
        }
        for v, d in rows
        if v.input_fact_ids and set(v.input_fact_ids) <= fact_ids
    ]

    return {
        "symbol": security.symbol,
        "issuer": issuer.name,
        "sources": [
            {
                "id": d.id,
                "document_type": d.document_type,
                "url": d.url,
                "local_path": d.local_path,
                "source_tier": d.source_tier,
            }
            for d in documents
        ],
        "facts": [
            {
                "id": f.id,
                "line_item": f.line_item,
                "period_end": f.period_end.isoformat(),
                "period_type": f.period_type,
                "scope": f.scope,
                "value": float(f.value),
                "unit": f.unit,
                "source_document_id": f.source_document_id,
                "is_restated": f.is_restated,
            }
            for f in facts
        ],
        "ratios": ratios,
        "balance_sheet_flags": reconcile_balance_sheet(db, issuer.id),
    }
