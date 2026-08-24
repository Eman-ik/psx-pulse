"""
Populates external_identity_map from Equity-research's real coverage -- the one-time (well,
re-runnable) matching step that used to happen implicitly and repeatedly inside every bridge
file (backend/app/api/equity_research.py, psxagents/agents/utils/equity_research_tools.py)
every time either was called. Doing it once here, recorded with a real matched_at/match_method,
turns "some code re-derives this match by string comparison every request" into "one row every
consumer reads."

Matches on ticker (case-insensitive exact) since that's the only real anchor the two systems
share right now -- Equity-research's company_id/security_id are its own UUIDs, unrelated to
psx_fertilizer's issuer_id. This script does NOT invent a stronger match than that; if a ticker
match is wrong (e.g. a symbol reused after a merger), fix it by editing/deleting the row in
external_identity_map directly, not by making this script guess harder.

Idempotent: re-running updates existing rows (by the unique (issuer_id, external_system)
constraint) rather than duplicating them, so it's safe to run again after Equity-research
covers more companies.

Run with: backend/.venv/Scripts/python.exe backend/scripts/sync_equity_research_identity_map.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models import ExternalIdentityMap, Security
from app.db.session import SessionLocal

EXTERNAL_SYSTEM = "equity_research"
_DEFAULT_EQUITY_RESEARCH_DSN = "postgresql://equity_research:equity_research_dev@localhost:5433/equity_research"


def _fetch_equity_research_companies() -> list[tuple[str, str, str]]:
    """Returns (ticker, company_id, security_id) for every company Equity-research covers."""
    dsn = os.environ.get("EQUITY_RESEARCH_DATABASE_URL", _DEFAULT_EQUITY_RESEARCH_DSN)
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT s.ticker, c.id, s.id FROM core.companies c "
                "JOIN core.securities s ON s.company_id = c.id"
            )
            return [(row[0], str(row[1]), str(row[2])) for row in cur.fetchall()]
    finally:
        conn.close()


def main() -> None:
    equity_research_companies = _fetch_equity_research_companies()
    print(f"Equity-research reports {len(equity_research_companies)} ticker(s): "
          f"{[t for t, _, _ in equity_research_companies]}")

    with SessionLocal() as db:
        matched, unmatched = 0, []
        for ticker, company_id, security_id in equity_research_companies:
            security = db.execute(
                select(Security).where(Security.symbol == ticker.upper())
            ).scalar_one_or_none()
            if security is None:
                unmatched.append(ticker)
                continue

            stmt = pg_insert(ExternalIdentityMap).values(
                issuer_id=security.issuer_id,
                external_system=EXTERNAL_SYSTEM,
                external_id=company_id,
                external_security_id=security_id,
                ticker=ticker.upper(),
                match_method="ticker_exact",
            )
            stmt = stmt.on_conflict_do_update(
                constraint="uq_identity_map_issuer_system",
                set_={
                    "external_id": stmt.excluded.external_id,
                    "external_security_id": stmt.excluded.external_security_id,
                    "ticker": stmt.excluded.ticker,
                    "match_method": stmt.excluded.match_method,
                    "matched_at": stmt.excluded.matched_at,
                },
            )
            db.execute(stmt)
            matched += 1
        db.commit()

    print(f"Matched {matched}/{len(equity_research_companies)} ticker(s) into external_identity_map.")
    if unmatched:
        print(f"UNMATCHED (no psx_fertilizer security with this symbol): {unmatched}")


if __name__ == "__main__":
    main()
