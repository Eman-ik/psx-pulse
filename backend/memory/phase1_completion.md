---
name: phase1_data_coverage_formula_fixes
description: Phase 1 complete — all four engines corrected with transparent data coverage formulas, no hard-coded ceilings
metadata:
  type: project
---

# Phase 1: Data Coverage Formula Corrections — COMPLETE

**Status:** ✅ All formula fixes implemented and committed

## Summary

All four intelligence engines now calculate data coverage **transparently** using proportional formulas instead of hard-coded ceilings:
- WhatChangedEngine: Separates "comparisons_available" from "material_changes_detected"
- EarningsQualityEngine: Removes hard-coded 90% ceiling → transparent (evidence_count / 6) * 100
- ValuationContextEngine: Removes hard-coded ceiling → transparent (available_inputs / 6) * 100
- BusinessHealthEngine: Already proportional (available_metrics / 6) * 100
- ResearchOrchestrator: Returns three separate metrics instead of conflated single number

## Files Modified

1. ✅ `/d/khronos/psx-fertilizer/backend/app/analysis/what_changed.py` — Separates comparisons_available from material_changes_detected
2. ✅ `/d/khronos/psx-fertilizer/backend/app/analysis/earnings_quality_v2.py` — Transparent coverage formula (evidence_count / 6)
3. ✅ `/d/khronos/psx-fertilizer/backend/app/analysis/valuation_context.py` — Explicit input tracking, transparent formula
4. ✅ `/d/khronos/psx-fertilizer/backend/app/analysis/business_health.py` — Already proportional
5. ✅ `/d/khronos/psx-fertilizer/backend/app/analysis/research_orchestrator.py` — Three separate metrics (data_coverage_pct, evidence_quality, analytical_confidence)
6. ✅ `/d/khronos/psx-fertilizer/backend/tests/test_data_coverage_corrected.py` — Test suite created
7. ✅ `/d/khronos/psx-fertilizer/backend/PHASE1_COMPLETION_REPORT.md` — Full technical report

## Key Improvements

### WhatChangedEngine
- **Before:** Only counted comparisons where material change detected → artificially low coverage (50%)
- **After:** Counts comparisons where data exists, regardless of change magnitude → honest measurement
- **Output fields:** data_coverage_pct, changes_detected_pct, comparisons_available, material_changes

### EarningsQualityEngine
- **Before:** Hard-coded ceilings 40, 45, 65, 70, 80, 85, 90 → max 90% regardless of data
- **After:** data_coverage = (evidence_count / 6) * 100 → supports 0, 16.7, 33.3, 50, 66.7, 83.3, 100%
- **Separation:** data_coverage_pct (availability) independent from confidence (interpretation quality)

### ValuationContextEngine
- **Before:** Hard-coded 0 (no PE), 70 (current PE), 90 (with history) → stuck at 90%
- **After:** data_coverage = (available_inputs / 6) * 100 → explicit input tracking
- **Separation:** data_coverage_pct (availability) independent from analytical_confidence

### ResearchOrchestrator
- **Before:** Single conflated metric "confidence_score" mixing data availability + interpretation certainty
- **After:** Three separate metrics
  - `data_coverage_pct` — % of required data available (0-100, no ceiling)
  - `evidence_quality` — High/Medium/Low, derived from data_coverage + recency
  - `analytical_confidence` — High/Medium/Low, derived from engine agreement + signal clarity
- **Backward compat:** Old "confidence_score" still returned but deprecated

## Expected Impact

**With corrected formulas (before data ingestion):**
- FFC composite coverage: 64% → 67.5% (more honest, no false floor)
- EFERT composite coverage: 68% → 71% (proportional measurement)

**With Phase 2 data ingestion (quick wins):**
- Sector Median P/E → +7%
- Historical P/E Series → +10%
- Other Income FY2025 (FFC) → +3%
- Target: ~75–80% composite coverage

**With Phase 3 (OCF data):**
- Operating Cash Flow (all 5 years) → +20%
- Target: 100% honest coverage

## Testing

Test suite created at `/d/khronos/psx-fertilizer/backend/tests/test_data_coverage_corrected.py`

**Key test cases:**
- Immaterial revenue change (0.5%) still counts as "available"
- All 8 comparisons available = 100% coverage (not capped)
- Missing one metric reduces coverage proportionally
- All 6 earnings evidence items = 100% coverage (not hard-coded 90%)
- Data coverage independent from analytical confidence
- Valuation inputs tracked explicitly (no hard-coded 90%)
- ResearchOrchestrator returns three separate metrics
- High data coverage possible with low analytical confidence

Run with: `pytest tests/test_data_coverage_corrected.py -v`

## Principle

> A trustworthy 67% with exact explanation of what's missing is much more valuable than a fake 100%.

**New state:** Formulas are **honest, transparent, and fixable**. Coverage increases proportionally and predictably as data arrives.

---

**Phase 1 Status:** ✅ COMPLETE
**Next:** Phase 2 — Ingest quick-win data to reach ~75–80% composite coverage
