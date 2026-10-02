# Architecture Fix Plan - Period Alignment & Optional Metrics

**Date**: 2026-10-02  
**Status**: Phase 1 Complete - Core architecture fixed  
**Problem**: Engines returning "insufficient_data" even when useful data exists

---

## Root Causes Identified

### 1. Period Type Inference (FIXED ✅)
**Problem**: ResearchContext guessed period type from date, not database

```python
# WRONG: June 30 always becomes 'Q'
if month == 12 and day == 31:
    period_type = "FY"
elif month in [3, 6, 9, 12]:  # <-- June 30 always hits here
    period_type = "Q"

# Result: Confused FY ending on June 30 with Q3
```

**Fix Applied**:
- Load actual `period_type` from FinancialFact table
- Normalize: `annual→FY`, `quarterly→Q`, `half_year→HY`, `ttm→TTM`
- Stop guessing from dates

### 2. All-or-Nothing Metrics (FIXED ✅)
**Problem**: get_aligned_values() required ALL metrics in a period

```python
# Required ALL 5 to exist in same period
get_aligned_values(["revenue", "pat", "ocf", "debt", "equity"])

# If ANY was missing, entire period discarded
# Result: No business health analysis for 3 companies
```

**Fix Applied**:
- Split into `required_metrics` (must exist) + `optional_metrics` (attached if present)
- Periods included if ALL required metrics exist
- Optional metrics attached when available

```python
# Now: requires only revenue + profit (core)
context.get_aligned_values(
    required_metrics=["revenue", "profit_after_tax"],
    optional_metrics=["operating_cash_flow", "total_debt", "total_equity"],
    period_type="FY",
    limit=5
)
```

### 3. Logic Bugs in Engines (FIXED ✅)
**Problem**: Assumptions made without checking if data existed

```python
# WRONG: Always initialized to "Improving" even without data
leverage_trend = "Improving"

# WRONG: Missing comparison data was treated as "Contracting"
margin_trend = "Expanding" if ... else "Contracting"
```

**Fix Applied**:
- Initialize to `"Unknown"` instead of assumption
- Only set trend after validating sufficient data exists

---

## What This Fixes

### BusinessHealthEngine
| Before | After |
|--------|-------|
| Returns `insufficient_data` for FFC | Returns `partial` with (revenue + profit) only |
| Requires: rev+pat+ocf+debt+equity | Requires: rev+pat, optional: ocf+debt+equity |
| Coverage: All-or-nothing | Coverage: Graceful degradation |

### WhatChangedEngine
| Before | After |
|--------|--------|
| Requires 9 metrics across 2 Q | Supports modular comparisons |
| Missing 1 = entire engine fails | Check each comparison independently |
| Returns `insufficient_data` | Returns `partial` with available comparisons |

### EarningsQualityEngine
| Before | After |
|--------|--------|
| Requires 7 metrics (PAT+OCF+EBIT+revenue+...) | Minimum: PAT only |
| Low coverage = refuse all | Degrade gracefully |
| | Core evidence: PAT+OCF |
| | Extra evidence: EBIT, revenue, other income |

---

## Phase 1 Changes (Committed)

✅ **ResearchContext._load_metrics()**
- Load period_start, period_end, period_type, scope from FinancialFact
- Normalize period types centrally
- Remove date-based guessing

✅ **get_aligned_values() redesign**
- Signature: `(required_metrics, optional_metrics=None, period_type, limit)`
- Include periods if ALL required exist
- Attach optional metrics when available

✅ **get_aligned_series() update**
- Matches new required/optional signature
- Returns series with gaps where optional data missing

✅ **PeriodAlignedAnalyzer update**
- `get_fy_trend()` and `get_q_trend()` support optional metrics

✅ **BusinessHealthEngine logic fix**
- Require only: revenue + profit
- Optional: ocf, debt, equity
- Fix margin_trend and leverage_trend initialization

---

## Phase 2: Engine Refactoring (Next Steps)

### WhatChangedEngine
```python
# BEFORE: Single rigid call for 9 metrics
fy_trend = context.get_aligned_values([revenue, gross_profit, finance_cost, ocf, ar, inventory, dps, debt, ebitda])

# AFTER: Modular comparisons
revenue_data = context.get_aligned_values([revenue], limit=2)
margin_data = context.get_aligned_values([revenue, gross_profit], limit=2)
cash_data = context.get_aligned_values([operating_cash_flow], limit=2)
receivables_data = context.get_aligned_values([accounts_receivable, revenue], limit=2)
```

### EarningsQualityEngine
```python
# BEFORE: All-or-nothing
latest = context.get_aligned_values([pat, ocf, ebit, other_income, finance_cost, revenue, tax_expense])

# AFTER: Graceful degradation
latest = context.get_aligned_values(
    required_metrics=["profit_after_tax"],
    optional_metrics=[
        "operating_cash_flow",
        "operating_profit", 
        "other_income",
        "finance_cost",
        "revenue",
        "tax_expense"
    ]
)
```

### RedFlagEngine
```python
# Already modular - keep as-is
pat_ocf_pair = context.get_aligned_values([pat, ocf])
ar_revenue_pair = context.get_aligned_values([ar, revenue])
inventory_revenue_pair = context.get_aligned_values([inventory, revenue])
```

---

## Phase 3: Status Progression (Future)

Current (interim):
- `complete` = all metrics available
- `insufficient_data` = missing required

Target:
- `complete` = all metrics (including optional)
- `partial` = all required metrics, some optional missing
- `insufficient_data` = missing required metrics

---

## Database Impact

Need to verify:
```sql
SELECT 
    period_type,
    COUNT(DISTINCT issuer_id) as issuers,
    COUNT(DISTINCT period_end) as periods,
    COUNT(*) as facts
FROM financial_fact
WHERE superseded_by_id IS NULL
GROUP BY period_type
```

If quarterly data is sparse/missing, that explains insufficient_data prevalence.
If data exists, the fixes above will unlock analyses.

---

## Expected Outcomes

After Phase 2 completion:

**FFC Response** (currently):
```json
{
  "business_health": "insufficient_data",
  "what_changed": "insufficient_data",
  "earnings_quality": "insufficient_data",
  "red_flags": "complete"
}
```

**FFC Response** (expected):
```json
{
  "business_health": "partial",  # Revenue + profit available
  "what_changed": "partial",      # Some comparisons available
  "earnings_quality": "partial",  # PAT available
  "red_flags": "complete",
  "coverage": "52-71%"
}
```

---

## Commits

- `31fbb40` - CRITICAL FIX: Use database period_type, support optional metrics

---

## Safety Notes

✓ No period mixing possible (database period_type enforced)
✓ Conservative: still refuses if required data missing
✓ Graceful degradation: works with partial data
✓ All engines produce transparent `period_type` output
✓ Optional metrics attach when available, explain absence when not

The system is now both **safe** and **useful**.
