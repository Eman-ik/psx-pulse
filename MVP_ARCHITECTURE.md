# PSX Pulse MVP Architecture

---

## Data Flow Diagram

```
                         PSX PULSE MVP
                              │
                              ▼
                     ┌────────────────┐
                     │   NEXT.JS UI   │
                     │                │
                     │ Search         │
                     │ Financials     │
                     │ Peers          │
                     │ Insights       │
                     │ Evidence       │
                     └───────┬────────┘
                             │
                         REST / JSON
                             │
                             ▼
                     ┌────────────────┐
                     │    FASTAPI     │
                     │    (3 routes)  │
                     └───────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
     Company API       Financial API      Research API
          │                  │                  │
          │          ┌────────┴────────┐        │
          │          ▼                 ▼        │
          │      Calculations    Anomaly       │
          │         Engine       Detection     │
          │          │                │        │
          └──────────┼────────────────┼────────┘
                     │                │
                     ▼                ▼
             PostgreSQL Database
                     │
             ┌───────┼───────────────┐
             │       │               │
             ▼       ▼               ▼
         Companies Financials    Sources
             │       │
             └───────┴──────────────┐
                     │              │
                     ▼              ▼
              Validation      Extracted
              Framework       Facts
                     │              │
                     └──────┬───────┘
                            │
                    Data Ingestion Pipeline
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
    Annual            Quarterly           Announcements
    Reports           Results            & Events
```

---

## Database Schema (Sprint 1)

### Core Tables

#### `companies`
```sql
companies
---------
id                  SERIAL PRIMARY KEY
ticker              VARCHAR(10) UNIQUE NOT NULL
name                VARCHAR(255) NOT NULL
sector              VARCHAR(100)
industry            VARCHAR(100)
listed_date         DATE
fiscal_year_end     INT  -- Month (1-12)
currency            VARCHAR(3) DEFAULT 'PKR'
status              VARCHAR(20) DEFAULT 'active'  -- active, delisted, suspended
coverage_tier       VARCHAR(20) DEFAULT 'price_only'  -- price_only, partial, full
created_at          TIMESTAMP DEFAULT NOW()
updated_at          TIMESTAMP DEFAULT NOW()
```

#### `periods`
```sql
periods
-------
id                  SERIAL PRIMARY KEY
company_id          INT FOREIGN KEY REFERENCES companies(id)
period_type         VARCHAR(20) NOT NULL  -- annual, q1, q2, q3, q4, h1, h2
fiscal_year         INT NOT NULL
quarter             INT NULL  -- 1-4 if quarterly
start_date          DATE NOT NULL
end_date            DATE NOT NULL
created_at          TIMESTAMP DEFAULT NOW()

UNIQUE (company_id, period_type, fiscal_year, quarter)
```

#### `sources`
```sql
sources
-------
id                  SERIAL PRIMARY KEY
company_id          INT FOREIGN KEY REFERENCES companies(id)
source_type         VARCHAR(50) NOT NULL  -- annual_report, quarterly_results, announcement, etc
publisher           VARCHAR(255)
title               VARCHAR(500)
document_type       VARCHAR(100)  -- annual_report, financial_statements, etc
period_id           INT FOREIGN KEY REFERENCES periods(id) NULL
url                 VARCHAR(2000)
file_path           VARCHAR(500)  -- Local path to document
document_date       DATE
publication_date    DATE
retrieved_date      DATE
document_hash       VARCHAR(64)  -- SHA256 for reproducibility
status              VARCHAR(20) DEFAULT 'pending'  -- pending, extracted, validated, stored
created_at          TIMESTAMP DEFAULT NOW()

INDEX (company_id, source_type, period_id)
```

#### `documents`
```sql
documents
---------
id                  SERIAL PRIMARY KEY
source_id           INT FOREIGN KEY REFERENCES sources(id)
company_id          INT FOREIGN KEY REFERENCES companies(id)
document_type       VARCHAR(100)
period_id           INT FOREIGN KEY REFERENCES periods(id) NULL
file_path           VARCHAR(500)  -- s3://bucket/company/year/document.pdf
file_size           INT
file_hash           VARCHAR(64)
created_at          TIMESTAMP DEFAULT NOW()

INDEX (company_id, period_id)
```

#### `financial_facts`
```sql
financial_facts
---------------
id                  SERIAL PRIMARY KEY
company_id          INT FOREIGN KEY REFERENCES companies(id) NOT NULL
period_id           INT FOREIGN KEY REFERENCES periods(id) NOT NULL
metric              VARCHAR(100) NOT NULL  -- revenue, net_income, eps, etc
value               DECIMAL(15,2) NOT NULL
unit                VARCHAR(50)  -- PKR, shares, %, etc
currency            VARCHAR(3) DEFAULT 'PKR'
statement_type      VARCHAR(50)  -- income_statement, balance_sheet, cashflow, etc
consolidation_type  VARCHAR(50) DEFAULT 'consolidated'  -- consolidated, unconsolidated
source_id           INT FOREIGN KEY REFERENCES sources(id)
source_page         INT
extraction_method   VARCHAR(50) DEFAULT 'manual'  -- manual, ocr, structured
validation_status   VARCHAR(20) DEFAULT 'pending'  -- pending, validated, flagged, rejected
validation_notes    TEXT
created_at          TIMESTAMP DEFAULT NOW()
updated_at          TIMESTAMP DEFAULT NOW()

INDEX (company_id, period_id, metric)
INDEX (source_id)
UNIQUE (company_id, period_id, metric, consolidation_type)
```

#### `derived_metrics`
```sql
derived_metrics
---------------
id                  SERIAL PRIMARY KEY
company_id          INT FOREIGN KEY REFERENCES companies(id) NOT NULL
period_id           INT FOREIGN KEY REFERENCES periods(id) NOT NULL
metric_name         VARCHAR(100) NOT NULL  -- roe, fcf, debt_equity, etc
value               DECIMAL(15,4)
formula_version     VARCHAR(20) DEFAULT '1.0'
source_fact_ids     INT[]  -- Array of financial_fact IDs used in calculation
calculated_at       TIMESTAMP DEFAULT NOW()

INDEX (company_id, period_id, metric_name)
```

#### `research_insights`
```sql
research_insights
-----------------
id                  SERIAL PRIMARY KEY
company_id          INT FOREIGN KEY REFERENCES companies(id) NOT NULL
period_id           INT FOREIGN KEY REFERENCES periods(id) NOT NULL
insight_type        VARCHAR(50)  -- anomaly, trend, flag, etc
severity            VARCHAR(20)  -- low, medium, high
category            VARCHAR(50)  -- growth, profitability, leverage, etc
claim               TEXT
explanation         TEXT
supporting_fact_ids INT[]
supporting_source_ids INT[]
generated_at        TIMESTAMP DEFAULT NOW()

INDEX (company_id, insight_type)
```

---

## Core Models (SQLAlchemy)

```python
# app/models/company.py
class Company(Base):
    __tablename__ = "companies"
    
    id: int
    ticker: str
    name: str
    sector: str
    industry: str
    listed_date: date
    fiscal_year_end: int
    currency: str = "PKR"
    status: str = "active"
    coverage_tier: str = "price_only"
    
    periods = relationship("Period", back_populates="company")
    sources = relationship("Source", back_populates="company")
    financial_facts = relationship("FinancialFact", back_populates="company")
    
# app/models/period.py
class Period(Base):
    __tablename__ = "periods"
    
    id: int
    company_id: int
    period_type: str  # annual, q1, q2, etc
    fiscal_year: int
    quarter: int = None
    start_date: date
    end_date: date
    
    company = relationship("Company", back_populates="periods")
    financial_facts = relationship("FinancialFact", back_populates="period")
    
# app/models/financial_fact.py
class FinancialFact(Base):
    __tablename__ = "financial_facts"
    
    id: int
    company_id: int
    period_id: int
    metric: str
    value: Decimal
    unit: str
    currency: str = "PKR"
    statement_type: str
    consolidation_type: str = "consolidated"
    source_id: int
    source_page: int = None
    extraction_method: str = "manual"
    validation_status: str = "pending"
    validation_notes: str = None
    
    company = relationship("Company", back_populates="financial_facts")
    period = relationship("Period", back_populates="financial_facts")
    source = relationship("Source")
```

---

## API Structure (Sprint 1-4)

### Route 1: Company Service
```python
# app/api/companies.py

GET /api/companies/search?q=lucky
  → returns: [{ticker, name, sector, coverage_tier}]

GET /api/companies/{ticker}
  → returns: Company details with coverage badge

GET /api/companies/{ticker}/overview
  → returns: Business description, key metrics, recent events
```

### Route 2: Financial Service
```python
# app/api/financials.py

GET /api/companies/{ticker}/financials
  ?periods=5y (or specific periods)
  ?consolidation=consolidated
  → returns: Financial table with all validated facts

GET /api/companies/{ticker}/financials/{metric}
  → returns: {metric: value, source: {document, page}, history: [...]}

GET /api/companies/{ticker}/periods
  → returns: Available periods with data completeness
```

### Route 3: Research Service
```python
# app/api/research.py

GET /api/companies/{ticker}/peers
  → returns: Peer group with comparative metrics

GET /api/companies/{ticker}/insights
  → returns: Anomalies, trends, flags

GET /api/companies/{ticker}/sources
  → returns: All sources with extraction status

GET /api/companies/{ticker}/metrics/calculated
  → returns: ROE, FCF, margins, growth rates, etc
```

---

## Calculation Engine (Sprint 3)

### Philosophy
- **Deterministic:** Same input = same output
- **Documented:** Every formula documented
- **Lineage:** Every calculation tracks its sources
- **Testable:** 100% test coverage

### Module Structure
```python
# app/analysis/growth.py
def calculate_revenue_growth(company_id, period_id) -> float
def calculate_profit_growth(company_id, period_id) -> float
def calculate_eps_growth(company_id, period_id) -> float

# app/analysis/profitability.py
def calculate_gross_margin(company_id, period_id) -> float
def calculate_operating_margin(company_id, period_id) -> float
def calculate_net_margin(company_id, period_id) -> float
def calculate_roe(company_id, period_id) -> float
def calculate_roa(company_id, period_id) -> float

# app/analysis/leverage.py
def calculate_debt_equity(company_id, period_id) -> float
def calculate_current_ratio(company_id, period_id) -> float
def calculate_interest_coverage(company_id, period_id) -> float

# app/analysis/cashflow.py
def calculate_operating_cf_margin(company_id, period_id) -> float
def calculate_fcf(company_id, period_id) -> float
def calculate_fcf_margin(company_id, period_id) -> float
def calculate_fcf_conversion(company_id, period_id) -> float

# app/analysis/shareholder.py
def calculate_dividend_yield(company_id, period_id, current_price) -> float
def calculate_payout_ratio(company_id, period_id) -> float
def calculate_dividend_growth(company_id, period_id) -> float
```

### Example Implementation
```python
def calculate_roe(company_id: int, period_id: int) -> Dict:
    """
    ROE = Net Income / Average Shareholder Equity
    """
    current_period = get_period(period_id)
    prior_period = get_prior_period(company_id, period_id)
    
    current_net_income = get_fact(
        company_id, period_id, "net_income"
    )
    current_equity = get_fact(
        company_id, period_id, "total_equity"
    )
    prior_equity = get_fact(
        company_id, prior_period.id, "total_equity"
    )
    
    if not all([current_net_income, current_equity, prior_equity]):
        return {
            "status": "incomplete",
            "missing": [...]
        }
    
    average_equity = (
        float(current_equity.value) + float(prior_equity.value)
    ) / 2
    
    roe = float(current_net_income.value) / average_equity
    
    return {
        "value": roe * 100,  # As percentage
        "unit": "%",
        "formula": "Net Income / Average Equity",
        "sources": [
            current_net_income.source_id,
            current_equity.source_id,
            prior_equity.source_id
        ],
        "calculated_at": datetime.now()
    }
```

---

## Frontend Structure (Sprint 4)

### Pages
```
/search
/company/[ticker]
/company/[ticker]/financials
/company/[ticker]/peers
/company/[ticker]/insights
```

### Components
```
SearchBar.tsx
CompanyHeader.tsx
CoverageBadge.tsx
FinancialTable.tsx
FinancialChart.tsx
MetricCard.tsx
PeerTable.tsx
InsightCard.tsx
EvidencePanel.tsx
SourceBadge.tsx
PeriodSelector.tsx
AnomalyFlag.tsx
```

### Key Interaction: Evidence Panel
```
User clicks: Net Profit (FY2026) = 42.8bn

Evidence panel opens:
├── Value: 42.8bn
├── Prior: 31.0bn (FY2025)
├── Growth: +38.1%
├── Source: Lucky Cement Annual Report 2026
├── Page: 84
├── Consolidation: Consolidated
├── Validated: ✓
└── [Open PDF]
```

---

## Data Quality Standards

### Validation Rules

#### Balance Sheet Identity
```
Assets ≈ Liabilities + Equity
  Acceptable variance: ±0.5%
```

#### Cash Flow Reconciliation
```
Opening Cash + CF = Closing Cash
  Acceptable variance: ±1%
```

#### EPS Calculation
```
Net Income / Weighted Shares ≈ EPS
  Acceptable variance: ±2%
```

#### Unit Consistency
```
✓ PKR (all must be same denomination)
✗ Mix PKR and PKR million
```

#### Consolidation Consistency
```
✓ All consolidated statements together
✓ All unconsolidated statements together
✗ Mix consolidated and unconsolidated
```

#### Period Completeness
```
✓ FY2025 (Mar 31 2025)
✓ Q1 FY2026 (Jun 30 2025)
✗ Q1 FY2026 missing
```

---

## Validation Flags

### Automatic Flags (Sprint 5)

```
IF profit_growth >> revenue_growth
  FLAG: "Profit growth significantly exceeds revenue growth"
  ACTION: Investigate margin improvement vs other income

IF net_income ↑ AND operating_cf ↓
  FLAG: "Earnings/cash-flow divergence"
  ACTION: Investigate quality of earnings

IF receivables_growth >> revenue_growth
  FLAG: "Receivables growing faster than revenue"
  ACTION: Investigate collection quality

IF debt ↑ significantly AND interest_expense ↑
  FLAG: "Increasing financing burden"
  ACTION: Monitor debt serviceability

IF dividend > fcf
  FLAG: "Dividend exceeds free cash flow"
  ACTION: Monitor sustainability
```

---

## MVP Constraints (Enforce These)

1. **Data comes first**
   - Extract → Normalize → Validate → Store
   - Never skip validation
   - Never store unvalidated data

2. **UI only for validated data**
   - No "coming soon" or partial states
   - If data isn't ready, don't show it

3. **AI only explains validated data**
   - No predictions
   - No buy/sell/hold
   - Only: what changed, possible explanations, what to investigate

4. **Every number is traceable**
   - Click → source opens
   - No metrics without lineage
   - No calculated values without formula

5. **Three companies, perfect execution**
   - Don't add companies until current ones are flawless
   - Quality > quantity

---

## Success Criteria

**Sprint 0:** MVP roadmap finalized, architecture agreed, scope frozen  
**Sprint 1:** Database schema production-ready  
**Sprint 2:** LUCK data 100% validated and traceable  
**Sprint 3:** All financial calculations tested and documented  
**Sprint 4:** Frontend handles all use cases  
**Sprint 5:** Anomalies detected accurately  
**Sprint 6:** AI explanations are faithful to data  
**Sprint 7:** DGKC and CHCC ingested without pipeline changes  
**Sprint 8:** Real users can research a company in <20 minutes  

---

## Go Build

This is the architecture.  
This is the scope.  
Everything else is Phase 2.

**Let's execute.**
