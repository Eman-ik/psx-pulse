# PSX Pulse MVP Roadmap

**Status:** Sprint 0 - Freeze & Document  
**Last Updated:** 2026-10-01  
**Frozen Feature Set:** Yes  

---

## Vision

**One sentence:** Search a PSX company → get trustworthy structured financial history → understand what changed → compare peers → trace every number back to source.

**Solves:** Research time from 90 minutes → 10 minutes without sacrificing trust.

**For:** Usman, Hina, Ahmed, Rabia (and others like them)

---

## MVP Definition of Done

### Data
- ✓ 3-5 companies have complete structured financial data
- ✓ Annual + quarterly financials available
- ✓ Source provenance works (every number traceable)
- ✓ Validation catches errors (Assets = Liabilities + Equity)
- ✓ Consolidated/unconsolidated distinction enforced

### Research Engine
- ✓ Financial trends calculated (growth, margins, ratios)
- ✓ Peer comparison works (LUCK vs DGKC vs CHCC)
- ✓ Anomaly detection flags unusual changes
- ✓ Earnings quality assessment implemented
- ✓ Cash flow analysis works

### User Experience
- ✓ Search works (find company by ticker/name)
- ✓ Company page shows: Overview | Financials | Peers | Insights
- ✓ Financial table with annual + quarterly data
- ✓ Click any number → source panel opens
- ✓ Peer comparison table
- ✓ Insights page shows what changed and why

### AI
- ✓ AI only uses validated data
- ✓ AI explanations cite evidence
- ✓ AI does NOT produce BUY/SELL/HOLD recommendations
- ✓ AI clearly distinguishes fact from interpretation

### Validation
- ✓ Real users (Usman, Hina, etc.) can research a company
- ✓ Measure time saved (target: 10-20 minutes)
- ✓ Collect what they couldn't answer
- ✓ No more than 2-3 pain points reported

---

## 8-Sprint Roadmap

### Sprint 0: Freeze & Document (2 days)
**Status:** IN PROGRESS

**Objectives:**
- [ ] Archive experimental code on `archive` branch
- [ ] Create `mvp` branch (fresh start)
- [ ] Document MVP architecture
- [ ] Document what stays, what goes
- [ ] Establish development standards

**Deliverables:**
- MVP_ROADMAP.md (this file)
- MVP_ARCHITECTURE.md (data model + backend structure)
- DEVELOPMENT_STANDARDS.md (code quality, testing, validation)

**Definition of Done:**
- All experimental features documented and archived
- MVP branch is clean and ready for Sprint 1
- Team agrees on scope and won't deviate

---

### Sprint 1: Data Foundation (1 week)
**Objectives:**
- Build core database models
- Establish data ingestion pipeline
- Create source registry system
- Define validation rules

**Models to Create:**
```
companies
periods
financial_facts
sources
documents
metrics
```

**What NOT to build:**
- No screening engine
- No portfolio tracking
- No price prediction
- No agents
- No 22-stage pipeline
- No dashboard

**Deliverables:**
- Database schema
- Alembic migrations
- Source registry API
- Data validation framework

**Definition of Done:**
- Schema is peer-reviewed
- Migrations run cleanly
- All relationships tested

---

### Sprint 2: Lucky Cement Ingestion (1 week)
**Objective:** Get ONE company working perfectly

**Tasks:**
- [ ] Collect Lucky Cement documents:
  - Annual reports (3 years)
  - Quarterly results (8 quarters)
  - Relevant announcements
- [ ] Build extraction pipeline:
  - PDF → raw text
  - Text → financial tables
  - Tables → structured facts
- [ ] Store in database with full provenance
- [ ] Validate every extracted fact
- [ ] Manual verification (does extracted data match PDF?)

**Deliverables:**
- LUCK data in database
- 30+ financial facts with sources
- Extraction pipeline code
- Data quality report

**Definition of Done:**
- Every number is traceable to source
- Extracted data matches manual verification
- No validation errors

---

### Sprint 3: Financial Calculation Engine (4-7 days)
**Objective:** Convert raw facts to meaningful metrics

**Implement:**
```python
calculate_revenue_growth()
calculate_profit_growth()
calculate_gross_margin()
calculate_operating_margin()
calculate_net_margin()
calculate_roe()
calculate_roa()
calculate_debt_equity()
calculate_current_ratio()
calculate_fcf()
calculate_dividend_yield()
calculate_payout_ratio()
```

**All functions:**
- Deterministic (same input = same output)
- Documented
- Tested
- Include calculation lineage (which facts were used)

**Deliverables:**
- Calculation engine module
- Calculation lineage tracking
- 100% test coverage

**Definition of Done:**
- Calculations reproducible
- Formula documentation complete
- No LLM involved

---

### Sprint 4: Frontend MVP (1 week)
**Objective:** Build search → financials → insights UX

**Components to Build:**
```
SearchBar
CompanyHeader
CoverageBadge
FinancialTable
FinancialChart
MetricCard
PeerTable
InsightCard
EvidencePanel
SourceBadge
PeriodSelector
```

**Pages:**
```
/search
/company/[ticker]
/company/[ticker]/financials
/company/[ticker]/peers
/company/[ticker]/insights
```

**Key Interaction:**
- Click on any financial metric
- Evidence panel opens showing:
  - Value
  - Prior year value
  - Growth %
  - Source document
  - Page number
  - [Open Source] button

**Deliverables:**
- Responsive Next.js frontend
- All components tested
- Mobile-friendly

**Definition of Done:**
- No "coming soon" features
- All links work
- No console errors

---

### Sprint 5: Research Intelligence (1 week)
**Objective:** Anomaly detection and trend analysis

**Implement:**
```
Growth analysis
  - Revenue growth >> profit growth?
  - EPS growth vs revenue growth

Profitability shifts
  - Margin compression/expansion
  - ROE changes

Cash flow divergence
  - Net income ↑ but Operating CF ↓?
  - FCF coverage analysis

Receivables quality
  - Receivables growth >> revenue growth?
  - Days sales outstanding changes

Leverage changes
  - Debt increasing
  - Interest burden rising

Dividend sustainability
  - Dividend > FCF?
  - Payout ratio rising
```

**All flags include:**
- What changed
- Scale (small/medium/large)
- Possible explanations (not predictions)
- Sources

**Deliverables:**
- Anomaly detection module
- Flag generation engine
- Flag explanation templates

**Definition of Done:**
- Flags are accurate
- No false positives
- All supported by data

---

### Sprint 6: AI Explanation Layer (3-5 days)
**Objective:** Constrained AI that only explains validated facts

**System receives:**
```
validated_facts: {revenue, profit, margins, debt, ...}
calculated_metrics: {roe, fcf, growth, ...}
detected_flags: {anomalies, changes}
source_metadata: {documents, pages, dates}
```

**AI does NOT:**
- Predict stock price
- Recommend buy/sell/hold
- Invent missing data
- Make causal claims beyond evidence

**AI does:**
```
"What changed?"
  Net profit increased 38%, significantly faster than 
  revenue (+8%). This divergence likely reflects margin 
  improvement, lower finance costs, or other-income gains.

"Why might it have changed?"
  Likely drivers (in order of magnitude):
  1. Margin improvement (+X%)
  2. Finance cost reduction (+Y%)
  3. Tax benefit (+Z%)

"What should the user investigate?"
  - Check gross margin: did it improve?
  - Check finance costs: lower interest paid?
  - Check other income: any one-offs?

"Sources"
  - Annual Report 2026, Page 84
  - Quarterly Results Q4 2026
  - Previous annual report for comparison
```

**Deliverables:**
- AI explanation service
- Constrained prompt system
- Citation mapping

**Definition of Done:**
- Every explanation cites sources
- No hallucinations
- AI admits uncertainty

---

### Sprint 7: DGKC + CHCC (1 week)
**Objective:** Stress-test pipeline with two more companies

**Why two more?**
- If extraction breaks on DGKC, you'll find it now
- If validation catches errors, you'll see them now
- If peer comparison fails, you'll know before 100 companies

**Tasks:**
- [ ] Ingest DGKC documents
- [ ] Ingest CHCC documents
- [ ] Run extraction pipeline
- [ ] Validate data
- [ ] Fix pipeline issues
- [ ] Build peer comparison

**Deliverables:**
- DGKC in database
- CHCC in database
- Peer table working
- Pipeline robustness report

**Definition of Done:**
- All three companies have clean data
- Peer comparison accurate
- No data conflicts

---

### Sprint 8: User Testing (1 week)
**Objective:** Validate MVP with real users

**Test Protocol:**
Give access to: Usman, Hina, Ahmed, Rabia

**Tell them:** "Research a company as you normally would. Don't ask me how to use it."

**Measure:**
- Time spent (target: 10-20 min)
- Excel use (target: minimal)
- Questions unanswered
- Errors encountered
- What they liked most

**Success criteria:**
- Time < 30 minutes
- No more than 2-3 pain points
- Users would use it again

**Deliverables:**
- User feedback summary
- Bug list (prioritized)
- Requested features (defer to V2)

**Definition of Done:**
- All testers complete workflow
- MVP is usable
- Clear roadmap for V2

---

## What Gets Removed

**Completely delete:**
- ❌ Dashboard (/ route)
- ❌ Ranking feature
- ❌ Portfolio tracking
- ❌ Trade Planning UI
- ❌ Unified Research-Trade Flow UI
- ❌ Institutional Research modules
- ❌ 22-stage pipeline (replace with 5 modules)
- ❌ Confidence scoring
- ❌ All "phase 2" experimental code

**Keep but refactor:**
- ✅ Research Studio (focus on data traceability)
- ✅ Screener (defer frontend, keep data layer)
- ✅ FastAPI backend (simplify to 3 services)
- ✅ PostgreSQL (use new schema)

**Future (NOT in MVP):**
- 🔮 Advanced screening
- 🔮 Quant models
- 🔮 Agentic research
- 🔮 Price prediction
- 🔮 Portfolio optimization

---

## Architecture Principles (Non-Negotiable)

1. **Never reverse dependencies**
   ```
   SOURCE → INGESTION → RAW DATA → NORMALIZATION 
   → VALIDATION → DATABASE → CALCULATIONS → RESEARCH → API → UI
   
   Never: UI calculates financials
   Never: LLM invents data
   Never: Scraper directly populates UI
   ```

2. **Every fact needs provenance**
   ```
   Revenue = 123,400
   Source = Annual Report 2026
   Page = 84
   Date = 2026-09-30
   Consolidation = Consolidated
   ```

3. **Validation before storage**
   ```
   PDF → Extract → Normalize → Validate → Store
   
   If validation fails, flag for manual review
   Never store unvalidated data
   ```

4. **Calculation lineage**
   ```
   ROE = 18.4%
   Source facts:
     - Net Income: 12.8bn (Annual Report 2026)
     - Avg Equity: 69.9bn (Balance Sheet)
   ```

5. **UI only displays validated data**
   ```
   Questions tab shows only for companies with 
   complete, validated financials.
   
   Never show "coming soon" or partial data.
   ```

---

## Success Metrics (After MVP)

- **Research time:** 90 min → 10-20 min (80% reduction)
- **Data trust:** Users verify sources without leaving app
- **Coverage:** 3-5 companies perfectly researched
- **User satisfaction:** Net Promoter Score > 50

---

## Phase 2 Roadmap (Not starting until MVP is done)

Once MVP proves valuable:

```
MVP
  ↓
Expand to KSE-30 (top 30 liquid companies)
  ↓
Build sector intelligence (cement, fertilizer, E&P, banking)
  ↓
Add advanced peer comparison
  ↓
Build screening engine (on trusted data)
  ↓
Advanced analytics (ML models)
  ↓
PSX Pulse V2
```

**But not before MVP is solid.**

---

## Team Agreements

**This branch:**
- No feature creep
- No "eventually"
- No "phase 2" comments
- No experimental code

**Code review standards:**
- Every PR must say which sprint it serves
- Must not add scope
- Must cite the MVP_ROADMAP

**If unsure:**
- Ask: "Does this get us to MVP?"
- If no: defer to Phase 2

---

## Go Build

This is achievable.
This is focused.
This solves a real problem.

**Let's make it real.**
