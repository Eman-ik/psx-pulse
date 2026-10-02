# Running the Data Provenance Migration

## Prerequisites

```bash
cd backend
pip install -e .  # Install the project in editable mode
```

## Apply Migration

```bash
cd backend
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade ... -> f7e8d9c0a1b2
```

## What Changed in DB

1. **price_ohlcv table:**
   - Added `is_synthetic BOOLEAN DEFAULT false` (indexed)
   - Added `quality_status VARCHAR(20) DEFAULT 'unknown'` (check constraint)

2. **index_ohlcv table:**
   - Added `is_synthetic BOOLEAN DEFAULT false` (indexed)
   - Added `quality_status VARCHAR(20) DEFAULT 'unknown'` (check constraint)

3. **Existing data:**
   - All existing rows get `is_synthetic = false` (assume real)
   - All existing rows get `quality_status = 'unknown'` (legacy, needs audit)

## Post-Migration: Data Audit

After running the migration, identify and upgrade legacy rows:

```sql
-- View all legacy/unverified rows
SELECT COUNT(*) FROM price_ohlcv WHERE quality_status = 'unknown';

-- Mark psxdata rows as verified (they came from real PSX source)
UPDATE price_ohlcv 
SET quality_status = 'verified' 
WHERE source = 'psxdata' AND quality_status = 'unknown';

-- Mark other sources appropriately
UPDATE price_ohlcv 
SET quality_status = 'provisional' 
WHERE source = 'investing_com' AND quality_status = 'unknown';

-- Verify results
SELECT source, quality_status, COUNT(*) FROM price_ohlcv 
GROUP BY source, quality_status;
```

## Rollback (if needed)

```bash
alembic downgrade -1
```

---

**Status:** Safe to run on development DB. Test in staging before production.
