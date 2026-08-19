"""
Real bridge into the Equity-research project (D:/khronos/Equity-research) -- a
separate, deterministic 8-agent LangGraph pipeline that produces citation-grounded,
verified research reports, but only for the 3 companies it has real evidence for
(FFC, EFERT, FATIMA as of 2026-08). Rather than re-running that whole pipeline (which
makes real LLM calls and can take minutes), this queries its already-published,
already-persisted reports directly from its own Postgres DB -- the same tables
Equity-research's own apps/api/main.py serves its report viewer from
(analytical.research_reports / analytical.research_report_sections).

Deliberately honest about coverage: a ticker Equity-research has never researched
returns a clear "not covered" message, not a fabricated summary. Principle 5
(Equity-research's own term, kept here for consistency): failure/absence must be
visible, never silently guessed around.
"""

from __future__ import annotations

import os
from typing import Annotated

import psycopg2
from langchain_core.tools import tool

_DEFAULT_EQUITY_RESEARCH_DSN = "postgresql://equity_research:equity_research_dev@localhost:5433/equity_research"

_LATEST_REPORT_SQL = """
    SELECT r.id, r.status, r.is_preliminary, r.published_at
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


@tool
def get_equity_research_report(
    ticker: Annotated[str, "PSX ticker symbol, e.g. FFC"],
) -> str:
    """
    Retrieve the real, published, evidence-backed deep-dive research report for a
    company from the Equity-research project -- a separate deterministic 8-agent
    pipeline with citation-grounded claim extraction, verified financial reconciliation,
    and an independent verification pass. Covers only companies it has real evidence
    for (a small, currently 3-company set as of 2026-08) -- if the ticker isn't
    covered, this returns an honest NOT_COVERED message rather than guessing.
    Args:
        ticker (str): PSX ticker symbol, e.g. FFC
    Returns:
        str: The real report content (markdown, section by section), or a clear
        unavailable/not-covered message.
    """
    try:
        conn = _get_connection()
    except Exception as exc:  # noqa: BLE001 -- a DB outage must not crash the whole graph run
        return (
            f"EQUITY_RESEARCH_UNAVAILABLE: could not reach the Equity-research database "
            f"({exc}). This agent's assessment is unavailable for this run; do not "
            f"fabricate a substitute."
        )

    try:
        with conn.cursor() as cur:
            cur.execute(_LATEST_REPORT_SQL, (ticker,))
            row = cur.fetchone()
            if row is None:
                return (
                    f"NOT_COVERED: Equity-research has not published a report for "
                    f"'{ticker.upper()}'. As of 2026-08, its real coverage is limited "
                    f"to FFC, EFERT, and FATIMA. No deep-dive assessment is available "
                    f"for this ticker from this agent."
                )
            report_id, status, is_preliminary, published_at = row

            cur.execute(_SECTIONS_SQL, (str(report_id),))
            sections = cur.fetchall()
    finally:
        conn.close()

    header = (
        f"# Equity Research deep-dive report for {ticker.upper()}\n"
        f"# Status: {status}{' (preliminary)' if is_preliminary else ''}, "
        f"published {published_at if published_at else 'not yet published'}\n"
        f"# Source: Equity-research's real 8-agent pipeline (citation-grounded evidence, "
        f"deterministic financial engines, independent verification pass)\n\n"
    )

    parts = [header]
    for title, content, has_real_content, missing_evidence in sections:
        if not has_real_content:
            missing = ", ".join(missing_evidence) if missing_evidence else "insufficient evidence"
            parts.append(f"## {title}\n_Not yet available: {missing}._\n")
            continue
        parts.append(f"## {title}\n{content}\n")

    return "\n".join(parts)
