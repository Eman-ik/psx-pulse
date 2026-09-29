from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.db.models import (
    Announcement,
    BoardMembership,
    CorporateAction,
    FinancialFact,
    Issuer,
    OperationalMetric,
    Person,
    RatioDefinition,
    RatioValue,
    Security,
    SourceDocument,
    Thesis,
)
from app.etl.valuation_engine import _get_assumption
from app.universe import TIER_FULL, TIER_PRICE_ONLY, coverage_tier

# source_document.document_type used by the manual financial-statement seeds. For the three
# verified fertilizer companies this is genuinely-sourced analyst material; for the cement
# companies it is the unchecked figures manual_financials_seed_cement.py warns about. The
# coverage tier, not this type, decides which of those two a given company is.
MANUAL_ENTRY_DOCUMENT_TYPE = "analyst_report_manual_entry"

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("")
def list_companies(db: Session = Depends(get_db)) -> list[dict]:
    # Excludes parent/holding stubs (e.g. Fauji Foundation, Dawood Hercules) added purely for
    # the ownership graph — they have no Security/symbol, so they don't belong in a company
    # list meant for navigation. Issuer.securities.any() is the correct filter, not
    # is_psx_listed, since Dawood Hercules is genuinely PSX-listed but untracked here.
    # Also excludes delisted securities (e.g. FFBL, merged into FFC Dec 2024 per its own
    # Scheme-of-Arrangement announcements) via Security.is_active — historical FFBL data stays
    # in the DB and its overview page is still reachable directly, it just isn't offered as one
    # of the pilot's active/current companies anymore.
    issuers = db.execute(
        select(Issuer).where(Issuer.securities.any(Security.is_active.is_(True)))
    ).scalars().all()
    return [
        {
            "id": i.id,
            "name": i.name,
            "short_name": i.short_name,
            "sector_id": i.sector_id,
            "symbol": i.securities[0].symbol if i.securities else None,
        }
        for i in issuers
    ]


@router.get("/{issuer_id}")
def get_company(issuer_id: int, db: Session = Depends(get_db)) -> dict | None:
    issuer = db.get(Issuer, issuer_id)
    if issuer is None:
        return None
    return {"id": issuer.id, "name": issuer.name, "short_name": issuer.short_name}


def _parent_chain(db: Session, issuer: Issuer) -> list[dict]:
    chain = []
    current = issuer
    seen_ids = {issuer.id}
    while current.ultimate_parent_issuer_id is not None:
        parent = db.get(Issuer, current.ultimate_parent_issuer_id)
        if parent is None or parent.id in seen_ids:
            break  # guard against a cycle rather than looping forever
        chain.append({"id": parent.id, "name": parent.name, "is_psx_listed": parent.is_psx_listed})
        seen_ids.add(parent.id)
        current = parent
    return chain


def _operational_metrics(db: Session, issuer_id: int) -> dict[str, list[dict]]:
    rows = db.execute(select(OperationalMetric).where(OperationalMetric.issuer_id == issuer_id)).scalars().all()
    grouped: dict[str, list[dict]] = {}
    for r in rows:
        key = f"{r.metric_key}::{r.product}" if r.product else r.metric_key
        grouped.setdefault(key, []).append(
            {
                "product": r.product,
                "period_end": r.period_end.isoformat(),
                "value": float(r.value),
                "unit": r.unit,
            }
        )
    for series in grouped.values():
        series.sort(key=lambda row: row["period_end"])
    return grouped


def _latest_thesis(db: Session, issuer_id: int) -> dict | None:
    thesis = db.execute(
        select(Thesis).where(Thesis.issuer_id == issuer_id).order_by(Thesis.as_of_date.desc())
    ).scalars().first()
    if thesis is None:
        return None
    return {
        "as_of_date": thesis.as_of_date.isoformat(),
        "bull_case": thesis.bull_case,
        "base_case": thesis.base_case,
        "bear_case": thesis.bear_case,
        "key_catalysts": thesis.key_catalysts,
        "key_risks": thesis.key_risks,
        "author": thesis.author,
    }


def _subsidiary_contributions(db: Session, issuer: Issuer, subsidiaries: list[Issuer]) -> list[dict]:
    """Revenue/PAT contribution of each subsidiary to this (parent) issuer's own reported
    figures, for whichever years both sides have data. Scope (consolidated vs standalone)
    is assumed consistent but not independently confirmed — same caveat as elsewhere.
    """
    if not subsidiaries:
        return []

    parent_facts = {
        line_item: {
            f.period_end: float(f.value)
            for f in db.execute(
                select(FinancialFact).where(
                    FinancialFact.issuer_id == issuer.id,
                    FinancialFact.line_item == line_item,
                    FinancialFact.superseded_by_id.is_(None),
                )
            ).scalars()
        }
        for line_item in ("revenue", "profit_after_tax", "total_assets")
    }

    # One query for every subsidiary x line_item pair instead of one query per pair (3N
    # queries for N subsidiaries) -- grouped by (issuer_id, line_item) in Python below.
    subsidiary_by_id = {sub.id: sub for sub in subsidiaries}
    sub_facts_by_issuer_and_item: dict[tuple[int, str], list[FinancialFact]] = defaultdict(list)
    for f in db.execute(
        select(FinancialFact).where(
            FinancialFact.issuer_id.in_(subsidiary_by_id.keys()),
            FinancialFact.line_item.in_(("revenue", "profit_after_tax", "total_assets")),
            FinancialFact.superseded_by_id.is_(None),
        )
    ).scalars():
        sub_facts_by_issuer_and_item[(f.issuer_id, f.line_item)].append(f)

    results = []
    for sub in subsidiaries:
        for line_item in ("revenue", "profit_after_tax", "total_assets"):
            parent_by_year = parent_facts[line_item]
            if not parent_by_year:
                continue
            for f in sub_facts_by_issuer_and_item.get((sub.id, line_item), []):
                parent_value = parent_by_year.get(f.period_end)
                if parent_value is None or parent_value == 0:
                    continue
                results.append(
                    {
                        "subsidiary_id": sub.id,
                        "subsidiary_name": sub.name,
                        "line_item": line_item,
                        "period_end": f.period_end.isoformat(),
                        "subsidiary_value": float(f.value),
                        "parent_value": parent_value,
                        "contribution_pct": round(float(f.value) / parent_value * 100, 1),
                    }
                )
    return results


@router.get("/{issuer_id}/overview")
def get_company_overview(issuer_id: int, db: Session = Depends(get_db)) -> dict | None:
    """Aggregates everything the Company Research page needs into one call: profile,
    ownership chain, governance, financials (grouped by line item for easy charting),
    ratios (grouped by key), payouts, recent announcements and source lineage.

    live_quote is deliberately NOT fetched here (used to call fetch_live_snapshot()
    inline, holding this function's DB session open across a live scrape -- same
    connection-abort risk as GET /companies/comparison, see that endpoint's docstring).
    The frontend fetches it separately via GET /market/quote/{symbol} and merges it in
    client-side once the rest of this page has already rendered.
    """
    issuer = db.get(Issuer, issuer_id)
    if issuer is None:
        return None

    security = db.execute(select(Security).where(Security.issuer_id == issuer.id)).scalars().first()
    tier = coverage_tier(security.symbol) if security else TIER_PRICE_ONLY

    board = db.execute(
        select(BoardMembership, Person)
        .join(Person, Person.id == BoardMembership.person_id)
        .where(BoardMembership.issuer_id == issuer.id)
    ).all()

    subsidiaries = db.execute(
        select(Issuer).where(Issuer.ultimate_parent_issuer_id == issuer.id)
    ).scalars().all()

    facts = db.execute(
        select(FinancialFact).where(
            FinancialFact.issuer_id == issuer.id,
            FinancialFact.superseded_by_id.is_(None),
        )
    ).scalars().all()

    # Withhold anything derived from unverified figures, at the source rather than in the UI.
    #
    # Hiding the Ratios/Financials tabs is not enough: the Summary grid and the company header
    # read data.ratios and data.financials directly, so a quarantined company was still
    # rendering ROE and ROA immediately above a note promising they were withheld -- worse than
    # showing nothing, because the note makes it look deliberate.
    #
    # The split is by source document, not by line item. LUCK's facts come from two places: 42
    # from the unverified manual seed (total_assets, total_equity, gross_profit, inventory...)
    # and 25 scraped from dps.psx.com.pk (eps, market_cap, revenue, profit_after_tax). Only the
    # first set is tainted, so the PSX-scraped figures stay and the page keeps a real market cap
    # and EPS instead of going blank.
    #
    # Ratios go entirely. Some (P/E off scraped EPS) would survive the same reasoning, but
    # RatioValue does not record which facts fed it, so there is no cheap way to prove a given
    # ratio is clean. Withholding all of them is the conservative read, and it is what the
    # user-facing note already promises.
    if tier != TIER_FULL:
        manual_entry_doc_ids = set(
            db.execute(
                select(SourceDocument.id).where(
                    SourceDocument.issuer_id == issuer.id,
                    SourceDocument.document_type == MANUAL_ENTRY_DOCUMENT_TYPE,
                )
            ).scalars().all()
        )
        facts = [f for f in facts if f.source_document_id not in manual_entry_doc_ids]

    financials_by_line_item: dict[str, list[dict]] = {}
    for f in facts:
        financials_by_line_item.setdefault(f.line_item, []).append(
            {
                "period_end": f.period_end.isoformat(),
                "period_type": f.period_type,
                "scope": f.scope,
                "value": float(f.value),
                "unit": f.unit,
                "is_restated": f.is_restated,
            }
        )
    for series in financials_by_line_item.values():
        series.sort(key=lambda row: row["period_end"])

    ratio_rows = (
        db.execute(
            select(RatioValue, RatioDefinition)
            .join(RatioDefinition, RatioDefinition.id == RatioValue.ratio_definition_id)
            .where(RatioValue.issuer_id == issuer.id)
        ).all()
        if tier == TIER_FULL
        else []
    )
    ratios_by_key: dict[str, dict] = {}
    for ratio_value, definition in ratio_rows:
        bucket = ratios_by_key.setdefault(
            definition.key,
            {
                "name": definition.name,
                "category": definition.category,
                "unit": definition.unit,
                "formula": definition.formula_description,
                "values": [],
            },
        )
        bucket["values"].append({"period_end": ratio_value.period_end.isoformat(), "value": float(ratio_value.value)})
    for bucket in ratios_by_key.values():
        bucket["values"].sort(key=lambda row: row["period_end"])

    payouts = []
    if security is not None:
        payouts = [
            {
                "action_type": ca.action_type,
                "effective_date": ca.effective_date.isoformat(),
                "ratio_or_amount": float(ca.ratio_or_amount) if ca.ratio_or_amount is not None else None,
            }
            for ca in db.execute(
                select(CorporateAction)
                .where(CorporateAction.security_id == security.id)
                .order_by(CorporateAction.effective_date.desc())
            ).scalars()
        ]

    announcement_rows = db.execute(
        select(Announcement, SourceDocument)
        .join(SourceDocument, SourceDocument.id == Announcement.source_document_id)
        .where(Announcement.issuer_id == issuer.id)
        .order_by(Announcement.published_at.desc())
        .limit(10)
    ).all()
    announcements = [
        {
            "id": a.id,
            "title": a.title,
            "category": a.category,
            "published_at": a.published_at.isoformat(),
            "summary": a.summary,
            "sentiment_score": a.sentiment_score,
            "source_url": sd.url,
        }
        for a, sd in announcement_rows
    ]

    # Every SourceDocument carries its own issuer_id, so this picks up financial-fact,
    # operational-KPI, thesis and announcement sources alike — not just financial_fact's.
    sources = [
        {
            "document_type": s.document_type,
            "source_tier": s.source_tier,
            "url": s.url,
            "fetched_at": s.fetched_at.isoformat(),
        }
        for s in db.execute(
            select(SourceDocument).where(SourceDocument.issuer_id == issuer.id)
        ).scalars()
    ]

    settings = get_settings()

    capm = _get_assumption(db, issuer.id)
    beta = None
    if capm is not None:
        beta = {
            "value": float(capm.beta),
            "as_of_date": capm.as_of_date.isoformat(),
            "is_issuer_specific": capm.issuer_id is not None,
            "source_note": capm.source_note,
        }

    return {
        "issuer": {
            "id": issuer.id,
            "name": issuer.name,
            "short_name": issuer.short_name,
            "sector_id": issuer.sector_id,
            # The header used to hardcode "Fertilizer sector", which was harmless while the
            # pilot was one sector and wrong for all 18 cement companies the moment it wasn't.
            "sector_name": issuer.sector.name if issuer.sector else None,
            "business_description": issuer.business_description,
            "address": issuer.address,
            "website": issuer.website,
            "registrar": issuer.registrar,
            "auditor": issuer.auditor,
            "fiscal_year_end_month": issuer.fiscal_year_end_month,
            "is_conglomerate": issuer.is_conglomerate,
            "establishment_year": issuer.incorporation_date.year if issuer.incorporation_date else None,
        },
        "data_delay_notice": settings.data_delay_disclaimer,
        # How deeply this company is actually covered -- see app/universe.py. The frontend
        # uses this to decide whether the fundamentals-backed tabs (Ratios, Financials,
        # Analyst) can render truthfully, so it has to come from universe.py rather than
        # being inferred from whether the ratio dict happens to be empty: an empty ratio
        # grid reads as "no debt", not as "not entered yet".
        "coverage_tier": tier,
        "symbol": security.symbol if security else None,
        "security_id": security.id if security else None,
        "listing_status": security.listing_status if security else None,
        "free_float_pct": float(security.free_float_pct) if security and security.free_float_pct else None,
        "beta": beta,
        "parent_chain": _parent_chain(db, issuer),
        "subsidiaries": [{"id": s.id, "name": s.name} for s in subsidiaries],
        "board": [{"full_name": p.full_name, "role": bm.role} for bm, p in board],
        "live_quote": None,
        "financials": financials_by_line_item,
        "ratios": ratios_by_key,
        "payouts": payouts,
        "announcements": announcements,
        "sources": sources,
        "operational_metrics": _operational_metrics(db, issuer.id),
        "thesis": _latest_thesis(db, issuer.id),
        "subsidiary_contributions": _subsidiary_contributions(db, issuer, subsidiaries),
    }
