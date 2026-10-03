# Financial Semantics V2 — Status Report

**Date:** 2026-10-03  
**Overall Status:** 60% Complete (Infrastructure phase)  
**Ready for:** Phase 2 ingestion normalization

---

## Completed (Phase 1)

### 🟢 1. Critical Bug Fixes ✅
- **WhatChangedEngine**: Negative revenue classification (was: positive, now: negative)
- **WhatChangedEngine**: period_type accuracy (was: hardcoded "Q", now: actual period type)
- **BusinessHealthEngine**: Unsupported narrative validation (OCF claims now verified)
- **Commit**: 214e05a

### 🟢 2. Scope-Aware Aggregation ✅
- **Problem**: Consolidated + standalone financials mixed silently
- **Solution**: Scope preserved, conflicts detected, consolidated preferred
- **Impact**: No silent data loss; analyst visibility into scope conflicts
- **Commit**: 5147c35

### 🟢 3. Period Duration Infrastructure ✅
- **Database**: Added `duration_basis` field (discrete | ytd | point_in_time)
- **Detection**: Automatic pattern analysis (70% monotonic increase = YTD)
- **Tracking**: ResearchContext now tracks duration_basis by period
- **Validation**: Conflict detection for mixed-duration periods
- **Commit**: 4f2bc61

---

## In Progress (Phase 2)

### 🟡 4. Period Duration Ingestion Normalization (PENDING)
**What's needed:**
- Auto-detect duration_basis when loading facts from PSX filings
- Tag each FinancialFact with detected basis (discrete vs ytd)
- Store detection confidence
- Normalize YTD figures to discrete for downstream engines

**Why it matters:**
```
Without: Jun=55 (6M), Sep=90 (9M) → Engine: (90-55)/55 = 63.6% growth ❌
With:    Jun=55 [ytd], Sep=90 [ytd] → Engine: Invalid comparison detected ✅
         Or converts: Q3 discrete = 35, compares appropriately
```

**Effort:** ~3 hours

### 🟡 5. Golden Financial Test Fixtures (PENDING)
**What's needed:**
- Create fake companies with known-answer financial statements
- Test pathological cases (negative PAT, declining revenue, YTD data)
- Verify accounting correctness (not just API consistency)
- Examples:
  - FY22 Revenue=100, FY23=120, FY24=150; PAT=10→9→18
  - Negative PAT and revenue scenarios
  - YTD quarterly data mixed with discrete
  - Consolidated + standalone same period

**Why it matters:**
- Current tests verify Overview and Intelligence agree (same wrong answer)
- Need to verify they calculate correctly
- Financial correctness > API consistency

**Effort:** ~4 hours

---

## Not Yet Started (Phase 3)

### ⚪ 6. Multi-Period Earnings Quality (PENDING)
**Current:** Too simplistic (OCF > PAT × 1.1 threshold)
**Target:** 3–5 year analysis
- Cumulative OCF / Cumulative PAT (multi-year)
- Accrual ratio trend (declining = better quality)
- Cash flow conversion trend
- Tax rate consistency
- One-off normalization

**Effort:** ~2 hours

### ⚪ 7. Red Flags Spread Logic (PENDING)
**Current:** Broken for negative revenue
```python
if ar_growth > rev_growth * 1.3:  # -5% > -26%? YES
    flag = "AR growing faster than sales"  # But AR fell 5%!
```

**Target:** Use spread logic
```python
ar_growth - rev_growth > X_bps  # Handles negative cases
```

**Effort:** ~1 hour

### ⚪ 8. Narrative Validation (PENDING)
**Example:** "Revenue expanded for three consecutive periods"
- Current: Just checks `len(fy_trend) >= 3 and latest_growth > 0`
- Target: Verify actual consecutive increases (T > T-1 > T-2)

**Effort:** ~0.5 hours

---

## Testing Status

### ✅ API Tests
- All three test companies (FATIMA, FFC, EFERT) responding correctly
- Metrics decomposed properly
- Rationale generated
- Scope conflicts logged

### ⚠️ Financial Correctness Tests
- **Created**: test_financial_correctness.py (structure in place)
- **Status**: Awaiting Phase 2 to populate with real test data
- **Needed**: Golden fixtures (known-answer cases)

### ⚠️ Integration Tests
- Overview/Intelligence consistency: ✅ Working
- Scope-aware aggregation: ✅ Verified
- Period duration detection: ✅ Infrastructure ready

---

## Architecture Changes

### Before (Problem State)
```
Database (consolidated + standalone, discrete + YTD)
           ↓
ResearchContext (scope destroyed, duration unknown)
           ↓
Engines (metrics from incompatible periods, no validation)
           ↓
Analysis (potentially wrong, no error flags)
```

### After Phase 1 (Current)
```
Database (consolidated + standalone + duration_basis)
           ↓
ResearchContext (scope preserved, duration tracked, conflicts logged)
           ↓
Engines (ready for Phase 2 validation logic)
           ↓
Analysis (infrastructure for correctness)
```

### Target After Phase 2-3
```
Database (clean, tagged, normalized)
           ↓
ResearchContext (full metadata: scope, duration, period)
           ↓
Engines (validate comparability, reject invalid comparisons)
           ↓
Analysis (mathematically correct, analyst-visible rationale)
```

---

## Commits This Session

| Commit | Title | Impact |
|--------|-------|--------|
| 214e05a | Critical fixes: WhatChange bugs + narratives | Wrong classifications fixed |
| 5147c35 | Scope-aware aggregation | No silent data loss |
| 4f2bc61 | Period duration infrastructure | Quarterly semantics ready |

---

## Confidence Trajectory

| Dimension | Oct 2 | Oct 3 (Now) | Target |
|-----------|-------|-----------|--------|
| Architecture | 8/10 | 8/10 | 8.5/10 |
| Period Integrity | 7/10 | 7.5/10 | 8.5/10 |
| **Financial Logic** | 4.5/10 | 5.5/10 | 8/10 |
| **Investor Trust** | 4.5/10 | 5.5/10 | 8.5/10 |

---

## Recommendation

**Do NOT add features until Phase 2 is complete.**

Phase 2 is relatively quick (3+4=7 hours of focused work):
1. Implement ingestion auto-detect for duration_basis (~3h)
2. Build golden test fixtures (~4h)

**Payoff:** Architecture-to-production-quality jump
- Financial logic goes from 5.5 → 8/10
- Investor trust goes from 5.5 → 8.5/10
- Foundation for everything that comes after

**If you ship Phase 1 without Phase 2:**
- Architecture is great, but financial analysis still weak
- Each new engine will have similar issues (unsupported claims, missing validation)
- Better to fix the pipeline once than patch 9 engines

---

## Key Principle

**Make implicit calculations explicit.**

Not: "Revenue improved" with 70% confidence  
But: "Revenue grew 3.5% (FY24→FY25), confirmed by adjusted figures"

Not: "Business is Weakening" because we wrote a rule  
But: "Business is Weakening because earnings fell 21.3% despite 3.5% revenue growth, indicating margin compression of 388 bps"

The specificity is both for the analyst and for future debugging: if business later improves, we can trace exactly why.

---

## Files Modified

- `backend/app/db/models/financials.py` — Added duration_basis field
- `backend/app/analysis/evidence_context.py` — Scope + duration tracking
- `backend/app/analysis/what_changed.py` — Bug fixes
- `backend/app/analysis/business_health.py` — Narrative validation
- `backend/app/analysis/period_duration.py` — NEW detection + normalization
- `backend/tests/test_financial_correctness.py` — NEW golden fixtures structure
- `FINANCIAL_ANALYSIS_AUDIT.md` — Initial audit findings
- `PERIOD_DURATION_SEMANTICS.md` — Specification for period duration work

---

## Next Session Checklist

- [ ] Review Phase 2 requirements
- [ ] Implement ingestion auto-detect (period_duration.py integration)
- [ ] Populate golden test fixtures (test_financial_correctness.py)
- [ ] Run full test suite
- [ ] Verify on all 3 test companies
- [ ] Commit Phase 2 complete

---

## Long-term Vision

**Month 1:** Phase 1-2 complete → Financial logic 8/10, investor trust 8.5/10
**Month 2:** Multi-period analysis, leverage transparency → 8.5/10
**Month 3:** Sector-specific models, expanded company coverage
**Month 4:** Ready for serious investor reliance

This is the path from "impressive PSX platform" to "professional-grade research infrastructure."
