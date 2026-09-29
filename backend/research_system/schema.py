"""
Khronos Research & Information System — Data Model

Sprint 1-3: Security Master + Document Foundation + Financial Schema

This is the intellectual core of Khronos.
Data first → normalization second → calculations third → research intelligence fourth → UI fifth → AI last.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum, Numeric, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ════════════════════════════════════════════════════════════════════════════════
# SPRINT 1: SECURITY MASTER
# ════════════════════════════════════════════════════════════════════════════════

class Sector(Base):
    """PSX sector classification."""
    __tablename__ = "sector"

    sector_id = Column(Integer, primary_key=True)
    sector_name = Column(String(100), unique=True, nullable=False)
    # Example: "Fertilizer", "Cement", "Banking", "E&P"

    securities = relationship("Security", back_populates="sector")
    industries = relationship("Industry", back_populates="sector")

    def __repr__(self):
        return f"<Sector {self.sector_name}>"


class Industry(Base):
    """PSX industry classification."""
    __tablename__ = "industry"

    industry_id = Column(Integer, primary_key=True)
    industry_name = Column(String(100), nullable=False)
    sector_id = Column(Integer, ForeignKey("sector.sector_id"), nullable=False)

    sector = relationship("Sector", back_populates="industries")
    securities = relationship("Security", back_populates="industry")

    def __repr__(self):
        return f"<Industry {self.industry_name}>"


class ListingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELISTED = "DELISTED"


class Security(Base):
    """
    PSX security master.
    Single source of truth for company identity.
    """
    __tablename__ = "security"

    security_id = Column(Integer, primary_key=True)
    ticker = Column(String(10), unique=True, nullable=False)
    # Example: "FFC", "EFERT", "LUCK"

    company_name = Column(String(200), nullable=False)
    # Example: "Fauji Fertilizer Company Limited"

    legal_name = Column(String(300))
    # Official registered name

    sector_id = Column(Integer, ForeignKey("sector.sector_id"), nullable=False)
    industry_id = Column(Integer, ForeignKey("industry.industry_id"), nullable=False)

    listing_status = Column(SQLEnum(ListingStatus), default=ListingStatus.ACTIVE)
    listing_date = Column(Date)

    fiscal_year_end = Column(String(5))  # "30-JUN", "31-DEC", etc.

    shares_outstanding = Column(Numeric(20, 0))  # Number of shares
    free_float = Column(Float)  # Percentage (0-100)

    website = Column(String(255))
    psx_profile_url = Column(String(500))

    registered_office = Column(Text)

    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sector = relationship("Sector", back_populates="securities")
    industry = relationship("Industry", back_populates="securities")
    company_profile = relationship("CompanyProfile", uselist=False, back_populates="security")
    documents = relationship("Document", back_populates="security")
    announcements = relationship("Announcement", back_populates="security")
    financial_periods = relationship("FinancialPeriod", back_populates="security")

    def __repr__(self):
        return f"<Security {self.ticker}: {self.company_name}>"


class CompanyProfile(Base):
    """Company metadata (business, structure, people)."""
    __tablename__ = "company_profile"

    profile_id = Column(Integer, primary_key=True)
    security_id = Column(Integer, ForeignKey("security.security_id"), unique=True, nullable=False)

    description = Column(Text)  # Business description
    business_model = Column(Text)  # How they make money
    products_services = Column(Text)  # Products/services list
    geographies = Column(Text)  # Geographic presence (CSV or JSON)
    major_segments = Column(Text)  # Business segments

    subsidiaries = Column(Text)  # Subsidiary list
    holding_company = Column(String(100))  # Parent company if applicable

    auditor = Column(String(100))  # Audit firm

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    security = relationship("Security", back_populates="company_profile")

    def __repr__(self):
        return f"<CompanyProfile {self.security_id}>"


# ════════════════════════════════════════════════════════════════════════════════
# SPRINT 1: SOURCE REGISTRY
# ════════════════════════════════════════════════════════════════════════════════

class SourceType(str, Enum):
    PSX = "PSX"
    ANNUAL_REPORT = "ANNUAL_REPORT"
    QUARTERLY_REPORT = "QUARTERLY_REPORT"
    COMPANY_WEBSITE = "COMPANY_WEBSITE"
    CORPORATE_ANNOUNCEMENT = "CORPORATE_ANNOUNCEMENT"
    INVESTOR_PRESENTATION = "INVESTOR_PRESENTATION"
    SBP = "SBP"
    SECP = "SECP"
    NEWS = "NEWS"
    OTHER = "OTHER"


class AuthorityLevel(str, Enum):
    PRIMARY = "PRIMARY"      # Official/regulatory source
    SECONDARY = "SECONDARY"  # Company-verified
    TERTIARY = "TERTIARY"    # Third-party (media, analyst)


class Source(Base):
    """
    Information source registry.
    Every imported data traces back to a source.
    Enables auditability and verification.
    """
    __tablename__ = "source"

    source_id = Column(Integer, primary_key=True)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    source_name = Column(String(200), nullable=False)
    # Example: "PSX Official Announcements", "Company Annual Report 2025"

    source_url = Column(String(500))  # URL if applicable
    authority_level = Column(SQLEnum(AuthorityLevel), default=AuthorityLevel.SECONDARY)

    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="source")

    def __repr__(self):
        return f"<Source {self.source_name}>"


# ════════════════════════════════════════════════════════════════════════════════
# SPRINT 2: DOCUMENT FOUNDATION
# ════════════════════════════════════════════════════════════════════════════════

class DocumentType(str, Enum):
    ANNUAL_REPORT = "ANNUAL_REPORT"
    QUARTERLY_REPORT = "QUARTERLY_REPORT"
    RESULTS = "RESULTS"
    BOARD_MEETING = "BOARD_MEETING"
    DIVIDEND = "DIVIDEND"
    BONUS = "BONUS"
    RIGHTS = "RIGHTS"
    MATERIAL_INFORMATION = "MATERIAL_INFORMATION"
    INVESTOR_PRESENTATION = "INVESTOR_PRESENTATION"
    AGM = "AGM"
    OTHER = "OTHER"


class ProcessingStatus(str, Enum):
    RECEIVED = "RECEIVED"
    EXTRACTING = "EXTRACTING"
    EXTRACTED = "EXTRACTED"
    NORMALIZING = "NORMALIZING"
    NORMALIZED = "NORMALIZED"
    FAILED = "FAILED"


class Document(Base):
    """
    Document store (annual reports, quarterly reports, announcements, etc.).
    Every document associated with company + date + source.
    """
    __tablename__ = "document"

    document_id = Column(Integer, primary_key=True)
    security_id = Column(Integer, ForeignKey("security.security_id"), nullable=False)

    document_type = Column(SQLEnum(DocumentType), nullable=False)
    title = Column(String(400), nullable=False)

    publication_date = Column(Date, nullable=False)
    fiscal_year = Column(Integer)  # 2025, 2026, etc.
    fiscal_quarter = Column(Integer)  # 1, 2, 3, 4 for quarterly

    source_id = Column(Integer, ForeignKey("source.source_id"), nullable=False)
    source_url = Column(String(500))
    source_document_id = Column(String(100))  # ID from source system

    file_path = Column(String(500))  # Local storage path
    checksum = Column(String(64))  # SHA256 checksum

    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.RECEIVED)

    downloaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    security = relationship("Security", back_populates="documents")
    source = relationship("Source", back_populates="documents")
    financial_line_items = relationship("FinancialLineItem", back_populates="source_document")

    def __repr__(self):
        return f"<Document {self.title} ({self.publication_date})>"


# ════════════════════════════════════════════════════════════════════════════════
# SPRINT 3: FINANCIAL SCHEMA
# ════════════════════════════════════════════════════════════════════════════════

class PeriodType(str, Enum):
    ANNUAL = "ANNUAL"
    QUARTERLY = "QUARTERLY"


class StatementType(str, Enum):
    INCOME_STATEMENT = "INCOME_STATEMENT"
    BALANCE_SHEET = "BALANCE_SHEET"
    CASH_FLOW = "CASH_FLOW"


class FinancialPeriod(Base):
    """
    Fiscal period container.
    One record per company per fiscal period (year or quarter).
    """
    __tablename__ = "financial_period"

    period_id = Column(Integer, primary_key=True)
    security_id = Column(Integer, ForeignKey("security.security_id"), nullable=False)

    period_type = Column(SQLEnum(PeriodType), nullable=False)  # ANNUAL or QUARTERLY

    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer)  # 1-4 for quarterly; NULL for annual

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    publication_date = Column(Date, nullable=False)

    # Allows tracking which periods have been extracted/normalized
    is_complete = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    security = relationship("Security", back_populates="financial_periods")
    line_items = relationship("FinancialLineItem", back_populates="period")
    metrics = relationship("FinancialMetric", back_populates="period")

    def __repr__(self):
        period_str = f"FY{self.fiscal_year}" if self.period_type == PeriodType.ANNUAL else f"Q{self.fiscal_quarter} FY{self.fiscal_year}"
        return f"<FinancialPeriod {self.security_id} {period_str}>"


class MetricDefinition(Base):
    """
    Canonical metric definitions.
    Maps standardized metric codes to names and formulas.
    """
    __tablename__ = "metric_definition"

    metric_id = Column(Integer, primary_key=True)
    metric_code = Column(String(50), unique=True, nullable=False)
    # Example: "REVENUE", "NET_INCOME", "EPS", "ROE"

    metric_name = Column(String(200), nullable=False)
    statement_type = Column(SQLEnum(StatementType), nullable=True)
    # Income statement, balance sheet, or cash flow

    description = Column(Text)
    unit_type = Column(String(50))
    # "PKR_MILLIONS", "PERCENTAGE", "RATIO", "PER_SHARE", etc.

    def __repr__(self):
        return f"<MetricDefinition {self.metric_code}>"


class MetricAlias(Base):
    """
    Alias mappings for the same metric across different company reports.
    Example: "Sales" and "Revenue" both map to REVENUE.
    """
    __tablename__ = "metric_alias"

    alias_id = Column(Integer, primary_key=True)
    alias = Column(String(200), nullable=False)
    # Example: "Sales", "Net sales", "Revenue", "Turnover"

    metric_id = Column(Integer, ForeignKey("metric_definition.metric_id"), nullable=False)
    sector_id = Column(Integer, ForeignKey("sector.sector_id"), nullable=True)
    # Sector-specific if applicable

    confidence = Column(Float)  # 0-1: confidence in this mapping
    manual_review = Column(Boolean, default=False)  # Was this manually verified?

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MetricAlias {self.alias} → {self.metric_id}>"


class FinancialLineItem(Base):
    """
    Actual financial statement line items.
    Store raw numbers from annual/quarterly reports with standardized mapping.
    """
    __tablename__ = "financial_line_item"

    item_id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey("financial_period.period_id"), nullable=False)

    statement_type = Column(SQLEnum(StatementType), nullable=False)
    # INCOME_STATEMENT, BALANCE_SHEET, or CASH_FLOW

    metric_id = Column(Integer, ForeignKey("metric_definition.metric_id"), nullable=False)
    # The standardized metric code (e.g., REVENUE)

    reported_label = Column(String(300))
    # The label as it appeared in the original report (e.g., "Sales - net")

    value = Column(Numeric(20, 0), nullable=False)
    # Actual number (store as integers to avoid floating point issues)

    currency = Column(String(3), default="PKR")
    unit = Column(String(50))  # "MILLIONS", "THOUSANDS", "UNITS", etc.

    source_document_id = Column(Integer, ForeignKey("document.document_id"), nullable=False)

    extraction_confidence = Column(Float)  # 0-1: how confident we are in this extraction
    requires_review = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    period = relationship("FinancialPeriod", back_populates="line_items")
    source_document = relationship("Document", back_populates="financial_line_items")

    def __repr__(self):
        return f"<LineItem {self.metric_id} = {self.value} ({self.reported_label})>"


# ════════════════════════════════════════════════════════════════════════════════
# SPRINT 5: FINANCIAL METRICS (Derived)
# ════════════════════════════════════════════════════════════════════════════════

class FinancialMetric(Base):
    """
    Calculated financial metrics (not raw line items).
    Examples: EPS, ROE, Debt/Equity, Margins, Cash ratios.

    Important: Store calculated metrics separately from raw data.
    This allows versioning of calculation methodologies.
    """
    __tablename__ = "financial_metric"

    metric_id = Column(Integer, primary_key=True)
    security_id = Column(Integer, ForeignKey("security.security_id"), nullable=False)
    period_id = Column(Integer, ForeignKey("financial_period.period_id"), nullable=False)

    metric_code = Column(String(50), nullable=False)
    # Example: "EPS", "ROE", "DEBT_EQUITY", "CURRENT_RATIO"

    value = Column(Numeric(20, 4), nullable=False)

    calculation_version = Column(String(50), nullable=False)
    # Example: "fundamentals_v1" — allows tracking formula changes

    calculated_at = Column(DateTime, default=datetime.utcnow)

    period = relationship("FinancialPeriod", back_populates="metrics")

    def __repr__(self):
        return f"<Metric {self.metric_code}={self.value} v{self.calculation_version}>"


# ════════════════════════════════════════════════════════════════════════════════
# SPRINT 9: CORPORATE INFORMATION
# ════════════════════════════════════════════════════════════════════════════════

class AnnouncementType(str, Enum):
    FINANCIAL_RESULTS = "FINANCIAL_RESULTS"
    DIVIDEND = "DIVIDEND"
    BONUS = "BONUS"
    RIGHTS = "RIGHTS"
    BOARD_MEETING = "BOARD_MEETING"
    MATERIAL_INFORMATION = "MATERIAL_INFORMATION"
    DIRECTOR_TRANSACTION = "DIRECTOR_TRANSACTION"
    BOOK_CLOSURE = "BOOK_CLOSURE"
    AGM = "AGM"
    CREDIT_RATING = "CREDIT_RATING"
    OTHER = "OTHER"


class Announcement(Base):
    """PSX company announcements."""
    __tablename__ = "announcement"

    announcement_id = Column(Integer, primary_key=True)
    security_id = Column(Integer, ForeignKey("security.security_id"), nullable=False)

    announcement_type = Column(SQLEnum(AnnouncementType), nullable=False)
    title = Column(String(400), nullable=False)

    publication_timestamp = Column(DateTime, nullable=False)

    summary = Column(Text)  # AI-generated or extracted summary

    source_document_id = Column(Integer, ForeignKey("document.document_id"), nullable=True)
    source_url = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)

    security = relationship("Security", back_populates="announcements")

    def __repr__(self):
        return f"<Announcement {self.title} ({self.publication_timestamp})>"


class EventStatus(str, Enum):
    UPCOMING = "UPCOMING"
    OCCURRED = "OCCURRED"
    POSTPONED = "POSTPONED"
    CANCELLED = "CANCELLED"


class Event(Base):
    """Corporate events (AGM, board meeting, book closure, etc.)."""
    __tablename__ = "event"

    event_id = Column(Integer, primary_key=True)
    security_id = Column(Integer, ForeignKey("security.security_id"), nullable=True)

    event_type = Column(String(50), nullable=False)
    # AGM, BOARD_MEETING, BOOK_CLOSURE, etc.

    announcement_id = Column(Integer, ForeignKey("announcement.announcement_id"), nullable=True)
    # Links back to the announcement if applicable

    event_date = Column(Date, nullable=False)
    title = Column(String(400), nullable=False)

    status = Column(SQLEnum(EventStatus), default=EventStatus.UPCOMING)

    source_id = Column(Integer, ForeignKey("source.source_id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Event {self.title} ({self.event_date})>"


# ════════════════════════════════════════════════════════════════════════════════
# DATA QUALITY & TRACKING
# ════════════════════════════════════════════════════════════════════════════════

class DataStatus(str, Enum):
    VERIFIED = "VERIFIED"
    AUTO_EXTRACTED = "AUTO_EXTRACTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    STALE = "STALE"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"


class DataQuality(Base):
    """
    Track data quality flags and verification status.
    Crucial for understanding reliability of all information.
    """
    __tablename__ = "data_quality"

    quality_id = Column(Integer, primary_key=True)

    entity_type = Column(String(50), nullable=False)
    # Example: "financial_line_item", "announcement", "metric"

    entity_id = Column(Integer, nullable=False)
    # ID of the entity being tracked

    status = Column(SQLEnum(DataStatus), default=DataStatus.AUTO_EXTRACTED)

    is_verified = Column(Boolean, default=False)
    last_verified_at = Column(DateTime)
    verified_by = Column(String(100))

    notes = Column(Text)  # What issues were found?

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DataQuality {self.entity_type}:{self.entity_id} = {self.status}>"


# ════════════════════════════════════════════════════════════════════════════════
# MODULE 2: VALUATION & COMPARATIVE INTELLIGENCE
# ════════════════════════════════════════════════════════════════════════════════

class MarketSnapshot(Base):
    """
    Daily market data for valuation calculations.
    Source: PSX data feeds.
    """
    __tablename__ = "market_snapshot"

    snapshot_id = Column(Integer, primary_key=True)
    security_id = Column(Integer, ForeignKey("security.security_id"), nullable=False)

    snapshot_date = Column(Date, nullable=False)
    # Trading date or end of business day

    close_price = Column(Numeric(15, 2), nullable=False)
    # Share price in PKR

    shares_outstanding = Column(Numeric(20, 0), nullable=False)
    # Shares outstanding at this date (handles splits, rights, bonuses)

    market_cap = Column(Numeric(25, 0), nullable=False)
    # Market cap in PKR = price × shares

    free_float_market_cap = Column(Numeric(25, 0))
    # Free float market cap if available

    trading_volume = Column(Numeric(20, 0))
    # Daily trading volume

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketSnapshot {self.security_id} {self.snapshot_date} @ {self.close_price}>"


class ValuationInput(Base):
    """
    Valuation inputs derived from Module 1 financial data.
    TTM (trailing twelve months) values aggregated from quarterly/annual periods.
    """
    __tablename__ = "valuation_input"

    input_id = Column(Integer, primary_key=True)
    security_id = Column(Integer, ForeignKey("security.security_id"), nullable=False)

    as_of_date = Column(Date, nullable=False)
    # Date this valuation snapshot is as-of

    # TTM Values (from financial data)
    eps_ttm = Column(Numeric(10, 2))  # Earnings per share (trailing twelve months)
    book_value_per_share = Column(Numeric(10, 2))  # Total equity / shares
    revenue_ttm = Column(Numeric(20, 0))  # Revenue (trailing twelve months)
    ebitda_ttm = Column(Numeric(20, 0))  # EBITDA (trailing twelve months)
    free_cash_flow_ttm = Column(Numeric(20, 0))  # FCF (trailing twelve months)
    dividend_per_share_ttm = Column(Numeric(10, 2))  # DPS (trailing twelve months)

    # Balance sheet items
    total_debt = Column(Numeric(20, 0))  # Short + long-term debt
    cash_and_equivalents = Column(Numeric(20, 0))  # Cash position
    total_equity = Column(Numeric(20, 0))  # Shareholders equity

    # Market data snapshot
    shares_outstanding = Column(Numeric(20, 0), nullable=False)
    close_price = Column(Numeric(15, 2), nullable=False)
    market_cap = Column(Numeric(25, 0), nullable=False)

    # Flags
    normalized = Column(Boolean, default=False)  # One-offs removed
    ttm_complete = Column(Boolean, default=True)  # 12 months of data available

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ValuationInput {self.security_id} {self.as_of_date}>"


class ValuationSnapshot(Base):
    """
    Calculated valuation multiples.
    Store current and historical valuation ratios for analysis.
    """
    __tablename__ = "valuation_snapshot"

    snapshot_id = Column(Integer, primary_key=True)
    security_id = Column(Integer, ForeignKey("security.security_id"), nullable=False)

    snapshot_date = Column(Date, nullable=False)
    # Date this valuation is as-of

    # Valuation multiples
    pe_ratio = Column(Numeric(8, 2))  # Price / EPS
    pb_ratio = Column(Numeric(8, 2))  # Price / Book value per share
    ps_ratio = Column(Numeric(8, 2))  # Market cap / Revenue
    ev_ebitda_ratio = Column(Numeric(8, 2))  # Enterprise value / EBITDA
    fcf_yield = Column(Numeric(6, 2))  # FCF / Market cap (%)
    dividend_yield = Column(Numeric(6, 2))  # DPS / Price (%)

    # Enterprise value
    enterprise_value = Column(Numeric(25, 0))  # Market cap + debt - cash

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ValuationSnapshot {self.security_id} {self.snapshot_date}>"


class ValuationMetricApplicability(Base):
    """
    Sector-specific rules for which valuation metrics are most relevant.
    Different sectors use different valuation approaches.
    """
    __tablename__ = "valuation_metric_applicability"

    applicability_id = Column(Integer, primary_key=True)
    sector_id = Column(Integer, ForeignKey("sector.sector_id"), nullable=False)

    metric_code = Column(String(50), nullable=False)
    # Example: "PE", "PB", "EV_EBITDA", "FCF_YIELD", "DIVIDEND_YIELD"

    priority = Column(Integer, default=0)
    # 1 = Primary, 2 = Secondary, 3 = Tertiary

    enabled = Column(Boolean, default=True)
    # Whether to display for this sector

    description = Column(Text)
    # Why this metric is useful for this sector

    created_at = Column(DateTime, default=datetime.utcnow)

    sector = relationship("Sector")

    def __repr__(self):
        return f"<Applicability {self.sector_id} {self.metric_code}>"


# ════════════════════════════════════════════════════════════════════════════════
# MODULE 6: TRADE PLANNING & RISK MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════════

class TradeType(str, Enum):
    """Trade classification."""
    MOMENTUM = "MOMENTUM"
    BREAKOUT = "BREAKOUT"
    VALUE = "VALUE"
    MEAN_REVERSION = "MEAN_REVERSION"
    EVENT = "EVENT"
    DIVIDEND = "DIVIDEND"
    LONG_TERM_ACCUMULATION = "LONG_TERM_ACCUMULATION"
    MANUAL = "MANUAL"


class TimeHorizon(str, Enum):
    """Trade time horizon."""
    INTRADAY = "INTRADAY"           # 1-5 days
    SWING = "SWING"                 # 1-4 weeks
    SHORT_TERM = "SHORT_TERM"       # 1-3 months
    MEDIUM_TERM = "MEDIUM_TERM"     # 3-12 months
    LONG_TERM = "LONG_TERM"         # 1Y+


class StopType(str, Enum):
    """Stop-loss methodology."""
    TECHNICAL = "TECHNICAL"           # Below support level
    ATR = "ATR"                       # Multiple of ATR
    PERCENTAGE = "PERCENTAGE"         # Simple % risk
    MANUAL = "MANUAL"                 # User-defined
    THESIS_INVALIDATION = "THESIS_INVALIDATION"


class TradeStatus(str, Enum):
    """Trade plan lifecycle."""
    DRAFT = "DRAFT"
    WATCHING = "WATCHING"
    READY = "READY"
    ENTERED = "ENTERED"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    STOPPED_OUT = "STOPPED_OUT"


class TradePlan(Base):
    """
    Trade plan for disciplined capital deployment.

    Captures entry/exit strategy, position sizing, and risk metrics
    before capital is committed.
    """
    __tablename__ = "trade_plan"

    trade_plan_id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False)
    # User identifier (from auth system)

    security_id = Column(Integer, ForeignKey("security.security_id"), nullable=False)
    ticker = Column(String(10), nullable=False)
    # Denormalized for convenience

    # ────────────────────────────────────────────────────────────────────────
    # PLAN METADATA
    # ────────────────────────────────────────────────────────────────────────

    status = Column(SQLEnum(TradeStatus), default=TradeStatus.DRAFT)

    trade_type = Column(SQLEnum(TradeType), nullable=True)
    time_horizon = Column(SQLEnum(TimeHorizon), nullable=True)

    # ────────────────────────────────────────────────────────────────────────
    # ENTRY LEVELS
    # ────────────────────────────────────────────────────────────────────────

    entry_price = Column(Numeric(20, 4), nullable=False)
    # Planned entry price

    entry_zone_low = Column(Numeric(20, 4), nullable=True)
    entry_zone_high = Column(Numeric(20, 4), nullable=True)
    # Entry zone (±% around planned entry)

    # ────────────────────────────────────────────────────────────────────────
    # EXIT LEVELS
    # ────────────────────────────────────────────────────────────────────────

    stop_price = Column(Numeric(20, 4), nullable=False)
    # Stop-loss price

    stop_type = Column(SQLEnum(StopType), nullable=True)
    # Why the stop exists (TECHNICAL, ATR, etc.)

    target_1 = Column(Numeric(20, 4), nullable=True)
    target_2 = Column(Numeric(20, 4), nullable=True)
    target_3 = Column(Numeric(20, 4), nullable=True)
    # Multiple targets for partial exits

    # ────────────────────────────────────────────────────────────────────────
    # RISK PARAMETERS
    # ────────────────────────────────────────────────────────────────────────

    portfolio_value = Column(Numeric(20, 0), nullable=False)
    # Total portfolio size (PKR)

    risk_percent = Column(Numeric(5, 2), nullable=False)
    # Risk per trade as % (e.g., 1.0 for 1%)

    max_loss_amount = Column(Numeric(20, 0), nullable=True)
    # Calculated: portfolio × risk% (PKR)

    max_position_percent = Column(Numeric(5, 2), default=20.0)
    # Max position as % of portfolio

    # ────────────────────────────────────────────────────────────────────────
    # POSITION SIZING
    # ────────────────────────────────────────────────────────────────────────

    position_size = Column(Integer, nullable=True)
    # Number of shares calculated

    capital_required = Column(Numeric(20, 0), nullable=True)
    # Total capital to deploy (PKR)

    allocation_pct = Column(Numeric(5, 2), nullable=True)
    # Position as % of portfolio

    # ────────────────────────────────────────────────────────────────────────
    # RISK/REWARD
    # ────────────────────────────────────────────────────────────────────────

    risk_reward_1 = Column(Numeric(10, 2), nullable=True)
    risk_reward_2 = Column(Numeric(10, 2), nullable=True)
    risk_reward_3 = Column(Numeric(10, 2), nullable=True)
    # R/R ratios for each target (e.g., 3.0 = 1:3)

    # ────────────────────────────────────────────────────────────────────────
    # TRADE THESIS
    # ────────────────────────────────────────────────────────────────────────

    entry_thesis = Column(Text, nullable=True)
    # Why are we entering? What is the opportunity?

    invalidation_thesis = Column(Text, nullable=True)
    # What specific condition would prove us wrong?

    notes = Column(Text, nullable=True)
    # Additional context or considerations

    # ────────────────────────────────────────────────────────────────────────
    # AUDIT TRAIL
    # ────────────────────────────────────────────────────────────────────────

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ────────────────────────────────────────────────────────────────────────
    # EXECUTION TRACKING (when trade is active)
    # ────────────────────────────────────────────────────────────────────────

    entered_at = Column(DateTime, nullable=True)
    # When position was actually opened

    actual_entry_price = Column(Numeric(20, 4), nullable=True)
    # What price we actually got

    closed_at = Column(DateTime, nullable=True)
    # When position was closed

    exit_reason = Column(String(100), nullable=True)
    # TARGET_HIT, STOPPED_OUT, CANCELLED, etc.

    # ────────────────────────────────────────────────────────────────────────
    # RELATIONSHIPS
    # ────────────────────────────────────────────────────────────────────────

    security = relationship("Security")

    def __repr__(self):
        return f"<TradePlan {self.ticker} {self.status.value} entry={self.entry_price}>"
