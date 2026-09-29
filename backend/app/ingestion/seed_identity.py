"""Identity-master seed: sector pilots (Fertilizer + Cement) plus full-market expansion.

Idempotent: safe to re-run. Uses get-or-create on Sector.name / Issuer.name / Security.symbol,
all of which are unique columns, so repeated runs never duplicate rows.
"""

import logging
import re
import json
from pathlib import Path

import psxdata
from sqlalchemy.orm import Session

from app.db.models import Issuer, Sector, Security
from app.ingestion.psx_live import CEMENT_SECTOR_COMPANIES, FERTILIZER_SECTOR_COMPANIES

logger = logging.getLogger(__name__)

SECTOR_NAME = "Fertilizer"
_UNIVERSE_SNAPSHOT = Path(__file__).resolve().parents[2] / "data" / "universe_snapshot.json"


def _snapshot_companies(sector: str, fallback: list[dict[str, str]]) -> list[dict[str, str]]:
    """Use the reviewed 23-company universe snapshot for identity seeding.

    The live-quote lists are intentionally narrower because the quote source does not serve
    every active security reliably; they must not define which companies Research Studio can
    search. The fallback keeps first-run tooling usable if the snapshot is missing.
    """
    if not _UNIVERSE_SNAPSHOT.exists():
        return fallback
    payload = json.loads(_UNIVERSE_SNAPSHOT.read_text(encoding="utf-8"))
    snapshot_rows = [
        {"symbol": row["symbol"], "name": row["name"]}
        for row in payload["entries"]
        if row["sector"].upper() == sector.upper()
    ]
    by_symbol = {row["symbol"]: row for row in snapshot_rows}
    ordered = [by_symbol[row["symbol"]] for row in fallback if row["symbol"] in by_symbol]
    seen = {row["symbol"] for row in ordered}
    return ordered + [row for row in snapshot_rows if row["symbol"] not in seen]

# Sector classifications that are fund-like entities (mutual funds/modarabas/REITs/govt paper),
# not operating companies -- standard equity metrics (P/E, ROE, DCF) don't fit them. Excluded
# from seed_full_market() per the 2026-08-04 scope-expansion decision; can be added back as
# their own category later with different valuation logic, without touching this seed.
FUND_LIKE_SECTORS = {
    "CLOSE - END MUTUAL FUND",
    "MODARABAS",
    "REAL ESTATE INVESTMENT TRUST",
    "BILLS AND BONDS",
}

_RIGHTS_ISSUE_RE = re.compile(r"\(right|right\)", re.IGNORECASE)


def _get_or_create_sector(db: Session, name: str) -> Sector:
    sector = db.query(Sector).filter(Sector.name == name).one_or_none()
    if sector is None:
        sector = Sector(name=name)
        db.add(sector)
        db.flush()
        logger.info("Created sector %s", name)
    return sector


def _get_or_create_issuer(db: Session, name: str, sector: Sector) -> Issuer:
    issuer = db.query(Issuer).filter(Issuer.name == name).one_or_none()
    if issuer is None:
        issuer = Issuer(name=name, sector_id=sector.id)
        db.add(issuer)
        db.flush()
        logger.info("Created issuer %s", name)
    elif issuer.sector_id != sector.id:
        issuer.sector_id = sector.id
    return issuer


def _get_or_create_security(db: Session, symbol: str, issuer: Issuer) -> Security:
    security = db.query(Security).filter(Security.symbol == symbol).one_or_none()
    if security is None:
        security = Security(symbol=symbol, issuer_id=issuer.id)
        db.add(security)
        db.flush()
        logger.info("Created security %s", symbol)
    return security


def seed_fertilizer_sector(db: Session) -> list[Security]:
    """Ensures the Fertilizer sector and its 7 pilot issuers/securities exist. Returns the securities."""
    sector = _get_or_create_sector(db, SECTOR_NAME)
    securities = []
    for company in _snapshot_companies("FERTILIZER", FERTILIZER_SECTOR_COMPANIES):
        issuer = _get_or_create_issuer(db, company["name"], sector)
        security = _get_or_create_security(db, company["symbol"], issuer)
        securities.append(security)
    db.commit()
    return securities


def seed_cement_sector(db: Session) -> list[Security]:
    """Ensures the Cement sector and its pilot issuers/securities exist. Returns the securities."""
    sector = _get_or_create_sector(db, "Cement")
    securities = []
    for company in _snapshot_companies("CEMENT", CEMENT_SECTOR_COMPANIES):
        issuer = _get_or_create_issuer(db, company["name"], sector)
        security = _get_or_create_security(db, company["symbol"], issuer)
        securities.append(security)
    db.commit()
    return securities


def seed_full_market(db: Session) -> list[Security]:
    """Ensures identity rows exist for the full PSX equity universe, sourced live from
    psxdata.symbols() -- not a hardcoded list, since the point is full-market coverage.

    Excludes: debt instruments (is_debt), GEM board (is_gem), ETFs (is_etf), rights issues
    (name matches "(Right)"/"Right)"), and fund-like entities (FUND_LIKE_SECTORS) -- none of
    these fit standard equity-research metrics (P/E, ROE, DCF), per the 2026-08-04
    scope-expansion decision. Preference/class shares (e.g. AGLNCPS, GCILB) are NOT deduped
    against their common-share issuer -- psxdata gives no parent-symbol link to do that
    reliably, so each becomes its own Issuer. Known simplification, not a bug: check for
    near-duplicate Issuer.name values (e.g. "X Limited" vs "X Non-Voting (Pref) Class A")
    before assuming two search results are genuinely different companies.

    PSX's own sector_name (40-ish real categories, ALL CAPS) is the sector taxonomy source of
    truth per that same decision -- title-cased here only for display consistency with the
    existing "Fertilizer"/"Cement" Sector rows (which were seeded the same way). A blank
    sector_name (~50 rows as of 2026-08-04) does NOT mean delisted -- it's a psxdata
    classification gap, not trading evidence -- these get an explicit "Unclassified" sector
    bucket instead of being silently dropped. Actual trading status is verify_active_listings.py's
    job, not this seed's -- keep those concerns separate.

    Idempotent, additive-only: never removes an Issuer/Security this run's symbol list doesn't
    include, since psxdata's snapshot could be transiently incomplete and this must not be
    mistaken for a delisting signal.
    """
    symbols_df = psxdata.symbols()
    equity = symbols_df[(~symbols_df["is_debt"]) & (~symbols_df["is_gem"]) & (~symbols_df["is_etf"])]
    equity = equity[~equity["sector_name"].isin(FUND_LIKE_SECTORS)]
    equity = equity[~equity["name"].apply(lambda n: bool(_RIGHTS_ISSUE_RE.search(str(n))))]

    securities = []
    for _, row in equity.iterrows():
        raw_sector = str(row["sector_name"]).strip()
        sector_name = raw_sector.title() if raw_sector else "Unclassified"
        sector = _get_or_create_sector(db, sector_name)
        issuer = _get_or_create_issuer(db, str(row["name"]).strip(), sector)
        security = _get_or_create_security(db, str(row["symbol"]).strip(), issuer)
        securities.append(security)
    db.commit()
    logger.info("seed_full_market: %d securities across %d sectors", len(securities), equity["sector_name"].nunique())
    return securities


if __name__ == "__main__":
    import sys
    from app.db.session import SessionLocal

    sector_arg = sys.argv[1] if len(sys.argv) > 1 else "fertilizer"
    with SessionLocal() as session:
        if sector_arg == "cement":
            result = seed_cement_sector(session)
        elif sector_arg == "full":
            result = seed_full_market(session)
        else:
            result = seed_fertilizer_sector(session)
        if sector_arg == "full":
            print(f"Seeded {len(result)} securities")
        else:
            print(f"Seeded {len(result)} securities: {[s.symbol for s in result]}")
