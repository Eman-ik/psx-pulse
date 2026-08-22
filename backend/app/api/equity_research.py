"""
Bridges the frontend's Research Studio into the real Equity-research project's
published reports, instead of the frontend generating its own ungrounded single-shot
LLM narrative (the previous /api/research/analyze implementation, which called
Anthropic directly with only a light DB context dump -- no citation grounding, no
verification pass, none of the deterministic engines the real pipeline runs).

Same DB and query shape psxagents/agents/utils/equity_research_tools.py already uses
to bridge the TradingAgents fork into the same reports -- kept consistent so both
consumers read one real source of truth instead of drifting.

Deliberately honest about coverage and completeness: a ticker Equity-research has
never researched returns not_covered=true, and a section without has_real_content
is returned as-is (title + missing_evidence) rather than papering over the gap --
Equity-research's own Principle 5: failure/absence must be visible, never silently
guessed around.
"""

from __future__ import annotations

import os

import psycopg2
from fastapi import APIRouter

router = APIRouter(prefix="/equity-research", tags=["equity-research"])

_DEFAULT_EQUITY_RESEARCH_DSN = "postgresql://equity_research:equity_research_dev@localhost:5433/equity_research"

_LATEST_REPORT_SQL = """
    SELECT r.id, r.status, r.is_preliminary, r.published_at, c.legal_name
    FROM analytical.research_reports r
    JOIN core.companies c ON c.id = r.company_id
    JOIN core.securities s ON s.company_id = c.id
    WHERE upper(s.ticker) = upper(%s)
    ORDER BY r.published_at DESC NULLS LAST, r.created_at DESC
    LIMIT 1
"""

_SECTIONS_SQL = """
    SELECT title, content, has_real_content, missing_evidence
    FROM analytical.research_report_sections
    WHERE research_report_id = %s
    ORDER BY section_order
"""


def _get_connection():
    dsn = os.environ.get("EQUITY_RESEARCH_DATABASE_URL", _DEFAULT_EQUITY_RESEARCH_DSN)
    return psycopg2.connect(dsn)


@router.get("/{ticker}")
def get_equity_research_report(ticker: str) -> dict:
    ticker_upper = ticker.upper()

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
            cur.execute(_LATEST_REPORT_SQL, (ticker_upper,))
            row = cur.fetchone()
            if row is None:
                return {
                    "ticker": ticker_upper,
                    "not_covered": True,
                    "unavailable": False,
                    "coverage_note": "Equity-research's real, citation-grounded pipeline "
                    "currently only has evidence for FFC, EFERT, and FATIMA.",
                }
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
