"""Consistency check for external_identity_map -- the bridge between psx_fertilizer
and Equity-research's separate databases (see app/api/equity_research.py's module
docstring). Two databases evolving independently means this mapping can silently
drift out of date; this script makes that drift visible instead of assumed-away.

Unlike sync_equity_research_identity_map.py (which POPULATES/updates the mapping),
this script only READS and reports -- it never writes to either database. Run it
periodically (or after either database changes) to catch:

  1. UNMAPPED: an Equity-research company with no external_identity_map row at all
     (sync_equity_research_identity_map.py already reports this as "UNMATCHED";
     duplicated here so this one script is the single place to check everything).
  2. ORPHANED: an external_identity_map row whose external_id/external_security_id
     no longer exists in Equity-research (e.g. deleted or renamed on that side
     since the mapping was created).
  3. STALE: a mapping row's `ticker` no longer matches the current
     Security.symbol for that issuer_id on the psx_fertilizer side (e.g. a ticker
     change after this mapping was made) -- would silently resolve requests to the
     wrong company's data if left unnoticed.

Exit code is 1 if any drift is found, 0 if the mapping is fully consistent --
usable as a scheduled check, not just an ad-hoc read.

Run with: backend/.venv/Scripts/python.exe scripts/check_identity_drift.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2
from sqlalchemy import select

from app.db.models import ExternalIdentityMap, Security
from app.db.session import SessionLocal

EXTERNAL_SYSTEM = "equity_research"
_DEFAULT_EQUITY_RESEARCH_DSN = "postgresql://equity_research:equity_research_dev@localhost:5433/equity_research"


def _fetch_equity_research_companies() -> dict[str, tuple[str, str]]:
    """ticker -> (company_id, security_id) for every company Equity-research covers."""
    dsn = os.environ.get("EQUITY_RESEARCH_DATABASE_URL", _DEFAULT_EQUITY_RESEARCH_DSN)
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT s.ticker, c.id, s.id FROM core.companies c "
                "JOIN core.securities s ON s.company_id = c.id"
            )
            return {row[0].upper(): (str(row[1]), str(row[2])) for row in cur.fetchall()}
    finally:
        conn.close()


def main() -> None:
    equity_research = _fetch_equity_research_companies()

    with SessionLocal() as db:
        mappings = db.execute(select(ExternalIdentityMap).where(ExternalIdentityMap.external_system == EXTERNAL_SYSTEM)).scalars().all()
        symbol_by_issuer = {
            s.issuer_id: s.symbol for s in db.execute(select(Security)).scalars().all()
        }

    mapped_tickers = {m.ticker.upper() for m in mappings}

    unmapped = sorted(set(equity_research) - mapped_tickers)

    orphaned = []
    for m in mappings:
        real = equity_research.get(m.ticker.upper())
        if real is None or real[0] != m.external_id or real[1] != m.external_security_id:
            orphaned.append(m)

    stale = []
    for m in mappings:
        current_symbol = symbol_by_issuer.get(m.issuer_id)
        if current_symbol is not None and current_symbol.upper() != m.ticker.upper():
            stale.append((m, current_symbol))

    print(f"Equity-research: {len(equity_research)} companies. external_identity_map: {len(mappings)} rows.\n")

    print(f"UNMAPPED ({len(unmapped)}): Equity-research company with no mapping row")
    for t in unmapped:
        print(f"  {t}")

    print(f"\nORPHANED ({len(orphaned)}): mapping row whose Equity-research target no longer matches")
    for m in orphaned:
        print(f"  issuer_id={m.issuer_id} ticker={m.ticker} -> external_id={m.external_id} (not found or changed in Equity-research)")

    print(f"\nSTALE ({len(stale)}): mapping ticker no longer matches psx_fertilizer's current Security.symbol")
    for m, current in stale:
        print(f"  issuer_id={m.issuer_id} mapping says {m.ticker}, Security.symbol is now {current}")

    total_drift = len(unmapped) + len(orphaned) + len(stale)
    print(f"\n{'DRIFT FOUND' if total_drift else 'CONSISTENT'}: {total_drift} issue(s).")
    sys.exit(1 if total_drift else 0)


if __name__ == "__main__":
    main()
