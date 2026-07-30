"""Identity-master seed for sector pilots (Fertilizer + Cement).

Idempotent: safe to re-run. Uses get-or-create on Sector.name / Issuer.name / Security.symbol,
all of which are unique columns, so repeated runs never duplicate rows.
"""

import logging

from sqlalchemy.orm import Session

from app.db.models import Issuer, Sector, Security
from app.ingestion.psx_live import CEMENT_SECTOR_COMPANIES, FERTILIZER_SECTOR_COMPANIES

logger = logging.getLogger(__name__)

SECTOR_NAME = "Fertilizer"


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
    for company in FERTILIZER_SECTOR_COMPANIES:
        issuer = _get_or_create_issuer(db, company["name"], sector)
        security = _get_or_create_security(db, company["symbol"], issuer)
        securities.append(security)
    db.commit()
    return securities


def seed_cement_sector(db: Session) -> list[Security]:
    """Ensures the Cement sector and its pilot issuers/securities exist. Returns the securities."""
    sector = _get_or_create_sector(db, "Cement")
    securities = []
    for company in CEMENT_SECTOR_COMPANIES:
        issuer = _get_or_create_issuer(db, company["name"], sector)
        security = _get_or_create_security(db, company["symbol"], issuer)
        securities.append(security)
    db.commit()
    return securities


if __name__ == "__main__":
    import sys
    from app.db.session import SessionLocal

    sector_arg = sys.argv[1] if len(sys.argv) > 1 else "fertilizer"
    with SessionLocal() as session:
        if sector_arg == "cement":
            result = seed_cement_sector(session)
        else:
            result = seed_fertilizer_sector(session)
        print(f"Seeded {len(result)} securities: {[s.symbol for s in result]}")
