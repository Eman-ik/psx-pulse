"""
Research Studio ORM Models (R1-R7)
SQLAlchemy models for financial research database
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Numeric, BigInteger,
    Boolean, Text, JSON, ForeignKey, Index, Enum as SQLEnum,
    create_engine, select
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship, Session
import enum

Base = declarative_base()

# ============================================================================
# R1: Company Master & Registry
# ============================================================================

class Sector(Base):
    __tablename__ = "sectors"

    sector_id = Column(Integer, primary_key=True)
    sector_name = Column(String(100), nullable=False, unique=True)
    sub_sector = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    companies = relationship("Company", back_populates="sector")

class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, unique=True, index=True)
    legal_name = Column(String(255), nullable=False)
    display_name = Column(String(255))
    sector_id = Column(Integer, ForeignKey("sectors.sector_id"))
    fiscal_year_end = Column(String(20))  # "December", "June", etc.
    shares_outstanding = Column(BigInteger)
    free_float = Column(Numeric(5, 2))  # 0-100 percentage
    website = Column(String(255))
    psx_profile_url = Column(String(255))
    psx_company_id = Column(String(50))
    status = Column(String(20), default="active")  # active, suspended, delisted, merged
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sector = relationship("Sector", back_populates="companies")
    documents = relationship("Document", back_populates="company")
    financial_statements = relationship("FinancialStatement", back_populates="company")
    financial_metrics = relationship("FinancialMetric", back_populates="company")
    stock_prices = relationship("StockPrice", back_populates="company")
    valuations = relationship("Valuation", back_populates="company")
    announcements = relationship("Announcement", back_populates="company")
    corporate_events = relationship("CorporateEvent", back_populates="company")
    research_sessions = relationship("ResearchSession", back_populates="company")

# ============================================================================
# R2: Document Warehouse & Filing System
# ============================================================================

class DocumentType(str, enum.Enum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "h1"
    RESULT = "result"
    DIVIDEND = "dividend"
    BOARD_MEETING = "board_meeting"
    MATERIAL_INFO = "material_info"
    AGM = "agm"
    EOGM = "eogm"
    PRESENTATION = "presentation"

class DocumentExtractionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    MANUAL_REVIEW = "manual_review"

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    fiscal_year = Column(Integer)
    fiscal_quarter = Column(Integer)  # 1, 2, 3, 4 or NULL for annual
    announcement_date = Column(Date)
    reporting_period_end = Column(Date, index=True)
    filing_date = Column(Date)
    source = Column(String(50), nullable=False)  # 'psx', 'company_website', 'manual'
    source_url = Column(String(500))
    local_file_path = Column(String(500))
    file_size_bytes = Column(Integer)
    file_hash = Column(String(64))  # SHA-256 for deduplication
    extracted_text = Column(Text)
    extraction_status = Column(SQLEnum(DocumentExtractionStatus), default=DocumentExtractionStatus.PENDING)
    extraction_error = Column(Text)
    ocr_confidence = Column(Numeric(3, 2))  # 0-1 if OCR was used
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="documents")
    document_sources = relationship("DocumentSource", back_populates="document", cascade="all, delete-orphan")
    financial_statements = relationship("FinancialStatement", back_populates="source_document")
    financial_metrics = relationship("FinancialMetric", back_populates="source_document")

class DocumentSource(Base):
    __tablename__ = "document_sources"

    source_id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=False, index=True, ondelete="CASCADE")
    page_number = Column(Integer)
    section_type = Column(String(50), index=True)  # 'income_statement', 'balance_sheet', 'cash_flow', 'footnote', 'text'
    table_or_section_name = Column(String(255))
    extracted_text = Column(Text)
    extraction_method = Column(String(50))  # 'manual', 'ocr', 'api'
    extraction_confidence = Column(Numeric(3, 2))  # 0-1
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="document_sources")

# ============================================================================
# R3: Financial Statements & Line Items
# ============================================================================

class StatementType(str, enum.Enum):
    INCOME = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"

class AuditStatus(str, enum.Enum):
    AUDITED = "audited"
    UNAUDITED = "unaudited"
    REVIEWED = "reviewed"

class FinancialStatement(Base):
    __tablename__ = "financial_statements"

    statement_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    statement_type = Column(SQLEnum(StatementType), nullable=False)
    fiscal_year = Column(Integer, nullable=False, index=True)
    fiscal_quarter = Column(Integer)  # NULL for annual
    reporting_period_end = Column(Date, index=True)
    currency = Column(String(3), default="PKR")
    source_document_id = Column(Integer, ForeignKey("documents.document_id"))
    source_page = Column(Integer)
    is_consolidated = Column(Boolean, default=True)
    audit_status = Column(SQLEnum(AuditStatus))
    extracted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="financial_statements")
    source_document = relationship("Document", back_populates="financial_statements")
    line_items = relationship("StatementLineItem", back_populates="statement", cascade="all, delete-orphan")

class StatementLineItem(Base):
    __tablename__ = "statement_line_items"

    line_item_id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, ForeignKey("financial_statements.statement_id"), nullable=False, index=True, ondelete="CASCADE")
    line_name = Column(String(255), nullable=False)
    line_code = Column(String(50), index=True)  # standard accounting codes
    value = Column(BigInteger)  # in base units (e.g., PKR rupees, not millions)
    value_in_thousands = Column(BigInteger)  # derived: value / 1000
    line_order = Column(Integer)  # for hierarchy display
    parent_line_item_id = Column(Integer, ForeignKey("statement_line_items.line_item_id"))
    is_subtotal = Column(Boolean, default=False)
    extraction_method = Column(String(50))  # 'manual', 'ocr', 'template'
    confidence = Column(Numeric(3, 2), default=1.0)  # 0-1 for OCR extraction
    created_at = Column(DateTime, default=datetime.utcnow)

    statement = relationship("FinancialStatement", back_populates="line_items")
    parent = relationship("StatementLineItem", remote_side=[line_item_id])

# ============================================================================
# R4: Metrics & KPI Definitions
# ============================================================================

class MetricCategory(str, enum.Enum):
    PROFITABILITY = "profitability"
    EFFICIENCY = "efficiency"
    LIQUIDITY = "liquidity"
    LEVERAGE = "leverage"
    VALUATION = "valuation"
    GROWTH = "growth"

class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    metric_id = Column(Integer, primary_key=True)
    metric_code = Column(String(50), nullable=False, unique=True, index=True)  # REV, COGS, PAT, EPS, ROE, ROA, PE, PB, etc.
    display_name = Column(String(100))
    description = Column(Text)
    calculation_formula = Column(Text)  # SQL or text formula for documentation
    unit = Column(String(50))  # 'PKR', '%', 'ratio', 'years', etc.
    category = Column(SQLEnum(MetricCategory))  # profitability, efficiency, liquidity, leverage, valuation, growth
    is_sector_specific = Column(Boolean, default=False)
    calculation_method = Column(String(50))  # 'reported', 'derived', 'manual'
    created_at = Column(DateTime, default=datetime.utcnow)

    financial_metrics = relationship("FinancialMetric", back_populates="metric")

class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    metric_value_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    metric_id = Column(Integer, ForeignKey("metric_definitions.metric_id"), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False, index=True)
    fiscal_quarter = Column(Integer)  # NULL for annual
    period_end = Column(Date, index=True)
    value = Column(Numeric(18, 4))
    unit = Column(String(50))
    source_document_id = Column(Integer, ForeignKey("documents.document_id"))
    source_statement_id = Column(Integer, ForeignKey("financial_statements.statement_id"))
    is_ttm = Column(Boolean, default=False)  # trailing twelve months
    is_calculated = Column(Boolean, default=False)  # reported vs. derived
    calculation_notes = Column(Text)
    confidence = Column(Numeric(3, 2), default=1.0)  # 0-1
    calculated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="financial_metrics")
    metric = relationship("MetricDefinition", back_populates="financial_metrics")
    source_document = relationship("Document", back_populates="financial_metrics")

# ============================================================================
# R5: Stock Prices & Valuations
# ============================================================================

class StockPrice(Base):
    __tablename__ = "stock_prices"

    price_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    price_date = Column(Date, nullable=False, index=True)
    open_price = Column(Numeric(10, 2))
    high_price = Column(Numeric(10, 2))
    low_price = Column(Numeric(10, 2))
    close_price = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    market_cap = Column(BigInteger)  # in PKR (rupees)
    source = Column(String(50))  # 'psx', 'yahoo', 'manual'
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="stock_prices")

class Valuation(Base):
    __tablename__ = "valuations"

    valuation_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    valuation_date = Column(Date, nullable=False, index=True)
    metric_code = Column(String(50), nullable=False, index=True)  # pe_ratio, pb_ratio, ps_ratio, ev_ebitda, dividend_yield, fcf_yield
    metric_value = Column(Numeric(10, 4))
    sector_median = Column(Numeric(10, 4))
    sector_percentile = Column(Numeric(5, 2))  # 0-100
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="valuations")

# ============================================================================
# R6: Announcements & Corporate Events
# ============================================================================

class AnnouncementType(str, enum.Enum):
    RESULT = "result"
    DIVIDEND = "dividend"
    BOARD_MEETING = "board_meeting"
    BUYBACK = "buyback"
    RIGHT_ISSUE = "right_issue"
    MERGER = "merger"
    ACQUISITION = "acquisition"
    MATERIAL_INFO = "material_info"
    AGM = "agm"
    EOGM = "eogm"
    MANAGEMENT_CHANGE = "management_change"
    PROJECT_UPDATE = "project_update"

class Announcement(Base):
    __tablename__ = "announcements"

    announcement_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    announcement_type = Column(SQLEnum(AnnouncementType), nullable=False, index=True)
    announcement_date = Column(Date, nullable=False, index=True)
    title = Column(String(500))
    raw_text = Column(Text)
    parsed_data = Column(JSONB)  # structured extraction: {eps_new, eps_old, pat_new, pat_old, dividend, etc.}
    classification_confidence = Column(Numeric(3, 2))
    impact_score = Column(Numeric(3, 2))  # -1 to 1 (negative to positive)
    source = Column(String(50))  # 'psx', 'company_website'
    source_url = Column(String(500))
    related_document_id = Column(Integer, ForeignKey("documents.document_id"))
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="announcements")

class CorporateEvent(Base):
    __tablename__ = "corporate_events"

    event_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # groups multiple announcements
    event_date = Column(Date, index=True)
    summary = Column(Text)
    document_ids = Column(ARRAY(Integer))  # array of related document IDs
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="corporate_events")

# ============================================================================
# R7: AI Research Sessions & Responses
# ============================================================================

class ResearchSession(Base):
    __tablename__ = "research_sessions"

    session_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), index=True)
    user_id = Column(String(100))  # placeholder for auth
    session_type = Column(String(50))  # 'analysis', 'comparison', 'exploration'
    context_snapshot = Column(JSONB)  # captured metrics, announcements, etc. at time of session
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="research_sessions")
    ai_responses = relationship("AIResponse", back_populates="session", cascade="all, delete-orphan")

class AIResponse(Base):
    __tablename__ = "ai_responses"

    response_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("research_sessions.session_id"), nullable=False, index=True, ondelete="CASCADE")
    query = Column(Text, nullable=False)
    response_text = Column(Text)
    source_citations = Column(JSONB)  # [{document_id, page, metric_id, line_item_id}, ...]
    confidence_score = Column(Numeric(3, 2))
    generated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ResearchSession", back_populates="ai_responses")

# ============================================================================
# Utility: Audit Trail & Data Lineage
# ============================================================================

class DataLineage(Base):
    __tablename__ = "data_lineage"

    lineage_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), index=True)
    metric_code = Column(String(50))
    metric_value_id = Column(Integer, ForeignKey("financial_metrics.metric_value_id"), index=True)
    source_document_id = Column(Integer, ForeignKey("documents.document_id"), index=True)
    source_page = Column(Integer)
    source_section = Column(String(255))
    extracted_text_snippet = Column(Text)
    calculation_chain = Column(JSONB)  # JSON array of calculation steps
    verified_by = Column(String(100))
    verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
