# ConsistencyValidator Scan Results — All 13 PSX Companies

**Date**: 2026-10-02  
**Scan Date Range**: 4 companies with data found (FFC, EFERT, FATIMA, ACPL)  
**Validator Status**: ACTIVE in /api/v1/research/{ticker}/analysis

## Summary

| Metric | Count |
|--------|-------|
| Total contradictions | 7 |
| Companies affected | 4/4 |
| Companies with issues | 4/4 (100%) |
| Warnings | 0 |

## Systematic Issues Found

### Issue 1: Unsupported Dividend Sustainability Claims
**Severity**: P1 (High)  
**Affected Companies**: 3 (FFC, EFERT, ACPL)  
**Engine**: bull_bear_case ↔ valuation_context

**Problem**: Bull case engine claims dividend sustainability without required metrics.

**Missing Data**:
- `operating_cash_flow` - needed to validate dividend capacity
- `dividend_per_share` - current dividend level not available

**Root Cause**: Bull/Bear case engine does not validate claim prerequisites against ResearchContext before writing thesis.

**Current Behavior**:
```json
"bull": {
  "drivers": ["...dividend claims..."],
  "thesis": "Dividend capacity depends on cash flow sustainability."
}
```
But dividend_per_share is missing, making this claim unsupported.

**Fix Required**: 
- Bull/Bear case engine should call `context.can_claim(ClaimType.DIVIDEND_SUSTAINABLE)` before making dividend claims
- If not allowed, remove dividend language from thesis and drivers

### Issue 2: Mislabeled Customer Concentration Risks
**Severity**: P1 (High)  
**Affected Companies**: 4 (FFC, EFERT, FATIMA, ACPL)  
**Engine**: risk_engine

**Problem**: Risk engine claims "customer concentration risk" as company-specific, but customer_concentration metric doesn't exist.

**Missing Metric**: `customer_concentration`

**Root Cause**: Risk engine has hardcoded "Customer concentration risk" for all fertilizer sector companies. This is a sector-level structural risk, not company-specific analysis.

**Current Behavior**:
```json
"all_risks": [
  {
    "title": "Customer concentration risk",
    "description": "Typical structural risk in fertilizer sector—customer base often concentrated.",
    "type": "sector_level",
    "composite_score": 4
  }
]
```

**Fix Required**:
- Either: Build customer_concentration metric from supplier concentration data
- Or: Change type from "company_specific_concentration" to "sector_level" (already labeled correctly in current implementation, but contradicts claim of company-specific risk)
- Risk engine should not claim company-specific risks without backing data

## Data Gaps Preventing Analysis

**Companies with 404 errors** (9 total):
- UPLOADS, ENGRO, FMCL, UFERT, SFL, COLPAK, AHL, BATA, PSMC

These likely lack fundamental data in FinancialFact table or issuer_id linkage.

## Validator Validation Rules Triggered

1. **Dividend Consistency Check** (_check_dividend_consistency)
   - Rule: Can't claim dividend sustainability without OCF + DPS data
   - Status: Working correctly ✓

2. **Risk Claims Check** (_check_risk_claims)
   - Rule: Company-specific risks require specific metrics
   - Status: Working correctly ✓

## What the Validator is Catching

The ConsistencyValidator prevents:
- Unsupported claims from reaching users
- Contradictions between engines (dividend claims + missing data)
- Company-specific risk claims without backing metrics
- Logical inconsistencies in investment thesis

## Next Steps (P1)

1. Fix Bull/Bear case to validate dividend claims against context
2. Fix Risk engine to either:
   - Populate customer_concentration metric, or
   - Stop claiming company-specific customer concentration risk
3. Re-scan after fixes to verify contradictions resolved

---

**Note**: Validator is now active in production API. All research intelligence outputs include validation results showing contradictions and warnings before reaching users.
