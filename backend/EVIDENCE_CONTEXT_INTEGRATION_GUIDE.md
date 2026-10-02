# Evidence Context Integration Guide

**Status:** Evidence Context framework complete. Now migrate all 9 engines to use it.

**Goal:** Every engine reads from ONE source of truth (ResearchContext) and outputs confidence separately from assessment.

---

## Architecture

```
Database
    ↓
ResearchContext (single scan, complete inventory)
    ↓
    ├─ Business Health Engine
    ├─ What Changed Engine
    ├─ Earnings Quality Engine (v2 - reference implementation)
    ├─ Bull/Bear Case Engine
    ├─ Red Flags Engine
    ├─ Risk Engine
    ├─ Catalyst Engine
    ├─ Valuation Context Engine
    └─ What to Watch Engine
    ↓
All outputs feed into ConsistencyValidator
    ↓
User receives analysis + evidence context + validation report
```

---

## Key Changes Per Engine

### **REFERENCE: Earnings Quality v2** (earnings_quality_v2.py)

Pattern to follow for ALL engines:

```python
from app.analysis.evidence_context import ResearchContext, ContextualizedOutput

def analyze(db: Session, issuer_id: int) -> Dict:
    # 1. Create shared context (ONE database scan)
    context = ResearchContext(db, issuer_id)
    output = ContextualizedOutput("earnings_quality", context)
    
    # 2. Check data availability upfront
    has_ocf = context.has_metric("operating_cash_flow")
    has_pat = context.has_metric("profit_after_tax")
    
    # 3. If critical data missing, degrade gracefully
    if not has_pat:
        return {
            "status": "insufficient_data",
            "reason": "Profit after tax not available",
        }
    
    # 4. Build analysis
    issues = []
    if has_ocf:
        # Compare OCF vs PAT
        ...
    else:
        issues.append("Operating cash flow unavailable—cannot validate.")
    
    # 5. Assign quality AND confidence AND coverage
    if critical_missing:
        quality = "Moderate (provisional)"
        confidence = "Low"
        coverage = 60
    elif issues:
        quality = "Moderate"
        confidence = "Medium"
        coverage = 85
    else:
        quality = "High"
        confidence = "High"
        coverage = 95
    
    # 6. Output with context
    output.set_assessment(
        assessment=quality,
        score=...,
        narrative="...",
        confidence=confidence,
        data_coverage=coverage,
    )
    
    result = output.to_dict()
    
    # 7. Validate for contradictions
    result["validation"] = output.validate()
    
    return result
```

---

## Migration Checklist

### Business Health Engine

**File:** `app/analysis/business_health.py`

**Changes needed:**
```python
# ADD these imports
from app.analysis.evidence_context import ResearchContext, ContextualizedOutput

# ADD this at start of analyze()
context = ResearchContext(db, issuer_id)
output = ContextualizedOutput("business_health", context)

# REPLACE all metric lookups
# OLD: revenue = BusinessHealthEngine.get_series(db, issuer_id, "revenue")
# NEW: revenue = context.get_series("revenue", periods=3)

# REPLACE assessment logic
# Degrade gracefully:
if not context.has_metric("revenue"):
    return {"status": "insufficient_data"}

# Add confidence/coverage
output.set_assessment(
    assessment=overall,
    narrative=narrative,
    confidence="High" if revenue and pat and ocf else "Medium",
    data_coverage=context.domain_status("business_health")["coverage_pct"],
)
```

**Effort:** 1-2 hours

---

### What Changed Engine

**File:** `app/analysis/what_changed.py`

**Changes needed:**
```python
# Import Evidence Context
from app.analysis.evidence_context import ResearchContext, ContextualizedOutput

# Use shared context
context = ResearchContext(db, issuer_id)
output = ContextualizedOutput("what_changed", context)

# Get periods from context (not raw queries)
periods = sorted(
    set(p for m in context.metrics.values() for p in m.periods)
)[-2:]

# Degrade when data missing
if len(periods) < 2:
    return {"status": "insufficient_data"}

# Extract values from context
rev_latest = context.get_value("revenue", periods[-1])
rev_prior = context.get_value("revenue", periods[-2])

# FIX SYNTHESIS BUG: Don't claim "no offsetting concerns" if AR rose
if any("receivable" in c.lower() for c in negative_changes):
    # Receivables ARE offsetting
    interpretation = "...but deterioration in receivables quality weakens..."
else:
    interpretation = "...no offsetting concerns"

# Add confidence based on what we have
output.set_assessment(
    assessment="Complete" if len(periods) >= 2 else "Partial",
    narrative=interpretation,
    confidence=context.domain_status("what_changed")["confidence"],
)
```

**Effort:** 1-2 hours

---

### Earnings Quality Engine

**File:** `app/analysis/earnings_quality.py` → Replace with `earnings_quality_v2.py`

**Status:** ✅ Already refactored. Copy earnings_quality_v2.py to earnings_quality.py after testing.

**Effort:** 0 hours (already done)

---

### Bull/Bear Case Engine

**File:** `app/analysis/bull_bear_case.py`

**Critical changes:**

```python
from app.analysis.evidence_context import ResearchContext, ContextualizedOutput

def analyze(db: Session, issuer_id: int) -> Dict:
    context = ResearchContext(db, issuer_id)
    
    # ⚠️ FIX: Cannot claim valuation without PE_RATIO
    if not context.can_claim("valuation"):
        # Remove valuation language from bull/bear thesis
        # NO: "Current valuation reflects modest expectations"
        # YES: "Current earnings trajectory suggests..."
    
    # ⚠️ FIX: Cannot claim dividend without OCF + DPS
    if not context.can_claim("dividend_sustainable"):
        # Remove "dividend sustainability is strong"
        # Replace with: "Dividend sustainability cannot yet be assessed"
    
    # Build thesis only with allowed claims
    bull_drivers = []
    if context.has_metric("revenue"):
        bull_drivers.append("Revenue growth suggests...")
    
    # Get confidence from context
    bull_output = ContextualizedOutput("bull_bear_case", context)
    bull_output.set_assessment(
        assessment=bull_case,
        confidence=context.domain_status("bull_bear_case")["confidence"],
    )
```

**Key fixes:**
1. Remove valuation language if PE missing
2. Remove dividend claims if OCF/DPS missing
3. Get confidence from context

**Effort:** 2 hours

---

### Red Flags Engine

**File:** `app/analysis/red_flags.py`

**Changes needed:**
```python
from app.analysis.evidence_context import ResearchContext

context = ResearchContext(db, issuer_id)

# Get series from context instead of raw queries
revenue = context.get_series("revenue", periods=3)
pat = context.get_series("profit_after_tax", periods=3)
ocf = context.get_series("operating_cash_flow", periods=3)

# If OCF missing, cannot flag "OCF falling despite profits"
if not context.has_metric("operating_cash_flow"):
    # Remove this flag
    # flags = [f for f in flags if "operating cash flow weakness" not in f["title"]]

output.set_assessment(
    assessment="Complete" if len(flags) > 0 else "No flags",
    confidence=context.domain_status("red_flags")["confidence"],
)
```

**Effort:** 1 hour

---

### Risk Engine

**File:** `app/analysis/risk_engine.py`

**Critical fix: Company-specific vs. Sector-level risks**

```python
from app.analysis.evidence_context import ResearchContext

context = ResearchContext(db, issuer_id)

risks = []

# ⚠️ FIX: Cannot claim "customer concentration" without data
if context.has_metric("customer_concentration"):
    risks.append({
        "title": "Customer concentration",
        "type": "company_specific",
        ...
    })
else:
    risks.append({
        "title": "Customer concentration risk",
        "type": "sector_level",
        "description": "Typical risk in fertilizer sector (not company-specific)"
    })

output.set_assessment(
    confidence=context.domain_status("risk_engine")["confidence"],
)
```

**Effort:** 1 hour

---

### Catalyst Engine

**File:** `app/analysis/catalyst_engine.py`

**Critical: Mock data gate**

```python
def analyze(db: Session, issuer_id: int) -> Dict:
    # Check data source
    context = ResearchContext(db, issuer_id)
    
    # TODO: Integrate with announcement database
    # For now, gate mock data
    
    return {
        "status": "mock_data",
        "reason": "Catalyst data not yet integrated from announcement database",
        "expected_catalysts": [
            "Quarterly results",
            "Dividend announcements",
            "Major announcements"
        ],
        "note": "Complete integration in Phase 2"
    }
```

**Effort:** 0 hours (gate it until data integrated)

---

### Valuation Context Engine

**File:** `app/analysis/valuation_context.py`

**Status:** ✅ Already handles unavailable gracefully

**Minimal changes:**
```python
from app.analysis.evidence_context import ResearchContext

context = ResearchContext(db, issuer_id)

# Already correct pattern:
if not context.has_metric("pe_ratio"):
    return {
        "assessment": "Valuation: Unavailable",
        "confidence": "None",
    }

# Just add confidence from context
output.set_assessment(
    confidence=context.domain_status("valuation")["confidence"],
)
```

**Effort:** 30 minutes

---

### What to Watch Engine

**File:** `app/analysis/what_to_watch.py`

**Changes:**
```python
from app.analysis.evidence_context import ResearchContext

context = ResearchContext(db, issuer_id)

# Use context getters
revenue = context.get_value("revenue")
gross_profit = context.get_value("gross_profit")
ocf = context.get_value("operating_cash_flow")

# Degrade thresholds when data missing
if context.has_metric("operating_cash_flow"):
    watch_metrics.append({
        "metric": "Operating cash flow",
        "current": f"PKR {ocf:,.0f}m",
        ...
    })
else:
    watch_metrics.append({
        "metric": "Operating cash flow",
        "current": "Data unavailable",
        "note": "Cannot set watch thresholds without baseline"
    })

output.set_assessment(
    confidence=context.domain_status("what_to_watch")["confidence"],
)
```

**Effort:** 1 hour

---

## Integration Steps

### 1. Validate Evidence Context Works (30 min)

```bash
# Test against FFC
python -c "
from app.db.session import SessionLocal
from app.db.models import Security
from sqlalchemy import select
from app.analysis.evidence_context import ResearchContext

db = SessionLocal()
ffc = db.execute(select(Security).where(Security.symbol == 'FFC')).scalar()
context = ResearchContext(db, ffc.issuer_id)

print(context.summary())
print()
print(context.confidence_summary())
"
```

### 2. Migrate Engines (6 hours, parallel)

- Business Health: 2 hours
- What Changed: 1.5 hours
- Bull/Bear: 2 hours
- Red Flags: 1 hour
- Risk: 1 hour
- Valuation: 0.5 hours
- What to Watch: 1 hour
- Earnings Quality: ✅ Done
- Catalyst: Gate it (0.5 hours)

### 3. Test on FFC Again (30 min)

```bash
python test_engines.py
```

Expected output changes:
- Earnings Quality: "High" → "Moderate (provisional)" with `confidence: Low` due missing OCF
- Bull/Bear: Valuation language removed
- All others: Confidence/coverage separated from assessment

### 4. Consistency Validator Tests (30 min)

```python
from app.analysis.consistency_validator import ConsistencyValidator

all_outputs = {
    "business_health": ...,
    "what_changed": ...,
    ...
}

validator = ConsistencyValidator(context, all_outputs)
report = validator.validate_all()

print(validator.report())
```

Should show: "No contradictions detected" after migrations.

### 5. Test on FATIMA and EFERT (30 min)

Test that all 3 issuers pass consistency checks.

---

## Success Criteria

✅ All engines use Evidence Context  
✅ All engines separate confidence from assessment  
✅ All engines degrade gracefully when data missing  
✅ No prohibited claims without supporting data  
✅ All 3 issuers (FFC, FATIMA, EFERT) pass consistency validator  
✅ Zero contradictions in output  

---

## Expected Changes to Output

### Before (Contradiction)

```json
{
  "business_health": {
    "components": { "earnings_quality": "Weak" }
  },
  "earnings_quality": {
    "assessment": "High",
    "score": 92
  }
}
```

### After (Consistent)

```json
{
  "business_health": {
    "assessment": "Stable",
    "components": { "earnings_quality": "Unknown" },
    "confidence": "Medium"
  },
  "earnings_quality": {
    "assessment": "Moderate (provisional)",
    "score": 68,
    "confidence": "Low",
    "data_coverage_pct": 60,
    "missing_critical_metrics": ["operating_cash_flow"]
  }
}
```

Difference: Both now acknowledge missing OCF. No contradiction.

---

## Timeline

- **Day 1:** Evidence Context validation + Earnings Quality v2 testing
- **Day 2:** Migrate 4 major engines (Business Health, What Changed, Bull/Bear, Red Flags)
- **Day 3:** Migrate remaining 4 engines + Consistency Validator testing
- **Day 4:** Test on all 3 issuers, fix any issues
- **Day 5:** Confidence review, documentation, production readiness

**Total:** 3-4 working days to achieve zero-contradiction baseline.

---

## Files Created

✅ `app/analysis/evidence_context.py` — Core framework  
✅ `app/analysis/earnings_quality_v2.py` — Reference implementation  
✅ `app/analysis/consistency_validator.py` — Cross-engine validation  
✅ This guide

---

## Notes

- Evidence Context scans the database once per issuer, not once per metric
- All engines read from the SAME ResearchContext (no redundant queries)
- Prohibited claims are enforced by code, not documentation
- Confidence and coverage are always reported alongside assessment
- Contradictions are caught by ConsistencyValidator before users see output
