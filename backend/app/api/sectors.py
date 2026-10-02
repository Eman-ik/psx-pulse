from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Issuer, OperationalMetric, Sector, Security

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


def _company_entry(issuer: Issuer) -> dict:
    symbol = next((s.symbol for s in issuer.securities if s.is_active), None)
    return {"id": issuer.id, "name": issuer.name, "symbol": symbol}


def _sector_overview(db: Session, sector_name: str) -> dict:
    """Generic sector overview — filters strictly by sector name so multi-sector DB is correct."""
    from app.api.comparison import _latest_by_issuer

    sector = db.execute(select(Sector).where(Sector.name == sector_name)).scalar_one_or_none()
    if sector is None:
        return {
            "sector_name": sector_name,
            "psx_sector_code": None,
            "company_count": 0,
            "companies": [],
            "aggregate_market_cap_pkr": None,
            "companies_with_market_cap": 0,
            "not_available": _NOT_AVAILABLE,
        }

    issuers = db.execute(
        select(Issuer).where(
            Issuer.sector_id == sector.id,
            Issuer.securities.any(Security.is_active.is_(True)),
        )
    ).scalars().all()
    issuer_ids = {i.id for i in issuers}

    all_market_caps = _latest_by_issuer(db, "market_cap")
    market_cap_by_issuer = {iid: v for iid, v in all_market_caps.items() if iid in issuer_ids}
    aggregate_market_cap_pkr = sum(market_cap_by_issuer.values()) if market_cap_by_issuer else None

    return {
        "sector_name": sector_name,
        "psx_sector_code": sector.psx_sector_code,
        "company_count": len(issuers),
        "companies": [_company_entry(i) for i in issuers],
        "aggregate_market_cap_pkr": aggregate_market_cap_pkr,
        "companies_with_market_cap": len(market_cap_by_issuer),
        "not_available": _NOT_AVAILABLE,
    }


@router.get("/fertilizer")
def fertilizer_sector(db: Session = Depends(get_db)) -> dict:
    """Fertilizer sector overview — figures built only from ingested pilot data.

    Delisted issuers (e.g. FFBL, ENGRO) are excluded via Security.is_active.
    Filtered strictly to the Fertilizer sector so adding other sectors doesn't pollute counts.
    """
    from app.api.comparison import _latest_by_issuer

    sector = db.execute(select(Sector).where(Sector.name == "Fertilizer")).scalar_one_or_none()
    if sector is None:
        return {**_sector_overview(db, "Fertilizer"),
                "avg_capacity_utilization_pct": None,
                "companies_with_utilization_data": 0,
                "total_production_volume": None,
                "companies_with_production_data": 0}

    issuers = db.execute(
        select(Issuer).where(
            Issuer.sector_id == sector.id,
            Issuer.securities.any(Security.is_active.is_(True)),
        )
    ).scalars().all()
    issuer_ids = {i.id for i in issuers}

    all_market_caps = _latest_by_issuer(db, "market_cap")
    market_cap_by_issuer = {iid: v for iid, v in all_market_caps.items() if iid in issuer_ids}
    aggregate_market_cap_pkr = sum(market_cap_by_issuer.values()) if market_cap_by_issuer else None

    utilization_by_issuer = _latest_metric_by_issuer(db, "capacity_utilization_pct", None)
    production_by_issuer = _latest_metric_by_issuer(db, "production_volume", "fertilizer_total")
    utilization_by_issuer = {k: v for k, v in utilization_by_issuer.items() if k in issuer_ids}
    production_by_issuer = {k: v for k, v in production_by_issuer.items() if k in issuer_ids}

    return {
        "sector_name": "Fertilizer",
        "psx_sector_code": sector.psx_sector_code,
        "company_count": len(issuers),
        "companies": [_company_entry(i) for i in issuers],
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


@router.get("/cement")
def cement_sector(db: Session = Depends(get_db)) -> dict:
    """Cement sector overview — same methodology as /sectors/fertilizer.

    Cement-specific KPIs (dispatches, clinker production) will be added once operational
    KPI data is ingested. Currently returns the generic overview with market cap only.
    """
    from app.api.comparison import _latest_by_issuer

    sector = db.execute(select(Sector).where(Sector.name == "Cement")).scalar_one_or_none()
    if sector is None:
        return {
            "sector_name": "Cement",
            "psx_sector_code": None,
            "company_count": 0,
            "companies": [],
            "aggregate_market_cap_pkr": None,
            "companies_with_market_cap": 0,
            "avg_capacity_utilization_pct": None,
            "companies_with_utilization_data": 0,
            "not_available": _NOT_AVAILABLE,
        }

    issuers = db.execute(
        select(Issuer).where(
            Issuer.sector_id == sector.id,
            Issuer.securities.any(Security.is_active.is_(True)),
        )
    ).scalars().all()
    issuer_ids = {i.id for i in issuers}

    all_market_caps = _latest_by_issuer(db, "market_cap")
    market_cap_by_issuer = {iid: v for iid, v in all_market_caps.items() if iid in issuer_ids}
    aggregate_market_cap_pkr = sum(market_cap_by_issuer.values()) if market_cap_by_issuer else None

    utilization_by_issuer = _latest_metric_by_issuer(db, "capacity_utilization_pct", None)
    utilization_by_issuer = {k: v for k, v in utilization_by_issuer.items() if k in issuer_ids}

    return {
        "sector_name": "Cement",
        "psx_sector_code": sector.psx_sector_code,
        "company_count": len(issuers),
        "companies": [_company_entry(i) for i in issuers],
        "aggregate_market_cap_pkr": aggregate_market_cap_pkr,
        "companies_with_market_cap": len(market_cap_by_issuer),
        "avg_capacity_utilization_pct": (
            sum(utilization_by_issuer.values()) / len(utilization_by_issuer) if utilization_by_issuer else None
        ),
        "companies_with_utilization_data": len(utilization_by_issuer),
        "not_available": _NOT_AVAILABLE,
    }
