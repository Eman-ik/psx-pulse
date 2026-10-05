# MetricExtractor Analysis: Robustness & Gaps

## Test Results Summary
**Tested against 5 realistic income statement fixtures:**
- ✓ 4/5 pass (FFC-style, EFERT-style, complex tables, naming variations)
- ✗ 1/5 fail (narrative/prose format)

## What the Current Extractor Handles Well

### ✓ Strength 1: Column Position Invariant
- Works when current year is first OR last column
- Correctly picks the first large number on matching line
- **Why:** Simple regex matching of comma-separated numbers

### ✓ Strength 2: Metric Naming Flexibility  
- Handles aliases: "Operating Profit", "EBIT", "Earnings Before Interest"
- Substring matching is forgiving of variations
- **Why:** Alias list covers common PSX fertilizer company naming

### ✓ Strength 3: Table Structure Variance
- Works with complex layouts (multiple expense categories, different spacing)
- Handles PKR thousands vs PKR units (metric value stays same, unit constant)
- **Why:** Line-by-line extraction ignores table structure

## What Fails

### ✗ Weakness 1: Narrative/Prose Format
**Fixture:** Narrative-style reporting (common in some companies' sustainability/integrated reports)
- **Problem:** "450 million" embedded in prose extracted as "15.0" (spurious number)
- **Root Cause:** Line-by-line regex on prose picks wrong numbers
- **Fix Needed:** Detect and skip narrative sections; flag for manual review

### ✗ Weakness 2 (Untested): Scanned PDF Images
- Current extractor uses pdfplumber text extraction
- Fails on image-based PDFs (no OCR fallback)
- **Fix Needed:** Detect when PDF has no extractable text; flag for OCR or manual handling

### ✗ Weakness 3 (Untested): Multi-Currency Presentations
- Some reports show PKR + USD or PKR + other currency
- Current extraction picks first number (might be wrong currency)
- **Fix Needed:** Currency detection; prefer PKR

### ✗ Weakness 4: Derived Metrics
- EBITDA: often "Operating Profit + Depreciation + Amortization"
- DPS: "Interim + Final" or stated separately
- **Fix Needed:** Pattern recognition for "+" in lines (e.g., "1.50 + 1.00 = 2.50")

## Recommended Fallback Strategy Stack

### Priority 1: Statement-Aware Detection (Improves 50%+ of edge cases)
```python
def detect_statement_type(page_text):
    """Return: 'income_statement', 'balance_sheet', 'cash_flow', 'narrative', or 'unknown'"""
    if any(x in page_text.upper() for x in ['STATEMENT OF PROFIT AND LOSS', 'INCOME STATEMENT', 'P&L']):
        return 'income_statement'
    if any(x in page_text.upper() for x in ['BALANCE SHEET', 'STATEMENT OF POSITION']):
        return 'balance_sheet'
    if 'CASH FLOW' in page_text.upper():
        return 'cash_flow'
    
    # Heuristic: narrative has more prose (lowercase words, "the", "which", etc)
    lowercase_ratio = sum(1 for c in page_text if c.islower()) / len(page_text)
    if lowercase_ratio > 0.7 and 'million' in page_text.lower():
        return 'narrative'
    
    return 'unknown'
```

### Priority 2: Number Context Extraction (For narrative)
```python
def extract_from_narrative(text, metric_name):
    """For prose like 'Operating profit reached PKR 450 million', extract 450."""
    import re
    
    # Pattern: [word] [number] [million/thousand/...]
    patterns = [
        rf'{metric_name}.*?(\d+(?:,\d{{3}})*)\s+(million|thousand|lakh)',
        rf'{metric_name}.*?PKR\s+(\d+(?:,\d{{3}})*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            num = match.group(1).replace(',', '')
            unit = match.group(2) if match.lastindex > 1 else None
            
            # Scale to thousands (consistent with table-based extraction)
            multiplier = {'thousand': 1, 'lakh': 100, 'million': 1000}.get(unit, 1)
            return float(num) * multiplier
    
    return None
```

### Priority 3: Derived Metric Handling
```python
def extract_derived_metric(text, metric_name):
    """Handle metrics like DPS = interim + final."""
    
    if metric_name == 'dividend_per_share':
        # Look for pattern: "1.50 + 1.00 = 2.50" or "[interim] + [final]"
        match = re.search(r'(\d+\.\d+)\s*\+\s*(\d+\.\d+)(?:\s*=\s*(\d+\.\d+))?', text)
        if match:
            interim = float(match.group(1))
            final = float(match.group(2))
            stated = float(match.group(3)) if match.lastindex >= 3 else None
            
            # Use stated if available, else calculate
            return stated or (interim + final)
    
    return None
```

### Priority 4: Scanned PDF Detection
```python
def detect_scanned_pdf(pdf_pages):
    """Return True if PDF appears to be scanned (image-based)."""
    
    # Check first 3 pages
    for page in pdf_pages[:3]:
        text = page.extract_text() or ""
        
        # Scanned PDFs extract almost no text
        if len(text.strip()) < 100:
            return True
    
    return False

# Usage: If detected, flag extraction as "requires_ocr" and skip
```

## Implementation Roadmap

### Phase 1: Detection Layer (Week 1)
- [ ] Add `detect_statement_type()` function
- [ ] Add `detect_scanned_pdf()` check  
- [ ] Flag suspicious extractions (narrative_fallback_used, scanned_pdf, etc)
- [ ] Tests: 6 fixtures covering all cases

### Phase 2: Narrative Fallback (Week 2)
- [ ] Implement prose pattern extraction
- [ ] Add narrative metric discovery
- [ ] Test on Fixture: narrative_format
- [ ] Coverage target: 80%+ on mixed format reports

### Phase 3: Derived Metrics (Week 2)
- [ ] Pattern recognition for "A + B = C"
- [ ] DPS calculation from interim + final
- [ ] EBITDA = OP + D&A parsing
- [ ] Test on real DPS presentations

### Phase 4: Quality Scoring (Week 3)
- [ ] Extraction quality flags: "extracted_from_table" vs "extracted_from_narrative" vs "calculated"
- [ ] Confidence scores per metric (high: table extraction, low: narrative)
- [ ] Surface in research API for downstream decisions

## Code Entry Points to Modify

1. **`MetricExtractor.extract_metrics_from_pdf()`** - Add detection layer
2. **`MetricExtractor._extract_number_from_line()`** - Call narrative fallback if needed
3. **New method:** `MetricExtractor._extract_from_narrative_section()`
4. **New method:** `MetricExtractor._extract_derived_metric()`
5. **`FinancialFact` model** - Add `extraction_method` field to track source (table vs narrative vs derived)

## Success Metrics

- **Coverage:** FFC + EFERT 2023-2025 reports → 90%+ metric extraction rate (vs current ~85%?)
- **Accuracy:** Spot-check extracted values against manual PDF review
- **Robustness:** Handle edge cases (narrative, multi-currency, calculated) gracefully

## Risk Mitigation

- **Risk:** Narrative extraction pulls wrong numbers
  - **Mitigation:** Always log raw extracted text + confidence score; manual review before use
  
- **Risk:** Over-engineering for edge cases  
  - **Mitigation:** Prioritize: FFC + EFERT first, generalize later; fallback to "manual_review_needed" flag
  
- **Risk:** Scanned PDFs fail silently
  - **Mitigation:** Explicit "requires_ocr" flag in extraction result; never silently omit

## Notes

- Current line-by-line extraction is actually quite robust for structured tables
- Main gap is unstructured/narrative reporting and calculated metrics
- Safe approach: flag uncertain extractions, don't silently guess
- PSX companies tend toward structured statements, so 80/20 rule suggests focus on detecting + fallback for edge 20%
