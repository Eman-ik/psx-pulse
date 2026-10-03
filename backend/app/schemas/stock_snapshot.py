"""Stock Snapshot — Unified Pydantic schema combining all company data sources.

A snapshot is the complete picture of a single company at one point in time.
It combines:
- Market data (current price, volume, market cap)
- Financial metrics (growth, profitability, leverage, cash flow)
- Valuation ratios (P/E, P/B, dividend yield)
- Technical indicators (support, resistance, trend)
- Recent events (announcements)
- Macro context (sector, economic indicators)
- Data quality tracking (source, confidence, staleness)

The snapshot is the primary data structure passed through the research pipeline.
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class MarketData(BaseModel):
    """Current and recent market data."""
    ticker: str
    price: Optional[float] = None
    price_date: Optional[date] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None  # in millions
    free_float_pct: Optional[float] = None
    source: str = "PSX"


class FinancialMetrics(BaseModel):
    """Multi-period financial metrics."""
    revenue_growth_pct: Optional[float] = None
    pat_growth_pct: Optional[float] = None
    net_margin_pct: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    roa_pct: Optional[float] = None
    roe_pct: Optional[float] = None
    current_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None
    ocf_to_pat_ratio: Optional[float] = None
    latest_period_end: Optional[date] = None
    periods_available: int = 0


class ValuationData(BaseModel):
    """Valuation multiples and yields."""
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield_pct: Optional[float] = None
    peg_ratio: Optional[float] = None
    fcf_yield_pct: Optional[float] = None
    book_value_per_share: Optional[float] = None


class TechnicalIndicators(BaseModel):
    """Price action and technical levels."""
    support_52w_low: Optional[float] = None
    resistance_52w_high: Optional[float] = None
    current_price: Optional[float] = None
    avg_volume_30d: Optional[int] = None
    trend: Optional[str] = None  # "uptrend", "downtrend", "consolidation"
    trend_strength: Optional[float] = None  # 0-100%


class RecentEvent(BaseModel):
    """A single announcement or material event."""
    date: date
    title: str
    body: Optional[str] = None
    source: str = "PSX"


class MacroContext(BaseModel):
    """Economic and sector context."""
    sector: Optional[str] = None
    subsector: Optional[str] = None
    market_cap_bracket: Optional[str] = None  # "micro", "small", "mid", "large"
    kse_100_level: Optional[float] = None
    kse_100_change_pct: Optional[float] = None
    forex_pkr_usd: Optional[float] = None


class DataQuality(BaseModel):
    """Metadata about data sources and confidence."""
    snapshot_time: datetime = Field(default_factory=datetime.utcnow)
    market_data_confidence: str = "low"  # "low", "medium", "high"
    financial_data_confidence: str = "low"
    market_data_freshness_days: int = 999
    financial_data_freshness_days: int = 999
    data_issues: List[str] = Field(default_factory=list)
    missing_data_fields: List[str] = Field(default_factory=list)


class StockSnapshot(BaseModel):
    """Complete snapshot of a company at one point in time.

    Combines market, financial, valuation, technical, event, and macro data.
    This is the primary data structure flowing through research engines.

    Design:
    - All fields optional: a real snapshot rarely has everything
    - Source traceability: each section knows where data came from
    - Confidence tracking: explicitly note data quality
    - Staleness tracking: know how old the data is
    """
    ticker: str
    company_name: Optional[str] = None

    market: MarketData
    financials: Optional[FinancialMetrics] = None
    valuation: Optional[ValuationData] = None
    technical: Optional[TechnicalIndicators] = None
    macro: Optional[MacroContext] = None

    recent_events: List[RecentEvent] = Field(default_factory=list)
    quality: DataQuality = Field(default_factory=DataQuality)

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }
    )

    def has_complete_fundamentals(self) -> bool:
        """Check if snapshot has enough financial data to analyze."""
        if not self.financials:
            return False
        f = self.financials
        required = [f.revenue_growth_pct, f.pat_growth_pct, f.net_margin_pct]
        return sum(1 for x in required if x is not None) >= 2

    def get_data_gaps(self) -> List[str]:
        """Identify missing critical data."""
        gaps = []
        if not self.market.price:
            gaps.append("market_price")
        if not self.financials or self.financials.periods_available < 2:
            gaps.append("financial_history")
        if not self.valuation or self.valuation.pe_ratio is None:
            gaps.append("valuation_multiples")
        if not self.technical or self.technical.support_52w_low is None:
            gaps.append("technical_levels")
        return gaps
