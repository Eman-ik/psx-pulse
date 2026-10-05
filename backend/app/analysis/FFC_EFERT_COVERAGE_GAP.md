# FFC & EFERT: Data Coverage Gap Matrix

## Expected Data Requirements

To achieve genuine 100% data coverage, each company requires:

### Financial Statements (Annual: 5 years minimum)
| Field | Expected | Status | Missing |
|-------|----------|--------|---------|
| Revenue | FY2021–FY2025 | ✓ | None |
| Gross Profit | FY2021–FY2025 | ✓ | None |
| Operating Profit (EBIT) | FY2021–FY2025 | ✓ | None |
| Profit After Tax (PAT) | FY2021–FY2025 | ✓ | None |
| Operating Cash Flow | FY2021–FY2025 | ✗ | ALL YEARS |
| Finance Cost (Interest) | FY2021–FY2025 | ✓ | None |
| Tax Expense | FY2021–FY2025 | ✓ | None |
| Other Income | FY2021–FY2025 | ✗ | FY2025 (has FY2024) |

### Balance Sheet (Annual: 5 years minimum)
| Field | Expected | Status | Missing |
|-------|----------|--------|---------|
| Total Equity | FY2021–FY2025 | ✓ | None |
| Total Debt | FY2021–FY2025 | ✓ | None |
| Accounts Receivable | FY2021–FY2025 | ✓ | None |
| Inventory | FY2021–FY2025 | ✓ | None |

### Shareholder Metrics (Annual)
| Field | Expected | Status | Missing |
|-------|----------|--------|---------|
| EPS (Earnings Per Share) | FY2021–FY2025 | ✓ | None |
| DPS (Dividend Per Share) | FY2021–FY2025 | ✓ | None |

### Valuation (Point-in-time)
| Field | Expected | Status | Missing |
|-------|----------|--------|---------|
| Current P/E | Latest (as of 2026-10-02) | ✓ | None |
| Historical P/E | 5 years (FY2021–FY2025) | ✗ | **Only current available** |
| P/B Ratio | Latest | ✓ | None |
| ROE | Calculated from equity + PAT | ✓ | None |
| Sector Median P/E | Latest | ✗ | MISSING |

### Technical Data
| Field | Expected | Status | Missing |
|-------|----------|--------|---------|
| Daily Close Prices | ≥252 trading days | ✓ | None |

### Company Metadata
| Field | Expected | Status | Missing |
|-------|----------|--------|---------|
| Company Profile | Current | ✓ | None |
| Sector Classification | Current | ✓ | None |
| PSX Announcements | Recent (last 6 months) | ✓ | None |

---

## FFC (Fauji Fertilizer Co)

### Current Coverage Status
**Available Data Points:** 16 of 20 critical fields
**Missing Critical Inputs:**
1. Operating Cash Flow — All 5 years
2. Historical P/E Series — All 5 years  
3. Sector Median P/E — Current
4. Other Income — FY2025 only

### Current Coverage Calculation
- Business Health: 83% (5 of 6 metrics: rev, pat, gp, nm, de; missing ocf)
- What Changed: 50% (4 of 8 comparisons measurable; ocf + others blocked by data gaps)
- Earnings Quality: 65% (4 of 6 evidence pieces; missing ocf + other_income)
- Valuation: 70% (current pe only; missing hist pe, sector median)
- **Composite: 64%** (average before consistency penalty)

### Path to 100% Coverage
| Gap | Effort | Impact | Priority |
|-----|--------|--------|----------|
| Operating Cash Flow (5 years) | 4–6 hrs | +20% | CRITICAL |
| Historical P/E (5 years) | 1–2 hrs | +10% | HIGH |
| Other Income (FY2025) | 30 min | +3% | MEDIUM |
| Sector Median P/E | 30 min | +7% | HIGH |

**Estimated Final Coverage:** 100% (after all 4 gaps filled)

---

## EFERT (Engro Fertilizer)

### Current Coverage Status  
**Available Data Points:** 17 of 20 critical fields
**Missing Critical Inputs:**
1. Operating Cash Flow — All 5 years
2. Historical P/E Series — All 5 years
3. Sector Median P/E — Current

EFERT is in better position than FFC (has all 5 years of Other Income).

### Current Coverage Calculation
- Business Health: 83% (5 of 6 metrics; missing ocf)
- What Changed: 50% (4 of 8 comparisons; ocf + others blocked)
- Earnings Quality: 70% (5 of 6 evidence pieces; missing ocf only)
- Valuation: 70% (current pe only; missing hist pe, sector median)
- **Composite: 68%** (average before consistency penalty)

### Path to 100% Coverage
| Gap | Effort | Impact | Priority |
|-----|--------|--------|----------|
| Operating Cash Flow (5 years) | 4–6 hrs | +20% | CRITICAL |
| Historical P/E (5 years) | 1–2 hrs | +10% | HIGH |
| Sector Median P/E | 30 min | +7% | HIGH |

**Estimated Final Coverage:** 100% (after all 3 gaps filled)

---

## Shared Data Sources

These three items will fix BOTH companies simultaneously:

### 1. Operating Cash Flow Ingestion (4–6 hours)
**Source:** PSX Annual Reports → Cash Flow Statements
**Period:** FY2021, FY2022, FY2023, FY2024, FY2025
**Method:**
- Parse "Operating Cash Flow" line from audited cash flow statements
- Both companies are PSX-listed; OCF is mandatory disclosure
- Store in: `financial_metrics.operating_cash_flow` with period alignment

**File to Modify:** `backend/app/etl/financials_ingestion.py`
- Add function: `parse_cash_flow_statement(annual_report_pdf)`
- Map line items to database schema

### 2. Historical P/E Series (1–2 hours)
**Source:** PSX Historical Price Data + Existing EPS Series
**Period:** FY2021–FY2025 year-end
**Calculation:** `P/E(year) = YearEndPrice(year) / Annual EPS(year)`
**Method:**
- Use existing price_history table filtered to FY year-end dates
- Join with existing eps series (already in database)
- Calculate and store in: `valuation_multiples.historical_pe`

**File to Modify:** `backend/app/etl/valuation_ingestion.py`
- Add function: `calculate_historical_pe_series(issuer_id, start_year, end_year)`
- Query logic: `WHERE date = last_trading_day_of_year(year)`

### 3. Sector Median P/E (30 min)
**Source:** Computed from all PSX Fertilizer companies
**Universe:** FFC, EFERT, MARI (ICI Pakistan), AICL (available if data exists)
**Method:**
- Query current P/E for all 4 fertilizer companies
- Calculate median
- Cache and refresh quarterly

**File to Modify:** `backend/app/analysis/valuation_context.py`
- Add method: `get_sector_median_pe(sector: str, as_of_date: date) -> float`
- Fallback: Use median of available peers if not all 4 have data

---

## Total Effort & Timeline

**FFC:** 9–11 hours to 100%
**EFERT:** 8–10 hours to 100%
**Both in parallel:** ~10–12 hours (shared work on 3 ingestion tasks)

### Phased Approach (Recommended)

**Phase 1 (2 hours)** — Quick wins; reach ~75–80%
- Ingest Other Income FY2025 (FFC only)
- Calculate Sector Median P/E
- Calculate Historical P/E Series

**Phase 2 (4–6 hours)** — OCF ingestion; reach ~95–100%
- Build OCF parser
- Ingest OCF for both companies (FY2021–FY2025)
- Validate cross-engine consistency

**Phase 3 (2 hours)** — Testing & reporting
- Unit tests for 100% coverage scenario
- Integration tests for immaterial-change handling
- Final gap validation

---

## Next Step

Once this gap matrix is reviewed and prioritized:
1. Which gaps to address first?
2. Can you provide OCF data for FY2021–FY2025 for both companies (from their audited annual reports)?
3. Once data is ready, ingestion sequence will be straightforward.

**Honest coverage is the goal:** 76% with exact explanation > 100% with hard-coded ceilings.
