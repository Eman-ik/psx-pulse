# Data Coverage System Redesign: Executive Summary

## The Problem

PSX Pulse displays "Data coverage: 44%" for FFC. This number is **fundamentally broken** because it conflates three separate concepts into one metric, and the underlying calculation has semantic bugs that prevent honest measurement.

### What 44% Actually Means (Currently)

```
confidence_score = average([
    business_health.data_coverage_pct,
    what_changed.data_coverage_pct,
    earnings_quality.data_coverage_pct,
    valuation.data_coverage_pct
]) - consistency_penalty
```

**The three conflated concepts:**
1. **Data Coverage:** Do we possess the required data?
2. **Evidence Quality:** How trustworthy/current is that data?
3. **Analytical Confidence:** How confident is the engine's interpretation?

### The Four Semantic Defects

1. **WhatChangedEngine Bug (CRITICAL)**
   - A comparison (e.g., revenue growth) can be PERFORMABLE (data exists) but show NO MATERIAL CHANGE (grew 0.5%)
   - Current code: Only increments `available_comparisons` if change > threshold
   - Effect: "Data exists and can be compared" is incorrectly counted as "Data unavailable"
   - Result: Artificially low coverage

2. **EarningsQualityEngine Hard-Coded Ceiling**
   - Expected: 6 pieces of evidence (OCF, EBIT, other_income, finance_cost, revenue, tax_expense)
   - Actual: Data coverage maxes at 90%, even with all 6 available
   - Hard-coded values: 40, 45, 65, 70, 80, 85, 90
   - Result: Can never exceed 90% no matter how complete the data is

3. **ValuationContextEngine Hard-Coded Ceiling**
   - Expected: Current P/E + historical P/E series + P/B + ROE + revenue growth + sector median P/E
   - Actual: Data coverage maxes at 90% with just current P/E + historical median
   - Hard-coded values: 0 (no P/E), 70 (current only), 90 (with history)
   - Result: Missing P/B, sector median, etc. are never reflected in coverage

4. **BusinessHealthEngine Metric-Based Counting**
   - Counts successfully DERIVED metrics (revenue_growth, pat_growth, etc.), not available UNDERLYING DATA
   - If derivation fails (division by zero, missing period), coverage drops despite data presence
   - Less severe than others, but still conflates "data existence" with "successful calculation"

### The Ceiling Effect

**Theoretical maximum coverage with current system:**
```
max(business_health) = 100%
max(what_changed) = 100%
max(earnings_quality) = 90%  ← Hard-coded ceiling
max(valuation) = 90%         ← Hard-coded ceiling

average = (100 + 100 + 90 + 90) / 4 = 95%
minus consistency_penalty (-20 if validation fails) = 75%
```

**100% coverage is mathematically impossible** even with perfect data.

---

## The Solution

### Separate Three Concepts

#### 1. Data Coverage (0–100%, honest measurement)
Percentage of expected required data actually available.

```
data_coverage_pct = (available_required_observations / expected_required_observations) * 100
```

Does NOT depend on:
- Whether a derived metric succeeded
- Whether a change was "material"
- Assessment confidence
- Interpretation quality

#### 2. Evidence Quality (High / Medium / Low)
Reliability, recency, provenance of available data.

- **High:** Audited financial statements, < 12 months old
- **Medium:** Quarterly reports, self-reported, 12–24 months old
- **Low:** > 24 months old, secondary sources, unverified

#### 3. Analytical Confidence (High / Medium / Low)
Confidence in the engine's interpretation given available evidence.

- **High:** Clear, unambiguous signal from multiple metrics
- **Medium:** Some ambiguity or conflicting indicators
- **Low:** Weak or limited evidence base

### Key Fixes

#### WhatChangedEngine: Separate Availability from Detection
```python
# BEFORE (buggy)
if growth_rate > 2%:
    available_comparisons += 1  # Only if material change

# AFTER (correct)
comparisons_available += 1  # Count ability to compare
if growth_rate > 2%:
    material_changes.append(...)  # Separately track detection

data_coverage_pct = (comparisons_available / 8) * 100
changes_detected_pct = (len(material_changes) / 8) * 100

# Result: Revenue data existing but growing 0.5% = 100% coverage, 0% detection
```

#### EarningsQualityEngine: Remove Hard-Coded Ceiling
```python
# BEFORE
if all_6_present and no_issues:
    data_coverage = 90  # Hard-coded ceiling

# AFTER
available = count(evidence present)
data_coverage_pct = (available / 6) * 100
# 0, 16.7, 33.3, 50, 66.7, 83.3, or 100
```

#### ValuationContextEngine: Explicit Input Tracking
```python
# BEFORE
if has_current_pe and has_historical_median:
    data_coverage = 90  # Hard-coded

# AFTER
required_inputs = ["current_pe"]
optional_inputs = ["historical_pe_series", "pb_ratio", "roe", "revenue_growth", "sector_median_pe"]
available_required = count(required present)
available_optional = count(optional present)
data_coverage_pct = ((available_required + available_optional) / 6) * 100
# Can reach 100% if all 6 present
```

#### ResearchOrchestrator: Return Three Metrics
```python
# BEFORE
{
    "confidence_score": 64,  # Conflated, confusing
}

# AFTER
{
    "data_coverage": {
        "business_health_pct": 83,
        "what_changed_pct": 50,
        "earnings_quality_pct": 65,
        "valuation_pct": 70,
        "composite_pct": 67,
    },
    "evidence_quality": {
        "business_health": "High",
        "what_changed": "Medium",
        "earnings_quality": "Low",
        "valuation": "Medium",
        "composite": "Medium",
    },
    "analytical_confidence": {
        "business_health": "Medium",
        "what_changed": "Low",
        "earnings_quality": "Medium",
        "valuation": "Medium",
        "overall": "Medium",
    },
}
```

---

## FFC & EFERT Gap Analysis

### FFC Current State
- **Data Coverage:** 64% (average of engines)
- **Missing Critical Data:**
  1. Operating Cash Flow (FY2021–FY2025) — CRITICAL
  2. Historical P/E Series (FY2021–FY2025)
  3. Sector Median P/E
  4. Other Income (FY2025 only)

### EFERT Current State
- **Data Coverage:** 68% (average of engines)
- **Missing Critical Data:**
  1. Operating Cash Flow (FY2021–FY2025) — CRITICAL
  2. Historical P/E Series (FY2021–FY2025)
  3. Sector Median P/E

### Path to 100%

| Task | Effort | Impact |
|------|--------|--------|
| Fix calculation logic (all engines) | 8–10 hours | Enables honest measurement |
| Ingest Operating Cash Flow (5 years) | 4–6 hours | Adds ~20% to composite |
| Calculate Historical P/E (5 years) | 1–2 hours | Adds ~10% to composite |
| Calculate Sector Median P/E | 30 min | Adds ~7% to composite |
| Other Income FY2025 (FFC) | 30 min | Adds ~3% to composite |
| Tests + validation | 2 hours | Prevents regression |

**Total:** ~17–22 hours to reach genuine 100% for both companies with correct formulas

---

## What NOT to Do

❌ **Do not hard-code "100%"** to make the system look better
❌ **Do not fabricate missing OCF** values by deriving from other metrics
❌ **Do not adjust thresholds** to inflate coverage percentages
❌ **Do not rename the metric** to hide the problem

---

## What to Do Next

### Immediate (This Session)
1. ✅ Audit complete (DATA_COVERAGE_AUDIT.md)
2. ✅ Gap matrix complete (FFC_EFERT_COVERAGE_GAP.md)
3. ⏳ Review findings with stakeholders

### Phase 1 (Next 2–3 Days)
1. Implement corrected formulas in all 4 engines
2. Update ResearchOrchestrator to return three separate metrics
3. Add comprehensive test suite
4. Validate FFC/EFERT against expected results

### Phase 2 (Next 1–2 Weeks)
1. Ingest Operating Cash Flow data for both companies
2. Calculate historical P/E series
3. Calculate sector median P/E
4. Run full validation: expect 100% composite coverage

### Phase 3 (Ongoing)
1. Update frontend to display all three metrics clearly
2. Educate users: explain the difference between coverage, quality, and confidence
3. Maintain data integrity: prevent future hard-coded ceilings

---

## Key Principle

> A trustworthy 76% with exact explanation is much more valuable than a fake 100%.

The user deserves to know:
- **What data we have:** Honest data coverage percentage
- **How good it is:** Evidence quality assessment
- **How confident we are:** Analytical confidence in the interpretation
- **What's missing:** Specific gaps in the gap matrix

This builds trust. Hard-coded 100% destroys it.

---

## Affected Files (To Fix)

1. `/d/khronos/psx-fertilizer/backend/app/analysis/business_health.py` — Review metric counting logic
2. `/d/khronos/psx-fertilizer/backend/app/analysis/what_changed.py` — **Critical:** Separate availability from change detection
3. `/d/khronos/psx-fertilizer/backend/app/analysis/earnings_quality_v2.py` — **Critical:** Remove hard-coded ceilings, use transparent formula
4. `/d/khronos/psx-fertilizer/backend/app/analysis/valuation_context.py` — **Critical:** Remove hard-coded ceilings, explicit input tracking
5. `/d/khronos/psx-fertilizer/backend/app/analysis/research_orchestrator.py` — Return three separate metrics
6. `/d/khronos/psx-fertilizer/backend/app/analysis/evidence_context.py` — Ensure output structures support new metrics
7. `/d/khronos/psx-fertilizer/backend/app/etl/financials_ingestion.py` — Add OCF parsing
8. `/d/khronos/psx-fertilizer/backend/app/etl/valuation_ingestion.py` — Add historical P/E calculation
9. `/d/khronos/psx-fertilizer/backend/tests/test_data_coverage.py` — **New:** Comprehensive test suite
10. `/d/khronos/psx-fertilizer/frontend/src/components/research/studio/IntelligenceSnapshot.tsx` — Update to show three metrics

---

## Documents Provided

1. **DATA_COVERAGE_AUDIT.md** — Complete analysis of all four engines, semantic defects, corrected design
2. **FFC_EFERT_COVERAGE_GAP.md** — Detailed gap matrix for both companies, ingestion plan, effort estimates
3. **COVERAGE_REDESIGN_SUMMARY.md** — This document (executive overview)

---

**Ready to proceed with Phase 1 implementation?**
