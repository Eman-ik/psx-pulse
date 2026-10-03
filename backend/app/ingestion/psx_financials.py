"""Annual financial-statement headline figures + PSX/Capital-Stake-reported ratios.

Scraped from the same dps.psx.com.pk/company/{symbol} page as announcements/payouts
(confirmed server-rendered, no JS needed). This page only exposes Sales, Profit after
Taxation and EPS — not a full income statement, and no balance sheet or cash flow at all.
That's a real limitation of this free source, not a parsing gap: a fuller statement would
need manual analyst entry from annual-report PDFs (see Milestone 1 plan), which this module
does not attempt.

The Ratios table on the same page (Gross Profit Margin, Net Profit Margin, EPS Growth, PEG)
is Capital Stake's own calculation, not derived from facts we track here, so it's stored as
evidence class "third_party_estimate", separate from app/etl/ratio_engine.py's own
independently-computed ratios (which only exist for line items we actually have inputs for).
"""

import hashlib
import logging
from datetime import date, timedelta

from bs4 import BeautifulSoup
from bs4.element import Tag
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    EvidenceLink,
    FinancialFact,
    Issuer,
    RatioDefinition,
    RatioValue,
    Security,
    SourceDocument,
)
from app.ingestion.psx_announcements import BASE_URL, HEADERS
from app.ingestion.duration_normalizer import FactDurationTagger, IngestionValidator
import httpx

logger = logging.getLogger(__name__)

# PSX table row label -> our canonical taxonomy key
LINE_ITEM_MAP = {
    "Sales": "revenue",
    "Profit after Taxation": "profit_after_tax",
    "EPS": "eps",
}

# PSX/Capital Stake ratio row label -> (our key, unit)
THIRD_PARTY_RATIO_MAP = {
    "Gross Profit Margin (%)": ("gross_profit_margin_reported", "percent"),
    "Net Profit Margin (%)": ("net_profit_margin_reported", "percent"),
    "EPS Growth (%)": ("eps_growth_reported", "percent"),
    "PEG": ("peg_reported", "ratio"),
}

MONTH_TO_NUM = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}


def _parse_value(text: str) -> float | None:
    text = text.strip().replace(",", "")
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return -value if negative else value


def _fiscal_year_end_month(soup: BeautifulSoup) -> int:
    """Returns the fiscal year end month number, defaulting to December if not found."""
    for head in soup.select("#profile .item__head"):
        if head.get_text(strip=True) == "Fiscal Year End":
            month_text = head.find_next_sibling("p")
            if month_text:
                month_name = month_text.get_text(strip=True)
                return MONTH_TO_NUM.get(month_name, 12)
    return 12


def _year_column_to_period(year: int, fiscal_month: int) -> tuple[date, date]:
    """Annual columns are labeled by the calendar year the fiscal year ends in."""
    if fiscal_month == 12:
        return date(year, 1, 1), date(year, 12, 31)
    # Last day of fiscal_month: first day of the following month, minus one day.
    period_end = (date(year, fiscal_month, 28) + timedelta(days=10)).replace(day=1) - timedelta(days=1)
    period_start = date(year - 1, fiscal_month + 1, 1)
    return period_start, period_end


def _parse_annual_table(table: Tag) -> tuple[list[int], dict[str, dict[int, float | None]]]:
    header_cells = table.find("thead").find_all("th")[1:]
    years = [int(th.get_text(strip=True)) for th in header_cells]

    data: dict[str, dict[int, float | None]] = {}
    body = table.find("tbody")
    for tr in body.find_all("tr"):
        cells = tr.find_all("td")
        label = cells[0].get_text(strip=True)
        values = {years[i]: _parse_value(cells[i + 1].get_text()) for i in range(len(years))}
        data[label] = values
    return years, data


def _parse_equity_profile(soup: BeautifulSoup) -> dict[str, float | None]:
    """Parses the #equity section: Market Cap (000's), Shares, Free Float (count), Free Float (%).

    Both "Free Float" labels are identical text — distinguished positionally (count comes
    before percent) since that ordering is consistent with the page's own layout.
    """
    section = soup.find("div", id="equity")
    if section is None:
        return {}

    items = section.select(".stats_item")
    free_float_seen = 0
    result: dict[str, float | None] = {}
    for item in items:
        label = item.select_one(".stats_label")
        value = item.select_one(".stats_value")
        if label is None or value is None:
            continue
        label_text = label.get_text(strip=True)
        value_text = value.get_text(strip=True)
        if "Market Cap" in label_text:
            result["market_cap"] = _parse_value(value_text.replace(",", ""))
        elif label_text == "Shares":
            result["shares_outstanding"] = _parse_value(value_text.replace(",", ""))
        elif label_text == "Free Float":
            free_float_seen += 1
            if free_float_seen == 1:
                result["free_float_shares"] = _parse_value(value_text.replace(",", ""))
            else:
                result["free_float_pct"] = _parse_value(value_text.replace("%", ""))
    return result


def fetch_company_financials_html(symbol: str) -> str | None:
    try:
        response = httpx.get(f"{BASE_URL}/company/{symbol}", headers=HEADERS, timeout=20)
        response.raise_for_status()
        return response.text
    except Exception as exc:
        logger.warning("Failed to fetch %s for financials: %s", symbol, exc)
        return None


def ingest_company_financials(db: Session, security: Security, symbol: str) -> dict[str, int]:
    issuer = security.issuer
    html = fetch_company_financials_html(symbol)
    if html is None:
        return {"facts_inserted": 0, "ratios_inserted": 0, "skipped": 0}

    soup = BeautifulSoup(html, "lxml")

    equity_profile = _parse_equity_profile(soup)
    if equity_profile.get("free_float_pct") is not None:
        security.free_float_pct = equity_profile["free_float_pct"]
        db.add(security)

    financials_section = soup.find("div", id="financials")
    ratios_section = soup.find("div", id="ratios")

    # One source document per scrape, hashed on the full page so a re-scrape only creates a
    # new document/version when the underlying figures actually change.
    content_hash = hashlib.sha256(html.encode()).hexdigest()
    source_document = db.execute(
        select(SourceDocument).where(SourceDocument.content_hash == content_hash)
    ).scalar_one_or_none()
    if source_document is None:
        source_document = SourceDocument(
            issuer_id=issuer.id,
            url=f"{BASE_URL}/company/{symbol}",
            content_hash=content_hash,
            document_type="financials_snapshot",
            source_tier="primary",
        )
        db.add(source_document)
        db.flush()

    facts_inserted = skipped = 0

    # Market cap and shares outstanding are point-in-time (not tied to a fiscal period), so
    # they use period_type="snapshot" with period_end = the scrape date, and are always
    # re-inserted fresh rather than checked against an "existing" period match — unlike
    # annual facts, a stale snapshot is actively misleading (market cap moves daily).
    today = date.today()
    duration_tagger = FactDurationTagger(db)

    for key in ("market_cap", "shares_outstanding"):
        value = equity_profile.get(key)
        if value is None:
            continue

        fact = FinancialFact(
            issuer_id=issuer.id,
            line_item=key,
            period_start=today,
            period_end=today,
            period_type="snapshot",
            scope="standalone",
            unit="PKR_thousand" if key == "market_cap" else "shares",
            value=value,
            source_document_id=source_document.id,
        )

        # Auto-detect and tag duration_basis
        fact, metadata = duration_tagger.tag_fact(fact)

        db.add(fact)
        facts_inserted += 1

    if financials_section is None:
        logger.warning("No #financials section found for %s", symbol)
        db.commit()
        return {"facts_inserted": facts_inserted, "ratios_inserted": 0, "skipped": 0}

    annual_panel = financials_section.find("div", class_="tabs__panel", attrs={"data-name": "Annual"})
    annual_table = annual_panel.find("table") if annual_panel else None
    if annual_table is None:
        db.commit()
        return {"facts_inserted": facts_inserted, "ratios_inserted": 0, "skipped": 0}

    fiscal_month = _fiscal_year_end_month(soup)
    years, financial_rows = _parse_annual_table(annual_table)

    for label, key in LINE_ITEM_MAP.items():
        values_by_year = financial_rows.get(label, {})
        for year, value in values_by_year.items():
            if value is None:
                skipped += 1
                continue
            period_start, period_end = _year_column_to_period(year, fiscal_month)
            existing = db.execute(
                select(FinancialFact).where(
                    FinancialFact.issuer_id == issuer.id,
                    FinancialFact.line_item == key,
                    FinancialFact.period_end == period_end,
                    FinancialFact.period_type == "annual",
                    FinancialFact.scope == "standalone",
                    FinancialFact.superseded_by_id.is_(None),
                )
            ).scalars().first()
            if existing is not None:
                skipped += 1
                continue
            unit = "PKR_thousand" if key != "eps" else "PKR"

            fact = FinancialFact(
                issuer_id=issuer.id,
                line_item=key,
                period_start=period_start,
                period_end=period_end,
                period_type="annual",
                scope="standalone",  # verified: matches FFC standalone statements — see docs/source_registry.yaml
                unit=unit,
                value=value,
                source_document_id=source_document.id,
            )

            # Auto-detect and tag duration_basis
            fact, metadata = duration_tagger.tag_fact(fact)

            db.add(fact)
            facts_inserted += 1

    ratios_inserted = 0
    if ratios_section is not None:
        ratio_table = ratios_section.find("table")
        if ratio_table is not None:
            _, ratio_rows = _parse_annual_table(ratio_table)
            for label, (key, unit) in THIRD_PARTY_RATIO_MAP.items():
                values_by_year = ratio_rows.get(label, {})
                for year, value in values_by_year.items():
                    if value is None:
                        continue
                    period_start, period_end = _year_column_to_period(year, fiscal_month)
                    ratio_def = _get_or_create_third_party_ratio_definition(db, key, label, unit)
                    existing = db.execute(
                        select(RatioValue).where(
                            RatioValue.ratio_definition_id == ratio_def.id,
                            RatioValue.issuer_id == issuer.id,
                            RatioValue.period_end == period_end,
                        )
                    ).scalar_one_or_none()
                    if existing is not None:
                        continue
                    ratio_value = RatioValue(
                        ratio_definition_id=ratio_def.id,
                        issuer_id=issuer.id,
                        period_end=period_end,
                        period_type="annual",
                        scope="standalone",
                        value=value,
                        input_fact_ids=[],
                    )
                    db.add(ratio_value)
                    db.flush()
                    db.add(
                        EvidenceLink(
                            evidence_class="third_party_estimate",
                            target_table="ratio_value",
                            target_id=ratio_value.id,
                            source_document_id=source_document.id,
                            note="Capital Stake, via PSX company page — not independently derived.",
                        )
                    )
                    ratios_inserted += 1

    db.commit()
    return {"facts_inserted": facts_inserted, "ratios_inserted": ratios_inserted, "skipped": skipped}


def _get_or_create_third_party_ratio_definition(db: Session, key: str, label: str, unit: str) -> RatioDefinition:
    existing = db.execute(select(RatioDefinition).where(RatioDefinition.key == key)).scalar_one_or_none()
    if existing is not None:
        return existing
    category = "valuation" if key == "peg_reported" else ("growth" if "growth" in key else "profitability")
    definition = RatioDefinition(
        key=key,
        formula_version=1,
        name=label,
        category=category,
        formula_description="As displayed by Capital Stake via the PSX company page; not derived from our own tracked financial_fact inputs.",
        unit=unit,
    )
    db.add(definition)
    db.flush()
    return definition


if __name__ == "__main__":
    import sys

    from app.db.session import SessionLocal
    from app.ingestion.psx_prices import db_active_securities
    from app.ingestion.seed_identity import seed_cement_sector, seed_fertilizer_sector

    logging.basicConfig(level=logging.INFO)

    # Usage: python -m app.ingestion.psx_financials [sector]
    # sector: "fertilizer" (default), "cement", "pilot" (both, the OLD meaning of "all"), or
    # "market" (every active Security). ingest_company_financials() itself was always
    # symbol-agnostic -- this CLI just never exposed a way to run it past the fertilizer+
    # cement pilot, the exact same "all" footgun app/ingestion/psx_prices.py already had and
    # fixed (see that module's __main__ comment). "all" now means "market", not "pilot" --
    # keeping the old fert+cement-only meaning under "all" here after fixing it everywhere
    # else would just move the footgun, not remove it.
    sector_arg = sys.argv[1] if len(sys.argv) > 1 else "fertilizer"

    with SessionLocal() as session:
        securities: list = []
        if sector_arg in ("fertilizer", "pilot"):
            securities += seed_fertilizer_sector(session)
        if sector_arg in ("cement", "pilot"):
            securities += seed_cement_sector(session)
        if sector_arg in ("market", "all"):
            securities = db_active_securities(session)

        for security in securities:
            stats = ingest_company_financials(session, security, security.symbol)
            print(f"{security.symbol}: {stats}")
