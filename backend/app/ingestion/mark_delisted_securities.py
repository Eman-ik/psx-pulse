"""Marks securities that have stopped trading as delisted, with the corporate action that
caused it, so this is reproducible from a fresh DB rather than a one-off manual fix.

Idempotent: safe to re-run (checks Security.is_active / an existing CorporateAction with the
same security_id + action_type + effective_date before writing).
"""

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Announcement, CorporateAction, Security, SourceDocument

logger = logging.getLogger(__name__)

# symbol -> (action_type, announced_date, effective_date, evidence_announcement_title)
# effective_date is the last trading day on file (price_ohlcv), used as the best available
# proxy for when the listing actually ended, since PSX doesn't publish a single canonical
# "delisting effective date" field we can scrape.
DELISTED_SECURITIES: dict[str, dict] = {
    "FFBL": {
        "action_type": "merger",
        "announced_date": date(2024, 12, 13),
        "effective_date": date(2024, 12, 20),
        # Used to look up the SourceDocument for provenance (source_document_id on the
        # CorporateAction row) -- the Lahore High Court's sanction order for the Scheme of
        # Arrangement merging FFBL into FFC.
        "evidence_announcement_title": (
            "Certified True Copy of the Order of Honorable Lahore High Court and the "
            "Sanctioned Scheme of Arrangement"
        ),
    },
    "ENGRO": {
        "action_type": "merger",
        # A 3-party "Scheme of Arrangement of Dawood Hercules Corporation Limited, Engro
        # Corporation Limited and DH Partners Limited" -- unlike FFBL's announcements, none of
        # ENGRO's own filings on file use the word "merger" explicitly (we only have headline
        # titles, not the underlying PDFs), so the exact restructuring mechanics (e.g. whether
        # DAWH is the surviving entity) aren't independently confirmed here. "merger" is used
        # as the closest fit in CORPORATE_ACTION_TYPES, not a verified legal characterization.
        # What IS independently verified: ENGRO stopped trading after 2025-01-03 (confirmed
        # both in this pilot's own price_ohlcv and via a live psxdata.stocks("ENGRO", ...) call
        # returning zero bars for 2025-2026) -- that fact, not the legal label, is why it's
        # excluded from the active pilot.
        "announced_date": date(2024, 12, 27),
        "effective_date": date(2025, 1, 3),
        "evidence_announcement_title": (
            "PUBLICATION OF BOOK CLOSURE NOTICE FOR IMPLEMENTATION OF THE SCHEME OF "
            "ARRANGEMENT OF DAWOOD HERCULES CORPORATION LIMITED, ENGRO CORPORATION LIMITED "
            "AND DH PARTNERS LIMITED"
        ),
    },
}


def mark_delisted_securities(db: Session) -> dict[str, str]:
    results = {}
    for symbol, spec in DELISTED_SECURITIES.items():
        security = db.execute(select(Security).where(Security.symbol == symbol)).scalar_one_or_none()
        if security is None:
            results[symbol] = "security not found, skipped"
            continue

        if security.listing_status != "delisted" or security.is_active:
            security.listing_status = "delisted"
            security.is_active = False

        existing_action = db.execute(
            select(CorporateAction).where(
                CorporateAction.security_id == security.id,
                CorporateAction.action_type == spec["action_type"],
                CorporateAction.effective_date == spec["effective_date"],
            )
        ).scalar_one_or_none()
        if existing_action is not None:
            results[symbol] = "already recorded"
            continue

        evidence = db.execute(
            select(Announcement, SourceDocument)
            .join(SourceDocument, SourceDocument.id == Announcement.source_document_id)
            .where(
                Announcement.issuer_id == security.issuer_id,
                Announcement.title == spec["evidence_announcement_title"],
            )
        ).first()
        source_document_id = evidence[1].id if evidence else None

        db.add(
            CorporateAction(
                security_id=security.id,
                action_type=spec["action_type"],
                announced_date=spec["announced_date"],
                effective_date=spec["effective_date"],
                source_document_id=source_document_id,
            )
        )
        results[symbol] = f"marked delisted, corporate_action inserted (source_document_id={source_document_id})"

    db.commit()
    return results


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        print(mark_delisted_securities(session))
