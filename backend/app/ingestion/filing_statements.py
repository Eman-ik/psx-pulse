"""Statement figures from two source types, each stored with evidence and checked before storing.

1. PSX company page annual table (sales, profit after tax, EPS). Its figures are standalone:
   they equal FFC's own standalone statements for the same periods.
2. The standalone statement of financial position inside a company's interim report on PSX. Its
   audited year-end column supplies the prior year-end balance sheet. The balance sheet must tie out
   (assets = liabilities + equity, subtotals = sum of their rows) in both columns, or the whole set
   goes to quarantine and nothing is stored.

A value that conflicts with one already on file is quarantined for review, never overwritten.
"""

import hashlib
import io
import json
import logging
import re
from datetime import datetime, timezone

import httpx
import pdfplumber
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Extraction, FinancialFact, IngestionRun, QuarantinedRow, Security, SourceDocument
from app.ingestion.manual_financials_seed import _fiscal_period
from app.ingestion.psx_announcements import BASE_URL, HEADERS
from app.ingestion.psx_financials import fetch_company_financials_html
from app.ingestion.runs import ingestion_run

logger = logging.getLogger(__name__)

SCOPE = "standalone"
PSX_ANNUAL_ITEMS = {"Sales": "revenue", "Profit after Taxation": "profit_after_tax", "EPS": "eps"}
UNIT = {"eps": "PKR"}
ROW = re.compile(r"^(?P<label>.+?)\s+(?:(?P<note>\d{1,2})\s+)?(?P<cur>[\d,]{4,})\s+(?P<prior>[\d,]{4,})$")
SUBTOTAL = re.compile(r"^(?P<cur>[\d,]{4,})\s+(?P<prior>[\d,]{4,})$")


class TieOutError(ValueError):
    pass


def _quarantine(db: Session, run: IngestionRun, key: str, payload: dict, reason: str) -> None:
    db.add(QuarantinedRow(ingestion_run_id=run.id, target_table="financial_fact", natural_key=key, payload=payload, reason=reason))
    run.rows_rejected += 1
    run.add_error(f"{key}: {reason}")


def _store_fact(db, run, security, line_item, year, value, doc, extraction, published_at=None, publication_doc=None) -> None:
    issuer = security.issuer
    if issuer.fiscal_year_end_month is None:
        raise ValueError(f"{security.symbol}: fiscal year-end month is not on file")
    start, end = _fiscal_period(year, issuer.fiscal_year_end_month)
    run.rows_seen += 1
    existing = db.execute(select(FinancialFact).where(
        FinancialFact.issuer_id == issuer.id, FinancialFact.line_item == line_item, FinancialFact.period_end == end,
        FinancialFact.period_type == "annual", FinancialFact.scope == SCOPE, FinancialFact.superseded_by_id.is_(None),
    )).scalar_one_or_none()
    if existing is not None:
        if abs(float(existing.value) - float(value)) <= (0.01 if line_item == "eps" else 1.0):
            return
        _quarantine(db, run, f"{security.symbol}:{line_item}:{end}", {"on_file": float(existing.value), "incoming": value,
                    "incoming_source": doc.url}, "conflicts with the value already on file; not overwritten")
        return
    db.add(FinancialFact(
        issuer_id=issuer.id, line_item=line_item, period_start=start, period_end=end, period_type="annual", scope=SCOPE,
        unit=UNIT.get(line_item, "PKR_thousand"), value=value, source_document_id=doc.id, extraction_id=extraction.id,
        published_at=published_at, publication_document_id=publication_doc.id if publication_doc else None,
        ingestion_run_id=run.id,
    ))
    run.rows_inserted += 1


def _get_or_create_document(db: Session, issuer_id: int, url: str, document_type: str, content_hash: str) -> SourceDocument:
    doc = db.execute(select(SourceDocument).where(SourceDocument.content_hash == content_hash)).scalar_one_or_none()
    if doc is None:
        doc = SourceDocument(issuer_id=issuer_id, url=url, content_hash=content_hash, document_type=document_type, source_tier="primary")
        db.add(doc)
        db.flush()
    return doc


def _num(text: str) -> float:
    return float(text.replace(",", "").replace("(", "-").replace(")", ""))


# ── 1. PSX company-page annual table ───────────────────────────────────────────────

def load_psx_annual_table(db: Session, security: Security, run: IngestionRun, years: list[int]) -> int:
    html = fetch_company_financials_html(security.symbol)
    if html is None:
        run.add_error(f"{security.symbol}: company page could not be fetched")
        return 0
    section = BeautifulSoup(html, "lxml").find(id="financials")
    table = section.find("table") if section else None
    if table is None:
        run.add_error(f"{security.symbol}: no annual financial table on the company page")
        return 0
    columns = [th.get_text(strip=True) for th in table.find_all("th")][1:]
    rows = {tr.find_all("td")[0].get_text(strip=True): [td.get_text(strip=True) for td in tr.find_all("td")[1:]]
            for tr in table.find("tbody").find_all("tr")}
    raw = {"columns": columns, "rows": rows, "units": "Rupees '000 (EPS in Rupees)", "scope": SCOPE,
           "scope_basis": "Matches the company's own standalone statements for the same periods."}
    doc = _get_or_create_document(db, security.issuer_id, f"{BASE_URL}/company/{security.symbol}", "financials_snapshot",
                                  hashlib.sha256(f"psx-annual::{security.symbol}::{json.dumps(raw, sort_keys=True)}".encode()).hexdigest())
    extraction = Extraction(source_document_id=doc.id, method="parsed", raw_json=raw)
    db.add(extraction)
    db.flush()
    before = run.rows_inserted
    for year in years:
        if str(year) not in columns:
            run.add_error(f"{security.symbol}: year {year} not in the PSX table ({columns})")
            continue
        for label, item in PSX_ANNUAL_ITEMS.items():
            if label not in rows:
                run.add_error(f"{security.symbol}: row {label!r} missing from the PSX table")
                continue
            _store_fact(db, run, security, item, year, _num(rows[label][columns.index(str(year))]), doc, extraction)
    return run.rows_inserted - before


# ── 2. Standalone balance sheet from an interim report on PSX ──────────────────────

def _rows(lines: list[str]) -> list[tuple[str | None, float, float, str]]:
    parsed = []
    for line in lines:
        line = line.strip()
        m = ROW.match(line)
        if m:
            parsed.append((m["label"].strip(), _num(m["cur"]), _num(m["prior"]), line))
            continue
        m = SUBTOTAL.match(line)
        if m:
            parsed.append((None, _num(m["cur"]), _num(m["prior"]), line))
    return parsed


def parse_balance_sheet(page_texts: list[str]) -> dict[str, dict]:
    """Returns {line_item: {"value": prior-year-end value, "current": interim value, "raw_line": ...}}.
    Raises TieOutError unless the statement ties out in both columns."""
    text = "\n".join(page_texts)
    if "CONSOLIDATED" in text.upper() or "Audited" not in text:
        raise TieOutError("pages are not the standalone statement with an audited year-end column")
    lines = [ln for page in page_texts for ln in page.splitlines()]
    index = {i: row for i, ln in enumerate(lines) if (row := (_rows([ln]) or [None])[0])}

    def labelled(label: str):
        for i, (lab, cur, prior, raw) in index.items():
            if lab is not None and lab.lower().startswith(label.lower()):
                return i, cur, prior, raw
        raise TieOutError(f"row {label!r} not found")

    def subtotal_after(i: int):
        for j in sorted(k for k in index if k > i):
            if index[j][0] is None:
                return j, index[j][1], index[j][2], index[j][3]
            if index[j][0].isupper():  # reached the next total
                break
        raise TieOutError(f"no unlabelled subtotal after line {i}")

    def header(title: str) -> int:
        return next(i for i, ln in enumerate(lines) if ln.strip() == title)

    total_assets, total_liab, total_el = labelled("TOTAL ASSETS"), labelled("TOTAL LIABILITIES"), labelled("TOTAL EQUITY AND LIABILITIES")
    ca_i, cl_i = labelled("Cash and bank balances")[0], labelled("Provision for taxation")[0]
    equity = subtotal_after(labelled("to fair value")[0])
    current_assets, current_liab = subtotal_after(ca_i), subtotal_after(cl_i)

    for col, name in ((1, "current"), (2, "prior")):
        if abs(total_assets[col] - total_el[col]) > 0.5:
            raise TieOutError(f"{name} column: total assets != total equity and liabilities")
        if abs(total_liab[col] + equity[col] - total_el[col]) > 0.5:
            raise TieOutError(f"{name} column: liabilities + equity != total equity and liabilities")
        for h, sub, label in ((header("CURRENT ASSETS"), current_assets, "current assets"), (header("CURRENT LIABILITIES"), current_liab, "current liabilities")):
            parts = sum(index[k][col] for k in index if h < k < sub[0] and index[k][0] is not None)
            if abs(parts - sub[col]) > 0.5:
                raise TieOutError(f"{name} column: {label} subtotal != sum of its rows")

    singles = {"inventory": "Stock in trade", "trade_debts": "Trade debts", "short_term_investments": "Short term investments",
               "cash_and_bank": "Cash and bank balances"}
    picked = {"total_assets": total_assets, "total_liabilities": total_liab, "total_equity": equity,
              "current_assets": current_assets, "current_liabilities": current_liab,
              **{item: labelled(label) for item, label in singles.items()}}
    return {item: {"value": r[2], "current": r[1], "raw_line": r[3]} for item, r in picked.items()}


def load_interim_comparative_balance_sheet(db: Session, security: Security, run: IngestionRun, report_url: str, year: int) -> int:
    doc = db.execute(select(SourceDocument).where(SourceDocument.url == report_url, SourceDocument.issuer_id == security.issuer_id)).scalar_one_or_none()
    if doc is None:
        run.add_error(f"{security.symbol}: {report_url} is not a known announcement document")
        return 0
    response = httpx.get(report_url, headers=HEADERS, timeout=180)
    response.raise_for_status()
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        texts = [(i, page.extract_text() or "") for i, page in enumerate(pdf.pages, start=1)]
    pages = [(i, t) for i, t in texts if "STATEMENT OF FINANCIAL POSITION" in t.upper() and "CONSOLIDATED" not in t.upper()
             and ("TOTAL ASSETS" in t or "TOTAL LIABILITIES" in t)]
    try:
        figures = parse_balance_sheet([t for _, t in pages])
    except (TieOutError, StopIteration) as exc:
        _quarantine(db, run, f"{security.symbol}:balance_sheet:{year}", {"url": report_url, "pages": [i for i, _ in pages]}, f"tie-out failed: {exc}")
        return 0
    extraction = Extraction(source_document_id=doc.id, method="parsed", raw_json={
        "pdf_sha256": hashlib.sha256(response.content).hexdigest(), "pages": [i for i, _ in pages], "scope": SCOPE,
        "column": f"audited year-end {year} (comparative column of the interim report)", "units": "Rupees '000",
        "lines": {k: v["raw_line"] for k, v in figures.items()}, "checks": "assets = liabilities + equity; subtotals = sum of rows; both columns"})
    db.add(extraction)
    db.flush()
    before = run.rows_inserted
    for item, f in figures.items():
        _store_fact(db, run, security, item, year, f["value"], doc, extraction, published_at=doc.published_at, publication_doc=doc)
    return run.rows_inserted - before


if __name__ == "__main__":
    import sys

    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)
    symbol, report_url = sys.argv[1], sys.argv[2]
    with SessionLocal() as session:
        security = session.execute(select(Security).where(Security.symbol == symbol)).scalar_one()
        with ingestion_run(session, "psx_filing", table="financial_fact", symbol=symbol, report=report_url) as run:
            added_table = load_psx_annual_table(session, security, run, [2024, 2025])
            added_bs = load_interim_comparative_balance_sheet(session, security, run, report_url, 2025)
            session.commit()
        print({"psx_table_facts": added_table, "balance_sheet_facts": added_bs, "run": run.id, "status": run.status, "errors": run.errors})
