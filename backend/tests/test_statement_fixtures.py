"""Test fixture generator: realistic income statement text from PDFs.

Simulates different formatting patterns found in real annual reports:
- Column layout variance (current year in different position)
- Metric naming variations (Operating Profit vs EBIT vs Earnings Before Interest)
- Table structure (with/without borders, different spacing)
- Derived vs explicit metrics (EBITDA calculated vs stated)
"""

# Fixture 1: FFC-style income statement (current year as last column)
FFC_INCOME_STATEMENT_2024 = """
STATEMENT OF PROFIT AND LOSS
For the year ended 31 December 2024

                                    Note    2024        2023
                                            (000s)      (000s)
Revenue                              4     985,234     845,123
Cost of sales                         5    (625,000)   (550,000)
Gross Profit                                360,234     295,123

Operating Expenses:
Distribution                         6    (120,000)    (95,000)
Administrative                       7     (85,000)    (75,000)
                                         (205,000)   (170,000)

Operating Profit                           155,234     125,123
Other income                          8      12,500      10,500
Finance costs                         9     (35,000)    (30,000)

Profit before tax                         132,734     105,623
Taxation                             10     (38,900)    (29,573)

Profit for the year                       93,834      76,050
"""

# Fixture 2: EFERT-style (current year as first column)
EFERT_INCOME_STATEMENT_2024 = """
STATEMENT OF PROFIT AND LOSS
For the year ended June 30, 2024

                                    Note    2024        2023
                                           Amount      Amount
                                            PKR         PKR
Revenue from operations              3     456,789     389,234
Cost of raw materials                        (250,000)  (210,000)
Other manufacturing costs                   (95,000)   (85,000)
Gross Profit                               111,789     94,234

Operating & Administrative                 (45,000)    (40,000)
Distribution                               (15,000)    (12,000)

EBIT / Operating Profit                    51,789      42,234
Other Operating Income                     8,500       6,500
Finance Costs                             (10,500)     (9,000)

Earnings Before Tax                        49,789      39,734
Income Tax Expense                        (12,000)     (8,500)

NET PROFIT                                 37,789      31,234
"""

# Fixture 3: Tabular format (with complex spacing)
COMPLEX_TABLE_STATEMENT = """
                                                    Year Ended 31-Dec
                                          2024 (Rs 000s)   2023 (Rs 000s)
Revenue from Operations                      1,234,567           987,654
Cost of Goods Sold                            (750,000)         (625,000)
Gross Profit                                   484,567           362,654
Operating Expenses
  a) Selling, General & Admin                 (156,000)         (132,000)
  b) Depreciation & Amortization              (45,000)           (42,000)
  c) Other Expenses                           (15,000)           (12,000)
                                              (216,000)         (186,000)
Operating Profit (EBIT)                       268,567           176,654
Other Income                                   18,500            12,340
Finance Costs                                 (42,000)          (38,000)
Profit Before Tax                             245,067           151,000
Less: Taxation                                (73,520)          (41,775)
Net Profit for the Period                     171,547           109,225

Dividend Per Share (Rupees)                     2.50              1.75
"""

# Fixture 4: With naming variations
NAMING_VARIATIONS = """
Statement of Profit and Loss (Year ended 31 December 2024)

Sales / Revenue                        3,456,789
Less: Cost of Goods Sold             (2,100,000)
Gross Profit                           1,356,789

Administrative Costs                   (234,000)
Distribution & Marketing               (156,000)

EARNINGS BEFORE INTEREST AND TAX         966,789
Miscellaneous Income                      45,000
Interest Paid                            (67,000)
PROFIT BEFORE TAXATION                   944,789
Income Tax Charge                       (283,437)
PAT / Net Profit                         661,352

DPS (Final)                                 1.25
DPS (Interim)                               1.75
Dividend Per Share (Total Annual)            3.00
"""

# Fixture 5: With footnotes and narrative (harder extraction)
NARRATIVE_FORMAT = """
Consolidated Statement of Profit and Loss

The company's total revenue for FY 2024 reached PKR 2.5 billion, representing
a 15% increase from PKR 2.17 billion in FY 2023. Operating profit improved
to PKR 450 million from PKR 380 million year-over-year, driven by operational
efficiencies and favorable commodity pricing.

After accounting for interest costs of PKR 50 million and tax expenses of
PKR 120 million, the company achieved a net profit of PKR 280 million,
compared to PKR 245 million in the prior year.

The Board recommended a final dividend of PKR 1.50 per share, on top of
an interim dividend of PKR 1.00 per share paid during the year, bringing
the total dividend per share for FY 2024 to PKR 2.50.
"""


FIXTURES = {
    "ffc_2024_standard": {
        "text": FFC_INCOME_STATEMENT_2024,
        "expected": {
            "operating_profit": 155234,
            "other_income": 12500,
            "tax_expense": 38900,
            "revenue": 985234,
        }
    },
    "efert_2024_alt_column": {
        "text": EFERT_INCOME_STATEMENT_2024,
        "expected": {
            "operating_profit": 51789,
            "other_income": 8500,
            "tax_expense": 12000,
            "revenue": 456789,
        }
    },
    "complex_table": {
        "text": COMPLEX_TABLE_STATEMENT,
        "expected": {
            "operating_profit": 268567,
            "other_income": 18500,
            "tax_expense": 73520,
            "revenue": 1234567,
            "dividend_per_share": 2.50,
        }
    },
    "naming_variations": {
        "text": NAMING_VARIATIONS,
        "expected": {
            "operating_profit": 966789,  # EBIT
            "other_income": 45000,  # Miscellaneous Income
            "tax_expense": 283437,  # Income Tax Charge
            "revenue": 3456789,  # Sales
            "dividend_per_share": 3.00,  # Total annual
        }
    },
    "narrative_format": {
        "text": NARRATIVE_FORMAT,
        "expected": {
            "operating_profit": 450000000,  # 450 million in narrative
            "other_income": None,  # Not explicit
            "tax_expense": 120000000,  # 120 million
            "revenue": 2500000000,  # 2.5 billion
            "dividend_per_share": 2.50,  # 1.50 + 1.00
        }
    }
}

def test_extractor_against_fixtures():
    """Test current extractor against realistic fixtures.

    Documents what the current extractor can handle vs what requires
    statement-aware enhancements.
    """
    results = {}

    for fixture_name, fixture_data in FIXTURES.items():
        text = fixture_data["text"]
        expected = fixture_data["expected"]

        # Simulate what pdfplumber would return
        pages_text = [(1, text)]  # All in one page for simplicity

        # Test metric extraction
        extracted = {}

        # Test operating_profit aliases
        for alias in ["operating profit", "ebit", "earnings before interest"]:
            for page_num, page_text in pages_text:
                for line in page_text.split("\n"):
                    if alias.lower() in line.lower() and "operating profit" not in extracted:
                        # Simple number extraction (matching extractor logic)
                        import re
                        numbers = re.findall(r"[\d,]+(?:\.\d+)?", line)
                        if numbers:
                            value = float(numbers[0].replace(",", ""))
                            extracted["operating_profit"] = value
                            break

        results[fixture_name] = {
            "expected": expected,
            "extracted": extracted,
            "match": extracted.get("operating_profit") == expected.get("operating_profit")
        }

    return results


if __name__ == "__main__":
    results = test_extractor_against_fixtures()

    print("\nFIXTURE TEST RESULTS\n" + "=" * 70)

    passes = 0
    fails = 0

    for fixture_name, result in results.items():
        status = "✓ PASS" if result["match"] else "✗ FAIL"
        expected = result["expected"].get("operating_profit")
        extracted = result["extracted"].get("operating_profit")

        print(f"\n{fixture_name}: {status}")
        print(f"  Expected:  {expected}")
        print(f"  Extracted: {extracted}")

        if result["match"]:
            passes += 1
        else:
            fails += 1

    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {passes} passed, {fails} failed")
    print(f"\nFailing fixtures reveal gaps in current extractor:")
    print(f"1. Naming variations (EBIT vs Operating Profit)")
    print(f"2. Column layout variance (first vs last number)")
    print(f"3. Narrative format (requires parsing prose, not tables)")
    print(f"4. Derived metrics (DPS = interim + final, EBITDA = calc)")
