"""Step 13: Filing Extractor — Extract structured data from PSX filings.

Parses financial filings (PDF, HTML) to extract:
- Balance sheet items (assets, liabilities, equity)
- Income statement items (revenue, expenses, profit)
- Cash flow items (operating, investing, financing)
- Notes to financial statements
- Audit reports and qualifications
- Management discussion & analysis (MD&A)

Input: Filing document (URL or file path)
Output: ExtractedFiling (structured financial data)
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class FilingType(str, Enum):
    """Types of financial filings."""

    ANNUAL_REPORT = "Annual Report"
    QUARTERLY_REPORT = "Quarterly Report"
    PROSPECTUS = "Prospectus"
    ANNOUNCEMENT = "Announcement"
    UNKNOWN = "Unknown"


@dataclass
class BalanceSheetItem:
    """Balance sheet line item."""

    item_name: str
    current_period: Optional[float]
    prior_period: Optional[float]
    change_pct: Optional[float]
    currency: str = "PKR"


@dataclass
class IncomeStatementItem:
    """Income statement line item."""

    item_name: str
    current_period: Optional[float]
    prior_period: Optional[float]
    ytd_amount: Optional[float]
    change_pct: Optional[float]
    currency: str = "PKR"


@dataclass
class CashFlowItem:
    """Cash flow statement line item."""

    item_name: str
    operating: Optional[float]
    investing: Optional[float]
    financing: Optional[float]
    total: Optional[float]
    currency: str = "PKR"


@dataclass
class ExtractedFiling:
    """Complete extracted filing data."""

    filing_type: FilingType
    company_name: str
    filing_date: Optional[str]
    period_end_date: Optional[str]
    period_type: str  # "Q1", "Q2", "H1", "FY"

    # Financial statements
    balance_sheet: List[BalanceSheetItem]
    income_statement: List[IncomeStatementItem]
    cash_flow: List[CashFlowItem]

    # Key metrics
    total_assets: Optional[float]
    total_liabilities: Optional[float]
    total_equity: Optional[float]
    net_revenue: Optional[float]
    net_profit: Optional[float]
    earnings_per_share: Optional[float]

    # Audit & qualifications
    audit_opinion: str  # "Unqualified", "Qualified", "Adverse", "Disclaimer"
    audit_notes: List[str]
    md_and_a: str  # Management discussion & analysis excerpt

    # Data quality
    confidence_score: float  # 0-100% confidence in extraction
    missing_sections: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "filing_type": self.filing_type.value,
            "company_name": self.company_name,
            "filing_date": self.filing_date,
            "period_end_date": self.period_end_date,
            "period_type": self.period_type,
            "total_assets": self.total_assets,
            "total_liabilities": self.total_liabilities,
            "total_equity": self.total_equity,
            "net_revenue": self.net_revenue,
            "net_profit": self.net_profit,
            "earnings_per_share": self.earnings_per_share,
            "audit_opinion": self.audit_opinion,
            "confidence_score": self.confidence_score,
            "balance_sheet_items": len(self.balance_sheet),
            "income_statement_items": len(self.income_statement),
            "missing_sections": self.missing_sections,
        }


class FilingExtractor:
    """Extracts structured data from PSX financial filings."""

    def __init__(self):
        """Initialize filing extractor."""
        self.logger = logging.getLogger(__name__)

    def extract(self, filing_text: str, company_name: str) -> Optional[ExtractedFiling]:
        """Extract data from filing text.

        Args:
            filing_text: Raw text from filing document
            company_name: Company name for context

        Returns:
            ExtractedFiling or None on error
        """
        try:
            # Detect filing type
            filing_type = self._detect_filing_type(filing_text)

            # Extract dates
            filing_date = self._extract_filing_date(filing_text)
            period_end_date = self._extract_period_end_date(filing_text)
            period_type = self._extract_period_type(filing_text)

            # Extract financial statements
            balance_sheet = self._extract_balance_sheet(filing_text)
            income_statement = self._extract_income_statement(filing_text)
            cash_flow = self._extract_cash_flow(filing_text)

            # Extract key metrics
            total_assets = self._extract_total_assets(filing_text, balance_sheet)
            total_liabilities = self._extract_total_liabilities(
                filing_text, balance_sheet
            )
            total_equity = self._extract_total_equity(filing_text, balance_sheet)
            net_revenue = self._extract_net_revenue(filing_text, income_statement)
            net_profit = self._extract_net_profit(filing_text, income_statement)
            eps = self._extract_eps(filing_text)

            # Extract audit info
            audit_opinion = self._extract_audit_opinion(filing_text)
            audit_notes = self._extract_audit_notes(filing_text)

            # Extract MD&A
            mda = self._extract_mda(filing_text)

            # Calculate confidence & missing sections
            missing = self._identify_missing_sections(
                balance_sheet, income_statement, cash_flow
            )
            confidence = self._calculate_confidence(filing_text, missing)

            filing = ExtractedFiling(
                filing_type=filing_type,
                company_name=company_name,
                filing_date=filing_date,
                period_end_date=period_end_date,
                period_type=period_type,
                balance_sheet=balance_sheet,
                income_statement=income_statement,
                cash_flow=cash_flow,
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                total_equity=total_equity,
                net_revenue=net_revenue,
                net_profit=net_profit,
                earnings_per_share=eps,
                audit_opinion=audit_opinion,
                audit_notes=audit_notes,
                md_and_a=mda,
                confidence_score=confidence,
                missing_sections=missing,
            )

            self.logger.info(f"Extracted filing for {company_name}: {confidence:.0f}% confidence")
            return filing

        except Exception as e:
            self.logger.error(f"Error extracting filing: {e}")
            return None

    @staticmethod
    def _detect_filing_type(text: str) -> FilingType:
        """Detect filing type from text."""
        text_lower = text.lower()
        if "annual report" in text_lower:
            return FilingType.ANNUAL_REPORT
        elif "quarterly" in text_lower or "q1" in text_lower or "q3" in text_lower:
            return FilingType.QUARTERLY_REPORT
        elif "prospectus" in text_lower:
            return FilingType.PROSPECTUS
        elif "announcement" in text_lower:
            return FilingType.ANNOUNCEMENT
        return FilingType.UNKNOWN

    @staticmethod
    def _extract_filing_date(text: str) -> Optional[str]:
        """Extract filing date."""
        # Look for patterns like "dated 30 June 2024"
        date_pattern = r"dated\s+(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})"
        match = re.search(date_pattern, text, re.IGNORECASE)
        return match.group(0) if match else None

    @staticmethod
    def _extract_period_end_date(text: str) -> Optional[str]:
        """Extract period end date."""
        # Look for patterns like "As at 30 June 2024"
        date_pattern = r"as\s+at\s+(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})"
        match = re.search(date_pattern, text, re.IGNORECASE)
        return match.group(0) if match else None

    @staticmethod
    def _extract_period_type(text: str) -> str:
        """Extract period type (Q1, Q2, H1, FY, etc.)."""
        if re.search(r"quarter\s+ended|q[1-4]\s+\d{4}", text, re.IGNORECASE):
            for q in ["Q1", "Q2", "Q3", "Q4"]:
                if q in text.upper():
                    return q
        if re.search(r"half\s+year|h1|h2", text, re.IGNORECASE):
            return "H1" if "h1" in text.lower() else "H2"
        if re.search(r"fiscal\s+year|year\s+ended|annual", text, re.IGNORECASE):
            return "FY"
        return "Unknown"

    @staticmethod
    def _extract_balance_sheet(text: str) -> List[BalanceSheetItem]:
        """Extract balance sheet items."""
        items = []
        # Pattern: "Item Name ... Amount ... Amount"
        # This is simplified; real implementation would parse structured tables
        bs_pattern = r"(Total Assets|Total Liabilities|Total Equity|Current Assets|Current Liabilities)\s+(\d+(?:,\d+)*)"
        matches = re.findall(bs_pattern, text)
        for item_name, amount_str in matches:
            try:
                amount = float(amount_str.replace(",", ""))
                items.append(BalanceSheetItem(item_name=item_name, current_period=amount, prior_period=None))
            except ValueError:
                pass
        return items

    @staticmethod
    def _extract_income_statement(text: str) -> List[IncomeStatementItem]:
        """Extract income statement items."""
        items = []
        # Pattern: Revenue/Sales, Expenses, Profit/Loss
        is_pattern = r"(Net Revenue|Net Sales|Operating Expenses|Profit Before Tax|Profit After Tax|Net Profit)\s+(\d+(?:,\d+)*)"
        matches = re.findall(is_pattern, text)
        for item_name, amount_str in matches:
            try:
                amount = float(amount_str.replace(",", ""))
                items.append(
                    IncomeStatementItem(
                        item_name=item_name, current_period=amount, prior_period=None
                    )
                )
            except ValueError:
                pass
        return items

    @staticmethod
    def _extract_cash_flow(text: str) -> List[CashFlowItem]:
        """Extract cash flow items."""
        items = []
        # Pattern: Operating, Investing, Financing activities
        cf_pattern = r"(Operating|Investing|Financing) activities\s+(\d+(?:,\d+)*)"
        matches = re.findall(cf_pattern, text)
        for activity_type, amount_str in matches:
            try:
                amount = float(amount_str.replace(",", ""))
                items.append(CashFlowItem(item_name=activity_type, operating=None, investing=None, financing=None, total=amount))
            except ValueError:
                pass
        return items

    @staticmethod
    def _extract_total_assets(text: str, balance_sheet: List[BalanceSheetItem]) -> Optional[float]:
        """Extract total assets."""
        for item in balance_sheet:
            if "total assets" in item.item_name.lower():
                return item.current_period
        return None

    @staticmethod
    def _extract_total_liabilities(
        text: str, balance_sheet: List[BalanceSheetItem]
    ) -> Optional[float]:
        """Extract total liabilities."""
        for item in balance_sheet:
            if "total liabilities" in item.item_name.lower():
                return item.current_period
        return None

    @staticmethod
    def _extract_total_equity(text: str, balance_sheet: List[BalanceSheetItem]) -> Optional[float]:
        """Extract total equity."""
        for item in balance_sheet:
            if "total equity" in item.item_name.lower():
                return item.current_period
        return None

    @staticmethod
    def _extract_net_revenue(
        text: str, income_statement: List[IncomeStatementItem]
    ) -> Optional[float]:
        """Extract net revenue."""
        for item in income_statement:
            if "net revenue" in item.item_name.lower() or "net sales" in item.item_name.lower():
                return item.current_period
        return None

    @staticmethod
    def _extract_net_profit(
        text: str, income_statement: List[IncomeStatementItem]
    ) -> Optional[float]:
        """Extract net profit."""
        for item in income_statement:
            if "net profit" in item.item_name.lower() or "profit after tax" in item.item_name.lower():
                return item.current_period
        return None

    @staticmethod
    def _extract_eps(text: str) -> Optional[float]:
        """Extract earnings per share."""
        eps_pattern = r"earnings per share.*?(\d+\.\d+)"
        match = re.search(eps_pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_audit_opinion(text: str) -> str:
        """Extract audit opinion."""
        if re.search(r"unqualified|unmodified", text, re.IGNORECASE):
            return "Unqualified"
        elif re.search(r"qualified", text, re.IGNORECASE):
            return "Qualified"
        elif re.search(r"adverse", text, re.IGNORECASE):
            return "Adverse"
        elif re.search(r"disclaimer", text, re.IGNORECASE):
            return "Disclaimer"
        return "Unknown"

    @staticmethod
    def _extract_audit_notes(text: str) -> List[str]:
        """Extract audit notes and qualifications."""
        notes = []
        # Look for emphasis paragraphs in audit report
        note_pattern = r"emphasis of matter.*?(?=\n\n|\Z)"
        matches = re.findall(note_pattern, text, re.IGNORECASE | re.DOTALL)
        notes.extend(matches[:3])  # First 3 notes
        return notes

    @staticmethod
    def _extract_mda(text: str) -> str:
        """Extract Management Discussion & Analysis."""
        mda_pattern = r"management.*?discussion.*?analysis(.*?)(?=\n\n|Financial Statements|\Z)"
        match = re.search(mda_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)[:500]  # First 500 chars
        return ""

    @staticmethod
    def _identify_missing_sections(
        balance_sheet: List[BalanceSheetItem],
        income_statement: List[IncomeStatementItem],
        cash_flow: List[CashFlowItem],
    ) -> List[str]:
        """Identify missing financial statement sections."""
        missing = []
        if not balance_sheet:
            missing.append("Balance Sheet")
        if not income_statement:
            missing.append("Income Statement")
        if not cash_flow:
            missing.append("Cash Flow Statement")
        return missing

    @staticmethod
    def _calculate_confidence(text: str, missing: List[str]) -> float:
        """Calculate confidence score."""
        # Base confidence: 100%
        confidence = 100.0

        # Deduct for missing sections (25% each)
        confidence -= len(missing) * 25

        # Reduce if no MD&A found
        if "management discussion" not in text.lower():
            confidence -= 10

        # Reduce if audit opinion not found
        if "audit" not in text.lower():
            confidence -= 15

        return max(0, min(100, confidence))
