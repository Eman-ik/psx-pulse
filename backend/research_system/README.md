# Khronos Research & Information System

## Overview

This is the **intellectual core of Khronos**: a structured Company Research Terminal that answers six fundamental questions before any investment decision is made:

1. **WHAT IS THIS COMPANY?** (Overview, Business Model)
2. **HOW DOES IT MAKE MONEY?** (Business Model, Segments)
3. **HOW HAS THE BUSINESS PERFORMED?** (Financials, Metrics, Trends)
4. **HOW FINANCIALLY STRONG IS IT?** (Leverage, Liquidity, Cash)
5. **HOW DOES IT COMPARE WITH COMPETITORS?** (Peers, Sector Context)
6. **WHAT IMPORTANT EVENTS/INFORMATION HAVE CHANGED RECENTLY?** (Announcements, Events)
7. *(Later)* **WHAT IS IT WORTH?** (Valuation - after foundation is solid)

## Architecture Principle

> **Data first → Normalization second → Calculations third → Research intelligence fourth → UI fifth → AI last.**

This is the opposite of how most AI-first finance companies build systems. We're building the right way: solid foundation first, intelligence built on top of trustworthy data.

## Current State

- `Equity-research/` exists as a working prototype (data platform, research engine, sector engines, API, tests)
- `khronos/` has quant forecasting (working) and multi-engine terminal (scaffolding)
- **Missing**: Structured research data model

## What We're Building Now

### Sprint 1-3: Research Data Foundation

File: `schema.py` (SQLAlchemy ORM models)

#### Sprint 1: Security Master
```
Security Master is the single source of truth for all PSX companies.
Every system that touches company data goes through security_id.

Tables:
- security (company identity)
- sector (PSX sectors)
- industry (PSX industries)
- company_profile (business metadata)
- source (information source registry)
```

**Why this matters:**
- No more "FFC" meaning different things in different systems
- All data (prices, financials, announcements) keys on security_id
- Enables auditability and verification

#### Sprint 2: Document Foundation
```
Documents are the source of all truth.
Annual reports, quarterly reports, announcements, presentations.

Tables:
- document (document registry)
- Processing pipeline: RECEIVED → EXTRACTING → EXTRACTED → NORMALIZING → NORMALIZED
```

**Why this matters:**
- Every number comes from somewhere
- AI can cite sources
- Historical archive for research

#### Sprint 3: Financial Schema
```
Structured financial statements without loss of original information.

Tables:
- financial_period (fiscal period container)
- financial_line_item (raw statement line items)
- metric_definition (canonical metric codes)
- metric_alias (maps reported labels to canonical codes)
```

**Why this matters:**
- Standardize across companies (REVENUE maps from "Sales", "Net sales", "Turnover")
- Preserve original labels for verification
- Foundation for calculation layer

### Sprint 4-5: Normalization & Calculation Engines

#### Sprint 4: Extraction/Normalization Pipeline
```
Document PDF → Extract tables → Map labels → Validate → Standardize → Store
```

#### Sprint 5: Financial Metric Engine
```
Formulas calculate derived metrics from normalized statements.

Examples:
- Revenue Growth (YoY, CAGR)
- Profitability Ratios (Margins, ROA, ROE, ROIC)
- Leverage (Debt/Equity, Debt/EBITDA, Interest Coverage)
- Liquidity (Current Ratio, Quick Ratio)
- Cash Flow (CFO, FCF, CFO/NI)

Table:
- financial_metric (calculated metrics with calculation_version tracking)
```

**Why calculation versioning matters:**
If you later change how you calculate ROE, you need to know which historical values used which formula.

## Data Model Explanation

### Security Master

```python
Security
├── ticker: "FFC"
├── company_name: "Fauji Fertilizer Company Limited"
├── sector: Fertilizer
├── industry: Nitrogenous Fertilizer
├── listing_date: 1977
├── fiscal_year_end: "30-JUN"
└── relationships:
    ├── company_profile (business description, auditor, website, etc.)
    ├── documents (all linked documents)
    ├── announcements (PSX announcements)
    └── financial_periods (all fiscal periods)
```

**Key design decision**: Everything that relates to FFC lives under security_id=1 (example). No ticker string confusion.

### Document Registry

```python
Document
├── title: "FFC Annual Report FY2026"
├── publication_date: 2026-08-15
├── fiscal_year: 2026
├── fiscal_quarter: null (annual)
├── document_type: ANNUAL_REPORT
├── source: Company Annual Report
├── processing_status: EXTRACTED
└── contains:
    └── financial_line_items (revenue, costs, profit, etc.)
```

**Key design decision**: Processing pipeline with status tracking.
- RECEIVED: Uploaded, awaiting extraction
- EXTRACTING: ML model extracting tables
- EXTRACTED: Tables extracted, awaiting normalization
- NORMALIZING: Labels being mapped to canonical codes
- NORMALIZED: Ready for calculations

### Financial Statements

```python
FinancialPeriod
├── security: FFC
├── fiscal_year: 2026
├── fiscal_quarter: null (annual)
├── period_start: 2025-07-01
├── period_end: 2026-06-30
└── contains:
    └── financial_line_items (actual numbers)
        ├── metric_code: REVENUE
        ├── reported_label: "Sales - Net"
        ├── value: 182,500,000,000 PKR
        ├── source_document: FFC Annual Report FY2026
        └── extraction_confidence: 0.98
```

**Key design decision**: Store both standardized metric codes AND reported labels.
- Standardized codes enable calculations
- Original labels enable verification
- Extraction confidence tracks ML accuracy

### Metric Definitions

```python
MetricDefinition
├── metric_code: "REVENUE"
├── metric_name: "Revenue"
├── statement_type: INCOME_STATEMENT
└── aliases:
    ├── "Sales"
    ├── "Net sales"
    ├── "Turnover"
    ├── "Operating revenue"
    └── (sector-specific: DGKC might call it "Advances")
```

**Key design decision**: Map once, use everywhere.
Different companies report revenue as:
- Sales
- Net sales
- Turnover
- Operating revenue

One MetricAlias table standardizes this. The ML system learns: "when the reported label is X, it means REVENUE." Then calculations use REVENUE consistently.

### Calculated Metrics (Sprint 5)

```python
FinancialMetric
├── security: FFC
├── period: FY2026
├── metric_code: "ROE"
├── value: 24.3
├── calculation_version: "fundamentals_v1"
```

**Key design decision**: Calculation versioning.
If you later change your ROE formula, new calculations use `fundamentals_v2`, old ones stay as `fundamentals_v1`. This means:
- Historical trends remain consistent
- You can see impact of methodology changes
- No confusion about which formula was used when

## API Layer (Sprint 6)

Once data model is solid:

```
GET /api/securities → all companies
GET /api/securities/{ticker} → company identity
GET /api/securities/{ticker}/profile → business info
GET /api/securities/{ticker}/financials → raw statements
GET /api/securities/{ticker}/metrics → calculated metrics
GET /api/securities/{ticker}/peers → comparable companies
GET /api/securities/{ticker}/announcements → PSX announcements
GET /api/securities/{ticker}/events → upcoming/past events
GET /api/securities/{ticker}/documents → linked documents
```

## Company Research Terminal (Sprint 7+)

Only after the data foundation exists, build the UI:

```
FFC | Fauji Fertilizer Company Limited
Fertilizer | Market Cap: 450bn | P/E: 12.5x | Yield: 6.2%

Price     Market Cap     P/E       Dividend Yield
xxx       xxx bn         x.x       x.x%

1M        3M             1Y
+x%       +x%            +x%

[OVERVIEW] [FINANCIALS] [FUNDAMENTALS] [PEERS] [ANNOUNCEMENTS] [EVENTS] [DOCUMENTS]
```

## Integration with Quant System

Once this Research System is solid, the Quant Engine (which we just built) can plug in:

```
Company Research Terminal
      ↓
    (Structured data: financials, metrics, peers, announcements)
      ↓
Quant Forecast Engine
      ↓
Signal Qualification Gate
      ↓
Investment Signal (BUY/SELL/HOLD/NO_SIGNAL)
```

The research system provides the foundation; quant adds the intelligence layer.

## Folder Structure

```
khronos/
│
├── research_system/
│   ├── schema.py ..................... SQLAlchemy models (Sprints 1-5)
│   ├── security_master.py ........... Sprint 1 implementation
│   ├── document_management.py ....... Sprint 2 implementation
│   ├── financial_extraction.py ...... Sprint 3-4 implementation
│   ├── fundamental_metrics.py ....... Sprint 5 implementation
│   ├── api.py ....................... Sprint 6 API layer
│   ├── README.md (this file)
│   └── tests/
│
├── platform/
│   ├── database/ .................... SQLAlchemy session, migrations
│   ├── api/ ......................... FastAPI + endpoints
│   └── auth/ ........................ Auth layer
│
├── frontend/
│   └── (React/Next.js company terminal UI)
│
├── engines/
│   ├── fundamentals/ ................ Metric calculations
│   ├── quant/ ....................... Quant forecast (existing)
│   └── research/ .................... Research AI (Equity-research/)
│
└── (existing files continue)
```

## Development Order (Sprints)

| Sprint | Task | Output |
|--------|------|--------|
| 1 | Security Master | security, sector, industry, company_profile, source |
| 2 | Document Foundation | document, document upload/storage pipeline |
| 3 | Financial Schema | financial_period, financial_line_item, metric_definition, metric_alias |
| 4 | Normalization Pipeline | Extract labels → Map to canonical codes → Validate → Store |
| 5 | Metric Engine | Formulas for growth, profitability, leverage, liquidity, cash flow |
| 6 | API Layer | /securities, /profile, /financials, /metrics, /peers, /announcements, /events |
| 7 | Company Terminal (FFC) | UI for single company - perfect before scaling |
| 8 | Peer System | Add EFERT, FATIMA, etc. + peer comparisons |
| 9 | Announcements + Events | Ingest PSX info, track upcoming dates |
| 10 | Research AI | Connect Equity-research/ engine to structured data |

## Success Metrics

**Sprint 1-3 Complete When:**
- [ ] Every PSX company has one canonical security_id
- [ ] Documents can be uploaded and associated with companies
- [ ] Financial statements can be extracted and stored with standardized metrics

**Sprint 4-5 Complete When:**
- [ ] Extraction pipeline converts PDFs to structured numbers
- [ ] Label normalization (500+ alias mappings)
- [ ] Metric calculations verified (test against manual calculations)

**Sprint 6-7 Complete When:**
- [ ] FFC Company Terminal works perfectly
- [ ] All information is sourced and auditable
- [ ] No AI text needed; data speaks for itself

## Not Included (Yet)

This system does NOT include:
- Price prediction (Quant engine does that)
- Buy/sell signals (Signal gate does that)
- Portfolio management
- Trade execution
- Order management
- Position sizing
- Complex sentiment analysis

Those are separate systems built on top of this foundation.

## Starting Point

Today's task (Sprint 1):
1. Create the database schema (done: `schema.py`)
2. Implement security_master.py with company ingestion
3. Test: all PSX companies have security_id
4. Create simple API: GET /companies → all PSX tickers

This is the foundation. Everything else builds on it.
