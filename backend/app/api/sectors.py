from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Issuer, OperationalMetric, Sector

router = APIRouter(prefix="/sectors", tags=["sectors"])

# Fields the docx's sector-card spec asks for that we have no real ingested source for yet
# (no PBS/GDP-contribution feed, no PSX index-weight feed, no export-data feed). Listed
# explicitly rather than fabricated, per this project's data-governance rule.
_NOT_AVAILABLE = [
    "gdp_contribution_pct",
    "psx_index_weight_pct",
    "export_contribution",
]


def _latest_metric_by_issuer(db: Session, metric_key: str, product: str | None) -> dict[int, float]:
    conditions = [OperationalMetric.metric_key == metric_key]
    conditions.append(
        OperationalMetric.product.is_(None) if product is None else OperationalMetric.product == product
    )
    rows = db.execute(select(OperationalMetric).where(*conditions)).scalars().all()
    latest: dict[int, tuple] = {}
    for m in rows:
        key = (m.period_end, m.id)
        if m.issuer_id not in latest or key > latest[m.issuer_id][0]:
            latest[m.issuer_id] = (key, float(m.value))
    return {issuer_id: value for issuer_id, (_, value) in latest.items()}


@router.get("/fertilizer")
def fertilizer_sector(db: Session = Depends(get_db)) -> dict:
    """Fertilizer sector overview built only from data already ingested for the pilot's
    7 companies: real company count, real aggregate market cap (sum of latest financial_fact
    market_cap per issuer), and real average/aggregate operational KPIs. Fields the docx
    describes but we have no ingested source for are listed under not_available instead of
    being guessed.
    """
    from app.api.comparison import _latest_by_issuer

    sector = db.execute(select(Sector).where(Sector.name == "Fertilizer")).scalar_one_or_none()
    issuers = db.execute(select(Issuer).where(Issuer.securities.any())).scalars().all()

    market_cap_by_issuer = _latest_by_issuer(db, "market_cap")
    aggregate_market_cap_pkr = sum(market_cap_by_issuer.values()) if market_cap_by_issuer else None

    utilization_by_issuer = _latest_metric_by_issuer(db, "capacity_utilization_pct", None)
    production_by_issuer = _latest_metric_by_issuer(db, "production_volume", "fertilizer_total")

    return {
        "sector_name": "Fertilizer",
        "psx_sector_code": sector.psx_sector_code if sector else None,
        "company_count": len(issuers),
        "companies": [i.name for i in issuers],
        "aggregate_market_cap_pkr": aggregate_market_cap_pkr,
        "companies_with_market_cap": len(market_cap_by_issuer),
        "avg_capacity_utilization_pct": (
            sum(utilization_by_issuer.values()) / len(utilization_by_issuer) if utilization_by_issuer else None
        ),
        "companies_with_utilization_data": len(utilization_by_issuer),
        "total_production_volume": sum(production_by_issuer.values()) if production_by_issuer else None,
        "companies_with_production_data": len(production_by_issuer),
        "not_available": _NOT_AVAILABLE,
    }
