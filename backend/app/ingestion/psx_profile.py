"""Company profile + governance scraper: business description, key people, address,
website, registrar, auditor, fiscal year end — from the same PSX company page's
#profile section (server-rendered, confirmed via the same approach as announcements/
financials). Also resolves ownership chains that PSX states directly in the business
description text (e.g. "a subsidiary of Engro Corporation Limited").

Unlisted parent entities (Fauji Foundation, and any other non-PSX-listed holding
company found this way) are created as minimal Issuer stubs — no Security, no sector —
purely so the ownership graph has somewhere to point. is_psx_listed=False marks these.
"""

import hashlib
import logging
import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import BoardMembership, IngestionRun, Issuer, Person, SourceDocument
from app.ingestion.runs import ingestion_run
from app.ingestion.psx_announcements import BASE_URL, HEADERS
from app.ingestion.psx_financials import MONTH_TO_NUM, fetch_company_financials_html

logger = logging.getLogger(__name__)

# Known parent-entity name -> canonical Issuer name, so re-runs match the same stub
# instead of creating duplicates from slightly different text extractions.
KNOWN_PARENT_ALIASES = {
    "fauji foundation": "Fauji Foundation",
    "dawood hercules corporation limited": "Dawood Hercules Corporation Limited",
    "engro corporation limited": "Engro Corporation Limited",
}

# Regexes over the business description text — PSX's own wording is fairly consistent
# ("a subsidiary of X", "a subsidiary of X (the Y Company)"), but this is still text-
# matching over free-form prose, so it can miss phrasings not seen in our 7 examples.
PARENT_PATTERNS = [
    re.compile(r"subsidiary of ([A-Z][A-Za-z .&'-]+?(?:Limited|Company|Foundation))", re.IGNORECASE),
]


def _parse_profile_section(soup: BeautifulSoup) -> dict:
    section = soup.find("div", id="profile")
    if section is None:
        return {}

    result: dict = {}
    for head in section.select(".item__head"):
        label = head.get_text(strip=True)
        value_p = head.find_next_sibling("p")
        if value_p is None:
            continue
        text = value_p.get_text(" ", strip=True)
        if label == "BUSINESS DESCRIPTION":
            result["business_description"] = text
        elif label == "ADDRESS":
            result["address"] = text
        elif label == "WEBSITE":
            result["website"] = text
        elif label == "REGISTRAR":
            result["registrar"] = text
        elif label == "AUDITOR":
            result["auditor"] = text
        elif label == "Fiscal Year End":
            result["fiscal_year_end_month"] = MONTH_TO_NUM.get(text)  # None if PSX shows something unexpected

    people_block = section.find("div", class_="profile__item--people")
    key_people = []
    if people_block is not None:
        table = people_block.find("table")
        if table is not None:
            for tr in table.find("tbody").find_all("tr"):
                cells = tr.find_all("td")
                if len(cells) >= 2:
                    key_people.append((cells[0].get_text(strip=True), cells[1].get_text(strip=True)))
    result["key_people"] = key_people
    return result


def _extract_parent_name(business_description: str) -> str | None:
    for pattern in PARENT_PATTERNS:
        match = pattern.search(business_description)
        if match:
            raw_name = match.group(1).strip().rstrip(".")
            return KNOWN_PARENT_ALIASES.get(raw_name.lower(), raw_name)
    return None


def _get_or_create_parent_stub(db: Session, name: str) -> Issuer:
    existing = db.execute(select(Issuer).where(Issuer.name == name)).scalar_one_or_none()
    if existing is not None:
        return existing
    # Dawood Hercules is itself PSX-listed (symbol DAWH) but not in our Fertilizer-sector
    # pilot universe (see app/ingestion/psx_live.py's note on why it was dropped from the
    # live-quote list) — still real, still worth existing as a graph node with no sector.
    is_psx_listed = "hercules" in name.lower()
    issuer = Issuer(name=name, is_psx_listed=is_psx_listed)
    db.add(issuer)
    db.flush()
    logger.info("Created parent/holding issuer stub: %s (psx_listed=%s)", name, is_psx_listed)
    return issuer


def _get_or_create_person(db: Session, full_name: str) -> Person:
    existing = db.execute(select(Person).where(Person.full_name == full_name)).scalar_one_or_none()
    if existing is not None:
        return existing
    person = Person(full_name=full_name)
    db.add(person)
    db.flush()
    return person


def _record_profile_document(db: Session, issuer: Issuer, symbol: str, section_text: str) -> None:
    """One source_document per distinct profile content; an unchanged re-fetch just refreshes
    fetched_at, so 'profile as of' always reflects the last successful retrieval."""
    content_hash = hashlib.sha256(f"profile::{symbol}::{section_text}".encode()).hexdigest()
    existing = db.execute(select(SourceDocument).where(SourceDocument.content_hash == content_hash)).scalar_one_or_none()
    if existing is not None:
        existing.fetched_at = datetime.now(timezone.utc)
        return
    db.add(SourceDocument(
        issuer_id=issuer.id, url=f"{BASE_URL}/company/{symbol}", content_hash=content_hash,
        document_type="company_profile", source_tier="primary",
    ))


def ingest_company_profile(db: Session, issuer: Issuer, symbol: str, run: IngestionRun) -> dict[str, int]:
    failed = {"profile_updated": 0, "board_members_inserted": 0, "parent_linked": 0}
    html = fetch_company_financials_html(symbol)  # same page fetch as psx_financials.py
    if html is None:
        run.add_error(f"{symbol}: company page could not be fetched")
        db.commit()
        return failed

    soup = BeautifulSoup(html, "lxml")
    profile = _parse_profile_section(soup)
    if not profile:
        run.add_error(f"{symbol}: no #profile section on the company page")
        db.commit()
        return failed
    section = soup.find("div", id="profile")
    _record_profile_document(db, issuer, symbol, section.get_text(" ", strip=True))

    issuer.business_description = profile.get("business_description")
    issuer.address = profile.get("address")
    issuer.website = profile.get("website")
    issuer.registrar = profile.get("registrar")
    issuer.auditor = profile.get("auditor")
    issuer.fiscal_year_end_month = profile.get("fiscal_year_end_month")
    db.add(issuer)

    parent_linked = 0
    description = profile.get("business_description") or ""
    parent_name = _extract_parent_name(description)
    if parent_name:
        parent = _get_or_create_parent_stub(db, parent_name)
        if parent.id != issuer.id and issuer.ultimate_parent_issuer_id != parent.id:
            issuer.ultimate_parent_issuer_id = parent.id
            db.add(issuer)
            parent_linked = 1

    board_members_inserted = 0
    existing_roles = {
        bm.person_id
        for bm in db.execute(select(BoardMembership).where(BoardMembership.issuer_id == issuer.id)).scalars()
    }
    for full_name, role in profile.get("key_people", []):
        person = _get_or_create_person(db, full_name)
        if person.id in existing_roles:
            continue
        db.add(BoardMembership(person_id=person.id, issuer_id=issuer.id, role=role))
        board_members_inserted += 1

    run.rows_inserted += board_members_inserted + 1
    db.commit()
    return {
        "profile_updated": 1,
        "board_members_inserted": board_members_inserted,
        "parent_linked": parent_linked,
    }


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        from app.db.models import Security

        securities = session.execute(select(Security).where(Security.is_active.is_(True))).scalars().all()
        with ingestion_run(session, "psx_company_page", table="issuer_profile", symbols=[s.symbol for s in securities]) as run:
            for security in securities:
                stats = ingest_company_profile(session, security.issuer, security.symbol, run)
                print(f"{security.symbol}: {stats}")
