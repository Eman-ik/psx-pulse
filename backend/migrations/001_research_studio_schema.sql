-- Research Studio: Core Schema (R1-R7)
-- PostgreSQL

-- ============================================================================
-- R1: Company Master & Registry
-- ============================================================================

CREATE TABLE IF NOT EXISTS sectors (
    sector_id SERIAL PRIMARY KEY,
    sector_name VARCHAR(100) NOT NULL UNIQUE,
    sub_sector VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
    company_id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    legal_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    sector_id INTEGER REFERENCES sectors(sector_id),
    fiscal_year_end VARCHAR(20), -- "December", "June", etc.
    shares_outstanding BIGINT,
    free_float DECIMAL(5,2), -- 0-100 percentage
    website VARCHAR(255),
    psx_profile_url VARCHAR(255),
    psx_company_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, delisted, merged
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_companies_ticker ON companies(ticker);
CREATE INDEX idx_companies_sector ON companies(sector_id);

-- ============================================================================
-- R2: Document Warehouse & Filing System
-- ============================================================================

CREATE TABLE IF NOT EXISTS documents (
    document_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id),
    document_type VARCHAR(50) NOT NULL, -- annual, quarterly, h1, result, dividend, board_meeting, material_info, ags, eogm, presentation
    fiscal_year INTEGER,
    fiscal_quarter INTEGER, -- 1, 2, 3, 4 or NULL for annual
    announcement_date DATE,
    reporting_period_end DATE,
    filing_date DATE,
    source VARCHAR(50) NOT NULL, -- 'psx', 'company_website', 'manual'
    source_url VARCHAR(500),
    local_file_path VARCHAR(500),
    file_size_bytes INTEGER,
    file_hash VARCHAR(64), -- SHA-256 for deduplication
    extracted_text TEXT,
    extraction_status VARCHAR(50) DEFAULT 'pending', -- pending, success, failed, manual_review
    extraction_error TEXT,
    ocr_confidence DECIMAL(3,2), -- 0-1 if OCR was used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_company ON documents(company_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_fiscal ON documents(fiscal_year, fiscal_quarter);
CREATE INDEX idx_documents_date ON documents(announcement_date, reporting_period_end);

CREATE TABLE IF NOT EXISTS document_sources (
    source_id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    page_number INTEGER,
    section_type VARCHAR(50), -- 'income_statement', 'balance_sheet', 'cash_flow', 'footnote', 'text'
    table_or_section_name VARCHAR(255),
    extracted_text TEXT,
    extraction_method VARCHAR(50), -- 'manual', 'ocr', 'api'
    extraction_confidence DECIMAL(3,2), -- 0-1
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_sources_document ON document_sources(document_id);
CREATE INDEX idx_document_sources_section ON document_sources(section_type);

-- ============================================================================
-- R3: Financial Statements & Line Items
-- ============================================================================

CREATE TABLE IF NOT EXISTS financial_statements (
    statement_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id),
    statement_type VARCHAR(50) NOT NULL, -- 'income_statement', 'balance_sheet', 'cash_flow'
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER, -- NULL for annual
    reporting_period_end DATE,
    currency VARCHAR(3) DEFAULT 'PKR',
    source_document_id INTEGER REFERENCES documents(document_id),
    source_page INTEGER,
    is_consolidated BOOLEAN DEFAULT TRUE,
    audit_status VARCHAR(50), -- 'audited', 'unaudited', 'reviewed'
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_financial_statements_company ON financial_statements(company_id);
CREATE INDEX idx_financial_statements_period ON financial_statements(fiscal_year, fiscal_quarter);

CREATE TABLE IF NOT EXISTS statement_line_items (
    line_item_id SERIAL PRIMARY KEY,
    statement_id INTEGER NOT NULL REFERENCES financial_statements(statement_id) ON DELETE CASCADE,
    line_name VARCHAR(255) NOT NULL,
    line_code VARCHAR(50), -- standard accounting codes
    value BIGINT, -- in base units (e.g., PKR rupees, not millions)
    value_in_thousands BIGINT, -- derived: value / 1000
    line_order INTEGER, -- for hierarchy display
    parent_line_item_id INTEGER REFERENCES statement_line_items(line_item_id),
    is_subtotal BOOLEAN DEFAULT FALSE,
    extraction_method VARCHAR(50), -- 'manual', 'ocr', 'template'
    confidence DECIMAL(3,2), -- 0-1 for OCR extraction
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_statement_line_items_statement ON statement_line_items(statement_id);
CREATE INDEX idx_statement_line_items_code ON statement_line_items(line_code);

-- ============================================================================
-- R4: Metrics & KPI Definitions
-- ============================================================================

CREATE TABLE IF NOT EXISTS metric_definitions (
    metric_id SERIAL PRIMARY KEY,
    metric_code VARCHAR(50) NOT NULL UNIQUE, -- REV, COGS, GROSS_PROFIT, PAT, EPS, ROE, ROA, PE, PB, etc.
    display_name VARCHAR(100),
    description TEXT,
    calculation_formula TEXT, -- SQL or text formula for documentation
    unit VARCHAR(50), -- 'PKR', '%', 'ratio', 'years', etc.
    category VARCHAR(50), -- 'profitability', 'efficiency', 'liquidity', 'leverage', 'valuation', 'growth'
    is_sector_specific BOOLEAN DEFAULT FALSE,
    calculation_method VARCHAR(50), -- 'reported', 'derived', 'manual'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metric_definitions_code ON metric_definitions(metric_code);

CREATE TABLE IF NOT EXISTS financial_metrics (
    metric_value_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id),
    metric_id INTEGER NOT NULL REFERENCES metric_definitions(metric_id),
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER, -- NULL for annual
    period_end DATE,
    value DECIMAL(18,4),
    unit VARCHAR(50),
    source_document_id INTEGER REFERENCES documents(document_id),
    source_statement_id INTEGER REFERENCES financial_statements(statement_id),
    is_ttm BOOLEAN DEFAULT FALSE, -- trailing twelve months
    is_calculated BOOLEAN DEFAULT FALSE, -- reported vs. derived
    calculation_notes TEXT,
    confidence DECIMAL(3,2) DEFAULT 1.0, -- 0-1
    calculated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_financial_metrics_company ON financial_metrics(company_id);
CREATE INDEX idx_financial_metrics_metric ON financial_metrics(metric_id);
CREATE INDEX idx_financial_metrics_period ON financial_metrics(fiscal_year, fiscal_quarter);
CREATE INDEX idx_financial_metrics_date ON financial_metrics(period_end);
CREATE UNIQUE INDEX idx_financial_metrics_unique ON financial_metrics(company_id, metric_id, fiscal_year, fiscal_quarter);

-- ============================================================================
-- R5: Stock Prices & Valuations
-- ============================================================================

CREATE TABLE IF NOT EXISTS stock_prices (
    price_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id),
    price_date DATE NOT NULL,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    volume BIGINT,
    market_cap BIGINT, -- in PKR (rupees)
    source VARCHAR(50), -- 'psx', 'yahoo', 'manual'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stock_prices_company ON stock_prices(company_id);
CREATE INDEX idx_stock_prices_date ON stock_prices(price_date);
CREATE UNIQUE INDEX idx_stock_prices_unique ON stock_prices(company_id, price_date);

CREATE TABLE IF NOT EXISTS valuations (
    valuation_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id),
    valuation_date DATE NOT NULL,
    metric_code VARCHAR(50) NOT NULL, -- pe_ratio, pb_ratio, ps_ratio, ev_ebitda, dividend_yield, fcf_yield
    metric_value DECIMAL(10,4),
    sector_median DECIMAL(10,4),
    sector_percentile DECIMAL(5,2), -- 0-100
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_valuations_company ON valuations(company_id);
CREATE INDEX idx_valuations_date ON valuations(valuation_date);
CREATE INDEX idx_valuations_metric ON valuations(metric_code);

-- ============================================================================
-- R6: Announcements & Corporate Events
-- ============================================================================

CREATE TABLE IF NOT EXISTS announcements (
    announcement_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id),
    announcement_type VARCHAR(50) NOT NULL, -- 'result', 'dividend', 'board_meeting', 'buyback', 'right_issue', 'merger', 'acquisition', 'material_info', 'agm', 'management_change', 'project_update'
    announcement_date DATE NOT NULL,
    title VARCHAR(500),
    raw_text TEXT,
    parsed_data JSONB, -- structured extraction: {eps_new, eps_old, pat_new, pat_old, dividend, etc.}
    classification_confidence DECIMAL(3,2),
    impact_score DECIMAL(3,2), -- -1 to 1 (negative to positive)
    source VARCHAR(50), -- 'psx', 'company_website'
    source_url VARCHAR(500),
    related_document_id INTEGER REFERENCES documents(document_id),
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_announcements_company ON announcements(company_id);
CREATE INDEX idx_announcements_type ON announcements(announcement_type);
CREATE INDEX idx_announcements_date ON announcements(announcement_date);

CREATE TABLE IF NOT EXISTS corporate_events (
    event_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id),
    event_type VARCHAR(50) NOT NULL, -- groups multiple announcements
    event_date DATE,
    summary TEXT,
    document_ids INTEGER[], -- array of related document IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_corporate_events_company ON corporate_events(company_id);
CREATE INDEX idx_corporate_events_date ON corporate_events(event_date);

-- ============================================================================
-- R7: AI Research Sessions & Responses
-- ============================================================================

CREATE TABLE IF NOT EXISTS research_sessions (
    session_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(company_id),
    user_id VARCHAR(100), -- placeholder for auth
    session_type VARCHAR(50), -- 'analysis', 'comparison', 'exploration'
    context_snapshot JSONB, -- captured metrics, announcements, etc. at time of session
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_responses (
    response_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES research_sessions(session_id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    response_text TEXT,
    source_citations JSONB, -- [{document_id, page, metric_id, line_item_id}, ...]
    confidence_score DECIMAL(3,2),
    generated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_responses_session ON ai_responses(session_id);

-- ============================================================================
-- Utility: Audit Trail
-- ============================================================================

CREATE TABLE IF NOT EXISTS data_lineage (
    lineage_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(company_id),
    metric_code VARCHAR(50),
    metric_value_id INTEGER REFERENCES financial_metrics(metric_value_id),
    source_document_id INTEGER REFERENCES documents(document_id),
    source_page INTEGER,
    source_section VARCHAR(255),
    extracted_text_snippet TEXT,
    calculation_chain TEXT, -- JSON array of calculation steps
    verified_by VARCHAR(100),
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_lineage_metric ON data_lineage(metric_value_id);
CREATE INDEX idx_data_lineage_document ON data_lineage(source_document_id);
