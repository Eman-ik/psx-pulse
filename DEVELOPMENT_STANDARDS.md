# Development Standards for MVP

**Effective immediately on `mvp` branch**

---

## The Golden Rule

**Every line of code must answer: "Does this get us to MVP?"**

If no: it's Phase 2. Defer it.

---

## Code Organization

### Backend Structure
```
app/
├── main.py              # FastAPI setup only
├── api/
│   ├── companies.py     # Company search, details
│   ├── financials.py    # Financial data, metrics
│   └── research.py      # Peers, insights, anomalies
├── services/
│   ├── company_service.py
│   ├── financial_service.py
│   └── research_service.py
├── analysis/
│   ├── growth.py
│   ├── profitability.py
│   ├── leverage.py
│   ├── cashflow.py
│   └── anomalies.py
├── models/
│   ├── company.py
│   ├── period.py
│   ├── financial_fact.py
│   ├── source.py
│   └── event.py
├── db/
│   ├── session.py
│   └── migrations/
└── validation/
    └── rules.py
```

### Frontend Structure
```
app/
├── page.tsx             # Redirect to search
├── search/
│   └── page.tsx
├── company/
│   └── [ticker]/
│       ├── page.tsx
│       ├── financials/
│       ├── peers/
│       └── insights/
└── components/
    ├── SearchBar.tsx
    ├── CompanyHeader.tsx
    ├── FinancialTable.tsx
    ├── PeerTable.tsx
    ├── InsightCard.tsx
    └── EvidencePanel.tsx
```

---

## What NOT to Do

### ❌ DO NOT
```python
# ❌ Don't calculate in the UI
export function CalculateROE() {
  return netIncome / avgEquity;  // NO
}

# ❌ Don't let LLM invent numbers
llm.prompt("What's the revenue?")  // NO

# ❌ Don't store unvalidated data
save_financial_fact(value, source=None)  // NO

# ❌ Don't mix concerns
class FinancialCalculation {
  def __init__(self):
    self.scrape_pdf()
    self.validate()
    self.calculate()
    self.update_ui()  // NO
}

# ❌ Don't create features for Phase 2
if sprint <= 8:
  build_screening_engine()  // NO
```

### ✅ DO

```python
# ✅ Calculate in the service layer
class FinancialService:
  def calculate_roe(company_id, period_id) -> float:
    # Get validated facts
    # Calculate deterministically
    # Return with lineage

# ✅ Validate before storage
def extract_and_store(pdf):
  facts = extract(pdf)
  for fact in facts:
    if not validate(fact):
      flag_for_review(fact)
      return
  store(facts)

# ✅ Let AI explain validated data
def explain_changes(company_id, period_id):
  facts = get_validated_facts(company_id, period_id)
  metrics = calculate_metrics(facts)
  flags = detect_anomalies(metrics)
  return llm.explain(facts, metrics, flags)

# ✅ Keep layers separate
source → extract → normalize → validate → store → calculate → explain
```

---

## Code Review Checklist

Every PR must pass these questions:

### Scope
- [ ] Does this get us to MVP?
- [ ] Or is it Phase 2?
- [ ] Does it add features beyond the 8-sprint roadmap?

### Architecture
- [ ] Does it follow the dependency hierarchy?
  ```
  SOURCE → INGESTION → NORMALIZATION → VALIDATION → DATABASE 
  → CALCULATIONS → RESEARCH → API → UI
  ```
- [ ] Does it reverse any dependencies?
- [ ] Is it mixing concerns?

### Data Quality
- [ ] Every new fact: does it have source provenance?
- [ ] Every calculation: does it have lineage?
- [ ] Every validation: is it enforced before storage?
- [ ] Is validation skipped anywhere?

### Testing
- [ ] For calculations: 100% test coverage?
- [ ] For API endpoints: all happy paths tested?
- [ ] For validation: edge cases covered?

### Documentation
- [ ] Every calculation: formula documented?
- [ ] Every API route: parameters documented?
- [ ] Every validation rule: why documented?

### Naming
- [ ] Functions named for what they compute (calculate_roe, not get_data)
- [ ] Variables named for what they hold (net_income, not value)
- [ ] No abbreviations except industry-standard (ROE, EPS, FCF)

---

## Validation Standards

### Every New Data Type Needs Validation Rules

```python
class FinancialFactValidator:
  # Accounting identity: Assets = Liabilities + Equity
  def validate_balance_sheet_identity(fact):
    variance = abs((assets - (liabilities + equity)) / assets)
    return variance <= 0.005  # 0.5% acceptable

  # Unit consistency: don't mix PKR and PKR million
  def validate_unit_consistency(facts):
    units = set(f.unit for f in facts)
    return len(units) == 1

  # Consolidation consistency
  def validate_consolidation_consistency(facts):
    consolidations = set(f.consolidation_type for f in facts)
    return len(consolidations) == 1

  # Period completeness
  def validate_period_completeness(company_id, period_id):
    required_metrics = [
      'revenue', 'gross_profit', 'operating_profit', 'net_income',
      'total_assets', 'total_liabilities', 'total_equity',
      'operating_cash_flow'
    ]
    have = get_extracted_metrics(company_id, period_id)
    return all(m in have for m in required_metrics)
```

### Data Pipeline Validation

```
PDF
 ↓ [Extraction]
 ├→ [Validation checks]
    ├ Unit consistency?
    ├ Range checks?
    ├ Reference integrity?
    ↓
 ├→ PASS: Store with validation_status='validated'
 ├→ FAIL: Flag with validation_status='flagged', require manual review
 ↓
Database (all data has provenance)
```

---

## Calculation Standards

### Every Calculation Needs

1. **Formula**: Clearly documented
```python
def calculate_roe(company_id, period_id):
  """
  ROE = Net Income / Average Shareholder Equity
  
  Average Equity = (Opening Equity + Closing Equity) / 2
  """
```

2. **Lineage**: Tracks source facts
```python
return {
  "value": roe,
  "formula": "Net Income / Average Equity",
  "source_facts": [
    {"id": net_income.id, "value": net_income.value},
    {"id": opening_equity.id, "value": opening_equity.value},
    {"id": closing_equity.id, "value": closing_equity.value}
  ]
}
```

3. **Tests**: 100% coverage
```python
def test_calculate_roe():
  # Test happy path
  # Test missing data
  # Test edge cases
  # Test zero cases
```

4. **Reproducibility**: Same input = same output, always
```python
# ✓ Deterministic
def calculate_roe(company_id, period_id):
  return get_net_income(company_id, period_id) / get_avg_equity(...)

# ✗ Non-deterministic
def calculate_roe(company_id, period_id):
  # Call external API (might fail)
  # Use current date (changes every day)
  # Use random seed
```

---

## Testing Standards

### API Endpoint Tests
```python
def test_get_company_financials():
  response = client.get("/api/companies/LUCK/financials")
  
  # Happy path
  assert response.status_code == 200
  assert response.json()["ticker"] == "LUCK"
  assert all(f["source_id"] for f in response.json()["facts"])
  
  # Validation
  assert all(f["validation_status"] == "validated" 
             for f in response.json()["facts"])

def test_get_company_not_found():
  response = client.get("/api/companies/NONEXISTENT/financials")
  assert response.status_code == 404

def test_no_incomplete_periods():
  response = client.get("/api/companies/LUCK/financials")
  # Never return incomplete periods
```

### Calculation Tests
```python
def test_roe_calculation():
  # Setup known values
  net_income = 100
  opening_equity = 500
  closing_equity = 600
  expected_roe = 100 / 550  # 18.18%
  
  # Test
  result = calculate_roe(company_id, period_id)
  assert abs(result["value"] - expected_roe) < 0.001
  assert len(result["source_facts"]) == 3

def test_roe_missing_data():
  # When equity data is missing
  result = calculate_roe(company_id, period_id)
  assert result["status"] == "incomplete"
  assert "missing" in result
```

### Validation Tests
```python
def test_validation_catches_mismatched_units():
  facts = [
    {"metric": "revenue", "value": 100, "unit": "PKR"},
    {"metric": "profit", "value": 50, "unit": "PKR million"}
  ]
  assert not validate_unit_consistency(facts)

def test_validation_catches_bad_balance_sheet():
  facts = {
    "assets": 100,
    "liabilities": 70,
    "equity": 40  # Should be 30
  }
  assert not validate_balance_sheet_identity(facts)
```

---

## Performance Standards

### For Calculations
```python
# Every calculation must complete in < 100ms
def test_calculation_performance():
  start = time.time()
  calculate_roe(company_id, period_id)
  assert time.time() - start < 0.1
```

### For API Endpoints
```python
# Every API endpoint must respond in < 500ms
def test_api_performance():
  start = time.time()
  client.get("/api/companies/LUCK/financials")
  assert time.time() - start < 0.5
```

---

## Git Commit Standards

### Every commit must say which sprint it serves

```
✓ Sprint 1: Add company model and period model
✓ Sprint 2: Extract LUCK annual report financials
✓ Sprint 3: Implement ROE calculation
✗ Add portfolio tracking feature (NO)
✗ WIP (NO - commits must be complete)
```

### Commit message format

```
<Sprint #>: <What changed>

<Why it matters>
<Link to roadmap section if relevant>
```

### Example
```
Sprint 1: Add PostgreSQL schema for companies and periods

Establishes core data model. Companies table holds company details, 
periods table organizes financial data by fiscal period (annual/quarterly).
All financial_facts reference both company and period.

Relates to: MVP_ROADMAP.md Sprint 1
```

---

## Code Style

### Python
```python
# Use type hints
def calculate_roe(company_id: int, period_id: int) -> float:
  pass

# Use constants for magic numbers
ACCEPTABLE_VARIANCE = 0.005  # 0.5%

# Use docstrings for formulas
def calculate_roe(company_id: int, period_id: int) -> float:
  """
  ROE = Net Income / Average Shareholder Equity
  """

# Use descriptive variable names
net_income = get_fact(company_id, period_id, "net_income")
opening_equity = get_fact(company_id, period_id, "total_equity")
```

### TypeScript
```typescript
// Use interfaces for data shapes
interface FinancialFact {
  id: number;
  metric: string;
  value: number;
  source_id: number;
  validation_status: "pending" | "validated" | "flagged";
}

// Use const for constants
const ACCEPTABLE_VARIANCE = 0.005;

// Use descriptive component names
<EvidencePanel fact={fact} source={source} />
```

---

## When You're Stuck

### Ask These Questions in Order
1. Does this get us to MVP? (If no, defer to Phase 2)
2. Does this break the dependency hierarchy? (If yes, refactor)
3. Does this skip validation? (If yes, add validation)
4. Is this testable? (If no, redesign)
5. Is this documented? (If no, add docs)

### If Still Stuck
- Comment in the PR with the question
- Tag the team for discussion
- Don't guess or hack

---

## One Final Thing

**This MVP is not about building quickly.**
**It's about building right.**

- Right data (validated, with provenance)
- Right calculations (deterministic, documented)
- Right UI (only for validated data)
- Right integration (no hallucinations)

**Slow down. Get it right. Then ship.**

**8 sprints. One chance to do this well.**
