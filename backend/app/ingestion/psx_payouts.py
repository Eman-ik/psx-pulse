"""Dividend/bonus/rights history from dps.psx.com.pk's per-company payouts endpoint.

Confirmed via browser network inspection: POST /company/payouts with {"symbol": SYMBOL}
returns the same HTML table rendered on the company page's Payouts tab. See
docs/source_registry.yaml for the same Capital-Stake-via-PSX-portal caveat as announcements.
"""

import logging
import re
from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CorporateAction, Security

logger = logging.getLogger(__name__)

BASE_URL = "https://dps.psx.com.pk"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) psx-fertilizer-research-pilot/0.1"}

# (D) cash dividend, (B) bonus shares, (R) rights issue — inferred from PSX's own abbreviation
# used in the "Details" column (e.g. "85%(i) (D)"); default to dividend when no code is present,
# since it's overwhelmingly the common case for these income-focused fertilizer names.
DETAIL_TYPE_CODES = {"D": "dividend", "B": "bonus", "R": "rights"}


def fetch_company_payouts(symbol: str) -> list[dict]:
    try:
        response = httpx.post(
            f"{BASE_URL}/company/payouts", data={"symbol": symbol}, headers=HEADERS, timeout=30
        )
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to fetch payouts for %s: %s", symbol, exc)
        return []

    soup = BeautifulSoup(response.text, "lxml")
    table = soup.find("table", class_="tbl")
    if table is None or table.find("tbody") is None:
        return []

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 4:
            continue
        rows.append(
            {
                "symbol": symbol,
                "announced_text": cells[0].get_text(strip=True),
                "period": cells[1].get_text(strip=True),
                "details": cells[2].get_text(strip=True),
                "book_closure": cells[3].get_text(strip=True),
            }
        )
    return rows


def _parse_details(details: str) -> tuple[str, float | None]:
    pct_match = re.search(r"([\d.]+)\s*%", details)
    amount = float(pct_match.group(1)) if pct_match else None
    code_match = re.search(r"\(([DBR])\)", details)
    action_type = DETAIL_TYPE_CODES.get(code_match.group(1), "dividend") if code_match else "dividend"
    return action_type, amount


def _parse_book_closure_start(book_closure: str) -> date | None:
    # e.g. "12/05/2026  - 14/05/2026 " -> first date, DD/MM/YYYY per PSX's own display format
    first = book_closure.split("-")[0].strip()
    try:
        return datetime.strptime(first, "%d/%m/%Y").date()
    except ValueError:
        return None


def _parse_announced_date(announced_text: str) -> date | None:
    # e.g. "April 29, 2026 2:58 PM" -> drop the trailing "2:58 PM" time part
    date_part = announced_text.rsplit(" ", 2)[0]
    try:
        return datetime.strptime(date_part, "%B %d, %Y").date()
    except (ValueError, IndexError):
        return None


def ingest_security_payouts(db: Session, security: Security) -> dict[str, int]:
    rows = fetch_company_payouts(security.symbol)
    inserted = skipped = 0

    existing_effective_dates = set(
        db.execute(
            select(CorporateAction.effective_date).where(CorporateAction.security_id == security.id)
        )
        .scalars()
        .all()
    )

    for row in rows:
        effective_date = _parse_book_closure_start(row["book_closure"])
        if effective_date is None or effective_date in existing_effective_dates:
            skipped += 1
            continue

        action_type, amount = _parse_details(row["details"])
        db.add(
            CorporateAction(
                security_id=security.id,
                action_type=action_type,
                announced_date=_parse_announced_date(row["announced_text"]),
                effective_date=effective_date,
                ratio_or_amount=amount,
                currency="PKR_PCT" if amount is not None else None,
            )
        )
        existing_effective_dates.add(effective_date)
        inserted += 1

    db.commit()
    return {"inserted": inserted, "skipped": skipped, "fetched": len(rows)}


if __name__ == "__main__":
    from app.db.session import SessionLocal
    from app.ingestion.seed_identity import seed_fertilizer_sector

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        securities = seed_fertilizer_sector(session)
        for security in securities:
            stats = ingest_security_payouts(session, security)
            print(f"{security.symbol}: {stats}")
