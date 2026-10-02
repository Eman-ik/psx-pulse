"""Equity Research Studio API. Everything here is read from stored, source-linked data; a
missing input is null/unavailable with a reason, never a default."""

import logging
import time
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.data_status import freshness
from app.api.deps import get_db
from app.api.fundamentals import fundamentals as fundamentals_payload
from app.db.models import (
    Announcement, BoardMembership, CorporateActionCoverage, FinancialFact, IndexOHLCV, IngestionRun, Issuer,
    MarketIndex, Person, PriceOHLCV, Security, SourceDocument,
)
from app.etl.industry_intelligence import SECTOR_PROFIT_DRIVERS
from app.research_system import research_view as rv
from app.research_system.momentum_screener import MAX_ANCHOR_GAP_DAYS, MomentumScreener
from app.research_system.technical_screener import TechnicalScreener

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/companies", tags=["research-studio"])

SECTOR_INDEX = {"Fertilizer": "FERTIX", "Cement": "CEMENTIX"}
HORIZONS = {"1m": 30, "3m": 91, "6m": 182, "12m": 365}
QUOTE_TTL_SECONDS = 300
_quote_cache: dict[str, tuple[float, dict]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _security(db: Session, ref: str) -> Security:
    stmt = select(Security).where(Security.id == int(ref)) if ref.isdigit() else select(Security).where(Security.symbol == ref.upper())
    security = db.execute(stmt).scalar_one_or_none()
    if security is None:
        raise HTTPException(status_code=404, detail="Unknown security")
    return security


def _latest_market_date(db: Session) -> date | None:
    return db.execute(select(func.max(PriceOHLCV.trade_date))).scalar()


def _profile_document(db: Session, issuer_id: int) -> SourceDocument | None:
    return db.execute(
        select(SourceDocument).where(SourceDocument.issuer_id == issuer_id, SourceDocument.document_type == "company_profile")
        .order_by(SourceDocument.fetched_at.desc())
    ).scalars().first()


def _price_snapshot(db: Session, security: Security) -> dict:
    fresh = freshness(db, PriceOHLCV, PriceOHLCV.security_id == security.id)
    bars = db.execute(
        select(PriceOHLCV).where(PriceOHLCV.security_id == security.id).order_by(PriceOHLCV.trade_date.desc()).limit(2)
    ).scalars().all()
    last = bars[0] if bars else None
    return {
        "close": float(last.close) if last else None,
        "change_pct": round((float(last.close) - float(bars[1].close)) / float(bars[1].close) * 100, 2) if len(bars) == 2 else None,
        "volume": last.volume if last else None,
        "badge": "DELAYED",
        "freshness": fresh,
    }


def _annual_series(payload: dict) -> tuple[dict[str, list[tuple[date, float]]], list[date]]:
    ratios: dict[str, list[tuple[date, float]]] = {}
    for r in payload["ratios"]:
        ratios.setdefault(r["key"], []).append((date.fromisoformat(r["period_end"]), r["value"]))
    periods = sorted({date.fromisoformat(f["period_end"]) for f in payload["facts"] if f["period_type"] == "annual"})
    return ratios, periods


def _events_summary(db: Session, issuer_id: int) -> dict:
    today = datetime.now(timezone.utc)
    rows = db.execute(
        select(Announcement.category, func.count(), func.max(Announcement.published_at))
        .where(Announcement.issuer_id == issuer_id, Announcement.published_at >= today - timedelta(days=90))
        .group_by(Announcement.category)
    ).all()
    return {"last_90_days": {c: n for c, n, _ in rows}, "latest": max((m for *_, m in rows), default=None)}


def _technical(db: Session, security: Security) -> dict | None:
    latest = _latest_market_date(db)
    signal = TechnicalScreener.screen_security(db, security, latest) if latest else None
    if signal is None:
        return None
    from dataclasses import asdict
    return asdict(signal)


def _research_view(db: Session, security: Security) -> dict:
    today = date.today()
    payload = fundamentals_payload(security.symbol, db)
    ratios, periods = _annual_series(payload)
    prices = freshness(db, PriceOHLCV, PriceOHLCV.security_id == security.id)
    technical = _technical(db, security)
    events = _events_summary(db, security.issuer_id)
    profile = _profile_document(db, security.issuer_id)

    domains = [
        rv.not_assessed("business_quality", "Business quality",
                        "No segment, capacity or competitive-position data on file. The company description is in the Business tab."),
        rv.financial_health(ratios, today),
        rv.earnings_quality(ratios.get("ocf_to_pat"), today),
        rv.not_assessed("valuation", "Valuation",
                        "No point-in-time multiples history or peer fundamentals to compare against. PSX's own reported P/E is on the Valuation tab as a reference."),
        rv.technical_condition(technical, prices["stale"]),
        rv.not_assessed("sentiment_event_risk", "Sentiment / event risk",
                        "Announcements are listed in News & Events, but no validated sentiment or impact model exists yet."),
    ]
    latest_period = periods[-1] if periods else None
    checks = {
        "prices_current": (not prices["stale"], f"Latest close {prices['as_of']}." if prices["as_of"] else "No prices."),
        "price_history": (bool(technical and technical["lookback_complete"]),
                          f"{technical['lookback_days']} closes on file (252 = one year)." if technical else "No recent bars."),
        "statements": (len(periods) >= 3 and latest_period is not None and rv.months_old(latest_period, today) <= rv.STALE_AFTER_MONTHS,
                       f"{len(periods)} annual periods, latest {latest_period}." if periods else "No financial statements on file."),
        "profile": (profile is not None, "Company profile retrieved from PSX." if profile else "No profile on file."),
        "recent_events": (bool(events["last_90_days"]), f"{sum(events['last_90_days'].values())} announcements in 90 days."),
    }
    confidence = rv.data_confidence(checks)
    return {"domains": domains, "data_confidence": confidence, "overall": rv.overall_view(domains, confidence),
            "methodology_version": "research-view-1.0"}


@router.get("/search")
def search(q: str = Query(min_length=1, max_length=40), db: Session = Depends(get_db)) -> dict:
    pattern = f"%{q.strip()}%"
    rows = db.execute(
        select(Security, Issuer).join(Issuer, Issuer.id == Security.issuer_id)
        .where(or_(Security.symbol.ilike(pattern), Issuer.name.ilike(pattern)))
        .order_by((Security.symbol != q.strip().upper()), Security.symbol).limit(10)
    ).all()
    return {
        "generated_at": _now(),
        "results": [
            {"security_id": s.id, "symbol": s.symbol, "name": i.name, "sector": i.sector.name if i.sector else None,
             "listing_status": s.listing_status, "price": _price_snapshot(db, s)}
            for s, i in rows
        ],
    }


@router.get("/{ref}/overview")
def overview(ref: str, db: Session = Depends(get_db)) -> dict:
    security = _security(db, ref)
    issuer = security.issuer
    view = _research_view(db, security)
    payload = fundamentals_payload(security.symbol, db)
    profile = _profile_document(db, issuer.id)
    return {
        "generated_at": _now(),
        "as_of": _latest_market_date(db).isoformat() if _latest_market_date(db) else None,
        "security_id": security.id,
        "symbol": security.symbol,
        "name": issuer.name,
        "sector": issuer.sector.name if issuer.sector else None,
        "listing_status": security.listing_status,
        "fiscal_year_end_month": issuer.fiscal_year_end_month,
        "website": issuer.website,
        "profile_source": {"url": profile.url, "retrieved_at": profile.fetched_at.isoformat()} if profile else None,
        "what_it_does": issuer.business_description,
        "price": _price_snapshot(db, security),
        "coverage": {
            "prices": True,
            "statements": bool(payload["facts"]),
            "profile": profile is not None,
            "tier": "full" if payload["facts"] else "price_only",
        },
        "research_view": view,
        "latest_events": _events(db, security, limit=5, offset=0, category=None)["events"],
    }


@router.get("/{ref}/research-view")
def research_view(ref: str, db: Session = Depends(get_db)) -> dict:
    security = _security(db, ref)
    return {"generated_at": _now(), "as_of": _now(), "security_id": security.id, "symbol": security.symbol,
            **_research_view(db, security)}


@router.get("/{ref}/business")
def business(ref: str, db: Session = Depends(get_db)) -> dict:
    security = _security(db, ref)
    issuer = security.issuer
    profile = _profile_document(db, issuer.id)
    source = {"url": profile.url, "retrieved_at": profile.fetched_at.isoformat()} if profile else None
    people = db.execute(
        select(Person.full_name, BoardMembership.role).join(BoardMembership, BoardMembership.person_id == Person.id)
        .where(BoardMembership.issuer_id == issuer.id)
    ).all()
    sector = (issuer.sector.name if issuer.sector else "").upper()
    parent = db.get(Issuer, issuer.ultimate_parent_issuer_id) if issuer.ultimate_parent_issuer_id else None
    return {
        "generated_at": _now(), "as_of": profile.fetched_at.isoformat() if profile else None,
        "security_id": security.id, "symbol": security.symbol,
        "description": {"text": issuer.business_description, "source": source},
        "facts": {k: {"value": v, "source": source} for k, v in {
            "address": issuer.address, "website": issuer.website, "registrar": issuer.registrar, "auditor": issuer.auditor,
            "fiscal_year_end_month": issuer.fiscal_year_end_month, "sector": issuer.sector.name if issuer.sector else None,
        }.items()},
        "parent": {"name": parent.name, "psx_listed": parent.is_psx_listed, "source": source,
                   "basis": "Stated in the PSX business description text."} if parent else None,
        "key_people": [{"name": n, "role": r, "source": source} for n, r in people],
        "segments_and_products": {"status": "NOT_ON_FILE", "items": []},
        "supply_chain": {
            "status": "NO_DISCLOSED_COUNTERPARTIES_ON_FILE",
            "disclosed": [],
            "note": "No named suppliers, customers or partners have been loaded from filings. None are inferred.",
        },
        "industry_dependencies": {
            "label": "INDUSTRY DEPENDENCY: sector-level drivers, not disclosed by this company",
            "items": SECTOR_PROFIT_DRIVERS.get(sector, []),
        },
    }


def _events(db: Session, security: Security, limit: int, offset: int, category: str | None) -> dict:
    stmt = (select(Announcement, SourceDocument).join(SourceDocument, SourceDocument.id == Announcement.source_document_id, isouter=True)
            .where(Announcement.issuer_id == security.issuer_id))
    if category:
        stmt = stmt.where(Announcement.category == category)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar()
    rows = db.execute(stmt.order_by(Announcement.published_at.desc()).limit(limit).offset(offset)).all()
    return {
        "total": total, "limit": limit, "offset": offset,
        "events": [
            {"id": a.id, "title": a.title, "category": a.category, "published_at": a.published_at.isoformat(),
             "retrieved_at": d.fetched_at.isoformat() if d else None, "source_url": d.url if d else None,
             "source_tier": d.source_tier if d else None}
            for a, d in rows
        ],
    }


@router.get("/{ref}/events")
def events(ref: str, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), category: str | None = None,
           db: Session = Depends(get_db)) -> dict:
    security = _security(db, ref)
    coverage = db.get(CorporateActionCoverage, security.id)
    result = _events(db, security, limit, offset, category)
    return {
        "generated_at": _now(), "as_of": result["events"][0]["published_at"] if result["events"] else None,
        "security_id": security.id, **result,
        "category_counts_90d": _events_summary(db, security.issuer_id)["last_90_days"],
        "corporate_actions": {
            "status": "SEARCHED" if coverage else "NOT_YET_SEARCHED",
            "covered_from": coverage.covered_from.isoformat() if coverage else None,
            "items": [],
            "note": "A missing corporate-action record outside the covered range means unknown, not none.",
        },
        "sentiment": {"status": "NOT_ASSESSED", "note": "No validated sentiment or impact model yet."},
    }


def _index_return(db: Session, index_id: int, latest: date, days: int, end_price: float) -> float | None:
    target = latest - timedelta(days=days)
    bar = db.execute(
        select(IndexOHLCV).where(
            IndexOHLCV.market_index_id == index_id,
            IndexOHLCV.trade_date <= target,
            IndexOHLCV.trade_date >= target - timedelta(days=MAX_ANCHOR_GAP_DAYS),
            IndexOHLCV.quality_status.in_(["verified", "provisional"])
        )
        .order_by(IndexOHLCV.trade_date.desc()).limit(1)
    ).scalar_one_or_none()
    return None if bar is None else round((end_price - float(bar.close)) / float(bar.close) * 100, 2)


@router.get("/{ref}/technicals")
def technicals(ref: str, bars: int = Query(252, ge=20, le=1000), db: Session = Depends(get_db)) -> dict:
    security = _security(db, ref)
    latest = _latest_market_date(db)
    signal = _technical(db, security)
    rows = list(reversed(db.execute(
        select(PriceOHLCV).where(PriceOHLCV.security_id == security.id).order_by(PriceOHLCV.trade_date.desc()).limit(bars)
    ).scalars().all()))
    recent = rows[-20:]
    volumes = [b.volume for b in recent if b.volume is not None]
    sector = security.issuer.sector.name if security.issuer.sector else None

    relative = {}
    if rows and latest:
        for code in ("KSE100", SECTOR_INDEX.get(sector)):
            index = db.execute(select(MarketIndex).where(MarketIndex.code == code)).scalar_one_or_none() if code else None
            last = db.execute(
                select(IndexOHLCV).where(
                    IndexOHLCV.market_index_id == index.id,
                    IndexOHLCV.trade_date == latest,
                    IndexOHLCV.quality_status.in_(["verified", "provisional"])
                )
            ).scalar_one_or_none() if index else None
            if last is None:
                relative[code or "SECTOR_INDEX"] = {"status": "UNAVAILABLE"}
                continue
            momentum = MomentumScreener.screen_security(db, security, latest, float(rows[-1].close))
            relative[code] = {"status": "AVAILABLE", "as_of": latest.isoformat(), "horizons": {
                h: {"stock": getattr(momentum, f"return_{h}") if momentum else None,
                    "index": _index_return(db, index.id, latest, d, float(last.close))} for h, d in HORIZONS.items()}}
    coverage = db.get(CorporateActionCoverage, security.id)
    return {
        "generated_at": _now(), "as_of": latest.isoformat() if latest else None, "security_id": security.id,
        "symbol": security.symbol, "freshness": freshness(db, PriceOHLCV, PriceOHLCV.security_id == security.id),
        "indicators": signal,
        "series": {
            "adjusted": False,
            "adjustment_note": "Raw closes. Dividends, bonus issues and splits are not adjusted for; "
                               + ("corporate actions were searched." if coverage else "corporate actions have not been searched, so jumps may be unflagged events."),
            "bars": [{"date": b.trade_date.isoformat(), "open": float(b.open), "high": float(b.high), "low": float(b.low),
                      "close": float(b.close), "volume": b.volume} for b in rows],
        },
        "liquidity": {
            "average_volume_20d": round(sum(volumes) / len(volumes)) if len(volumes) == 20 else None,
            "approx_value_traded_20d_pkr": round(sum(float(b.close) * b.volume for b in recent if b.volume is not None) / len(volumes)) if len(volumes) == 20 else None,
            "approx_value_note": "Close times volume; PSX does not supply value traded in this feed.",
            "zero_volume_days_in_window": sum(1 for b in rows if b.volume == 0),
            "window_days": len(rows),
        },
        "relative_performance": relative,
    }


@router.get("/{ref}/peers")
def peers(ref: str, db: Session = Depends(get_db)) -> dict:
    security = _security(db, ref)
    sector = security.issuer.sector.name if security.issuer.sector else None
    members = db.execute(
        select(Security).join(Issuer, Issuer.id == Security.issuer_id)
        .where(Security.is_active.is_(True), Issuer.sector_id == security.issuer.sector_id)
    ).scalars().all() if sector else [security]
    latest = _latest_market_date(db)
    rows = []
    for peer in members:
        tech = TechnicalScreener.screen_security(db, peer, latest) if latest else None
        mom = MomentumScreener.screen_security(db, peer, latest, tech.price) if tech else None
        payload = fundamentals_payload(peer.symbol, db)
        latest_ratio: dict[str, dict] = {}
        for r in payload["ratios"]:
            if r["key"] in ("net_profit_margin", "roe", "revenue_growth_yoy", "debt_to_equity", "current_ratio") and (
                    r["key"] not in latest_ratio or r["period_end"] > latest_ratio[r["key"]]["period_end"]):
                latest_ratio[r["key"]] = {"value": round(r["value"], 2), "period_end": r["period_end"]}
        rows.append({
            "symbol": peer.symbol, "name": peer.issuer.name, "is_subject": peer.id == security.id,
            "close": tech.price if tech else None,
            "returns": {h: getattr(mom, f"return_{h}") if mom else None for h in HORIZONS},
            "rsi": tech.rsi if tech else None,
            "fundamentals": {k: latest_ratio.get(k) for k in ("net_profit_margin", "roe", "revenue_growth_yoy", "debt_to_equity", "current_ratio")},
        })

    def percentile(horizon: str):
        values = [r["returns"][horizon] for r in rows if r["returns"][horizon] is not None]
        own = next((r["returns"][horizon] for r in rows if r["is_subject"]), None)
        return None if own is None or len(values) < 3 else round(sum(v <= own for v in values) / len(values) * 100)

    return {
        "generated_at": _now(), "as_of": latest.isoformat() if latest else None, "security_id": security.id,
        "peer_selection": {"method": "All active securities in the same sector in the issuer master. No size, market-cap or "
                                     "business-model matching.", "sector": sector, "count": len(rows)},
        "return_percentiles": {h: percentile(h) for h in HORIZONS},
        "rows": sorted(rows, key=lambda r: r["symbol"]),
        "note": "Fundamentals are N/A where no source-linked statements are on file; periods can differ between companies.",
    }


def _psx_quote(symbol: str) -> dict:
    cached = _quote_cache.get(symbol)
    if cached and time.time() - cached[0] < QUOTE_TTL_SECONDS:
        return cached[1]
    try:
        import psxdata
        row = psxdata.quote(symbol).iloc[0].to_dict()
        clean = lambda v: None if v is None or (isinstance(v, float) and v != v) else v
        result = {"status": "AVAILABLE", "retrieved_at": _now(), "source": "psxdata.quote (PSX data portal)", "badge": "DELAYED",
                  "pe_ratio": clean(row.get("pe_ratio")), "dividend_yield_pct": clean(row.get("dividend_yield")),
                  "change_1y_pct": clean(row.get("change_1y_pct")), "index_membership": (row.get("listed_in") or "").split(","),
                  "avg_volume_30d": clean(row.get("volume_avg_30d"))}
    except Exception:
        logger.exception("PSX quote fetch failed for %s", symbol)
        result = {"status": "UNAVAILABLE", "error_code": "PSX_QUOTE_FETCH_FAILED", "retrieved_at": _now()}
    _quote_cache[symbol] = (time.time(), result)
    return result


@router.get("/{ref}/valuation")
def valuation(ref: str, db: Session = Depends(get_db)) -> dict:
    security = _security(db, ref)
    return {
        "generated_at": _now(), "as_of": _now(), "security_id": security.id, "symbol": security.symbol,
        "psx_reported": _psx_quote(security.symbol),
        "computed": {
            "status": "UNAVAILABLE",
            "reason": "Own-history percentiles, peer multiples and scenarios need point-in-time EPS, book value and share counts, "
                      "which are not on file. Multiples are not estimated.",
        },
    }


@router.get("/{ref}/financials")
def financials(ref: str, db: Session = Depends(get_db)) -> dict:
    security = _security(db, ref)
    return {"generated_at": _now(), "security_id": security.id, **fundamentals_payload(security.symbol, db)}


@router.get("/{ref}/evidence")
def evidence(ref: str, db: Session = Depends(get_db)) -> dict:
    security = _security(db, ref)
    issuer_id = security.issuer_id
    payload = fundamentals_payload(security.symbol, db)
    prices = freshness(db, PriceOHLCV, PriceOHLCV.security_id == security.id)
    docs = db.execute(select(SourceDocument).where(SourceDocument.issuer_id == issuer_id)
                      .order_by(SourceDocument.published_at.desc().nullslast(), SourceDocument.fetched_at.desc())).scalars().all()
    fact_counts = dict(db.execute(
        select(FinancialFact.source_document_id, func.count())
        .where(FinancialFact.issuer_id == issuer_id, FinancialFact.superseded_by_id.is_(None))
        .group_by(FinancialFact.source_document_id)).all())
    runs = db.execute(select(IngestionRun).order_by(IngestionRun.id.desc()).limit(100)).scalars().all()
    latest_runs: dict[tuple, IngestionRun] = {}
    for r in runs:
        latest_runs.setdefault((r.source, (r.params or {}).get("table")), r)
    coverage = db.get(CorporateActionCoverage, security.id)
    ev = _events_summary(db, issuer_id)
    profile_doc = _profile_document(db, issuer_id)
    datasets = [
        {"dataset": "Daily prices", "status": "STALE" if prices["stale"] else "AVAILABLE" if prices["as_of"] else "MISSING",
         "as_of": prices["as_of"], "source": ", ".join(prices["sources"]) or None, "label": "DELAYED"},
        {"dataset": "Financial statements", "status": "AVAILABLE" if payload["facts"] else "MISSING",
         "as_of": payload["facts"][-1]["period_end"] if payload["facts"] else None,
         "source": ", ".join(sorted({s["local_path"] or s["url"] or "" for s in payload["sources"]})) or None, "label": "VERIFIED" if payload["facts"] else "MISSING"},
        {"dataset": "Derived ratios", "status": "AVAILABLE" if payload["ratios"] else "MISSING",
         "as_of": max((r["period_end"] for r in payload["ratios"]), default=None), "source": "Computed from the figures above",
         "label": "DERIVED" if payload["ratios"] else "MISSING"},
        {"dataset": "Company profile", "status": "AVAILABLE" if profile_doc else "MISSING",
         "as_of": profile_doc.fetched_at.isoformat() if profile_doc else None, "source": "PSX company page",
         "label": "VERIFIED" if profile_doc else "MISSING"},
        {"dataset": "Announcements", "status": "AVAILABLE" if ev["latest"] else "MISSING", "as_of": ev["latest"].isoformat() if ev["latest"] else None, "source": "PSX company page", "label": "VERIFIED"},
        {"dataset": "Corporate actions", "status": "SEARCHED" if coverage else "NOT_YET_SEARCHED", "as_of": coverage.covered_to.isoformat() if coverage else None, "source": None, "label": "MISSING" if not coverage else "VERIFIED"},
        {"dataset": "Sentiment model", "status": "NOT_BUILT", "as_of": None, "source": None, "label": "MISSING"},
    ]
    return {
        "generated_at": _now(), "as_of": _now(), "security_id": security.id, "datasets": datasets,
        "documents": [{"id": d.id, "type": d.document_type, "url": d.url, "local_path": d.local_path, "tier": d.source_tier,
                       "published_at": d.published_at.isoformat() if d.published_at else None,
                       "retrieved_at": d.fetched_at.isoformat(), "figures_linked": fact_counts.get(d.id, 0)} for d in docs],
        "latest_runs": [{"id": r.id, "source": s, "table": t, "status": r.status, "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                         "rows_inserted": r.rows_inserted, "error_count": len(r.errors or [])} for (s, t), r in latest_runs.items()],
        "balance_sheet_flags": payload["balance_sheet_flags"],
        "label_legend": {"VERIFIED": "From a source document and validated", "DERIVED": "Computed from verified inputs",
                         "DELAYED": "End-of-day public data", "STALE": "Older than the freshness threshold",
                         "MISSING": "No reliable value on file"},
    }
