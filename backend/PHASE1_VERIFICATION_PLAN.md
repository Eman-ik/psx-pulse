# Phase 1: Verification and Re-Measurement Plan

**Goal:** Verify semantic fixes are correct, then re-measure actual FFC/EFERT coverage with corrected formulas.

**Do NOT:**
- Build new ingestion pipelines
- Attempt to force FFC/EFERT to 100%
- Assume the current gap matrix is final
- Create derived data (historical P/E, sector median) before knowing what's missing

---

## Step 1: Verify Phase 1 Formula Fixes Are Correct

### 1a. WhatChangedEngine
**Requirement:** Separate `comparisons_available` from `material_changes_detected`

**Current state:** ✅ Implemented
- Line 32: `comparisons_available = 0  # Can we perform the comparison?`
- Line 33: `material_changes_detected = 0  # Did something change materially?`
- Line 67: Increment `comparisons_available` for revenue (ALWAYS, not just on material change)
- Line 252: `data_coverage = (comparisons_available / 8) * 100` ✅

**Test case needed:** Revenue grows 0.5% (immaterial) → must count as "available"

### 1b. EarningsQualityEngine
**Requirement:** Remove hard-coded ceilings (40, 45, 65, 70, 80, 85, 90)

**Current state:** ✅ Implemented
- Line 168: `data_coverage = (evidence_count / 6) * 100` ✅ 
- No hard-coded 90% ceiling
- Supports 0%, 16.7%, 33.3%, 50%, 66.7%, 83.3%, 100%

**Test case needed:** All 6 evidence items present → must equal 100%, not 90%

### 1c. ValuationContextEngine
**Requirement:** Remove hard-coded 0/70/90 ceilings; track inputs explicitly

**Current state:** ✅ Implemented
- Line 34: `expected_inputs = 6`
- Line 35: `available_inputs = 0`
- Lines 54-63: Count available inputs explicitly
- Line 121: `data_coverage = (available_inputs / expected_inputs) * 100` ✅
- No hard-coded ceiling

**Test case needed:** 5 of 6 inputs present → 83.3%, not 90%

### 1d. ResearchOrchestrator
**Requirement:** Separate data_coverage_pct, evidence_quality, analytical_confidence

**Current state:** ✅ Implemented
- Line 83-89: Calculate `data_coverage_pct` from engine averages
- Line 96-101: Calculate `evidence_quality` (High/Medium/Low)
- Line 105-118: Calculate `analytical_confidence` (High/Medium/Low)
- Line 123: Deprecated `confidence_score` for backward compat

**Test case needed:** High coverage + low confidence possible (conflicting signals)

---

## Step 2: Run Phase 1 Tests

```bash
# Test suite created for Phase 1 verification
pytest tests/test_data_coverage_corrected.py -v
```

Expected: All 9 test cases pass
- Immaterial revenue change counted as available ✅
- Complete data = 100% coverage (no ceiling) ✅
- Missing metrics reduce coverage proportionally ✅
- No hard-coded ceilings ✅
- Three metrics properly separated ✅

---

## Step 3: Re-Measure Actual Coverage (Database-Backed)

### 3a. Prepare measurement script
- Created: `scripts/remeasure_coverage.py`
- Runs corrected engines on real FFC/EFERT data
- Outputs:
  - Actual coverage % for each engine
  - Available metrics in database
  - Truly missing raw inputs (not derived, not misnamed)

### 3b. Run measurement
```bash
python scripts/remeasure_coverage.py
```

Expected output format:
```
COVERAGE MEASUREMENT: FFC
==================================================
COMPOSITE COVERAGE:
  Data Coverage:       XX%  (was 64%, now should be higher)
  Evidence Quality:    Medium/High
  Analysis Confidence: Medium/High

PER-ENGINE BREAKDOWN:
  business_health              XX%
  what_changed                 XX%
  earnings_quality             XX%
  valuation_context            XX%

AVAILABLE FINANCIAL INPUTS:
  revenue                      5 periods
  profit_after_tax             5 periods
  gross_profit                 4 periods
  operating_profit             0 periods   <- MISSING
  ...
```

---

## Step 4: Identify Real Gaps (After Re-Measurement)

**Gap categories:**

### A. Truly Missing Raw Data
- Not in database under any name
- Cannot be derived from existing fields
- **Example:** Operating cash flow (if not present at all)

### B. Metrics Present Under Different Names
- In database but under different canonical key
- Requires mapping, not ingestion
- **Example:** "operating_activities_cash_flow" vs "operating_cash_flow"
- **Check:** `identify_missing_inputs()` in remeasure script

### C. Derivable Data
- Can be calculated from existing fields
- **Do NOT ingest** — calculate on-demand
- **Examples:**
  - Historical P/E = Historical EPS ÷ Historical Price (both available)
  - Sector Median P/E = Median(Company P/Es) from peer universes
  - Cash Flow ratios = OCF ÷ Other metrics

### D. Missing Periods (Not Missing Metrics)
- Metric exists for some years but not others
- Extend ingestion of existing metrics, not new pipeline
- **Example:** Revenue for 2020–2023 but not 2024–2025

---

## Step 5: Report Findings

After re-measurement, produce new gap matrix:

| Input | Status | Location | Action |
|-------|--------|----------|--------|
| Revenue | ✅ Available | financial_fact.revenue (FY2020–2023) | Extend to 2024–2025 if needed |
| Operating Cash Flow | ❌ Missing | Not in database | Check if named differently first |
| Other Income | ❌ Missing | Not in database | Extract from annual reports |
| EPS | ? Status TBD | Check financial_fact | May exist as dividend_per_share equivalence |
| Historical P/E | 🔄 Derivable | (EPS + Price in DB) | Calculate on-demand, do NOT ingest |
| Sector Median P/E | 🔄 Derivable | (P/E from multiple issuers) | Calculate on-demand |

---

## What This Produces

**Before this process:**
- Assumptions about gaps (may be wrong)
- Premature ingestion pipelines (may be unnecessary)
- Inflated view of what's missing

**After this process:**
- Verified actual coverage with corrected semantics
- Clear list of truly missing raw inputs
- Identified which inputs are already in DB under different names
- Identified which "gaps" are just derived metrics

---

## Timeline

1. **Verify Phase 1 formulas** (15 min) — Review code, run tests
2. **Run re-measurement script** (10 min) — Execute against live database
3. **Analyze output** (30 min) — Identify real vs. derived vs. misnamed gaps
4. **Report findings** (20 min) — Document what's truly missing

**Total:** ~1 hour to answer "what's actually missing?"

Then, and only then, build ingestion for truly missing items.

---

## Expected Outcome

The semantic fix (removing hard-coded ceilings, separating metrics) will likely:
- Move FFC from 64% → **high 70s%** (10+ point jump)
- Move EFERT from 68% → **high 70s–low 80s%** (10+ point jump)

This alone may reduce the remaining gaps to 2–3 raw inputs instead of 10+.

**Hypothesis:** The gap matrix was inflated because the broken formulas conflated multiple problems. The real gaps are much smaller.
