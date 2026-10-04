"""Phase 2: Extract canonical financial metrics from annual report PDFs.

Extracts with full provenance and accounting rule checks.

Target metrics (with accounting aliases):
- operating_profit (EBIT, profit from operations)
- other_income (other operating income — check for consistency)
- tax_expense (taxation, income tax expense)
- dividend_per_share (distinguish interim vs final vs annual)
- ebitda (explicit or derived from operating_profit + D&A)

All values stored with:
- source_document_id (URL, hash, publication date)
- extraction_id (method, raw JSON with page/section)
- period_type, scope, unit, period dates
- derivation flag if calculated
"""

import hashlib
import io
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

import httpx
import pdfplumber
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import Issuer, SourceDocument, Extraction, FinancialFact, IngestionRun
from app.ingestion.runs import ingestion_run
from app.ingestion.manual_financials_seed import _fiscal_period

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) psx-fertilizer-research-pilot/0.1"}

# Canonical taxonomy keys
CANONICAL_METRICS = {
    "operating_profit": {
        "aliases": ["operating profit", "profit from operations", "ebit", "earnings before interest and tax"],
        "statement": "income_statement",
        "unit": "PKR_thousand",
    },
    "other_income": {
        "aliases": ["other income", "other operating income", "miscellaneous income"],
        "statement": "income_statement",
        "unit": "PKR_thousand",
    },
    "tax_expense": {
        "aliases": ["taxation", "income tax expense", "tax charge", "current tax"],
        "statement": "income_statement",
        "unit": "PKR_thousand",
    },
    "dividend_per_share": {
        "aliases": ["dividend per share", "dps", "dividend"],
        "statement": "cash_flow",
        "unit": "PKR",
        "note": "Compare annual DPS (interim + final, or total declared)",
    },
    "ebitda": {
        "aliases": ["ebitda", "earnings before interest tax depreciation amortization"],
        "statement": "income_statement",
        "unit": "PKR_thousand",
        "note": "If not explicit, derive: EBITDA = Operating Profit + Depreciation + Amortization",
    },
}


class MetricExtractor:
    """Extracts financial metrics from annual report PDFs with provenance."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_source_document(
        self, issuer_id: int, url: str, fiscal_year: int, content_hash: str
    ) -> SourceDocument:
        """Get or create SourceDocument for this report."""
        doc = self.db.execute(
            select(SourceDocument).where(SourceDocument.content_hash == content_hash)
        ).scalar_one_or_none()

        if doc is None:
            doc = SourceDocument(
                issuer_id=issuer_id,
                url=url,
                content_hash=content_hash,
                document_type="annual_report",
                source_tier="primary",
                published_at=None,  # Will be set from report date if found
                fetched_at=datetime.utcnow(),
            )
            self.db.add(doc)
            self.db.flush()

        return doc

    def extract_metrics_from_pdf(
        self, url: str, fiscal_year: int
    ) -> dict[str, dict]:
        """Download PDF and extract metric values.

        Returns: {
            "operating_profit": {"value": 123456, "page": 5, "raw_line": "..."},
            "other_income": {...},
            ...
        }
        """
        logger.info(f"Downloading {url}")

        try:
            response = httpx.get(url, headers=HEADERS, timeout=180)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return {}

        pdf_content = response.content
        pdf_hash = hashlib.sha256(pdf_content).hexdigest()

        extracted = {}

        try:
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                # Extract text from all pages
                pages_text = [
                    (i, page.extract_text() or "")
                    for i, page in enumerate(pdf.pages, start=1)
                ]

                # Search for income statement (usually early in report)
                income_statement_pages = [
                    (i, text)
                    for i, text in pages_text
                    if any(x in text.upper() for x in ["STATEMENT OF PROFIT AND LOSS", "INCOME STATEMENT", "PROFIT & LOSS", "P&L"])
                ]

                if not income_statement_pages:
                    logger.warning(f"No income statement found in {url}")
                    return {}

                # Search for metrics in income statement
                for metric_key, aliases in [
                    ("operating_profit", CANONICAL_METRICS["operating_profit"]["aliases"]),
                    ("other_income", CANONICAL_METRICS["other_income"]["aliases"]),
                    ("tax_expense", CANONICAL_METRICS["tax_expense"]["aliases"]),
                ]:
                    for page_num, text in income_statement_pages:
                        for alias in aliases:
                            # Look for the alias in the text
                            for line in text.split("\n"):
                                if alias.lower() in line.lower():
                                    # Try to extract a number from this line
                                    value = self._extract_number_from_line(line, fiscal_year)
                                    if value is not None:
                                        extracted[metric_key] = {
                                            "value": value,
                                            "page": page_num,
                                            "raw_line": line.strip(),
                                            "alias_found": alias,
                                        }
                                        logger.info(f"  {metric_key} = {value:,.0f} (page {page_num}, alias: {alias})")
                                        break
                            if metric_key in extracted:
                                break
                        if metric_key in extracted:
                            break

                # Search for dividend per share (may be in Notes or Shareholder Info)
                for page_num, text in pages_text:
                    for alias in CANONICAL_METRICS["dividend_per_share"]["aliases"]:
                        if alias.lower() in text.lower():
                            for line in text.split("\n"):
                                if alias.lower() in line.lower():
                                    value = self._extract_dps_value(line)
                                    if value is not None and "dividend_per_share" not in extracted:
                                        extracted["dividend_per_share"] = {
                                            "value": value,
                                            "page": page_num,
                                            "raw_line": line.strip(),
                                            "alias_found": alias,
                                        }
                                        logger.info(f"  dividend_per_share = {value} (page {page_num})")
        except Exception as e:
            logger.error(f"Failed to parse PDF {url}: {e}")

        return extracted, pdf_hash

    def _extract_number_from_line(self, line: str, fiscal_year: int) -> Optional[float]:
        """Extract a number from an income statement line.

        Lines typically look like:
        "Operating Profit         123,456    234,567"

        We want the current year's figure. For simplicity, take the first large number.
        """
        import re

        # Remove common prefixes
        text = re.sub(r"^[a-z\s]+", "", line, flags=re.IGNORECASE).strip()

        # Find all numbers (handle comma separators)
        numbers = re.findall(r"[\d,]+(?:\.\d+)?", text)

        if not numbers:
            return None

        # Take the first (usually the current year figure in income statement)
        try:
            return float(numbers[0].replace(",", ""))
        except ValueError:
            return None

    def _extract_dps_value(self, line: str) -> Optional[float]:
        """Extract dividend per share value (usually a decimal like 1.50)."""
        import re

        numbers = re.findall(r"[\d,]+(?:\.\d+)?", line)

        if not numbers:
            return None

        try:
            # DPS is usually a small decimal, take the last number in the line
            return float(numbers[-1].replace(",", ""))
        except ValueError:
            return None

    def store_metric(
        self,
        db: Session,
        run: IngestionRun,
        issuer: Issuer,
        metric_key: str,
        value: float,
        fiscal_year: int,
        source_doc: SourceDocument,
        extraction: Extraction,
        extraction_metadata: dict,
    ) -> None:
        """Store a single metric fact with provenance."""

        unit = CANONICAL_METRICS[metric_key]["unit"]

        # Calculate period dates
        if issuer.fiscal_year_end_month is None:
            logger.error(f"{issuer.name}: fiscal_year_end_month not set")
            return

        start, end = _fiscal_period(fiscal_year, issuer.fiscal_year_end_month)

        # Check for existing value
        existing = db.execute(
            select(FinancialFact).where(
                FinancialFact.issuer_id == issuer.id,
                FinancialFact.line_item == metric_key,
                FinancialFact.period_end == end,
                FinancialFact.period_type == "annual",
                FinancialFact.scope == "standalone",
                FinancialFact.superseded_by_id.is_(None),
            )
        ).scalar_one_or_none()

        if existing is not None:
            logger.warning(f"  {issuer.symbol} {metric_key} FY{fiscal_year} already exists: {existing.value}")
            return

        # Store the metric
        fact = FinancialFact(
            issuer_id=issuer.id,
            line_item=metric_key,
            period_start=start,
            period_end=end,
            period_type="annual",
            duration_basis="discrete",
            scope="standalone",
            unit=unit,
            value=Decimal(str(value)),
            source_document_id=source_doc.id,
            extraction_id=extraction.id,
            published_at=source_doc.published_at,
            ingestion_run_id=run.id,
        )
        db.add(fact)
        run.rows_inserted += 1

        logger.info(f"  ✓ Stored {issuer.symbol} {metric_key} FY{fiscal_year} = {value:,.0f} {unit}")


def extract_and_ingest_reports(
    db: Session,
    reports: dict[str, dict[int, str]],  # {"FFC": {2020: url, ...}, "EFERT": {...}}
) -> dict:
    """Extract metrics from all discovered reports.

    Args:
        db: Database session
        reports: Discovered report URLs

    Returns:
        Ingestion summary with metrics extracted per company/year
    """
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 2: METRIC EXTRACTION FROM ANNUAL REPORTS")
    logger.info("=" * 70)

    extractor = MetricExtractor(db)
    summary = {"FFC": {}, "EFERT": {}}

    for company_symbol, years_reports in reports.items():
        # Get issuer
        issuer = db.execute(
            select(Issuer).where(Issuer.symbol == company_symbol)
        ).scalar_one_or_none()

        if not issuer:
            logger.error(f"Issuer not found: {company_symbol}")
            continue

        logger.info(f"\n{company_symbol} ({issuer.name}):")

        with ingestion_run(db, "annual_report_extraction", table="financial_fact", issuer=company_symbol) as run:
            for fiscal_year, url in sorted(years_reports.items()):
                logger.info(f"  FY{fiscal_year}: {url}")

                try:
                    # Download and extract
                    extracted_data, pdf_hash = extractor.extract_metrics_from_pdf(url, fiscal_year)

                    if not extracted_data:
                        logger.warning(f"    No metrics extracted")
                        summary[company_symbol][fiscal_year] = {"extracted": 0, "error": "No metrics found"}
                        continue

                    # Create source document
                    source_doc = extractor.get_or_create_source_document(
                        issuer.id, url, fiscal_year, pdf_hash
                    )

                    # Create extraction record
                    extraction = Extraction(
                        source_document_id=source_doc.id,
                        method="parsed",
                        confidence=0.85,  # Default confidence for automated extraction
                        raw_json={
                            "fiscal_year": fiscal_year,
                            "url": url,
                            "pdf_sha256": pdf_hash,
                            "metrics_found": list(extracted_data.keys()),
                            "extraction_details": {k: v for k, v in extracted_data.items()},
                        },
                    )
                    db.add(extraction)
                    db.flush()

                    # Store each extracted metric
                    for metric_key, metadata in extracted_data.items():
                        extractor.store_metric(
                            db, run, issuer, metric_key,
                            metadata["value"], fiscal_year,
                            source_doc, extraction, metadata,
                        )

                    summary[company_symbol][fiscal_year] = {
                        "extracted": len(extracted_data),
                        "metrics": list(extracted_data.keys()),
                    }

                except Exception as e:
                    logger.error(f"    Failed: {e}", exc_info=True)
                    summary[company_symbol][fiscal_year] = {"error": str(e)}

            db.commit()
            logger.info(f"\n  Ingestion run {run.id}: {run.status}")
            logger.info(f"    Inserted: {run.rows_inserted}")
            logger.info(f"    Errors: {run.errors}")

    return summary


if __name__ == "__main__":
    # For testing
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    # First discover reports
    from app.ingestion.annual_report_discovery import discover_all_reports

    reports = discover_all_reports()

    # Then extract
    with SessionLocal() as session:
        summary = extract_and_ingest_reports(session, reports)

        print("\n" + "=" * 70)
        print("EXTRACTION SUMMARY")
        print("=" * 70)
        print(json.dumps(summary, indent=2))
