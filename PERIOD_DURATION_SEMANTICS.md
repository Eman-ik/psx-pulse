# Period Duration Semantics — Discrete vs YTD/Cumulative Quarterly Data

**Status:** Implementation Phase 1 (infrastructure in place, ingestion normalization pending)  
**Date:** 2026-10-03

---

## The Problem

Pakistani financial statements often report quarterly figures in two different ways:

### Discrete Quarter (Q3 only)
```
Q1 revenue = 25
Q2 revenue = 30  (Q2 only, not 6M cumulative)
Q3 revenue = 35  (Q3 only, not 9M cumulative)

YoY comparison: 35 vs prior-year Q3 (40) = -12.5% decline
```

### Cumulative/YTD Quarter (9M, 6M, 3M)
```
Jun revenue = 55  (6M cumulative: Q1 + Q2)
Sep revenue = 90  (9M cumulative: Q1 + Q2 + Q3)

Naive calculation: (90-55)/55 = 63.6% "growth"
Actual Q3 discrete: 90 - 55 = 35
```

**Impact:** Without distinguishing duration basis, growth comparisons are economically wrong.

---

## The Solution: `duration_basis` Field

Added to `FinancialFact` schema:

```sql
ALTER TABLE financial_fact ADD COLUMN duration_basis VARCHAR(20) DEFAULT 'discrete';
```

**Valid values:**
- `discrete` — Single quarter/period (Q3 only, not cumulative)
- `ytd` — Year-to-date cumulative (9M, 6M, 3M)
- `point_in_time` — Balance sheet items (assets, liabilities, equity)

---

## Implementation Status

### ✅ Phase 1: Infrastructure (COMPLETE)
- [x] Added `duration_basis` column to FinancialFact model
- [x] Updated ResearchContext to load and track duration_basis
- [x] Created PeriodDurationDetector for automatic detection
- [x] Created PeriodDurationNormalizer for conversion
- [x] Added conflict detection (logs mixed duration_basis in same period)
- [x] Added get_duration_basis() method to ResearchContext

### ⏳ Phase 2: Ingestion Normalization (PENDING)
- [ ] Auto-detect duration basis during ingestion
- [ ] Normalize YTD figures to discrete equivalent
- [ ] Store detection confidence

### ⏳ Phase 3: Analytical Integration (PENDING)
- [ ] Update WhatChangedEngine to reject mixed-duration comparisons
- [ ] Update BusinessHealthEngine to validate duration consistency
- [ ] Add warnings when comparing mixed durations
- [ ] Implement TTM (trailing twelve months) for better YoY comparisons

---

## Architecture

```python
# Database stores duration_basis with every fact
FinancialFact:
  period_end: 2025-09-30
  period_type: "Q"
  duration_basis: "ytd"  # This is 9M cumulative
  value: 90_000_000

# ResearchContext now tracks:
self._duration_bases[date(2025, 9, 30)] = "ytd"

# Engines can now check:
if context.get_duration_basis(period_end) == "ytd":
    # Handle YTD data (convert to discrete or reject comparison)
```

---

## Detection Logic

### Automatic Detection (PeriodDurationDetector)

**Point-in-time metrics** (always):
- Balance sheet items: total_assets, accounts_receivable, inventory, total_debt, equity, etc.

**Flow metrics** (detected by pattern):
- If values monotonically increase across quarters → likely YTD cumulative
- If values vary randomly → likely discrete quarterly
- Threshold: 70% increase ratio → YTD; otherwise discrete

### Example Detection
```python
quarters = [
    (2025-03-31, 25),  # Q1
    (2025-06-30, 55),  # 6M (25+30)
    (2025-09-30, 90),  # 9M (25+30+35)
]

# Pattern: 25 < 55 < 90 (monotonic)
# Conclusion: duration_basis = "ytd"
```

---

## Normalization

### Converting YTD to Discrete

```python
# If we know:
# - 9M revenue = 90
# - 6M revenue = 55

# Then Q3 discrete = 90 - 55 = 35
discrete_q3 = ytd_current - ytd_prior
```

### When to Normalize
- Only for flow metrics (income statement, cash flow)
- Only when converting YTD to discrete for analysis
- Never modify stored values (keep source truth)

---

## Conflict Detection

When database contains mixed duration_basis for same period:

```
[ResearchContext] Duration basis mismatches (mixed discrete/YTD in same period):
  revenue on 2025-09-30: mixed duration_basis (ytd vs discrete)
  profit_after_tax on 2025-09-30: mixed duration_basis (ytd vs discrete)
```

**Possible causes:**
- Different reporting methods across metrics
- Data entry error
- Company changed reporting convention

**Current handling:** Logs conflict, uses first encountered basis

---

## Next Steps

### Before Using for Analysis

1. **Database Migration**
   ```bash
   alembic revision --autogenerate -m "Add duration_basis to financial_fact"
   alembic upgrade head
   ```

2. **Ingestion Enhancement**
   - Implement automatic YTD detection in data loader
   - Tag each metric with detected duration_basis
   - Log detection confidence

3. **Engine Updates**
   - WhatChangedEngine: Reject quarterly-to-quarterly without same duration_basis
   - BusinessHealthEngine: Validate all metrics in period use same duration
   - RedFlagEngine: Convert YTD to discrete before ratio calculations

### Backward Compatibility
- Default `duration_basis = "discrete"` for existing data
- Engines work with or without duration_basis field
- Warnings logged if duration basis unknown

---

## Code Examples

### In Engines

```python
# BusinessHealthEngine
def analyze(context: ResearchContext):
    fy_trend = context.get_fy_trend(
        required_metrics=["revenue", "profit_after_tax"]
    )
    
    for period_data in fy_trend:
        period_end = period_data["period_end"]
        basis = context.get_duration_basis(period_end)
        
        if basis == "ytd":
            # For FY, should never be YTD (FY is always annual)
            # Log warning if encountered
            pass
        elif basis == "discrete":
            # Safe to use for growth calculations
            pass
```

### In Validators

```python
# Ensure period consistency
def validate_period_comparison(context, metric1_date, metric2_date):
    basis1 = context.get_duration_basis(metric1_date)
    basis2 = context.get_duration_basis(metric2_date)
    
    if basis1 != basis2:
        return False, f"Cannot compare {basis1} to {basis2}"
    
    return True, ""
```

---

## Key Principle

**Never compare metrics with different duration bases.**

- Discrete Q3 vs Discrete Q3 (prior year) → ✅ Valid
- YTD 9M vs YTD 9M (prior year) → ✅ Valid (if endpoints match)
- Discrete Q3 vs YTD 9M → ❌ Invalid (economically wrong)
- FY2025 vs Q3 2025 → ❌ Invalid (different period types)

---

## Testing

### Unit Tests (period_duration.py)

```python
def test_detect_ytd_from_monotonic_increase():
    """Increasing quarterly values indicate YTD cumulative."""
    quarters = [
        (date(2025, 3, 31), 25),
        (date(2025, 6, 30), 55),
        (date(2025, 9, 30), 90),
    ]
    assert PeriodDurationDetector.detect_duration("revenue", "Q", quarters) == "ytd"

def test_detect_discrete_from_variance():
    """Random variance indicates discrete quarters."""
    quarters = [
        (date(2025, 3, 31), 25),
        (date(2025, 6, 30), 18),
        (date(2025, 9, 30), 32),
    ]
    assert PeriodDurationDetector.detect_duration("revenue", "Q", quarters) == "discrete"
```

---

## Summary

**What's in place:**
- ✅ `duration_basis` field in database schema
- ✅ ResearchContext tracks and exposes duration_basis
- ✅ Conflict detection for mixed durations
- ✅ Detection logic (automatic pattern-based)
- ✅ Normalization utilities (YTD → discrete conversion)

**What's next:**
- Ingestion enhancement (automatic tagging)
- Engine integration (validation + safe comparisons)
- TTM calculation for better annual comparisons
- Analyst transparency (show duration basis in UI)

**Impact when complete:**
- Eliminates economically wrong quarterly comparisons
- Foundation for TTM-based analysis
- Enables point-in-time backtesting accuracy
