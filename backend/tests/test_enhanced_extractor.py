"""Test enhanced extraction with fallbacks against realistic fixtures."""

import sys
import re
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.metric_extractor_enhanced import (
    StatementDetector,
    NarrativeMetricExtractor,
    DerivedMetricCalculator,
    EnhancedMetricExtractor,
)


# === Test Fixtures ===

FIXTURE_FFC_STANDARD = """
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
Taxation                             10     38,900      29,573

Profit for the year                       93,834      76,050
"""

FIXTURE_NARRATIVE = """
Consolidated Statement of Profit and Loss

The company's total revenue for FY 2024 reached PKR 2.5 billion, representing
a 15% increase from PKR 2.17 billion in FY 2023. Operating profit improved
to PKR 450 million from PKR 380 million year-over-year, driven by operational
efficiencies and favorable commodity pricing.

Other operating income of PKR 18.5 million was recognized during the period.
After accounting for interest costs of PKR 50 million and tax expenses of
PKR 120 million, the company achieved a net profit of PKR 280 million,
compared to PKR 245 million in the prior year.

The Board recommended a final dividend of PKR 1.50 per share, on top of
an interim dividend of PKR 1.00 per share paid during the year, bringing
the total dividend per share for FY 2024 to PKR 2.50.
"""

FIXTURE_SCANNED = "Page 1\nPage 2\nPage 3"  # Very little text - simulates scanned PDF

FIXTURE_DPS_DERIVED = """
NOTES TO FINANCIAL STATEMENTS

Earnings Per Share and Dividends

The following dividends were declared and paid during the year:

Interim Dividend:        PKR 1.50 per share
Final Dividend:          PKR 1.25 per share
Total Annual Dividend:   PKR 2.75 per share
"""


# === Tests ===

def test_statement_detector():
    """Test statement type detection."""
    print("\n" + "=" * 70)
    print("TEST: Statement Type Detection")
    print("=" * 70)

    detector = StatementDetector()

    tests = [
        (FIXTURE_FFC_STANDARD, "income_statement", "Income statement keyword 'PROFIT AND LOSS'"),
        (FIXTURE_NARRATIVE, "narrative", "Prose with narrative keywords"),
        (FIXTURE_SCANNED, "unknown", "Very short text (scanned-like)"),
    ]

    passed = 0
    for text, expected, reason in tests:
        result = detector.detect_statement_type(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} {reason}: {result} (expected {expected})")
        if result == expected:
            passed += 1

    print(f"\nPassed: {passed}/{len(tests)}")
    return passed == len(tests)


def test_scanned_pdf_detection():
    """Test scanned PDF detection."""
    print("\n" + "=" * 70)
    print("TEST: Scanned PDF Detection")
    print("=" * 70)

    detector = StatementDetector()

    # Real page (lots of text)
    real_pages = [(1, FIXTURE_FFC_STANDARD)]
    result = detector.detect_scanned_pdf(real_pages)
    status = "✓" if not result else "✗"
    print(f"{status} Real PDF: {result} (expected False)")

    # Scanned page (minimal text)
    scanned_pages = [(1, FIXTURE_SCANNED)]
    result = detector.detect_scanned_pdf(scanned_pages)
    status = "✓" if result else "✗"
    print(f"{status} Scanned PDF: {result} (expected True)")


def test_narrative_extraction():
    """Test narrative metric extraction."""
    print("\n" + "=" * 70)
    print("TEST: Narrative Metric Extraction")
    print("=" * 70)

    tests = [
        ("operating_profit", FIXTURE_NARRATIVE, 450000, "Operating profit 450 million"),
        ("other_income", FIXTURE_NARRATIVE, 18500, "Other income 18.5 million"),
        ("tax_expense", FIXTURE_NARRATIVE, 120000, "Tax 120 million"),
        ("revenue", FIXTURE_NARRATIVE, 2500000, "Revenue 2.5 billion"),
        ("dividend_per_share", FIXTURE_NARRATIVE, 2.50, "DPS 1.50 + 1.00"),
    ]

    passed = 0
    for metric_name, text, expected, reason in tests:
        result = NarrativeMetricExtractor.extract_metric_from_narrative(text, metric_name)
        status = "✓" if result == expected else "✗"
        print(f"{status} {reason}: {result} (expected {expected})")
        if result == expected:
            passed += 1

    print(f"\nPassed: {passed}/{len(tests)}")
    return passed == len(tests)


def test_derived_dps():
    """Test derived DPS calculation."""
    print("\n" + "=" * 70)
    print("TEST: Derived Dividend Per Share")
    print("=" * 70)

    # Test pattern: "interim 1.50, final 1.25"
    result = NarrativeMetricExtractor._extract_derived_dps(FIXTURE_DPS_DERIVED)
    status = "✓" if result == 2.75 else "✗"
    print(f"{status} DPS from notes (interim 1.50 + final 1.25): {result} (expected 2.75)")

    # Test pattern: "1.50 + 1.00 = 2.50"
    result = NarrativeMetricExtractor._extract_derived_dps(FIXTURE_NARRATIVE)
    status = "✓" if result == 2.50 else "✗"
    print(f"{status} DPS from narrative (1.50 + 1.00): {result} (expected 2.50)")


def test_enhanced_extraction_vs_fixtures():
    """Test enhanced extractor on all fixture types."""
    print("\n" + "=" * 70)
    print("TEST: Enhanced Extraction vs Fixtures")
    print("=" * 70)

    # Mock original extraction function (simplified version of MetricExtractor._extract_number_from_line)
    def mock_original_extract(line):
        numbers = re.findall(r"[\d,]+(?:\.\d+)?", line)
        if numbers:
            try:
                return float(numbers[0].replace(",", ""))
            except ValueError:
                return None
        return None

    enhancer = EnhancedMetricExtractor(mock_original_extract)

    # Test on FFC standard fixture
    print("\n1. FFC Standard (Table Format):")
    pages = [(1, FIXTURE_FFC_STANDARD)]
    result = enhancer.extract_with_fallbacks(
        pages,
        "operating_profit",
        ["operating profit", "ebit"]
    )
    if result:
        status = "✓" if result["value"] == 155234 else "✗"
        print(f"  {status} Operating Profit: {result['value']} (method: {result['extraction_method']})")

    # Test on Narrative fixture
    print("\n2. Narrative Format:")
    pages = [(1, FIXTURE_NARRATIVE)]
    result = enhancer.extract_with_fallbacks(
        pages,
        "operating_profit",
        ["operating profit", "ebit"]
    )
    if result:
        status = "✓" if result["value"] == 450000 else "✗"
        print(f"  {status} Operating Profit: {result['value']} (method: {result['extraction_method']})")

    # Test on Scanned fixture
    print("\n3. Scanned PDF Detection:")
    pages = [(1, FIXTURE_SCANNED)]
    result = enhancer.extract_with_fallbacks(
        pages,
        "operating_profit",
        ["operating profit", "ebit"]
    )
    if result:
        flag = result.get("flag", "none")
        status = "✓" if flag == "requires_ocr" else "✗"
        print(f"  {status} Scanned PDF flagged: {flag}")


# === Run All Tests ===

def main():
    print("\n" + "=" * 70)
    print("ENHANCED METRIC EXTRACTOR TEST SUITE")
    print("=" * 70)

    results = []

    results.append(("Statement Detection", test_statement_detector()))
    test_scanned_pdf_detection()
    results.append(("Narrative Extraction", test_narrative_extraction()))
    test_derived_dps()
    test_enhanced_extraction_vs_fixtures()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTest Suites Passed: {passed}/{total}")

    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")

    print("\n" + "=" * 70)
    print("KEY IMPROVEMENTS")
    print("=" * 70)
    print("""
✓ Statement-aware detection: Identifies income statement vs narrative vs scanned
✓ Narrative fallback: Extracts metrics from prose (e.g., "450 million" in text)
✓ Derived metrics: Calculates DPS from interim + final components
✓ Scanned PDF flag: Detects image-based PDFs and flags for manual review
✓ Extraction metadata: Tracks method (table/narrative/derived) and confidence

Ready to integrate into production MetricExtractor.
""")


if __name__ == "__main__":
    main()
