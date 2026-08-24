"""
Real bridge into the Equity-research project (D:/khronos/Equity-research) -- a
separate, deterministic 8-agent LangGraph pipeline that produces citation-grounded,
verified research reports, but only for the companies it has real evidence for
(FFC, EFERT, FATIMA as of 2026-08).

Calls the psx-fertilizer backend's GET /equity-research/{ticker} endpoint rather than
querying Equity-research's Postgres DB directly. That used to mean this file carried its own
copy of the same SQL backend/app/api/equity_research.py also ran -- two independent
implementations of the same ticker match, which could silently drift. The backend endpoint is
now the one real implementation, resolving the ticker through psx_fertilizer's own
external_identity_map (see app/db/models/identity.py::ExternalIdentityMap) instead of matching
ticker strings against Equity-research's database directly -- this file just relays whatever
it says.

Deliberately honest about coverage: a ticker Equity-research has never researched
returns a clear "not covered" message, not a fabricated summary. Principle 5
(Equity-research's own term, kept here for consistency): failure/absence must be
visible, never silently guessed around.
"""

from __future__ import annotations

import os
from typing import Annotated

import requests
from langchain_core.tools import tool

_DEFAULT_BACKEND_BASE_URL = "http://localhost:8001"
_REQUEST_TIMEOUT_S = 15


def _backend_base_url() -> str:
    return os.environ.get("PSX_BACKEND_BASE_URL", _DEFAULT_BACKEND_BASE_URL)


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
    ticker_upper = ticker.upper()
    try:
        response = requests.get(
            f"{_backend_base_url()}/equity-research/{ticker_upper}", timeout=_REQUEST_TIMEOUT_S
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:  # noqa: BLE001 -- a backend/network outage must not crash the graph run
        return (
            f"EQUITY_RESEARCH_UNAVAILABLE: could not reach the psx-fertilizer backend's "
            f"equity-research bridge ({exc}). This agent's assessment is unavailable for "
            f"this run; do not fabricate a substitute."
        )

    if data.get("unavailable"):
        return (
            f"EQUITY_RESEARCH_UNAVAILABLE: {data.get('error', 'the Equity-research database '
            'is unreachable')}. This agent's assessment is unavailable for this run; do not "
            f"fabricate a substitute."
        )

    if data.get("not_covered"):
        note = data.get("coverage_note", "No deep-dive assessment is available for this ticker.")
        return f"NOT_COVERED: Equity-research has not published a report for '{ticker_upper}'. {note}"

    header = (
        f"# Equity Research deep-dive report for {ticker_upper}\n"
        f"# Status: {data.get('status')}{' (preliminary)' if data.get('is_preliminary') else ''}, "
        f"published {data.get('published_at') or 'not yet published'}\n"
        f"# Source: Equity-research's real 8-agent pipeline (citation-grounded evidence, "
        f"deterministic financial engines, independent verification pass)\n\n"
    )

    parts = [header]
    for section in data.get("sections", []):
        if not section.get("has_real_content"):
            missing = ", ".join(section.get("missing_evidence") or []) or "insufficient evidence"
            parts.append(f"## {section['title']}\n_Not yet available: {missing}._\n")
            continue
        parts.append(f"## {section['title']}\n{section['content']}\n")

    return "\n".join(parts)
