# Data Provenance & Source Policy

## Core Principle

**No synthetic, fabricated, or mock data may flow into research outputs.**

Every row in the system must be traceable to its origin. Missing data is acceptable; invented data is not.

---

## Source of Truth: Verified Data

### Market Prices (`price_ohlcv`, `index_ohlcv`)

| Source | Provider | Quality Status | Coverage | Usage |
|--------|----------|--------|----------|-------|
| PSX Historical | `psxdata` | `verified` | Daily since ~2010 | Technical analysis, backtesting, ML training |
| — | — | — | — | — |

**Rule:** All bars in production must have:
- `source = 'psxdata'`
- `is_synthetic = false`
- `quality_status = 'verified'`

Any other combination indicates a development/test fixture.

### Fundamentals & Financials

| Source | Document Type | Quality Status | Coverage |
|--------|---|--------|---|
| PSX Announcements | Annual/Quarterly/H1 | `verified` | 13 covered issuers, ~3yr lookback |
| SBP Macro Data | Benchmark indices | `verified` | Monthly, 10yr+ |
| — | — | — | — |

**Rule:** Every fact must link to a `SourceDocument`:
- PSX filing PDF (source_tier='primary')
- Company announcement
- Official regulatory publication

No manual seed data in production. Dev fixtures go in `backend/fixtures/`.

### Indices

| Index | Source | Quality Status |
|-------|--------|--------|
| KSE-100 | `psxdata` | `verified` |

---

## Development & Testing: Demo Data Only

### When Demo Data Is Appropriate

- Unit tests (use factories, fixtures, not production DB)
- Feature development before real data is available
- Integration tests with small golden datasets
- Frontend prototypes

### How to Enable Demo Data

```bash
# Mark data as synthetic in code:
IndexOHLCV(..., is_synthetic=True, quality_status='provisional')

# Or use an explicit dev environment variable:
KHRONOS_ENV=development
ENABLE_SYNTHETIC_PRICES=true  # never true in production
```

### Demo Data Guardrails

1. **Cannot be in production DB.** Use fixtures, in-memory DB, or separate dev database.
2. **Must be explicitly labeled.** `is_synthetic=True` is non-negotiable.
3. **Must be invisible to end users.** No synthetic data in `/research` or `/trade-planning` endpoints.
4. **Must be version-controlled as code.** `backend/fixtures/sample_companies.json`, never committed binary DB files.

---

## Quality Status Enum

Every price bar and fact carries a `quality_status`:

| Status | Meaning | Allowed In Research? |
|--------|---------|---|
| `unknown` | Legacy row, origin unclear | ❌ No — quarantine and audit |
| `verified` | From trusted source, cross-checked | ✅ Yes |
| `provisional` | Best effort, real attempt, may have gaps | ⚠️ Yes, with visibility of status |
| `rejected` | Known bad, should not be used | ❌ No — quarantine |

### Visibility Rules

- **verified/provisional:** Can be used in analysis. Frontend displays `quality_status` badge.
- **unknown/rejected:** Blocked at API boundary. Analyst must audit before use.

---

## Ingestion Runs & Audit Trail

Every data load creates an `IngestionRun`:

```
ingestion_run
├─ id: 42
├─ source: 'psxdata'
├─ started_at: 2026-10-02T14:30:00Z
├─ status: 'ok'
├─ rows_inserted: 252
├─ rows_rejected: 0
└─ errors: []

price_ohlcv rows 1001-1252 all have: ingestion_run_id=42
```

**Use:** Trace any price bar back to its load run. Inspect that run's log for errors.

---

## Preventing Synthetic Data Contamination

### What Not To Do

```python
# ❌ NEVER: Random fallback
try:
    data = fetch_from_psx()
except:
    data = generate_synthetic_data()  # This is how data got poisoned
    
# ❌ NEVER: Hardcoded fundamentals
return {'eps': 10.5, 'pe_ratio': 12}  # Fake data masquerading as research

# ❌ NEVER: WebSocket of random prices in production
asyncio.create_task(mock_market_feed())  # Investor sees invented prices
```

### What To Do Instead

```python
# ✅ DO: Explicit missing data
try:
    data = fetch_from_psx()
except PSXError as e:
    logger.error("PSX unavailable: %s", e)
    # Return None, not invented data
    # Frontend shows "Data unavailable"
    
# ✅ DO: Explicit fixtures
@pytest.fixture
def sample_ffc():
    return {
        'ticker': 'FFC',
        'eps': 15.2,  # From 2026-01-30 PSX announcement
        'source': 'tests/fixtures/ffc_q3_2025.json',
    }
    
# ✅ DO: Feature-flag demo data
if os.getenv("ENABLE_DEMO_REALTIME") == "true":
    asyncio.create_task(mock_market_feed())  # Dev only
```

---

## Enforcement

### At the Database Layer

```sql
-- All price bars must declare a source
ALTER TABLE price_ohlcv ADD CONSTRAINT ck_price_ohlcv_source_nonempty 
  CHECK (source <> '');

-- Quality status is constrained to enum
ALTER TABLE price_ohlcv ADD CONSTRAINT ck_price_ohlcv_quality_status 
  CHECK (quality_status IN ('unknown', 'verified', 'provisional', 'rejected'));
```

### At the API Layer

```python
# Research endpoints reject low-quality data
@router.get("/research-intelligence/{ticker}/analysis")
def research_analysis(ticker: str, db: Session = Depends(get_db)):
    # All prices used must have quality_status != 'rejected'
    prices = db.query(PriceOHLCV).filter(
        PriceOHLCV.quality_status != 'rejected',
        PriceOHLCV.is_synthetic == False,
    )
    # If insufficient real data, response indicates so
    coverage = len(prices)
    if coverage < 252:
        return {..., "data_coverage_pct": (coverage/252)*100}
```

### In Tests (CI/CD)

```python
def test_no_synthetic_data_in_research():
    """Ensure production research endpoints never serve synthetic bars."""
    response = client.get("/research-intelligence/FFC/analysis")
    assert response.status_code == 200
    prices = response.json()["prices"]
    assert all(not p["is_synthetic"] for p in prices)
```

---

## Rollback / Data Cleanup

If synthetic data is discovered in production:

1. **Identify the ingestion run:**
   ```sql
   SELECT DISTINCT ingestion_run_id FROM price_ohlcv 
   WHERE is_synthetic = true OR quality_status IN ('unknown', 'rejected');
   ```

2. **Quarantine the data:**
   ```sql
   UPDATE price_ohlcv SET quality_status = 'rejected'
   WHERE ingestion_run_id IN (...suspect runs...);
   ```

3. **Audit the run:**
   ```sql
   SELECT * FROM ingestion_run WHERE id = ...;
   SELECT * FROM ingestion_run.errors WHERE ingestion_run_id = ...;
   ```

4. **Rebuild from real source:**
   ```bash
   python -m app.ingestion.psx_prices --since 2025-01-01
   ```

---

## FAQ

**Q: Can I use 10-year estimated data while we build the real historical API?**
A: No. If the data is not available, say so. Use `data_coverage_pct` to show users what you have.

**Q: What if PSX goes offline for a day?**
A: The ingestion run records the error. Analysts see that data for that day is unavailable. You do not synthesize a price.

**Q: When is synthetic data acceptable?**
A: Tests, demos, and local development only. Never shipped to users.

**Q: Who verifies that data is actually from PSX?**
A: The ingestion script logs the source and run ID. Spot-check the PDF/filing.  Ultimately: the analyst reading the data is responsible. We make that responsibility visible.

---

**Last updated:** 2026-10-02  
**Next review:** When adding new data sources
