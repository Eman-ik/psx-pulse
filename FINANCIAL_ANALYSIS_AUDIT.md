# Financial Analysis Audit — October 3, 2026

**Overall Assessment:** 7/10 software, 4.5/10 investment-analysis trustworthiness

**Current Bottleneck:** Domain correctness, not architecture

---

## Critical Issues (Must Fix Before Feature Work)

### 🔴 1. Scope Destruction in ResearchContext
**Problem:** Database preserves `scope` (consolidated | standalone), but `_load_metrics()` reduces it to just `(metric, period_end, value)`. One silently overwrites the other.

**Impact:** A perfectly polished wrong analysis. No `insufficient_data` flag.

**Example:**
```
FFC 2026-06-30:
  consolidated: revenue = 100
  standalone:   revenue = 80
  
Result: One of them wins based on row order
```

**Fix Required:**
- Analytical key: `(metric, period_end, period_type, scope)`
- Explicit preferred scope (consolidated → standalone fallback)
- No cross-scope mixing
- Add scope conflict detection to validation

---

### 🔴 2. WhatChangedEngine Live Bugs

#### Bug 1: Negative Growth Classified as Positive
```python
growth_latest = (rev_latest - rev_prior) / rev_prior
positive.append(f"Revenue growth reached {growth_latest:.1%}.")
```

When revenue falls 100→80:
```
"Positive changes: Revenue growth reached -20.0%."
```

**Fix:** Branch logic:
```python
if growth > THRESHOLD:
    positive.append(...)
elif growth < -THRESHOLD:
    negative.append(...)
```

#### Bug 2: period_type Hardcoded to "Q" After FY Fallback
Code explicitly falls back from Q to FY, but response always returns:
```python
result["period_type"] = "Q"
```

**Fix:**
```python
result["period_type"] = period_type  # Use the variable
```

#### Bug 3: Missing Growth Acceleration Logic
Engine claims "Revenue growth accelerated from 8% to 17%" but only has 2 periods.
Need at least 3 for acceleration.

---

### 🔴 3. Period Duration Semantics Not Distinguished

**Problem:** No distinction between:
- Discrete quarter (Q3 2025)
- Cumulative YTD (9M 2025)
- Annual (FY 2025)

**Impact:** Revenue/PAT/OCF comparisons can be economically wrong.

**Example:**
```
Jun revenue = 55  (6M cumulative)
Sep revenue = 90  (9M cumulative)

Current: (90-55)/55 = 63.6% "growth"
Actual Q3 = 90-55 = 35 discrete revenue
```

**Data Model Needed:**
```python
FinancialFact:
  duration_basis:
    - discrete
    - ytd
    - annual
    - point_in_time
```

---

### 🔴 4. BusinessHealth Unsupported Narrative Claims

**Example 1:** "Revenue expanded for three consecutive periods"
```python
if len(fy_trend) >= 3 and latest_growth > 0:
    # claim expansion
```

But that doesn't verify: 110 > 90 > 130 > 100. Those are not consecutive increases.

**Example 2:** "Operating cash flow remains above reported earnings"
```python
if ocf_growth is not None:  # Doesn't actually check OCF > PAT
```

**Fix:** Rewrite all narratives to assert only what calculations actually verify.

---

## High-Priority Issues

### 🟠 5. Earnings Quality Too Heuristic
Current rules:
```
OCF > PAT × 1.1 → positive
OCF < PAT × 0.7 → issue
Other income > 25% PAT → issue
```

These are signals, not conclusions. Need multi-period:
- 3–5Y cumulative OCF / PAT
- Accrual ratio trend
- CFO conversion ratio
- Receivable days trend
- Inventory days trend

### 🟠 6. Red Flags Scale Poorly on Negative Revenue
```python
if ar_growth > rev_growth * 1.3:
    # Flag: AR growing faster than sales
```

When revenue falls -20% and AR falls -5%:
```
-5% > -26%  → True → triggers flag
```

But AR actually fell. Misleading.

**Fix:** Use spread logic:
```python
ar_growth - revenue_growth > X_bps
# with separate handling for revenue < 0
```

### 🟠 7. Business Health Leverage Logic Incomplete
```python
if de_latest > de_prior:
    trend = "Deteriorating"
```

No case for "Improving" from leverage reduction. Also uses absolute debt, not ratios.

Should calculate and trend:
- Debt / Equity
- Debt / EBITDA  
- Net Debt / EBITDA
- Interest coverage

---

## Testing Strategy

**Current:** Architectural consistency (Overview ≈ Intelligence). ❌ Insufficient.

**Needed:** Golden financial fixtures proving accounting correctness.

### Test 1: Known-Answer Case
```python
# Create fake company with exact known values
FY22 Revenue = 100
FY23 Revenue = 120
FY24 Revenue = 150
PAT = 10 → 9 → 18
OCF = 9 → 4 → 22

# Assert exact engine conclusions
assert engine.business_health == "Strengthening"
assert engine.earnings_quality == "Recovering"
```

### Test 2: Pathological Cases
- Negative PAT
- Negative revenue growth
- OCF crossing zero
- Zero dividend prior year
- Consolidated + standalone same date
- Q vs FY same date
- YTD quarterly data
- Restated financials
- Zero EBIT
- Negative equity

---

## Remediation Roadmap

| Priority | Issue | Files | Complexity | Est. Time |
|----------|-------|-------|------------|-----------|
| 1 | Fix WhatChanged bugs | what_changed.py | Low | 30 min |
| 2 | Add scope-aware aggregation | research_context.py, _load_metrics() | High | 2 hrs |
| 3 | Implement period duration semantics | period_alignment.py | High | 3 hrs |
| 4 | Rewrite BusinessHealth narratives | business_health.py | Medium | 1.5 hrs |
| 5 | Build golden test fixtures | test_financial_correctness.py | High | 4 hrs |
| 6 | Fix EarningsQuality multi-period | earnings_quality.py | Medium | 2 hrs |
| 7 | Fix RedFlags spread logic | red_flag_engine.py | Low | 1 hr |

**Total before feature work:** ~14 hours

---

## Why This Order

1. **WhatChanged bugs** are live and causing wrong classifications today
2. **Scope destruction** is silent and dangerous; fixing it enables correct prioritization later
3. **Period semantics** blocks all growth comparisons from being trustworthy
4. **Narratives** must be stripped of unsupported claims before any output is public
5. **Golden fixtures** provide the foundation for all future testing

---

## Next Phase: Financial Semantics v2

Once critical issues are fixed:
1. Scope-aware analysis (consolidated > standalone)
2. Period-duration normalization (discrete → YTD → annual)
3. Comparable-period selection logic (YoY, TTM, trend)
4. Accounting-derived ratios (proper interest coverage, FCF conversion, etc.)
5. Multi-period earnings quality (3–5Y cumulative, accrual ratio, tax rate)
6. Leverage ratios (Debt/Equity, Debt/EBITDA, Interest coverage)
7. Receivable/inventory trend analysis

---

## Confidence Trajectory

| Phase | Software | Accounting | Status |
|-------|----------|-----------|--------|
| Before audit | 6/10 | 4/10 | Contradictory |
| Post-architecture cleanup | 8/10 | 4.5/10 | Respectable but weak |
| After critical fixes | 8/10 | 6/10 | Trustworthy baseline |
| After Financial Semantics v2 | 8.5/10 | 8/10 | Professional-grade |

---

## Philosophy Shift

**Before:** "I have sparse financial data + Python rules → institutional conclusions"

**After:** "I know exactly what this number represents, which filing it came from, whether it is consolidated, which comparable period is economically correct, and therefore which conclusions the evidence permits."

**This distinction is everything.**
