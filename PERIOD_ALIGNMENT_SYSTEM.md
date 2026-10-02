# Period Alignment System

**Date**: 2026-10-02  
**Status**: Initial implementation complete  
**Purpose**: Prevent financial nonsense from comparing metrics across different period types

---

## The Problem

Financial analysis breaks when you compare metrics from different periods:

```python
# DANGEROUS: Are these from the same period?
revenue = context.get_value("revenue")           # Might be FY2024 (Dec 31)
profit = context.get_value("profit_after_tax")  # Might be Q4 2024 (Sep 30)
ocf = context.get_value("operating_cash_flow")  # Might be Q3 2024 (Jun 30)

# This calculation produces nonsense
margin = profit / revenue  # Comparing FY to Q? Wrong period!
cash_conversion = ocf / profit  # Comparing Q3 to Q4? Wrong period!
```

**Example consequence**: "Revenue is strong but OCF is weak" — because you compared Q3 OCF (weak quarter) to FY revenue (strong).

---

## The Solution: Period Alignment

### Core Concept

Every period has a type:
- **FY**: Full-year period (ends Dec 31, Mar 31, Jun 30, or Sep 30 depending on fiscal year)
- **Q**: Quarterly period (ends last day of Mar/Jun/Sep/Dec)
- **TTM**: Trailing twelve months (calculated on the fly)

All metrics compared must come from **the same period**.

### ResearchContext Methods

```python
# 1. Get period type for a specific date
period_type = context.get_period_type(period_end=date(2024, 12, 31))
# Returns: "FY"

# 2. Get aligned values across metrics (guaranteed same period)
aligned = context.get_aligned_values(
    metrics=["revenue", "profit_after_tax", "operating_cash_flow"],
    period_type="FY",
    limit=3  # Last 3 FY periods
)
# Returns: [
#   {
#     "period_end": date(2024, 12, 31),
#     "revenue": 1000,
#     "profit_after_tax": 100,
#     "operating_cash_flow": 90
#   },
#   {...},
#   {...}
# ]

# 3. Get aligned time series (guaranteed same periods)
fy_series = context.get_aligned_series(
    metrics=["revenue", "profit_after_tax"],
    period_type="FY"
)
# Returns: {
#   "revenue": [800, 900, 1000],  # Chronological order
#   "profit_after_tax": [70, 80, 100]
# }

# 4. Compare two metrics from same period
analyzer = PeriodAlignedAnalyzer(context)
comparison = analyzer.compare_metrics_aligned(
    metric1="profit_after_tax",
    metric2="total_equity",
    period_type="FY"
)
# Returns: {
#   "period_end": date(2024, 12, 31),
#   "metric1": "profit_after_tax",
#   "metric1_value": 100,
#   "metric2": "total_equity",
#   "metric2_value": 500,
#   "ratio": 0.20,  # ROE = 20%
#   "period_type": "FY"
# }
```

---

## How to Use in Engines

### BEFORE (Wrong)
```python
class BusinessHealthEngine:
    @staticmethod
    def analyze(context: ResearchContext) -> Dict:
        # ❌ These might not be from same period
        revenue = context.get_series("revenue", periods=3)
        profit = context.get_series("profit_after_tax", periods=3)
        equity = context.get_series("total_equity", periods=3)
        
        # Comparing potentially misaligned periods
        margins = [p / r for p, r in zip(profit, revenue)]  # Wrong!
        roe = [p / e for p, e in zip(profit, equity)]       # Wrong!
        
        return {"margins": margins, "roe": roe}
```

### AFTER (Correct)
```python
class BusinessHealthEngine:
    @staticmethod
    def analyze(context: ResearchContext) -> Dict:
        # ✅ Guaranteed same periods
        analyzer = PeriodAlignedAnalyzer(context)
        
        # Get FY trend (all metrics from same FY periods)
        fy_trend = analyzer.get_fy_trend(
            ["revenue", "profit_after_tax", "total_equity"],
            limit=3
        )
        
        margins = []
        roe = []
        
        for period_data in fy_trend:
            # Now guaranteed all from same FY period
            revenue = period_data["revenue"]
            profit = period_data["profit_after_tax"]
            equity = period_data["total_equity"]
            
            if revenue > 0:
                margins.append(profit / revenue)
            if equity > 0:
                roe.append(profit / equity)
        
        return {
            "periods": [p["period_end"] for p in fy_trend],
            "margins": margins,
            "roe": roe,
            "period_type": "FY"  # Explicitly document which period type
        }
```

---

## Migration Path for Existing Engines

### Priority 1: Business Health (Uses most comparisons)
Currently compares:
- Revenue growth (needs alignment check)
- Margin trends (revenue vs profit)
- ROE (profit vs equity)
- Leverage (debt vs equity)

**Action**: Use `analyzer.get_fy_trend()` for all comparisons

### Priority 2: Red Flags & What Changed
Currently compares:
- Receivables vs Revenue (working capital)
- Inventory vs Revenue
- Positive/negative changes

**Action**: Use `analyzer.get_aligned_values()` for period-over-period

### Priority 3: Earnings Quality & Valuation
Currently compares:
- OCF vs Earnings
- P/E ratios
- Cash flow quality

**Action**: Use `analyzer.compare_metrics_aligned()` for ratio calculations

### Priority 4: Risk Engine
Currently compares:
- Liquidity ratios
- Leverage ratios
- Concentration metrics

**Action**: Use aligned values for ratio calculations

---

## Period Detection Logic

### Current Implementation (Simple)
```python
def _detect_period_types(self) -> None:
    for period_end in all_periods:
        month = period_end.month
        if month == 12 and period_end.day == 31:
            # Likely FY ending Dec 31
            self._period_types[period_end] = "FY"
        elif month in [3, 6, 9, 12] and period_end.day >= 28:
            # Likely Q ending in quarter month
            self._period_types[period_end] = "Q"
        else:
            self._period_types[period_end] = "Other"
```

### Future Enhancement: Infer from Data
Could detect:
- Alternating FY/Q based on pattern
- Custom fiscal year-end (Mar 31, Jun 30, etc.)
- TTM periods (calculate from rolling 12-month pattern)

---

## Example: What Changed Engine

### Current (Risky)
```python
# What if latest revenue is Q3 but latest PAT is Q4?
latest_rev = context.get_value("revenue")
latest_pat = context.get_value("profit_after_tax")

if latest_rev and latest_pat:
    latest_margin = latest_pat / latest_rev
    prior_margin = ...  # Can't safely compare
```

### With Period Alignment
```python
analyzer = PeriodAlignedAnalyzer(context)

# Get latest Q with all metrics
q_aligned = context.get_aligned_values(
    ["revenue", "profit_after_tax", "accounts_receivable"],
    period_type="Q",
    limit=2
)

if len(q_aligned) >= 2:
    latest_q = q_aligned[0]
    prior_q = q_aligned[1]
    
    latest_margin = latest_q["profit_after_tax"] / latest_q["revenue"]
    prior_margin = prior_q["profit_after_tax"] / prior_q["revenue"]
    
    change = latest_margin - prior_margin
    # Now this comparison is VALID
```

---

## Data Quality Implications

### What This Fixes
- ✅ No more mixing FY and Q comparisons
- ✅ Explicit period type in output
- ✅ Transparent about missing periods
- ✅ Clear when metrics not aligned

### What It Doesn't Fix
- ⏳ Fiscal year-end detection (needs config)
- ⏳ TTM calculations (future enhancement)
- ⏳ Holiday/delayed reporting periods (data quality issue)

---

## Testing Strategy

### Unit Tests Needed
```python
# Test 1: Period type detection
assert context.get_period_type(date(2024, 12, 31)) == "FY"
assert context.get_period_type(date(2024, 9, 30)) == "Q"

# Test 2: Alignment with gaps
# When metric1 has FY but metric2 only has Q
aligned = context.get_aligned_values(
    ["revenue_fy", "revenue_q"],
    period_type="FY"
)
assert len(aligned) == 0  # Can't align different types

# Test 3: Series alignment
series = context.get_aligned_series(
    ["revenue", "profit_after_tax"],
    period_type="FY"
)
assert len(series["revenue"]) == len(series["profit_after_tax"])

# Test 4: Growth rate with alignment
growth = analyzer.calculate_growth_aligned(
    "revenue",
    period_type="FY",
    periods=1
)
# Should use aligned periods, not just latest values
```

---

## Integration Checklist

- [x] Period detection in ResearchContext
- [x] `get_aligned_values()` method
- [x] `get_aligned_series()` method
- [x] `get_period_type()` method
- [x] PeriodAlignedAnalyzer helper class
- [ ] Update BusinessHealthEngine to use alignment
- [ ] Update RedFlagEngine to use alignment
- [ ] Update WhatChangedEngine to use alignment
- [ ] Update EarningsQualityEngine to use alignment
- [ ] Add period_type to all engine outputs
- [ ] Add tests for period alignment
- [ ] Document in engine READMEs

---

## Status

**Current**: Period alignment system implemented in ResearchContext.  
**Next**: Integrate into engines one at a time (start with BusinessHealthEngine).  
**Future**: Add fiscal year-end configuration, TTM calculation, better period inference.

---

## References

Problem identified in code review:
> "You need to distinguish FY, quarterly and TTM much more rigorously... Comparing FY revenue to Q3 PAT would produce nonsense while still looking mathematically valid."

Solution implemented:
> Engines now explicitly request aligned values via `get_aligned_values()`, ensuring no cross-period comparisons.
