# PSX Data Ingestion Scripts

This directory contains scripts to ingest real-time PSX (Pakistan Stock Exchange) data into the research platform.

## Prerequisites

1. **Database**: PostgreSQL must be running and accessible at the configured connection string
2. **Python Dependencies**: Already installed (psxdata, sqlalchemy, psycopg2)
3. **Backend Environment**: .env file configured with database credentials

## Scripts

### 1. ingest_real_data.py
Complete data ingestion pipeline that fetches and populates:
- **Symbols**: All PSX listed companies and their metadata
- **Quotes**: Current prices (OHLCV) for all securities
- **Fundamentals**: EPS, P/E ratio, Book Value, Market Cap, Dividend Yield
- **Indices**: KSE-100, KSE-30, KMI-30 levels

**Usage:**
```bash
cd backend
python scripts/ingest_real_data.py
```

**Output:**
- Creates/updates Security, Issuer, Sector records
- Populates PriceOHLCV with today's quotes
- Populates FinancialFact with latest fundamentals
- Populates IndexOHLCV with today's index levels

**Time to Complete:** 2-5 minutes (first run takes longer due to initial data load)

### 2. ingest_daily_update.py (Optional - scheduled)
Can be run daily via cron/scheduler to keep data current:
```bash
# Linux/Mac cron job (runs daily at 16:00 - after market close)
0 16 * * 1-5 cd /path/to/backend && python scripts/ingest_real_data.py

# Windows Task Scheduler
# Create task to run: python scripts/ingest_real_data.py
# Recurrence: Daily at 16:00
```

## What Gets Populated

### Securities Table
- All PSX listed companies
- Company names and symbols
- Sector classification
- Market cap and listing date

### Prices Table (PriceOHLCV)
- Daily OHLCV data
- Current bid/ask spreads (if available)
- Trading volume
- Timestamp for each update

### Fundamentals Table (FinancialFact)
- EPS (Earnings Per Share)
- P/E Ratio
- Book Value Per Share
- Market Capitalization
- Dividend Yield
- Price-to-Book Ratio

### Indices Table (IndexOHLCV)
- KSE-100: Main equity index
- KSE-30: Large-cap index
- KMI-30: Medium-cap index

## Impact on Research Studio & Screeners

Once data is ingested:

### ✅ Research Studio (`/research`)
- **Company Terminal**: Real fundamentals displayed
- **Valuation Context**: P/E, P/B, Dividend Yield calculated
- **Peer Comparison**: Real market cap and metrics
- **18 Sections**: All sections have real data to analyze

### ✅ Screeners (`/screening`, `/technical`, `/momentum`)
- **Fundamental Screener**: Filters on real P/E, profitability, growth
- **Technical Screener**: Moving averages, RSI based on real prices
- **Momentum Screener**: Real multi-period returns calculated

### ✅ Market Overview (`/market`)
- **Live Indices**: KSE-100/30/KMI-30 real levels
- **Market Breadth**: Real advancers/decliners
- **Top Gainers/Losers**: Based on actual price movement
- **WebSocket**: Real prices stream to frontend

## Database Requirements

### Existing Tables (Auto-created by Alembic)
- `security` - Company/stock definitions
- `issuer` - Company information
- `sector` - Industry sectors
- `price_ohlcv` - Daily price data
- `financial_fact` - Fundamental metrics
- `market_index` - Index definitions
- `index_ohlcv` - Index levels

### Indexing
The ingestion script automatically uses indexed lookups for performance:
- symbol (Security)
- trade_date (PriceOHLCV, IndexOHLCV)
- market_index_id (IndexOHLCV)

## Error Handling

The ingestion script includes:
- ✅ Retry logic for network failures
- ✅ Graceful handling of missing data
- ✅ Transaction rollback on errors
- ✅ Detailed logging of all operations
- ✅ Duplicate prevention (checks before inserting)

## Troubleshooting

### "Connection refused" Error
**Problem**: PostgreSQL is not running
**Solution**: 
```bash
# Windows
net start postgresql-x64-14

# Linux
sudo systemctl start postgresql

# Mac
brew services start postgresql
```

### "No such module" Error
**Problem**: Python dependencies not installed
**Solution**:
```bash
pip install psxdata sqlalchemy psycopg2-binary
```

### "Permission denied" Error
**Problem**: User lacks database write permissions
**Solution**:
```bash
# Grant permissions to database user
psql -U postgres -c "GRANT ALL ON DATABASE khronos TO your_user;"
```

### Script runs but shows no data
**Problem**: PSX API is down or rate-limited
**Solution**:
- Wait 5 minutes and try again
- Check PSX website for maintenance windows
- Verify internet connection

## Data Freshness

- **Quotes**: Updated daily after market close (16:00 PKT)
- **Fundamentals**: Updated quarterly when new reports released
- **Indices**: Updated daily
- **WebSocket**: Real-time simulation via mock provider (can be connected to real feed)

## Next Steps

1. **Ensure PostgreSQL is running**
   ```bash
   psql -U postgres -d khronos -c "SELECT COUNT(*) FROM security;"
   ```

2. **Run the ingestion script**
   ```bash
   python backend/scripts/ingest_real_data.py
   ```

3. **Verify data**
   ```bash
   # Check securities loaded
   curl http://localhost:5000/api/companies
   
   # Check market overview
   curl http://localhost:5000/market/overview/snapshot
   ```

4. **Access the frontend**
   - Research Studio: http://localhost:3000/research
   - Screeners: http://localhost:3000/screening
   - Market: http://localhost:3000/market

## Support

If you encounter issues:
1. Check PostgreSQL is running
2. Verify .env configuration
3. Review logs in console output
4. Check PSX website status
5. Try again in a few minutes
