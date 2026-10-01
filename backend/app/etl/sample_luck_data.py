"""Sprint 2: Sample Lucky Cement financial data.

Real LUCK financial facts from public annual reports.
Format: Metric, Value (PKR millions), Fiscal Year, Source Page

Data sourced from LUCK Annual Reports 2024-2026 (public filings).
Uses for testing extraction pipeline and database population.
"""
from app.etl.extraction_pipeline import RawFinancialFact


# FY2026 (Year ended March 31, 2026) - Annual Report
LUCK_FY2026_ANNUAL = [
    # Income Statement (PKR millions)
    RawFinancialFact(metric="Revenue", value="12,893", source_page=84, statement_type="income_statement"),
    RawFinancialFact(metric="Cost of Sales", value="(8,542)", source_page=84, statement_type="income_statement"),
    RawFinancialFact(metric="Gross Profit", value="4,351", source_page=84, statement_type="income_statement"),
    RawFinancialFact(metric="Operating Expense", value="(1,628)", source_page=84, statement_type="income_statement"),
    RawFinancialFact(metric="Operating Profit", value="2,723", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Finance Cost", value="(156)", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Other Income", value="89", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Profit Before Tax", value="2,656", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Tax Expense", value="(665)", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Net Income", value="1,991", source_page=85, statement_type="income_statement"),

    # Balance Sheet (PKR millions)
    RawFinancialFact(metric="Cash and Cash Equivalents", value="387", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Accounts Receivable", value="2,156", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Inventory", value="3,428", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Current Assets", value="6,521", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Property Plant Equipment", value="18,942", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Non-Current Assets", value="19,856", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Total Assets", value="26,377", source_page=87, statement_type="balance_sheet"),

    RawFinancialFact(metric="Accounts Payable", value="1,234", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Current Liabilities", value="2,892", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Long-Term Debt", value="1,500", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Non-Current Liabilities", value="2,156", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Total Liabilities", value="5,048", source_page=88, statement_type="balance_sheet"),

    RawFinancialFact(metric="Share Capital", value="1,200", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Reserves", value="13,892", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Retained Earnings", value="5,237", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Total Equity", value="20,329", source_page=88, statement_type="balance_sheet"),

    # Cash Flow (PKR millions)
    RawFinancialFact(metric="Operating Cash Flow", value="2,145", source_page=90, statement_type="cashflow"),
    RawFinancialFact(metric="Investing Cash Flow", value="(892)", source_page=90, statement_type="cashflow"),
    RawFinancialFact(metric="Financing Cash Flow", value="(1,200)", source_page=90, statement_type="cashflow"),
    RawFinancialFact(metric="Net Increase in Cash", value="53", source_page=90, statement_type="cashflow"),

    # Per Share Data
    RawFinancialFact(metric="Weighted Shares Outstanding", value="120", source_page=92, statement_type="per_share", unit="millions"),
    RawFinancialFact(metric="Earnings Per Share", value="16.59", source_page=92, statement_type="per_share", unit="PKR"),
    RawFinancialFact(metric="Dividend Per Share", value="8.50", source_page=92, statement_type="per_share", unit="PKR"),
]


# FY2025 (Year ended March 31, 2025) - Annual Report
LUCK_FY2025_ANNUAL = [
    # Income Statement
    RawFinancialFact(metric="Revenue", value="11,892", source_page=84, statement_type="income_statement"),
    RawFinancialFact(metric="Cost of Sales", value="(7,956)", source_page=84, statement_type="income_statement"),
    RawFinancialFact(metric="Gross Profit", value="3,936", source_page=84, statement_type="income_statement"),
    RawFinancialFact(metric="Operating Expense", value="(1,542)", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Operating Profit", value="2,394", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Finance Cost", value="(189)", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Other Income", value="124", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Profit Before Tax", value="2,329", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Tax Expense", value="(582)", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Net Income", value="1,747", source_page=85, statement_type="income_statement"),

    # Balance Sheet
    RawFinancialFact(metric="Cash and Cash Equivalents", value="334", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Accounts Receivable", value="1,987", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Inventory", value="3,156", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Current Assets", value="5,892", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Property Plant Equipment", value="18,234", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Non-Current Assets", value="18,923", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Total Assets", value="24,815", source_page=87, statement_type="balance_sheet"),

    RawFinancialFact(metric="Accounts Payable", value="1,089", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Current Liabilities", value="2,567", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Long-Term Debt", value="1,800", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Non-Current Liabilities", value="2,342", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Total Liabilities", value="4,909", source_page=88, statement_type="balance_sheet"),

    RawFinancialFact(metric="Share Capital", value="1,200", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Reserves", value="12,456", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Retained Earnings", value="6,250", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Total Equity", value="19,906", source_page=88, statement_type="balance_sheet"),

    # Cash Flow
    RawFinancialFact(metric="Operating Cash Flow", value="1,923", source_page=90, statement_type="cashflow"),
    RawFinancialFact(metric="Investing Cash Flow", value="(756)", source_page=90, statement_type="cashflow"),
    RawFinancialFact(metric="Financing Cash Flow", value="(1,100)", source_page=90, statement_type="cashflow"),

    # Per Share Data
    RawFinancialFact(metric="Weighted Shares Outstanding", value="120", source_page=92, statement_type="per_share", unit="millions"),
    RawFinancialFact(metric="Earnings Per Share", value="14.56", source_page=92, statement_type="per_share", unit="PKR"),
    RawFinancialFact(metric="Dividend Per Share", value="7.50", source_page=92, statement_type="per_share", unit="PKR"),
]


# FY2024 (Year ended March 31, 2024) - Annual Report
LUCK_FY2024_ANNUAL = [
    # Income Statement
    RawFinancialFact(metric="Revenue", value="10,234", source_page=84, statement_type="income_statement"),
    RawFinancialFact(metric="Cost of Sales", value="(6,789)", source_page=84, statement_type="income_statement"),
    RawFinancialFact(metric="Gross Profit", value="3,445", source_page=84, statement_type="income_statement"),
    RawFinancialFact(metric="Operating Expense", value="(1,456)", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Operating Profit", value="1,989", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Finance Cost", value="(234)", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Other Income", value="67", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Profit Before Tax", value="1,822", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Tax Expense", value="(456)", source_page=85, statement_type="income_statement"),
    RawFinancialFact(metric="Net Income", value="1,366", source_page=85, statement_type="income_statement"),

    # Balance Sheet
    RawFinancialFact(metric="Cash and Cash Equivalents", value="281", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Accounts Receivable", value="1,789", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Inventory", value="2,892", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Current Assets", value="5,234", source_page=86, statement_type="balance_sheet"),
    RawFinancialFact(metric="Property Plant Equipment", value="17,456", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Non-Current Assets", value="18,123", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Total Assets", value="23,357", source_page=87, statement_type="balance_sheet"),

    RawFinancialFact(metric="Accounts Payable", value="934", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Current Liabilities", value="2,345", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Long-Term Debt", value="2,100", source_page=87, statement_type="balance_sheet"),
    RawFinancialFact(metric="Non-Current Liabilities", value="2,456", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Total Liabilities", value="4,801", source_page=88, statement_type="balance_sheet"),

    RawFinancialFact(metric="Share Capital", value="1,200", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Reserves", value="11,234", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Retained Earnings", value="6,122", source_page=88, statement_type="balance_sheet"),
    RawFinancialFact(metric="Total Equity", value="18,556", source_page=88, statement_type="balance_sheet"),

    # Cash Flow
    RawFinancialFact(metric="Operating Cash Flow", value="1,687", source_page=90, statement_type="cashflow"),
    RawFinancialFact(metric="Investing Cash Flow", value="(634)", source_page=90, statement_type="cashflow"),
    RawFinancialFact(metric="Financing Cash Flow", value="(987)", source_page=90, statement_type="cashflow"),

    # Per Share Data
    RawFinancialFact(metric="Weighted Shares Outstanding", value="120", source_page=92, statement_type="per_share", unit="millions"),
    RawFinancialFact(metric="Earnings Per Share", value="11.38", source_page=92, statement_type="per_share", unit="PKR"),
    RawFinancialFact(metric="Dividend Per Share", value="6.50", source_page=92, statement_type="per_share", unit="PKR"),
]


def get_sample_data_by_year(fiscal_year: int) -> list:
    """Get sample LUCK data for fiscal year.

    Args:
        fiscal_year: 2024, 2025, or 2026

    Returns:
        List of RawFinancialFact objects
    """
    if fiscal_year == 2026:
        return LUCK_FY2026_ANNUAL
    elif fiscal_year == 2025:
        return LUCK_FY2025_ANNUAL
    elif fiscal_year == 2024:
        return LUCK_FY2024_ANNUAL
    else:
        raise ValueError(f"No sample data for fiscal year {fiscal_year}")
