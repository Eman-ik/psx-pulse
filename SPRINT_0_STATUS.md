# Sprint 0: Freeze & Document

**Status:** ✅ COMPLETE  
**Date:** 2026-10-01  
**Branch:** `mvp` (created, pushed to GitHub)  

---

## What Happened

### 1. Transitioned from Experimental to MVP Phase
- Created `archive` branch (preserves all experimental work)
- Created `mvp` branch (fresh start for focused MVP)
- Both branches are on GitHub at https://github.com/Eman-ik/psx-pulse

### 2. Documented Everything
- **MVP_ROADMAP.md**: Complete 8-sprint roadmap with definitions of done
- **MVP_ARCHITECTURE.md**: Database schema, API structure, calculation engine, validation rules

### 3. Established Immutable Constraints
```
This MVP will:
✓ Search company → get trustworthy structured financials
✓ Understand what changed (trends, anomalies)
✓ Compare peers
✓ Trace every number to source

This MVP will NOT:
✗ Dashboard, Ranking, Portfolio
✗ Trade Planning, Unified Flow
✗ 22-stage pipeline
✗ Confidence scoring
✗ Price prediction
✗ Trading signals
```

### 4. Defined Success
**MVP is done when:**
- ✓ 3 companies (LUCK, DGKC, CHCC) have structured, validated financials
- ✓ Financial calculations are deterministic and documented
- ✓ UI lets users search → view financials → compare peers → trace sources
- ✓ AI only explains validated data (never predicts)
- ✓ Real users can research a company in 10-20 minutes

---

## Branches

### `main` (archived experimental work)
```
40f08e8 UI Reframing: Question-Driven Research Interface (Phase 1)
```
Keep this branch. It shows the entire experimental journey.

### `archive` (everything we're NOT building)
All experimental code is here:
- 22-stage pipeline
- Dashboard, ranking, portfolio
- Trade planning UI
- Unified flow
- Agents, screeners, ML models
- 8 different modules

This becomes Phase 2 roadmap once MVP is solid.

### `mvp` (ACTIVE - this is where we build)
```
e1dd333 MVP: Sprint 0 - Freeze experimental code, document MVP roadmap and architecture
  └── MVP_ROADMAP.md (this is your north star)
  └── MVP_ARCHITECTURE.md (build to this spec)
```

---

## Next Steps

### Immediately (Today)
1. **Read and agree on:**
   - MVP_ROADMAP.md (understand each sprint)
   - MVP_ARCHITECTURE.md (understand the schema)

2. **Discuss with team:**
   - Any concerns about scope?
   - Any blocking questions?
   - Any technical disagreements?

3. **Create team agreement:**
   - Will we enforce "no feature creep"?
   - Will we say "that's Phase 2" to out-of-scope requests?
   - Will we reject PRs that add to scope?

### Sprint 1 Planning (Start tomorrow or next week)
**Objective:** Build data foundation

**What to build:**
```
PostgreSQL schema:
├── companies
├── periods
├── financial_facts
├── sources
├── documents
├── derived_metrics
├── research_insights
```

**Deliverables:**
- [ ] Database schema (peer-reviewed)
- [ ] Alembic migrations
- [ ] Source registry API
- [ ] Data validation framework

**Definition of Done:**
- Schema is peer-reviewed
- Migrations run cleanly
- All relationships tested

---

## Important Principles

### Never Reverse Dependencies
```
SOURCE → INGESTION → NORMALIZATION → VALIDATION → DATABASE 
→ CALCULATIONS → RESEARCH → API → UI

NOT:
UI → Calculations
LLM → Invents data
Scraper → Populates UI
```

### Every Fact Needs Provenance
```
Revenue = 123,400 PKR million
Source = Lucky Cement Annual Report 2026
Page = 84
Date = 2026-09-30
Consolidation = Consolidated
```

### Validation Before Storage
```
PDF extracted, but validation fails?
→ Flag for manual review
→ Do NOT store unvalidated data
```

### UI Only for Validated Data
```
Questions tab = only shows for "full" coverage tier
No "coming soon" or partial states
If data isn't ready, don't show it
```

---

## What You Abandon (For Now)

These are in the `archive` branch and become Phase 2:

- ❌ Dashboard
- ❌ Ranking
- ❌ Portfolio
- ❌ Trade Planning UI
- ❌ Unified Research-Trade Flow UI
- ❌ Institutional Research modules (22-stage pipeline)
- ❌ Confidence scoring
- ❌ Multi-module experimental code

**All of this is preserved on `archive` branch.**

**When MVP proves valuable, these features come back on top of solid data foundation.**

---

## What You Keep (And Refactor)

- ✅ Research Studio (simplify for data traceability)
- ✅ Screener (keep data layer, defer frontend)
- ✅ FastAPI backend (simplify to 3 routes)
- ✅ PostgreSQL (new schema)

---

## Phase 2 Roadmap (Not starting until MVP is done)

Once MVP proves valuable:

```
MVP (Sprints 1-8)
  ↓
Expand to KSE-30 (top 30 liquid companies)
  ↓
Build sector intelligence (cement, fertilizer, E&P, banking)
  ↓
Add advanced peer comparison
  ↓
Build screening engine (on trusted data)
  ↓
ML models (on proven data quality)
  ↓
Agentic research
  ↓
PSX Pulse V2
```

**But not before MVP is solid.**

---

## Key Metrics

**After MVP (Sprint 8):**
- Research time: 90 min → 10-20 min (80% reduction)
- Data trust: Users verify sources without leaving app
- Coverage: 3 companies perfectly researched
- User satisfaction: Users would use it again

**Then Phase 2.**

---

## Team Agreements (Enforce These)

### On This Branch
- ✓ No feature creep
- ✓ No "eventually"
- ✓ No "phase 2" code
- ✓ No experimental features

### On Every PR
- [ ] PR must state which sprint it serves
- [ ] PR must not add scope
- [ ] PR must cite the MVP_ROADMAP

### If Unsure
Ask: "Does this get us to MVP?"
- YES → Do it
- NO → "That's Phase 2"

---

## Go Build

**You have:**
- ✅ Clear vision (search → financials → compare → trace)
- ✅ Frozen scope (no feature creep)
- ✅ 8-sprint roadmap (achievable)
- ✅ Clear definitions of done (testable)
- ✅ Immutable principles (enforced)

**You do NOT have:**
- ❌ 22 stages
- ❌ 8 modules
- ❌ Unvalidated confidence scores
- ❌ LLM hallucinations
- ❌ Vague "Phase 2" features

**This is focused. This is achievable. This solves a real problem.**

**Let's make it real.**

---

## Links

- **MVP Branch:** https://github.com/Eman-ik/psx-pulse/tree/mvp
- **Archive Branch:** https://github.com/Eman-ik/psx-pulse/tree/archive
- **Main (Experimental):** https://github.com/Eman-ik/psx-pulse/tree/main
