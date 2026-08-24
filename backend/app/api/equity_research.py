"""
Bridges the frontend's Research Studio into the real Equity-research project's
published reports, instead of the frontend generating its own ungrounded single-shot
LLM narrative (the previous /api/research/analyze implementation, which called
Anthropic directly with only a light DB context dump -- no citation grounding, no
verification pass, none of the deterministic engines the real pipeline runs).

Resolves the ticker through external_identity_map (this DB's own canonical cross-system
mapping -- see app/db/models/identity.py::ExternalIdentityMap) instead of matching ticker
strings directly against Equity-research's database. That used to mean re-deriving the same
fuzzy match on every request, here and independently again in
psxagents/agents/utils/equity_research_tools.py, which has since been switched to call this
endpoint instead of running its own copy of these queries -- one real implementation, one
source of truth for "which record in that other database is this company."

Deliberately honest about coverage and completeness: a ticker with no mapping row, or a
mapped company with no published report, returns not_covered=true; a section without
has_real_content is returned as-is (title + missing_evidence) rather than papering over the
gap -- Equity-research's own Principle 5: failure/absence must be visible, never silently
guessed around.
"""

from __future__ import annotations

import os

import psycopg2
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import ExternalIdentityMap, Security

router = APIRouter(prefix="/equity-research", tags=["equity-research"])

EXTERNAL_SYSTEM = "equity_research"
_DEFAULT_EQUITY_RESEARCH_DSN = "postgresql://equity_research:equity_research_dev@localhost:5433/equity_research"

_LATEST_REPORT_BY_COMPANY_SQL = """
    SELECT r.id, r.status, r.is_preliminary, r.published_at, c.legal_name
    FROM analytical.research_reports r
    JOIN core.companies c ON c.id = r.company_id
    WHERE c.id = %s
    ORDER BY r.published_at DESC NULLS LAST, r.created_at DESC
    LIMIT 1
"""

_SECTIONS_SQL = """
    SELECT title, content, has_real_content, missing_evidence
    FROM analytical.research_report_sections
    WHERE research_report_id = %s
    ORDER BY section_order
"""

_NOT_COVERED_NOTE = (
    "Equity-research's real, citation-grounded pipeline currently only has evidence for "
    "FFC, EFERT, and FATIMA. Run backend/scripts/sync_equity_research_identity_map.py after "
    "it covers a new company -- this endpoint only sees companies recorded in "
    "external_identity_map, not Equity-research's database directly."
)


def _get_connection():
    dsn = os.environ.get("EQUITY_RESEARCH_DATABASE_URL", _DEFAULT_EQUITY_RESEARCH_DSN)
    return psycopg2.connect(dsn)


def _not_covered(ticker: str, note: str = _NOT_COVERED_NOTE) -> dict:
    return {"ticker": ticker, "not_covered": True, "unavailable": False, "coverage_note": note}


@router.get("/{ticker}")
def get_equity_research_report(ticker: str, db: Session = Depends(get_db)) -> dict:
    ticker_upper = ticker.upper()

    security = db.execute(select(Security).where(Security.symbol == ticker_upper)).scalar_one_or_none()
    identity = None
    if security is not None:
        identity = db.execute(
            select(ExternalIdentityMap).where(
                ExternalIdentityMap.issuer_id == security.issuer_id,
                ExternalIdentityMap.external_system == EXTERNAL_SYSTEM,
            )
        ).scalar_one_or_none()

    if identity is None:
        return _not_covered(ticker_upper)

    try:
        conn = _get_connection()
    except Exception as exc:  # noqa: BLE001 -- a DB outage must not 500 the whole page
        return {
            "ticker": ticker_upper,
            "not_covered": False,
            "unavailable": True,
            "error": f"could not reach the Equity-research database ({exc})",
        }

    try:
        with conn.cursor() as cur:
            cur.execute(_LATEST_REPORT_BY_COMPANY_SQL, (identity.external_id,))
            row = cur.fetchone()
            if row is None:
                return _not_covered(
                    ticker_upper,
                    f"{ticker_upper} is mapped to Equity-research company "
                    f"{identity.external_id}, but no report has been published for it yet.",
                )
            report_id, status, is_preliminary, published_at, company_name = row

            cur.execute(_SECTIONS_SQL, (str(report_id),))
            sections = cur.fetchall()
    finally:
        conn.close()

    total = len(sections)
    real = sum(1 for _, _, has_real_content, _ in sections if has_real_content)

    return {
        "ticker": ticker_upper,
        "not_covered": False,
        "unavailable": False,
        "company_name": company_name,
        "status": status,
        "is_preliminary": is_preliminary,
        "published_at": published_at.isoformat() if published_at else None,
        "sections_total": total,
        "sections_with_real_content": real,
        "sections": [
            {
                "title": title,
                "content": content,
                "has_real_content": has_real_content,
                "missing_evidence": list(missing_evidence) if missing_evidence else [],
            }
            for title, content, has_real_content, missing_evidence in sections
        ],
    }
