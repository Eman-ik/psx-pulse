"""
R3: Financial Statement Parser & Normalizer
Extract structured financial data from FFC PDFs

Parses:
- Income Statement (Revenue, COGS, Gross Profit, Operating Profit, PAT, EPS)
- Balance Sheet (Assets, Liabilities, Equity)
- Cash Flow (CFO, CapEx, FCF, Dividends)

Outputs:
- statement_line_items table with source lineage
- Confidence scores for each extracted value
"""

import re
import logging
from datetime import date
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session

from models import (
    Company, Document, DocumentSource,
    FinancialStatement, StatementLineItem,
    StatementType, AuditStatus, DocumentExtractionStatus
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Income Statement Line Codes (Standard)
# ============================================================================

INCOME_STATEMENT_CODES = {
    "REV": ("Revenue", 100),
    "SALES_RETURN": ("Sales Return & Discounts", 105),
    "NET_SALES": ("Net Sales", 110),
    "COGS": ("Cost of Goods Sold", 200),
    "GROSS_PROFIT": ("Gross Profit", 300),
    "DISTRIBUTION": ("Distribution Costs", 310),
    "ADMIN": ("Administrative Expenses", 320),
    "OTHER_OPERATING": ("Other Operating Expenses", 330),
    "OPERATING_PROFIT": ("Operating Profit (EBIT)", 400),
    "FINANCE_COST": ("Finance Cost", 500),
    "OTHER_INCOME": ("Other Income", 600),
    "EBT": ("Profit Before Tax", 700),
    "TAX": ("Income Tax", 800),
    "PAT": ("Profit After Tax", 900),
    "EPS": ("Earnings Per Share", 1000),
    "DILUTED_EPS": ("Diluted EPS", 1010),
}

# ============================================================================
# Balance Sheet Line Codes (Standard)
# ============================================================================

BALANCE_SHEET_CODES = {
    # Assets
    "CASH": ("Cash & Cash Equivalents", 1100),
    "SHORT_TERM_INVESTMENT": ("Short-term Investments", 1105),
    "RECEIVABLES": ("Trade Receivables", 1110),
    "INVENTORY": ("Inventory", 1120),
    "PREPAID": ("Prepaid Expenses", 1130),
    "OTHER_CA": ("Other Current Assets", 1140),
    "CURRENT_ASSETS": ("Current Assets", 1150),

    "PPE": ("Property, Plant & Equipment", 1200),
    "GOODWILL": ("Goodwill", 1210),
    "INTANGIBLES": ("Intangible Assets", 1220),
    "LT_INVESTMENT": ("Long-term Investments", 1230),
    "DEFERRED_TAX_ASSET": ("Deferred Tax Asset", 1240),
    "OTHER_NCA": ("Other Non-Current Assets", 1250),
    "NON_CURRENT_ASSETS": ("Non-Current Assets", 1260),

    "TOTAL_ASSETS": ("Total Assets", 1300),

    # Liabilities
    "PAYABLES": ("Trade Payables", 1400),
    "SHORT_TERM_DEBT": ("Short-term Borrowings", 1410),
    "ACCRUED_EXPENSE": ("Accrued Expenses", 1420),
    "CURRENT_TAX": ("Current Tax Liability", 1430),
    "OTHER_CL": ("Other Current Liabilities", 1440),
    "CURRENT_LIABILITIES": ("Current Liabilities", 1450),

    "LONG_TERM_DEBT": ("Long-term Borrowings", 1500),
    "DEFERRED_TAX_LIABILITY": ("Deferred Tax Liability", 1510),
    "OTHER_NCL": ("Other Non-Current Liabilities", 1520),
    "NON_CURRENT_LIABILITIES": ("Non-Current Liabilities", 1530),

    "TOTAL_LIABILITIES": ("Total Liabilities", 1600),

    # Equity
    "SHARE_CAPITAL": ("Share Capital", 1700),
    "RESERVES": ("Reserves", 1710),
    "RETAINED_EARNINGS": ("Retained Earnings", 1720),
    "TOTAL_EQUITY": ("Total Shareholders' Equity", 1800),

    "TOTAL_LIABILITIES_EQUITY": ("Total Liabilities & Equity", 1900),
}

# ============================================================================
# Cash Flow Line Codes (Standard)
# ============================================================================

CASH_FLOW_CODES = {
    "PAT": ("Profit After Tax", 2100),
    "DEPRECIATION": ("Depreciation & Amortization", 2110),
    "PROVISIONS": ("Provisions", 2120),
    "WORKING_CAPITAL_CHANGE": ("Changes in Working Capital", 2130),
    "OTHER_OPERATING": ("Other Operating Activities", 2140),
    "CFO": ("Cash Flow from Operating Activities", 2200),

    "CAPEX": ("Capital Expenditure", 2300),
    "INVESTMENT_PROCEEDS": ("Proceeds from Investment Sale", 2310),
    "OTHER_INVESTING": ("Other Investing Activities", 2320),
    "CFI": ("Cash Flow from Investing Activities", 2400),

    "DEBT_PROCEEDS": ("Debt Proceeds", 2500),
    "DEBT_REPAYMENT": ("Debt Repayment", 2510),
    "DIVIDEND": ("Dividend Paid", 2520),
    "OTHER_FINANCING": ("Other Financing Activities", 2530),
    "CFF": ("Cash Flow from Financing Activities", 2600),

    "NET_CHANGE_CASH": ("Net Change in Cash", 2700),
    "BEGINNING_CASH": ("Beginning Cash Balance", 2710),
    "ENDING_CASH": ("Ending Cash Balance", 2800),
}

# ============================================================================
# FFC-Specific Parser Templates
# ============================================================================

@dataclass
class ExtractedLineItem:
    """Extracted financial line item"""
    line_code: str
    line_name: str
    value: Optional[int]  # in base units (rupees, not thousands)
    line_order: int
    source_page: Optional[int] = None
    source_text: Optional[str] = None
    extraction_method: str = "manual"
    confidence: float = 0.9

class FFCIncomeStatementParser:
    """Parse FFC income statement from annual report"""

    @staticmethod
    def parse(extracted_text: str, source_page: int) -> List[ExtractedLineItem]:
        """
        Extract income statement from PDF text

        FFC Annual Report format:
        --
        Revenue                     74,232,112  (in thousands)
        Cost of sales              (51,321,481)
        Gross profit                22,910,631
        Distribution                (3,241,212)
        Administrative              (2,831,241)
        Operating profit            16,838,178
        Finance cost                (3,221,122)
        Other income                 1,821,123
        Profit before tax           15,438,179
        Tax expense                 (3,695,843)
        Profit after tax            11,742,336
        Earnings per share               8.34
        --
        """

        items = []

        # Pattern: "Label Amount"
        # Handles: "Revenue 74,232,112" or "Cost of sales (51,321,481)"
        patterns = [
            (r"Revenue\s+([0-9,]+)\s*\(?([0-9,]+)?\)?", "REV"),
            (r"Cost of.*?sales?\s+\(?([0-9,]+)\)?", "COGS"),
            (r"Gross profit\s+([0-9,]+)", "GROSS_PROFIT"),
            (r"Distribution.*?\s+\(?([0-9,]+)\)?", "DISTRIBUTION"),
            (r"Administrative.*?\s+\(?([0-9,]+)\)?", "ADMIN"),
            (r"Operating profit.*?\s+([0-9,]+)", "OPERATING_PROFIT"),
            (r"Finance cost.*?\s+\(?([0-9,]+)\)?", "FINANCE_COST"),
            (r"Other income.*?\s+([0-9,]+)", "OTHER_INCOME"),
            (r"Profit before tax.*?\s+([0-9,]+)", "EBT"),
            (r"(?:Tax|Income tax).*?\s+\(?([0-9,]+)\)?", "TAX"),
            (r"Profit after tax.*?\s+([0-9,]+)", "PAT"),
            (r"(?:Earnings|EPS).*?per share.*?\s+([0-9.]+)", "EPS"),
        ]

        line_order = 100
        for pattern, code in patterns:
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                try:
                    # Extract number, remove commas
                    value_str = match.group(1).replace(",", "")

                    # Check if parentheses (negative)
                    is_negative = "(" in match.group(0)

                    # Convert to number
                    if "." in value_str:
                        value = float(value_str)
                    else:
                        value = int(value_str)

                    # Apply negative if needed
                    if is_negative:
                        value = -value

                    # Convert to base units (if in thousands, multiply by 1000)
                    if code in ["REV", "COGS", "GROSS_PROFIT", "OPERATING_PROFIT", "PAT", "EBT", "TAX"]:
                        if value > 10000:  # Likely in thousands
                            value = int(value * 1000)

                    line_name = INCOME_STATEMENT_CODES[code][0]

                    items.append(ExtractedLineItem(
                        line_code=code,
                        line_name=line_name,
                        value=int(value),
                        line_order=line_order,
                        source_page=source_page,
                        source_text=match.group(0),
                        confidence=0.95
                    ))
                    line_order += 10

                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse {code}: {e}")

        return items

class FFCBalanceSheetParser:
    """Parse FFC balance sheet"""

    @staticmethod
    def parse(extracted_text: str, source_page: int) -> List[ExtractedLineItem]:
        """Extract balance sheet from PDF text"""

        items = []

        patterns = [
            # Current Assets
            (r"Cash.*?and.*?equivalents?\s+([0-9,]+)", "CASH"),
            (r"Short.?term.*?investments?\s+([0-9,]+)", "SHORT_TERM_INVESTMENT"),
            (r"Trade receivables?\s+([0-9,]+)", "RECEIVABLES"),
            (r"Inventory\s+([0-9,]+)", "INVENTORY"),
            (r"Prepaid.*?expenses?\s+([0-9,]+)", "PREPAID"),
            (r"Current assets?\s+([0-9,]+)", "CURRENT_ASSETS"),

            # Non-Current Assets
            (r"Property.*?plant.*?equipment\s+([0-9,]+)", "PPE"),
            (r"Goodwill\s+([0-9,]+)", "GOODWILL"),
            (r"Intangible assets?\s+([0-9,]+)", "INTANGIBLES"),
            (r"Long.?term.*?investments?\s+([0-9,]+)", "LT_INVESTMENT"),
            (r"Non.?current assets?\s+([0-9,]+)", "NON_CURRENT_ASSETS"),

            (r"Total assets?\s+([0-9,]+)", "TOTAL_ASSETS"),

            # Current Liabilities
            (r"Trade payables?\s+([0-9,]+)", "PAYABLES"),
            (r"Short.?term.*?(?:borrowings?|debt)\s+([0-9,]+)", "SHORT_TERM_DEBT"),
            (r"Accrued.*?expenses?\s+([0-9,]+)", "ACCRUED_EXPENSE"),
            (r"Current.*?(?:tax|liabilities?)\s+([0-9,]+)", "CURRENT_LIABILITIES"),

            # Non-Current Liabilities
            (r"Long.?term.*?(?:borrowings?|debt)\s+([0-9,]+)", "LONG_TERM_DEBT"),
            (r"Non.?current.*?liabilities?\s+([0-9,]+)", "NON_CURRENT_LIABILITIES"),

            (r"Total.*?liabilities?\s+([0-9,]+)", "TOTAL_LIABILITIES"),

            # Equity
            (r"Share capital\s+([0-9,]+)", "SHARE_CAPITAL"),
            (r"Reserves?\s+([0-9,]+)", "RESERVES"),
            (r"Retained earnings?\s+([0-9,]+)", "RETAINED_EARNINGS"),
            (r"Total.*?(?:equity|shareholders)\s+([0-9,]+)", "TOTAL_EQUITY"),
        ]

        line_order = 1100
        for pattern, code in patterns:
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                try:
                    value_str = match.group(1).replace(",", "")
                    value = int(value_str)

                    # Convert to base units if in thousands
                    if value > 10000:
                        value = int(value * 1000)

                    line_name = BALANCE_SHEET_CODES[code][0]

                    items.append(ExtractedLineItem(
                        line_code=code,
                        line_name=line_name,
                        value=value,
                        line_order=line_order,
                        source_page=source_page,
                        source_text=match.group(0),
                        confidence=0.90
                    ))
                    line_order += 10

                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse {code}: {e}")

        return items

class FFCCashFlowParser:
    """Parse FFC cash flow statement"""

    @staticmethod
    def parse(extracted_text: str, source_page: int) -> List[ExtractedLineItem]:
        """Extract cash flow from PDF text"""

        items = []

        patterns = [
            # Operating Activities
            (r"Profit after tax\s+([0-9,]+)", "PAT"),
            (r"Depreciation.*?amortization\s+([0-9,]+)", "DEPRECIATION"),
            (r"Provisions?\s+([0-9,]+)", "PROVISIONS"),
            (r"(?:Changes?|Change).*?working capital\s+\(?([0-9,]+)\)?", "WORKING_CAPITAL_CHANGE"),
            (r"Cash from operating activities?\s+([0-9,]+)", "CFO"),

            # Investing Activities
            (r"Capital expenditure\s+\(?([0-9,]+)\)?", "CAPEX"),
            (r"Proceeds from.*?(?:sale|disposal)\s+([0-9,]+)", "INVESTMENT_PROCEEDS"),
            (r"Cash from investing activities?\s+\(?([0-9,]+)\)?", "CFI"),

            # Financing Activities
            (r"Debt proceeds?\s+([0-9,]+)", "DEBT_PROCEEDS"),
            (r"Debt repayment\s+\(?([0-9,]+)\)?", "DEBT_REPAYMENT"),
            (r"Dividend.*?paid\s+\(?([0-9,]+)\)?", "DIVIDEND"),
            (r"Cash from financing activities?\s+\(?([0-9,]+)\)?", "CFF"),

            # Net Change
            (r"Net change.*?cash\s+([0-9,]+)", "NET_CHANGE_CASH"),
            (r"(?:Opening|Beginning).*?cash\s+([0-9,]+)", "BEGINNING_CASH"),
            (r"(?:Closing|Ending).*?cash\s+([0-9,]+)", "ENDING_CASH"),
        ]

        line_order = 2100
        for pattern, code in patterns:
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                try:
                    value_str = match.group(1).replace(",", "")

                    # Handle negative values in parentheses
                    is_negative = "(" in match.group(0)

                    value = int(value_str)
                    if is_negative:
                        value = -value

                    # Convert to base units if in thousands
                    if abs(value) > 10000:
                        value = int(value * 1000)

                    line_name = CASH_FLOW_CODES[code][0]

                    items.append(ExtractedLineItem(
                        line_code=code,
                        line_name=line_name,
                        value=value,
                        line_order=line_order,
                        source_page=source_page,
                        source_text=match.group(0),
                        confidence=0.90
                    ))
                    line_order += 10

                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse {code}: {e}")

        return items

# ============================================================================
# Main Parser Orchestrator
# ============================================================================

class FinancialStatementParser:
    """Main parser - orchestrates all statement types"""

    def __init__(self, session: Session):
        self.session = session
        self.income_parser = FFCIncomeStatementParser()
        self.balance_sheet_parser = FFCBalanceSheetParser()
        self.cash_flow_parser = FFCCashFlowParser()

    def parse_document(self, document_id: int) -> Tuple[bool, str]:
        """
        Parse a single document and extract all financial statements

        Returns: (success: bool, message: str)
        """

        # Get document
        doc = self.session.query(Document).filter_by(document_id=document_id).first()
        if not doc:
            return False, f"Document {document_id} not found"

        logger.info(f"\nParsing Document {document_id}: {doc.document_type.value} {doc.fiscal_year} Q{doc.fiscal_quarter or 'A'}")

        # Get company
        company = self.session.query(Company).filter_by(company_id=doc.company_id).first()

        # Use extracted text (or would read from PDF in production)
        extracted_text = doc.extracted_text or ""

        if not extracted_text:
            return False, f"No extracted text for document {document_id}"

        statements_created = 0

        # Parse each statement type
        for statement_type in [StatementType.INCOME, StatementType.BALANCE_SHEET, StatementType.CASH_FLOW]:
            # Parse
            if statement_type == StatementType.INCOME:
                line_items = self.income_parser.parse(extracted_text, source_page=1)
            elif statement_type == StatementType.BALANCE_SHEET:
                line_items = self.balance_sheet_parser.parse(extracted_text, source_page=1)
            else:  # CASH_FLOW
                line_items = self.cash_flow_parser.parse(extracted_text, source_page=1)

            if not line_items:
                logger.info(f"  [SKIP] No {statement_type.value} items found")
                continue

            # Create statement record
            statement = FinancialStatement(
                company_id=doc.company_id,
                statement_type=statement_type,
                fiscal_year=doc.fiscal_year,
                fiscal_quarter=doc.fiscal_quarter,
                reporting_period_end=doc.reporting_period_end,
                currency="PKR",
                source_document_id=document_id,
                source_page=1,
                is_consolidated=True,
                audit_status=AuditStatus.AUDITED,
                extracted_at=__import__('datetime').datetime.utcnow()
            )

            self.session.add(statement)
            self.session.flush()  # Get statement_id

            # Create line items
            for item in line_items:
                line_item = StatementLineItem(
                    statement_id=statement.statement_id,
                    line_name=item.line_name,
                    line_code=item.line_code,
                    value=item.value,
                    value_in_thousands=item.value // 1000 if item.value else None,
                    line_order=item.line_order,
                    extraction_method=item.extraction_method,
                    confidence=float(item.confidence)
                )

                self.session.add(line_item)

            logger.info(f"  [OK] {statement_type.value}: {len(line_items)} line items extracted")
            statements_created += 1

        self.session.commit()

        return True, f"Parsed {statements_created} statements with {sum(len(line_items) for line_items in [])} line items"

    def parse_company_documents(self, company_id: int) -> dict:
        """Parse all documents for a company"""

        logger.info("\n" + "="*60)
        logger.info("R3: Financial Statement Parser")
        logger.info("="*60 + "\n")

        # Get all documents for company
        docs = self.session.query(Document).filter_by(
            company_id=company_id,
            extraction_status=DocumentExtractionStatus.SUCCESS
        ).all()

        if not docs:
            return {
                "status": "failed",
                "reason": "No documents with extracted text found. Run R2 first."
            }

        stats = {
            "total_documents": len(docs),
            "successfully_parsed": 0,
            "failed": 0,
            "statements_created": 0,
            "line_items_created": 0
        }

        for doc in docs:
            success, message = self.parse_document(doc.document_id)
            if success:
                stats["successfully_parsed"] += 1
            else:
                logger.error(f"  [FAILED] {message}")
                stats["failed"] += 1

        logger.info("\n" + "="*60)
        logger.info("R3: Parsing Complete")
        logger.info("="*60)
        logger.info(f"Total Documents:    {stats['total_documents']}")
        logger.info(f"Successfully Parsed: {stats['successfully_parsed']}")
        logger.info(f"Failed:             {stats['failed']}")
        logger.info("="*60 + "\n")

        return stats

def main():
    """Run parser"""
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/research_studio"
    )

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        from models import Company

        # Get FFC
        ffc = session.query(Company).filter_by(ticker="FFC").first()
        if not ffc:
            print("[ERROR] FFC not found. Run R1 initialization first.")
            return

        parser = FinancialStatementParser(session)
        result = parser.parse_company_documents(ffc.company_id)
        print(f"\nResult: {result}")

    finally:
        session.close()

if __name__ == "__main__":
    main()
