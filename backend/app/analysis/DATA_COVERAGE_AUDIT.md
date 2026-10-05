# Data Coverage Audit & Redesign

## Current Problem

The system displays "Data coverage: 44%" for FFC, calculated as an average of four engine-specific data_coverage_pct values, with a potential 20-point consistency penalty applied.

**The fundamental issue:** Three separate concepts are conflated into a single "data_coverage_pct" number:
1. **Data Coverage** — Do we actually possess the required data?
2. **Evidence Quality** — How trustworthy/current/source-backed is that data?
3. **Analytical Confidence** — How confident is the engine's interpretation?

## Existing System Analysis

### BusinessHealthEngine (lines 305)
```python
data_coverage = int((available_metrics / 6) * 100)
```
- Expected inputs: revenue, profit_after_tax, gross_profit, net_margin, operating_cash_flow, debt/equity
- **Issue:** Counts successfully *generated* metrics, not available *underlying data*
- A metric derivation failing (e.g., zero division) incorrectly reduces coverage despite data existence
- **Ceiling:** 100% (correct, in this engine)

### WhatChangedEngine (line 241)
```python
coverage = int((available_comparisons / 8) * 100)
```
- Eight expected comparisons: revenue growth, gross margin, finance cost, OCF, AR days, inventory growth, DPS/share, debt/EBITDA
- **Critical Bug:** `available_comparisons` increments ONLY when a material change occurs (>2% for revenue, >50 bps for margins, etc.)
- **Example:** Revenue data exists, is comparable, shows +0.5% growth, but available_comparisons does NOT increment because 0.5% < 2% threshold
- This is counted as "data unavailable" when it should be "data available, no material change"
- **Ceiling:** 100% (but unreachable in practice due to this bug)

### EarningsQualityEngine (lines 171-208)
```python
# Hard-coded ceilings based on evidence count:
if evidence_count < 2 + issues: data_coverage = 45
elif evidence_count < 4 + issues: data_coverage = 65
elif evidence_count >= 4 + issues: data_coverage = 80
elif evidence_count >= 4 + no_issues: data_coverage = 90  # ← CEILING
elif evidence_count >= 2 + OCF + no_issues: data_coverage = 85
elif evidence_count >= 2 + no_OCF + no_issues: data_coverage = 70
else: data_coverage = 40
```
- Expected evidence: OCF, EBIT, other_income, finance_cost, revenue, tax_expense (6 items)
- **Issue:** All six available = 90% coverage, not 100%
- Hard-coded values mix data availability with assessment confidence
- **Ceiling:** 90% (hard-coded, impossible to exceed)

### ValuationContextEngine (line 112)
```python
data_coverage = 90 if historical_median_pe else 70
```
- Expected inputs: current P/E, historical P/E series (5 years), P/B, ROE, revenue growth, sector median P/E
- **Issue:** Only considers P/E data presence, hard-codes 90% max
- Missing: P/B (book value), sector median P/E, revenue growth trend
- **Ceiling:** 90% (hard-coded, unreachable with all inputs present)

### ResearchOrchestrator (line 90)
```python
confidence_score = avg([business_health, what_changed, earnings_quality, valuation]) - consistency_penalty
```
- **Issue:** Names this generic metric "confidence_score" but it conflates three concepts
- Treats all four engines equally, but they measure different things
- Applies 20-point penalty if any cross-engine inconsistency detected
- **Result:** Theoretical max = (100 + 100 + 90 + 90) / 4 = 95%, minus 20 penalty = 75%

## Corrected Design

### Three Separate Concepts

#### 1. Data Coverage (0–100%)
Percentage of *expected required data* actually available.

```python
data_coverage_pct = (available_required_observations / expected_required_observations) * 100
```

**Does not depend on:**
- Whether a derived metric succeeded
- Whether a comparison showed material change
- Assessment confidence or quality judgment

**Example:**
- Expected: [revenue, pat, gross_profit, operating_cash_flow, debt, equity] = 6 fields
- Available: [revenue✓, pat✓, gross_profit✗, ocf✓, debt✓, equity✓] = 5 fields
- Coverage = (5/6) * 100 = 83%

#### 2. Evidence Quality (High / Medium / Low, or 0–100)
Reliability, recency, provenance of the available data.

- **High:** Audited financial statements (PSX filings), recent (< 12 months)
- **Medium:** Quarterly data, self-reported, or 12–24 months old
- **Low:** Data > 24 months old, derived from secondary sources, unverified

#### 3. Analytical Confidence (High / Medium / Low, or 0–100)
Confidence in the engine's *interpretation* given the available evidence.

- **High:** Clear, unambiguous signal from multiple metrics
- **Medium:** Some ambiguity or conflicting indicators
- **Low:** Weak or limited evidence base

### Corrected Engines

#### BusinessHealthEngine
```python
expected_metrics = {
    "revenue": "required",
    "profit_after_tax": "required",
    "gross_profit": "optional",
    "operating_cash_flow": "optional",
    "total_debt": "optional",
    "total_equity": "optional",
}

available = count(metrics present in latest aligned period)
expected_required = count of required metrics = 2
data_coverage_pct = (available / 6) * 100  # All 6 treated equally

evidence_quality = "High" if all_audited and recent else "Medium" if mostly_recent else "Low"

# Separately track analytical confidence
analytical_confidence = "High" if len(metrics) >= 4 and consistent else "Medium" if len(metrics) >= 3 else "Low"
```

#### WhatChangedEngine
**CRITICAL FIX:** Separate "data available" from "material change detected"

```python
# Track BOTH
comparisons_available = 0  # Counts whether we CAN perform the comparison
material_changes_detected = 0  # Counts whether change exceeded threshold

# For each comparison:
if data_exists:  # Revenue data exists?
    comparisons_available += 1  # Data AVAILABLE for comparison
    
    if abs(growth_rate) > THRESHOLD:  # Did it change materially?
        material_changes_detected += 1  # Change DETECTED
        positive_or_negative.append(...)

# Coverage depends on availability, NOT change detection
data_coverage_pct = (comparisons_available / 8) * 100
change_detected_pct = (material_changes_detected / 8) * 100

# Return both
{
    "data_coverage_pct": data_coverage_pct,  # Can we do the comparison?
    "changes_detected_pct": change_detected_pct,  # Did anything change?
    "analytical_confidence": "High" if material_changes_detected >= 3 else "Medium" if >= 2 else "Low"
}
```

#### EarningsQualityEngine
```python
expected_evidence = [
    "operating_cash_flow",
    "operating_profit",
    "other_income",
    "finance_cost",
    "revenue",
    "tax_expense",
]

available = count(evidence present for aligned period)
data_coverage_pct = (available / 6) * 100  # 0, 16.7, 33, 50, 66.7, 83.3, or 100

# Assessment confidence is separate
analytical_confidence = "High" if available >= 4 and no_issues else "Medium" if >= 2 else "Low"
```

#### ValuationContextEngine
```python
required_inputs = {
    "current_pe": "critical",
    "historical_pe_series": "important",  # 5-year median
}

optional_inputs = {
    "pb_ratio": "useful",
    "roe": "useful",
    "revenue_growth": "useful",
    "sector_median_pe": "useful",
}

available_required = count(required inputs)
available_optional = count(optional inputs)
expected_required = 1  # At minimum, need current P/E
expected_total = 6  # All six

if available_required == 0:
    data_coverage_pct = 0
    status = "insufficient_data"
else:
    # (required_present + optional_present) / expected_total * 100
    data_coverage_pct = ((available_required + available_optional) / expected_total) * 100

analytical_confidence = "High" if available_required >= 1 and available_optional >= 2 else "Medium" if >= 1 else "Low"
```

### ResearchOrchestrator
```python
# Return SEPARATE metrics, not conflated
result = {
    "data_coverage": {
        "business_health_pct": ...,
        "what_changed_pct": ...,
        "earnings_quality_pct": ...,
        "valuation_pct": ...,
        "composite_pct": average of above
    },
    "evidence_quality": {
        "business_health": "High" | "Medium" | "Low",
        "what_changed": ...,
        "earnings_quality": ...,
        "valuation": ...,
        "composite": "High" if all >= High, "Medium" if any >= Medium, else "Low"
    },
    "analytical_confidence": {
        "business_health": "High" | "Medium" | "Low",
        "what_changed": ...,
        "earnings_quality": ...,
        "valuation": ...,
        "overall": aggregate based on strength of signals
    },
    # Deprecated (for backward compatibility, with clear marking)
    "confidence_score_deprecated": "This mixes data coverage, evidence quality, and analytical confidence. Do not use for new features."
}
```

## Theoretical Coverage

Once corrected:

**Maximum possible composite data coverage (all 4 engines at 100%):**
```
(100 + 100 + 100 + 100) / 4 = 100%
```

**With missing one optional metric across the system:**
```
Valuation missing sector_median_pe: (100 + 100 + 100 + 83.3) / 4 = 95.8%
```

**With missing one required metric (e.g., no OCF for earnings quality):**
```
Earnings missing OCF: (100 + 100 + 83.3 + 100) / 4 = 95.8%
```

## Implementation Roadmap

1. ✅ Audit complete (THIS FILE)
2. Fix BusinessHealthEngine — measure underlying data availability
3. Fix WhatChangedEngine — separate comparisons_available from changes_detected
4. Fix EarningsQualityEngine — remove hard-coded ceilings, calculate transparent coverage
5. Fix ValuationContextEngine — explicit input tracking, remove hard-coded ceilings
6. Fix ResearchOrchestrator — return three separate metrics
7. Update Overview frontend to show:
   - Data coverage (by engine)
   - Evidence quality (by engine)
   - Analytical confidence (overall)
8. Add tests proving correct behavior
9. Generate FFC/EFERT gap reports
10. Ingest missing data to reach genuine 100%

## Testing Strategy

```python
# MUST PASS
def test_complete_dataset_equals_100_percent():
    """With all required metrics, coverage = 100%."""
    assert business_health_coverage == 100
    assert earnings_quality_coverage == 100
    # etc.

def test_missing_optional_metric_reduces_coverage():
    """Remove one optional input, coverage < 100%."""
    # e.g., remove operating_cash_flow
    assert coverage < 100
    assert coverage > 95

def test_unchanged_metric_still_counts_as_available():
    """Revenue exists, grows 0.5% (immaterial change), but is STILL available."""
    # WhatChangedEngine must count this as a comparison it COULD perform
    assert comparisons_available >= 1
    assert material_changes_detected == 0  # No material change
    
def test_analysis_confidence_independent_of_data_coverage():
    """High data coverage with conflicting signals = low analytical confidence."""
    # All data present but metrics disagree on health
    assert data_coverage_pct == 100
    assert analytical_confidence == "Low"

def test_no_synthetic_data():
    """Coverage never exceeds 100%, never hard-coded."""
    # Never seed missing values to inflate coverage
    # Never hard-code "90%" because that's "good enough"
    pass
```

---

**Next Step:** Review this document, then implement fixes in order.
