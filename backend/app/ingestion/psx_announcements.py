"""Company-filtered PSX announcements, scraped from dps.psx.com.pk/company/{symbol}.

That page server-renders an `#announcements` section with three tabbed panels
(Financial Results / Board Meetings / Others), each a plain HTML table of
Date / Title / Document(PDF) rows — no JS rendering required, confirmed via a
plain httpx GET. See docs/source_registry.yaml for the rights/notes on this source.

Note: PSX's own portal footer states this data is "powered by capitalstake.com" —
i.e. even PSX's public site is displaying Capital Stake-licensed data, not raw
PSX-only data. Treated as primary/free-tier for this dev pilot; recheck Capital
Stake's own terms of use before any public/commercial launch, same as the rest
of docs/rights_matrix.template.md.
"""

import hashlib
import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Announcement, IngestionRun, Issuer, SourceDocument
from app.etl.sentiment import classify_sentiment
from app.ingestion.runs import ingestion_run

logger = logging.getLogger(__name__)

BASE_URL = "https://dps.psx.com.pk"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) psx-fertilizer-research-pilot/0.1"}

# PSX's own tab names -> our announcement category taxonomy (app/db/models/announcements.py)
TAB_TO_CATEGORY = {
    "Financial Results": "results",
    "Board Meetings": "board",
    "Others": "other",
}


def fetch_company_announcements(symbol: str) -> list[dict]:
    """Scrapes the announcements section of one company's PSX page. Raises if the page
    can't be fetched or has no announcements section, so callers can tell failure from empty."""
    url = f"{BASE_URL}/company/{symbol}"
    response = httpx.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    section = soup.find("div", id="announcements")
    if section is None:
        raise ValueError(f"no #announcements section on {url}")

    rows = []
    for panel in section.find_all("div", class_="tabs__panel"):
        category = TAB_TO_CATEGORY.get(panel.get("data-name", ""), "other")
        table = panel.find("table", class_="tbl")
        if table is None or table.find("tbody") is None:
            continue
        for tr in table.find("tbody").find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 3:
                continue
            date_text = cells[0].get_text(strip=True)
            title = cells[1].get_text(strip=True)
            pdf_link = cells[2].find("a", href=lambda h: h and h.endswith(".pdf"))
            pdf_url = f"{BASE_URL}{pdf_link['href']}" if pdf_link else None
            rows.append(
                {
                    "symbol": symbol,
                    "category": category,
                    "date_text": date_text,
                    "title": title,
                    "pdf_url": pdf_url,
                }
            )
    return rows


def _parse_announcement_date(date_text: str) -> datetime:
    # PSX renders these as "Apr 30, 2026"
    return datetime.strptime(date_text, "%b %d, %Y").replace(tzinfo=timezone.utc)


def ingest_company_announcements(db: Session, issuer: Issuer, symbol: str, run: IngestionRun) -> dict[str, int]:
    """Fetches and stores announcements for one issuer, deduping on the PDF URL's content hash."""
    try:
        rows = fetch_company_announcements(symbol)
    except Exception as exc:
        logger.warning("Announcements fetch failed for %s: %s", symbol, exc)
        run.add_error(f"{symbol}: {type(exc).__name__}: {exc}")
        db.commit()
        return {"inserted": 0, "skipped": 0, "fetched": 0}
    inserted = skipped = 0

    for row in rows:
        if not row["pdf_url"]:
            skipped += 1
            continue

        content_hash = hashlib.sha256(row["pdf_url"].encode()).hexdigest()
        existing = db.execute(
            select(SourceDocument).where(SourceDocument.content_hash == content_hash)
        ).scalar_one_or_none()
        if existing is not None:
            skipped += 1
            continue

        try:
            published_at = _parse_announcement_date(row["date_text"])
        except ValueError:
            logger.warning("Unparseable date %r for %s, skipping", row["date_text"], symbol)
            skipped += 1
            continue

        source_document = SourceDocument(
            issuer_id=issuer.id,
            url=row["pdf_url"],
            content_hash=content_hash,
            document_type="announcement",
            source_tier="primary",
            published_at=published_at,
        )
        db.add(source_document)
        db.flush()

        db.add(
            Announcement(
                issuer_id=issuer.id,
                source_document_id=source_document.id,
                title=row["title"],
                category=row["category"],
                published_at=published_at,
                sentiment_score=classify_sentiment(row["title"]),
            )
        )
        inserted += 1

    run.rows_inserted += inserted
    db.commit()
    return {"inserted": inserted, "skipped": skipped, "fetched": len(rows)}


if __name__ == "__main__":
    import sys

    from app.db.session import SessionLocal
    from app.ingestion.psx_live import CEMENT_SECTOR_COMPANIES, FERTILIZER_SECTOR_COMPANIES
    from app.ingestion.seed_identity import seed_cement_sector, seed_fertilizer_sector

    logging.basicConfig(level=logging.INFO)

    # Usage: python -m app.ingestion.psx_announcements [sector]
    # sector: "fertilizer" (default), "cement", or "all"
    sector_arg = sys.argv[1] if len(sys.argv) > 1 else "fertilizer"

    with SessionLocal() as session:
        targets = []
        if sector_arg in ("fertilizer", "all"):
            by_symbol = {s.symbol: s for s in seed_fertilizer_sector(session)}
            targets += [by_symbol[c["symbol"]] for c in FERTILIZER_SECTOR_COMPANIES if c["symbol"] in by_symbol]
        if sector_arg in ("cement", "all"):
            by_symbol = {s.symbol: s for s in seed_cement_sector(session)}
            targets += [by_symbol[c["symbol"]] for c in CEMENT_SECTOR_COMPANIES if c["symbol"] in by_symbol]

        with ingestion_run(session, "psx_company_page", table="announcement", symbols=[s.symbol for s in targets]) as run:
            for security in targets:
                stats = ingest_company_announcements(session, security.issuer, security.symbol, run)
                print(f"{security.symbol}: {stats}")
