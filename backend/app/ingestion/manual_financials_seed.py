"""Manual financial-statement entry for FFC, EFERT and FATIMA, sourced from real analyst
research the user provided (not scraped) — full income statements and balance sheets that
go well beyond what psxdata/the PSX company page expose (Sales/PAT/EPS only).

Per the Milestone 1 plan's own design: v1 financial-statement depth is meant to come from
manual analyst entry, not automated PDF/OCR extraction. This module is that manual-entry
path, made concrete. Every value here traces to a specific source document via
source_document + financial_fact.source_document_id.

Sources:
- FFC 2020-2023: "RAP Workings updated.xlsx" (FFC P&L, FFC SOFP sheets) — an ACCA Research
  and Analysis Project workbook built from FFC's own annual reports.
- EFERT 2023-2025: "EFERT.docx" analysis + "EFERT_Debt_and_Activity_Ratio_Analysis_2024_2025.xlsx"
- FATIMA 2024-2025 (2022-2023 revenue/PAT only): "Fatima Fertilizer.pdf" — cites Fatima's own
  Annual Reports 2024/2025 and PACRA rating/sector reports as its underlying sources.

Reconciliation note: the FFC workbook's 2022 "TOTAL EQUITY AND LIABILITIES" (236,636,398) does
not equal its own "TOTAL ASSETS" (240,122,007) for the same year — a real discrepancy in the
source data, not a transcription bug introduced here. Entered as-is; app/etl/ratio_engine.py's
balance-sheet reconciliation check (see reconcile_balance_sheet) is designed to catch exactly
this kind of thing rather than silently picking one number.
"""

import hashlib
import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import FinancialFact, Issuer, SourceDocument

logger = logging.getLogger(__name__)

# issuer_name -> source label -> {line_item: {year: value}}, values in PKR thousands (except eps, in PKR)
FFC_DATA = {
    "source_label": "RAP Workings updated.xlsx (FFC P&L / FFC SOFP) — ACCA RAP workbook from FFC annual reports",
    "fiscal_year_end_month": 12,
    "facts": {
        "revenue": {2020: 97654753, 2021: 108650890, 2022: 109363817, 2023: 159471951},
        "cost_of_sales": {2020: 66071461, 2021: 69771813, 2022: 69317471, 2023: 95219741},
        "gross_profit": {2020: 31583292, 2021: 38879077, 2022: 40046346, 2023: 64252210},
        "finance_cost": {2020: 1873508, 2021: 2292115, 2022: 4868390, 2023: 5623775},
        "profit_after_tax": {2020: 20819459, 2021: 21896141, 2022: 20049510, 2023: 29673348},
        "total_assets": {2020: 172948758, 2021: 201006765, 2022: 240122007, 2023: 223280688},
        "total_liabilities": {2020: 130413087, 2021: 153492471, 2022: 189287046, 2023: 161428178},
        "total_equity": {2020: 42535671, 2021: 47514294, 2022: 47349352, 2023: 61852510},
        "current_assets": {2020: 111901597, 2021: 126269525, 2022: 155824731, 2023: 130123132},
        "current_liabilities": {2020: 81670893, 2021: 112168992, 2022: 161761667, 2023: 139216504},
        "inventory": {2020: 319989, 2021: 1048397, 2022: 19487801, 2023: 2067922},
        "trade_debts": {2020: 2287336, 2021: 833231, 2022: 371540, 2023: 48503},
        "cash_and_bank": {2020: 1153475, 2021: 1189578, 2022: 1519971, 2023: 858347},
        "short_term_investments": {2020: 81902113, 2021: 95196271, 2022: 100269870, 2023: 94736901},
    },
}

EFERT_DATA = {
    "source_label": "EFERT.docx + EFERT_Debt_and_Activity_Ratio_Analysis_2024_2025.xlsx — user-provided EFERT analysis",
    "fiscal_year_end_month": 12,
    "facts": {
        "revenue": {2023: 161666127, 2024: 186708958, 2025: 193247740},
        "cost_of_sales": {2023: 102243887, 2024: 125531671, 2025: 124898590},
        "profit_after_tax": {2023: 25680000, 2024: 30210000, 2025: 23770000},
        "total_assets": {2023: 147730000, 2024: 162920000, 2025: 199870000},
        "total_liabilities": {2023: 102700000, 2024: 116390000, 2025: 154910000},
        "total_equity": {2023: 45030000, 2024: 46530000, 2025: 44960000},
        "current_assets": {2024: 71060000, 2025: 99030000},
        "current_liabilities": {2024: 95070000, 2025: 125080000},
        "inventory": {2023: 5360000, 2024: 12200000, 2025: 11090000},
        "dividends_paid_total": {2025: 25370000},
    },
}

FATIMA_DATA = {
    "source_label": "Fatima Fertilizer.pdf — user-provided analysis citing Fatima Annual Reports 2024/2025 and PACRA",
    "fiscal_year_end_month": 12,
    "facts": {
        "revenue": {2022: 159700000, 2023: 235400000, 2024: 256920200, 2025: 276176600},
        "gross_profit": {2024: 91817100, 2025: 94424000},
        "operating_profit": {2024: 66973000, 2025: 66079900},
        "profit_after_tax": {2022: 14700000, 2023: 23000000, 2024: 36394800, 2025: 42059000},
        "eps": {2024: 17.33, 2025: 20.03},
        "total_assets": {2024: 316889000, 2025: 360894500},
        "total_equity": {2024: 144169000, 2025: 169864500},
        "current_assets": {2024: 156261100, 2025: 230249500},
        "current_liabilities": {2024: 97064300, 2025: 155018500},
        "operating_cash_flow": {2024: 5296900, 2025: 27933200},
        "dividend_per_share": {2024: 7.00, 2025: 6.00},
    },
}

# dividend_per_share is Rs/share (like eps), distinct from EFERT's dividends_paid_total which is
# an aggregate in PKR '000 — the earlier version of this module conflated the two under one
# "dividend_paid" key with mismatched units; unit is set per-line-item below, not assumed globally.
UNIT_OVERRIDES = {
    "eps": "PKR",
    "dividend_per_share": "PKR",
}


def _get_or_create_source_document(db: Session, issuer: Issuer, label: str) -> SourceDocument:
    content_hash = hashlib.sha256(f"manual-entry::{issuer.name}::{label}".encode()).hexdigest()
    existing = db.execute(
        select(SourceDocument).where(SourceDocument.content_hash == content_hash)
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    document = SourceDocument(
        issuer_id=issuer.id,
        url=None,
        content_hash=content_hash,
        document_type="analyst_report_manual_entry",
        source_tier="primary",
    )
    db.add(document)
    db.flush()
    return document


def _fiscal_period(year: int, fiscal_month: int) -> tuple[date, date]:
    """Return (period_start, period_end) for a fiscal year that ends in fiscal_month of `year`.

    December FYE: Jan 1 – Dec 31 (calendar year == fiscal year label).
    Non-December: period ends on the last day of fiscal_month in `year`, starts the
    following month one year prior (e.g. June 30 FYE → Jul 1 prior year – Jun 30 this year).
    """
    if fiscal_month == 12:
        return date(year, 1, 1), date(year, 12, 31)
    period_end = (date(year, fiscal_month, 28) + timedelta(days=10)).replace(day=1) - timedelta(days=1)
    period_start = date(year - 1, fiscal_month + 1, 1)
    return period_start, period_end


def seed_issuer_financials(db: Session, issuer_name: str, data: dict) -> dict[str, int]:
    issuer = db.execute(select(Issuer).where(Issuer.name == issuer_name)).scalar_one_or_none()
    if issuer is None:
        logger.warning("Issuer not found: %s", issuer_name)
        return {"inserted": 0, "skipped": 0}

    source_document = _get_or_create_source_document(db, issuer, data["source_label"])
    fiscal_month = data["fiscal_year_end_month"]

    inserted = skipped = superseded = 0
    for line_item, values_by_year in data["facts"].items():
        for year, value in values_by_year.items():
            period_start, period_end = _fiscal_period(year, fiscal_month)
            existing = db.execute(
                select(FinancialFact).where(
                    FinancialFact.issuer_id == issuer.id,
                    FinancialFact.line_item == line_item,
                    FinancialFact.period_end == period_end,
                    FinancialFact.period_type == "annual",
                    FinancialFact.scope == "consolidated",
                    FinancialFact.superseded_by_id.is_(None),
                )
            ).scalar_one_or_none()

            if existing is not None:
                if abs(float(existing.value) - float(value)) < 0.01:
                    skipped += 1
                    continue
                # Manual, source-traceable entry wins over an earlier scrape (e.g. psxdata's
                # Capital-Stake-standardized figures, which Capital Stake itself says "may
                # differ from issuer's annual report") — but the old value is kept, not
                # deleted, per the evidence model's restatement/versioning design.
                new_fact = FinancialFact(
                    issuer_id=issuer.id,
                    line_item=line_item,
                    period_start=period_start,
                    period_end=period_end,
                    period_type="annual",
                    scope="consolidated",
                    unit=UNIT_OVERRIDES.get(line_item, "PKR_thousand"),
                    value=value,
                    source_document_id=source_document.id,
                    is_restated=True,
                )
                db.add(new_fact)
                db.flush()
                existing.superseded_by_id = new_fact.id
                superseded += 1
                continue

            db.add(
                FinancialFact(
                    issuer_id=issuer.id,
                    line_item=line_item,
                    period_start=period_start,
                    period_end=period_end,
                    period_type="annual",
                    scope="consolidated",
                    unit=UNIT_OVERRIDES.get(line_item, "PKR_thousand"),
                    value=value,
                    source_document_id=source_document.id,
                )
            )
            inserted += 1

    db.commit()
    return {"inserted": inserted, "skipped": skipped, "superseded": superseded}


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        for issuer_name, data in [
            ("Fauji Fertilizer Company Limited", FFC_DATA),
            ("Engro Fertilizers Limited", EFERT_DATA),
            ("Fatima Fertilizer Company Limited", FATIMA_DATA),
        ]:
            stats = seed_issuer_financials(session, issuer_name, data)
            print(f"{issuer_name}: {stats}")
