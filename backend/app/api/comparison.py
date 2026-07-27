from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import FinancialFact, Issuer, RatioDefinition, RatioValue, Security
from app.ingestion.psx_live import FERTILIZER_SECTOR_COMPANIES, fetch_live_snapshots

router = APIRouter(prefix="/companies", tags=["companies"])


def _latest_by_issuer(db: Session, line_item: str) -> dict[int, float]:
    rows = db.execute(
        select(FinancialFact).where(
            FinancialFact.line_item == line_item,
            FinancialFact.superseded_by_id.is_(None),
        )
    ).scalars().all()
    latest: dict[int, tuple] = {}
    for f in rows:
        key = (f.period_end, f.id)
        if f.issuer_id not in latest or key > latest[f.issuer_id][0]:
            latest[f.issuer_id] = (key, float(f.value))
    return {issuer_id: value for issuer_id, (_, value) in latest.items()}


def _latest_ratio_by_issuer(db: Session, ratio_key: str) -> dict[int, float]:
    rows = db.execute(
        select(RatioValue, RatioDefinition)
        .join(RatioDefinition, RatioDefinition.id == RatioValue.ratio_definition_id)
        .where(RatioDefinition.key == ratio_key)
    ).all()
    latest: dict[int, tuple] = {}
    for ratio_value, _definition in rows:
        key = (ratio_value.period_end, ratio_value.id)
        if ratio_value.issuer_id not in latest or key > latest[ratio_value.issuer_id][0]:
            latest[ratio_value.issuer_id] = (key, float(ratio_value.value))
    return {issuer_id: value for issuer_id, (_, value) in latest.items()}


@router.get("/ratio-benchmarks")
def ratio_benchmarks(db: Session = Depends(get_db)) -> dict[str, dict]:
    """Peer-average (mean of each covered issuer's latest value) for every ratio key that has
    at least one value on file, so the Ratios tab can benchmark any ratio against the sector
    average rather than a hardcoded subset. Powers the Healthy/Average badges.
    """
    rows = db.execute(
        select(RatioValue, RatioDefinition).join(RatioDefinition, RatioDefinition.id == RatioValue.ratio_definition_id)
    ).all()
    latest_by_key_issuer: dict[str, dict[int, tuple]] = {}
    for ratio_value, definition in rows:
        by_issuer = latest_by_key_issuer.setdefault(definition.key, {})
        key = (ratio_value.period_end, ratio_value.id)
        if ratio_value.issuer_id not in by_issuer or key > by_issuer[ratio_value.issuer_id][0]:
            by_issuer[ratio_value.issuer_id] = (key, float(ratio_value.value))

    return {
        ratio_key: {
            "mean": sum(v for _, v in by_issuer.values()) / len(by_issuer),
            "count": len(by_issuer),
        }
        for ratio_key, by_issuer in latest_by_key_issuer.items()
        if by_issuer
    }


@router.get("/comparison")
def companies_comparison(db: Session = Depends(get_db)) -> list[dict]:
    """Batch comparison row per covered fertilizer issuer, shared by the Companies discovery
    table and each company's Competitors tab. Every field is either a live quote (psxdata) or
    the latest reconciled financial_fact/ratio_value on file — nothing here is fabricated;
    a field is null when no such record exists yet for that company.
    """
    issuers = db.execute(select(Issuer).where(Issuer.securities.any())).scalars().all()
    securities = db.execute(select(Security)).scalars().all()
    security_by_issuer = {s.issuer_id: s for s in securities}

    live_quotes = fetch_live_snapshots(FERTILIZER_SECTOR_COMPANIES)
    live_by_symbol = {q["symbol"]: q for q in live_quotes}

    market_cap_by_issuer = _latest_by_issuer(db, "market_cap")
    roe_by_issuer = _latest_ratio_by_issuer(db, "roe")
    debt_to_equity_by_issuer = _latest_ratio_by_issuer(db, "debt_to_equity")

    rows = []
    for issuer in issuers:
        security = security_by_issuer.get(issuer.id)
        symbol = security.symbol if security else None
        quote = live_by_symbol.get(symbol) if symbol else None
        rows.append(
            {
                "id": issuer.id,
                "symbol": symbol,
                "name": issuer.name,
                "price": quote.get("price") if quote else None,
                "change_pct": quote.get("change_pct") if quote else None,
                "market_cap": market_cap_by_issuer.get(issuer.id),
                "pe_ratio": quote.get("pe_ratio") if quote else None,
                "dividend_yield": quote.get("dividend_yield") if quote else None,
                "roe": roe_by_issuer.get(issuer.id),
                "debt_to_equity": debt_to_equity_by_issuer.get(issuer.id),
            }
        )
    return rows
