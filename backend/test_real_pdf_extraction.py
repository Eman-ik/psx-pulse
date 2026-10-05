#!/usr/bin/env python3
"""Test enhanced metric extractor on real EFERT FY2025 PDF."""

import sys
sys.path.insert(0, '.')

import pdfplumber
import re
from app.ingestion.metric_extractor_enhanced import (
    StatementDetector,
    NarrativeMetricExtractor,
    EnhancedMetricExtractor
)

print('='*70)
print('REAL PDF TEST: EFERT FY2025 Annual Report')
print('='*70)

pdf_path = 'test_fixtures/real_pdfs/EFERT_AR_2025.pdf'

with pdfplumber.open(pdf_path) as pdf:
    print(f'Total pages: {len(pdf.pages)}\n')

    # Extract text from first 80 pages (should include financial statements)
    pages_text = []
    for i, page in enumerate(pdf.pages[:80], start=1):
        text = page.extract_text() or ''
        pages_text.append((i, text))

    # Classify pages
    detector = StatementDetector()
    print('Page Classification (first 80 pages):')
    stmt_type_counts = {}
    income_stmt_pages = []

    for page_num, text in pages_text:
        stmt_type = detector.detect_statement_type(text)
        stmt_type_counts[stmt_type] = stmt_type_counts.get(stmt_type, 0) + 1
        if stmt_type == 'income_statement':
            income_stmt_pages.append(page_num)
            if len(income_stmt_pages) <= 3:
                print(f'  Page {page_num}: {stmt_type} ✓')

    print(f'\nStatement type summary:')
    for stmt_type, count in sorted(stmt_type_counts.items()):
        print(f'  {stmt_type}: {count} pages')

    if income_stmt_pages:
        print(f'\nIncome statement found on pages: {income_stmt_pages[:5]}...')

    # Test metric extraction
    print('\n' + '='*70)
    print('Testing Metric Extraction')
    print('='*70)

    def mock_extract(line):
        """Simplified number extraction (matching original extractor logic)."""
        numbers = re.findall(r'[\d,]+(?:\.\d+)?', line)
        if numbers:
            try:
                return float(numbers[0].replace(',', ''))
            except:
                return None
        return None

    enhancer = EnhancedMetricExtractor(mock_extract)

    # Test each metric
    metrics = [
        ('operating_profit', ['operating profit', 'ebit', 'earnings before interest']),
        ('other_income', ['other income', 'miscellaneous income']),
        ('tax_expense', ['taxation', 'income tax', 'tax charge']),
    ]

    results = {}
    for metric_key, aliases in metrics:
        result = enhancer.extract_with_fallbacks(pages_text, metric_key, aliases)
        results[metric_key] = result

        if result:
            print(f'\n✓ {metric_key}:')
            print(f'    Value: {result["value"]:,.0f}')
            print(f'    Method: {result["extraction_method"]}')
            print(f'    Confidence: {result["confidence"]}')
            print(f'    Page: {result.get("page", "?")}')
            if 'raw_line' in result:
                print(f'    Source: {result["raw_line"][:60]}...')
        else:
            print(f'\n✗ {metric_key}: NOT FOUND')

print('\n' + '='*70)
print('Real PDF Extraction Summary')
print('='*70)
found = sum(1 for r in results.values() if r)
total = len(results)
print(f'Extracted: {found}/{total} metrics')
if found > 0:
    print('✓ Enhanced extractor working on real PDF')
else:
    print('✗ No metrics found (may need regex pattern tuning)')

print('='*70)
