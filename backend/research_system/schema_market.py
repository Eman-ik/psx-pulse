"""
Market & Sector Intelligence Database Schema

Module 3: Index Master, Market Data, Sector Performance, Macro Context

Extends the core research_system schema with market-wide analysis capabilities.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text,
    Enum as SQLEnum, Numeric, Date, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ════════════════════════════════════════════════════════════════════════════════
# SPRINT M1: INDEX FOUNDATION
# ════════════════════════════════════════════════════════════════════════════════

class IndexType(str, Enum):
    """Classification of index types."""
    MARKET = "MARKET"           # KSE-100, KSE-30, etc.
    SECTOR = "SECTOR"           # Sector indices
    THEMATIC = "THEMATIC"       # Thematic indices
    OTHER = "OTHER"


class IndexMaster(Base):
    """
    PSX Index Master Data

    Single source of truth for all market indices.
    Supports: KSE-100, KSE-30, KMI-30, ALLSHR, Sector Indices
    """
    __tablename__ = "index_master"

    index_id = Column(Integer, primary_key=True)
    index_code = Column(String(20), unique=True, nullable=False)
    # Examples: "KSE-100", "KSE-30", "KMI-30", "ALLSHR", "BANK", "CEMENT"

    index_name = Column(String(200), nullable=False)
    # Examples: "Karachi Stock Exchange 100", "Cement Sector Index"

    index_type = Column(SQLEnum(IndexType), default=IndexType.MARKET)

    provider = Column(String(50), default="PSX")
    # Data provider: PSX, Bloomberg, Reuters, etc.

    base_date = Column(Date)
    # Date when index was launched

    base_value = Column(Numeric(15, 2))
    # Base value (usually 100 or 1000)

    description = Column(Text)
    # Index description and methodology

    active = Column(Boolean, default=True)
    # Whether index is currently tracked

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    index_prices = relationship("IndexPrice", back_populates="index_master", cascade="all, delete-orphan")
    index_constituents = relationship("IndexConstituent", back_populates="index_master", cascade="all, delete-orphan")
    market_snapshots = relationship("MarketSnapshot", back_populates="index")
    sector_snapshots = relationship("SectorSnapshot", back_populates="index")

    def __repr__(self):
        return f"<IndexMaster {self.index_code}: {self.index_name}>"


class IndexPrice(Base):
    """
    Daily Index Prices (OHLCV)

    Historical price data for all indices.
    """
    __tablename__ = "index_price"

    index_price_id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey("index_master.index_id"), nullable=False)
    date = Column(Date, nullable=False)

    open = Column(Numeric(15, 2))
    high = Column(Numeric(15, 2))
    low = Column(Numeric(15, 2))
    close = Column(Numeric(15, 2), nullable=False)

    volume = Column(Integer)
    # Trading volume (not always available for indices)

    turnover = Column(Numeric(20, 2))
    # Total traded value (PKR)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one price per index per date
    __table_args__ = (
        UniqueConstraint('index_id', 'date', name='uq_index_date'),
    )

    # Relationships
    index_master = relationship("IndexMaster", back_populates="index_prices")

    @property
    def daily_return(self):
        """Calculate daily return as percentage."""
        if not self.open or self.open == 0:
            return None
        return float((self.close - self.open) / self.open * 100)

    def __repr__(self):
        return f"<IndexPrice {self.index_id} {self.date}: {self.close}>"


class IndexConstituent(Base):
    """
    Index Constituents Mapping

    Which securities belong to which indices and at what weights.
    Maintains historical changes in constituent list.
    """
    __tablename__ = "index_constituent"

    constituent_id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey("index_master.index_id"), nullable=False)
    security_id = Column(Integer)
    # Foreign key to security.security_id (not defined in this schema)

    effective_from = Column(Date, nullable=False)
    # Date when security became/becomes a constituent

    effective_to = Column(Date)
    # Date when security stops being a constituent (NULL = still active)

    weight = Column(Numeric(5, 2))
    # Weight in index (%) - optional, may not always be known

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint per security per index per date
    __table_args__ = (
        UniqueConstraint('index_id', 'security_id', 'effective_from',
                        name='uq_index_security_date'),
    )

    # Relationships
    index_master = relationship("IndexMaster", back_populates="index_constituents")

    def __repr__(self):
        return f"<IndexConstituent Index:{self.index_id} Security:{self.security_id}>"


# ════════════════════════════════════════════════════════════════════════════════
# SPRINT M2: MARKET SNAPSHOT
# ════════════════════════════════════════════════════════════════════════════════

class MarketSnapshot(Base):
    """
    Daily Market Overview

    High-level market metrics calculated at end of each trading day.
    """
    __tablename__ = "market_snapshot"

    snapshot_id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey("index_master.index_id"), nullable=False)
    # Which index this snapshot is for (usually KSE-100)

    date = Column(Date, unique=True, nullable=False)

    total_volume = Column(Integer)
    # Total shares traded

    total_value_traded = Column(Numeric(20, 2))
    # Total PKR value traded

    advancers = Column(Integer)
    # Number of stocks advancing

    decliners = Column(Integer)
    # Number of stocks declining

    unchanged = Column(Integer)
    # Number of unchanged stocks

    upper_locks = Column(Integer)
    # Stocks hitting upper circuit (if applicable)

    lower_locks = Column(Integer)
    # Stocks hitting lower circuit (if applicable)

    new_52w_highs = Column(Integer)
    # Stocks making new 52-week highs

    new_52w_lows = Column(Integer)
    # Stocks making new 52-week lows

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    index = relationship("IndexMaster", back_populates="market_snapshots")

    @property
    def advance_decline_ratio(self) -> float:
        """Calculate advance/decline ratio."""
        if not self.decliners or self.decliners == 0:
            return 0.0
        return float(self.advancers / self.decliners) if self.advancers else 0.0

    @property
    def breadth_percent(self) -> float:
        """Calculate % of stocks advancing."""
        total = self.advancers + self.decliners + (self.unchanged or 0)
        if not total:
            return 0.0
        return float(self.advancers / total * 100) if total > 0 else 0.0

    def __repr__(self):
        return f"<MarketSnapshot {self.date}: A/D={self.advancers}/{self.decliners}>"


# ════════════════════════════════════════════════════════════════════════════════
# SPRINT M3: MARKET BREADTH
# ════════════════════════════════════════════════════════════════════════════════

class MarketRegime(str, Enum):
    """Classification of market regime."""
    BULLISH_BROAD = "BULLISH_BROAD"           # Strong rally, broad participation
    BULLISH_NARROW = "BULLISH_NARROW"         # Strong rally, narrow participation
    NEUTRAL = "NEUTRAL"                       # Sideways market
    BEARISH_BROAD = "BEARISH_BROAD"           # Decline with broad selling
    BEARISH_NARROW = "BEARISH_NARROW"         # Decline from few stocks
    HIGH_VOLATILITY = "HIGH_VOLATILITY"       # Uncertain, choppy


class MarketBreadth(Base):
    """
    Market Breadth Analysis

    % of stocks trading above moving averages.
    Key indicator of market health (broad vs narrow moves).
    """
    __tablename__ = "market_breadth"

    breadth_id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)

    pct_above_20dma = Column(Float)
    # % of stocks trading above 20-day moving average

    pct_above_50dma = Column(Float)
    # % of stocks trading above 50-day moving average

    pct_above_100dma = Column(Float)
    # % of stocks trading above 100-day moving average

    pct_above_200dma = Column(Float)
    # % of stocks trading above 200-day moving average

    advance_decline_ratio = Column(Float)
    # Ratio of advancing to declining stocks

    new_highs = Column(Integer)
    # Number of stocks making new 52-week highs

    new_lows = Column(Integer)
    # Number of stocks making new 52-week lows

    market_regime = Column(SQLEnum(MarketRegime))
    # Classified market regime

    regime_confidence = Column(Float)
    # Confidence in regime classification (0-1)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketBreadth {self.date}: Regime={self.market_regime}>"


# ════════════════════════════════════════════════════════════════════════════════
# SPRINT M4: SECTOR SNAPSHOT
# ════════════════════════════════════════════════════════════════════════════════

class SectorSnapshot(Base):
    """
    Daily Sector Performance

    Performance metrics for each sector.
    """
    __tablename__ = "sector_snapshot"

    sector_snapshot_id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey("index_master.index_id"), nullable=False)
    # Sector index reference (e.g., CEMENT, BANK sector index)

    date = Column(Date, nullable=False)

    return_1d = Column(Numeric(8, 4))
    # 1-day return (%)

    return_1w = Column(Numeric(8, 4))
    # 1-week return (%)

    return_1m = Column(Numeric(8, 4))
    # 1-month return (%)

    return_3m = Column(Numeric(8, 4))
    # 3-month return (%)

    return_6m = Column(Numeric(8, 4))
    # 6-month return (%)

    return_ytd = Column(Numeric(8, 4))
    # Year-to-date return (%)

    return_1y = Column(Numeric(8, 4))
    # 1-year return (%)

    volume = Column(Integer)
    # Total volume in sector

    value_traded = Column(Numeric(20, 2))
    # Total value traded (PKR)

    advancers = Column(Integer)
    # Stocks advancing in sector

    decliners = Column(Integer)
    # Stocks declining in sector

    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique: one snapshot per sector per date
    __table_args__ = (
        UniqueConstraint('index_id', 'date', name='uq_sector_date'),
    )

    # Relationships
    index = relationship("IndexMaster", back_populates="sector_snapshots")

    def __repr__(self):
        return f"<SectorSnapshot {self.index_id} {self.date}: 1D={self.return_1d}%>"


# ════════════════════════════════════════════════════════════════════════════════
# SPRINT M8: MACRO FOUNDATION
# ════════════════════════════════════════════════════════════════════════════════

class MacroFrequency(str, Enum):
    """Data frequency for macro series."""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"


class MacroSeries(Base):
    """
    Macro Economic Series Definition

    Registry of macro variables tracked (USD/PKR, policy rate, CPI, oil, etc.)
    """
    __tablename__ = "macro_series"

    series_id = Column(Integer, primary_key=True)
    series_code = Column(String(50), unique=True, nullable=False)
    # Examples: "USD_PKR", "POLICY_RATE", "CPI", "BRENT_OIL"

    series_name = Column(String(200), nullable=False)
    # Human-readable name: "USD/PKR Exchange Rate"

    unit = Column(String(20))
    # Unit of measurement: "%", "Rs", "USD/bbl", etc.

    frequency = Column(SQLEnum(MacroFrequency), default=MacroFrequency.DAILY)
    # How often is this series updated

    source = Column(String(100))
    # Data source: "State Bank", "FBR", "Bloomberg", "Reuters"

    description = Column(Text)
    # What this series measures and why it matters

    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    observations = relationship("MacroObservation", back_populates="series", cascade="all, delete-orphan")
    sector_exposures = relationship("SectorMacroExposure", back_populates="series", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MacroSeries {self.series_code}: {self.series_name}>"


class MacroObservation(Base):
    """
    Macro Economic Observations

    Historical values for each macro series.
    """
    __tablename__ = "macro_observation"

    observation_id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey("macro_series.series_id"), nullable=False)
    date = Column(Date, nullable=False)

    value = Column(Numeric(20, 4), nullable=False)
    # The actual observed value

    source_id = Column(String(100))
    # Source identifier if applicable

    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique: one observation per series per date
    __table_args__ = (
        UniqueConstraint('series_id', 'date', name='uq_series_date'),
    )

    # Relationships
    series = relationship("MacroSeries", back_populates="observations")

    def __repr__(self):
        return f"<MacroObservation {self.series_id} {self.date}: {self.value}>"


class MacroExposureType(str, Enum):
    """Type of relationship between sector and macro variable."""
    POSITIVE = "POSITIVE"           # Sector benefits from increase
    NEGATIVE = "NEGATIVE"           # Sector suffers from increase
    NEUTRAL = "NEUTRAL"             # No clear relationship


class SectorMacroExposure(Base):
    """
    Sector-Level Macro Exposures

    Which macro variables affect which sectors.
    Example: Banks → Policy Rate (negative), Oil → Energy Sector (positive)
    """
    __tablename__ = "sector_macro_exposure"

    exposure_id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey("index_master.index_id"), nullable=False)
    # Sector index (e.g., BANK, CEMENT, ENERGY)

    series_id = Column(Integer, ForeignKey("macro_series.series_id"), nullable=False)
    # Macro series (e.g., POLICY_RATE, BRENT_OIL)

    relationship_type = Column(SQLEnum(MacroExposureType))
    # POSITIVE: sector benefits from increase, NEGATIVE: sector hurt, NEUTRAL

    importance = Column(String(20))
    # HIGH, MEDIUM, LOW - how important is this relationship

    description = Column(Text)
    # Why this relationship exists and how it works

    confidence = Column(Float)
    # Confidence in the relationship (0-1)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    index = relationship("IndexMaster")
    series = relationship("MacroSeries", back_populates="sector_exposures")

    def __repr__(self):
        return f"<SectorMacroExposure Sector:{self.index_id} → Series:{self.series_id}>"


# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE: COMMON MACRO SERIES TO POPULATE
# ════════════════════════════════════════════════════════════════════════════════

"""
Common PSX-relevant macro series to track:

Daily/High Frequency:
- USD_PKR: USD/PKR exchange rate
- BRENT_OIL: Brent crude oil (USD/bbl)
- GOLD: Gold price (USD/oz)
- KSE100_CLOSE: KSE-100 closing level

Weekly:
- FOREIGN_RESERVES: SBP foreign reserves (USD millions)

Monthly:
- POLICY_RATE: SBP policy rate (%)
- CPI: Consumer Price Index (YoY %)
- CURRENT_ACCOUNT: Current account balance (PKR)
- IMPORT_BILLS: Import coverage (months)

Quarterly:
- GDP_GROWTH: Real GDP growth (%)

Annual/As Needed:
- INTEREST_COVERAGE: Average interest rates
- INFLATION_TARGET: SBP inflation target (%)

Commodity-Specific (Daily):
- COAL_PRICE: Coal price
- GAS_PRICE: Gas price
- UREA_PRICE: Urea prices (international)
- POTASH_PRICE: Potash prices

Sector-Specific Macro Links:
- Banks → POLICY_RATE (NEGATIVE)
- Oil & Gas → BRENT_OIL (POSITIVE)
- Energy → COAL_PRICE (POSITIVE)
- Fertilizer → GAS_PRICE, UREA_PRICE (POSITIVE)
- Autos → USD_PKR (POSITIVE - exports competitiveness)
- Textiles → USD_PKR (POSITIVE - export competitiveness)
- Cement → CONSTRUCTION_INDEX (POSITIVE)
"""
