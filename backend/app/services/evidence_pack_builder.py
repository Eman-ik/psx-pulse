"""Evidence Pack Builder — Package snapshot data for LLM analysis.

Creates an "evidence pack" from StockSnapshot that combines:
- Raw facts (market, technical, financial, macro)
- Deterministic calculations (ratios, growth rates)
- Data quality metadata
- Source traceability

This is the intermediate layer between raw data and LLM interpretation.
The pack contains all facts needed for analysis without raw numbers alone.

Input: StockSnapshot (complete company profile)
Output: EvidencePack (structured for LLM context)
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

from app.schemas.stock_snapshot import StockSnapshot

logger = logging.getLogger(__name__)


@dataclass
class EvidencePack:
    """Structured evidence package for LLM analysis."""

    # Company identification
    ticker: str
    company_name: Optional[str]
    sector: Optional[str]
    market_cap_bracket: Optional[str]

    # Market facts
    current_price: Optional[float]
    price_change_pct: Optional[float]
    daily_volume: Optional[int]
    free_float_pct: Optional[float]

    # Technical facts
    trend: Optional[str]
    trend_strength: Optional[float]
    support_level: Optional[float]
    resistance_level: Optional[float]
    distance_to_support_pct: Optional[float]
    distance_to_resistance_pct: Optional[float]
    liquidity_avg_volume: Optional[int]

    # Financial facts
    revenue_growth_pct: Optional[float]
    earnings_growth_pct: Optional[float]
    net_margin_pct: Optional[float]
    gross_margin_pct: Optional[float]
    return_on_equity_pct: Optional[float]
    return_on_assets_pct: Optional[float]
    debt_to_equity_ratio: Optional[float]
    current_ratio: Optional[float]
    interest_coverage_ratio: Optional[float]
    earnings_quality_ratio: Optional[float]
    periods_analyzed: int

    # Valuation facts
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    dividend_yield_pct: Optional[float]

    # Macro facts
    kse_100_level: Optional[float]
    kse_100_change_pct: Optional[float]
    index_context: str  # e.g., "market up 1.5%, stock up 0.8%"

    # Recent events
    recent_event_count: int
    recent_positive_events: int
    recent_negative_events: int
    latest_event_date: Optional[str]
    latest_event_type: Optional[str]

    # Data quality
    data_freshness_days: int
    market_data_confidence: str
    financial_data_confidence: str
    missing_data_fields: List[str]
    data_gaps_description: str

    # Derived insights
    sentiment: str  # "positive", "negative", "neutral", "mixed"
    confidence_score: float  # 0-100
    key_strengths: List[str]
    key_concerns: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def to_narrative(self) -> str:
        """Convert evidence pack to narrative format for LLM."""
        parts = [
            f"=== COMPANY PROFILE ===",
            f"Ticker: {self.ticker}",
            f"Name: {self.company_name or 'N/A'}",
            f"Sector: {self.sector or 'Unknown'}",
            f"Market Cap Bracket: {self.market_cap_bracket or 'Unknown'}",
            "",
            f"=== CURRENT MARKET STATUS ===",
            f"Price: {self.current_price or 'N/A'}",
            f"Change: {self.price_change_pct or 'N/A'}%",
            f"Volume: {self.daily_volume or 'N/A'} shares",
            f"Free Float: {self.free_float_pct or 'N/A'}%",
            "",
            f"=== TECHNICAL POSITION ===",
            f"Trend: {self.trend or 'Unknown'} ({self.trend_strength or 'N/A'}% strength)",
            f"Support (52W): {self.support_level or 'N/A'} ({self.distance_to_support_pct or 'N/A'}% below)",
            f"Resistance (52W): {self.resistance_level or 'N/A'} ({self.distance_to_resistance_pct or 'N/A'}% above)",
            "",
            f"=== FINANCIAL PERFORMANCE ===",
            f"Revenue Growth: {self.revenue_growth_pct or 'N/A'}%",
            f"Earnings Growth: {self.earnings_growth_pct or 'N/A'}%",
            f"Net Margin: {self.net_margin_pct or 'N/A'}%",
            f"Return on Equity: {self.return_on_equity_pct or 'N/A'}%",
            f"Debt/Equity: {self.debt_to_equity_ratio or 'N/A'}",
            f"Earnings Quality (OCF/PAT): {self.earnings_quality_ratio or 'N/A'}",
            "",
            f"=== VALUATION ===",
            f"P/E Ratio: {self.pe_ratio or 'N/A'}",
            f"P/B Ratio: {self.pb_ratio or 'N/A'}",
            f"Dividend Yield: {self.dividend_yield_pct or 'N/A'}%",
            "",
            f"=== MARKET CONTEXT ===",
            f"KSE-100: {self.kse_100_level or 'N/A'} ({self.kse_100_change_pct or 'N/A'}%)",
            f"Context: {self.index_context}",
            "",
            f"=== RECENT NEWS ===",
            f"Recent Events: {self.recent_event_count}",
            f"Positive: {self.recent_positive_events}, Negative: {self.recent_negative_events}",
            f"Latest: {self.latest_event_type or 'None'} ({self.latest_event_date or 'N/A'})",
            "",
            f"=== DATA QUALITY ===",
            f"Freshness: {self.data_freshness_days} days",
            f"Market Confidence: {self.market_data_confidence}",
            f"Financial Confidence: {self.financial_data_confidence}",
            f"Issues: {self.data_gaps_description or 'None'}",
            "",
            f"=== ANALYSIS ===",
            f"Sentiment: {self.sentiment.upper()}",
            f"Confidence: {self.confidence_score}%",
            f"Strengths: {', '.join(self.key_strengths) if self.key_strengths else 'None identified'}",
            f"Concerns: {', '.join(self.key_concerns) if self.key_concerns else 'None identified'}",
        ]
        return "\n".join(parts)


class EvidencePackBuilder:
    """Build evidence packs from StockSnapshot for LLM analysis."""

    def __init__(self):
        """Initialize builder."""
        self.logger = logging.getLogger(__name__)

    def build(self, snapshot: StockSnapshot) -> Optional[EvidencePack]:
        """Build evidence pack from snapshot.

        Args:
            snapshot: Complete stock snapshot

        Returns:
            EvidencePack ready for LLM analysis
        """
        if not snapshot:
            return None

        try:
            # Extract market facts
            current_price = snapshot.market.price if snapshot.market else None
            price_change_pct = snapshot.market.change_pct if snapshot.market else None

            # Extract technical facts
            trend = snapshot.technical.trend if snapshot.technical else None
            trend_strength = snapshot.technical.trend_strength if snapshot.technical else None
            support = snapshot.technical.support_52w_low if snapshot.technical else None
            resistance = snapshot.technical.resistance_52w_high if snapshot.technical else None

            # Calculate distance to support/resistance
            dist_support = self._calc_distance_pct(current_price, support, "above")
            dist_resistance = self._calc_distance_pct(current_price, resistance, "below")

            # Extract financial facts
            revenue_growth = snapshot.financials.revenue_growth_pct if snapshot.financials else None
            earnings_growth = snapshot.financials.pat_growth_pct if snapshot.financials else None
            net_margin = snapshot.financials.net_margin_pct if snapshot.financials else None
            periods = snapshot.financials.periods_available if snapshot.financials else 0

            # Extract valuation facts
            pe_ratio = snapshot.valuation.pe_ratio if snapshot.valuation else None
            dividend_yield = snapshot.valuation.dividend_yield_pct if snapshot.valuation else None

            # Extract macro facts
            kse_level = snapshot.macro.kse_100_level if snapshot.macro else None
            kse_change = snapshot.macro.kse_100_change_pct if snapshot.macro else None
            index_context = self._build_index_context(current_price, price_change_pct, kse_level, kse_change)

            # Extract event facts
            recent_events = snapshot.recent_events if snapshot.recent_events else []
            event_count = len(recent_events)
            positive_events = sum(1 for e in recent_events if "POSITIVE" in (e.body or "").upper())
            negative_events = sum(1 for e in recent_events if "NEGATIVE" in (e.body or "").upper())
            latest_event = recent_events[0] if recent_events else None

            # Assess data quality
            gaps = snapshot.quality.missing_data_fields if snapshot.quality else []
            gaps_desc = ", ".join(gaps) if gaps else "None"
            freshness_days = snapshot.quality.market_data_freshness_days if snapshot.quality else 999

            # Derive insights
            sentiment = self._assess_sentiment(
                snapshot.financials,
                snapshot.technical,
                snapshot.market
            )
            confidence = self._calc_confidence_score(snapshot.quality)
            strengths = self._identify_strengths(snapshot.financials, snapshot.technical)
            concerns = self._identify_concerns(snapshot.financials, snapshot.technical)

            pack = EvidencePack(
                ticker=snapshot.ticker,
                company_name=snapshot.company_name,
                sector=snapshot.macro.sector if snapshot.macro else None,
                market_cap_bracket=snapshot.macro.market_cap_bracket if snapshot.macro else None,
                current_price=current_price,
                price_change_pct=price_change_pct,
                daily_volume=snapshot.market.volume if snapshot.market else None,
                free_float_pct=snapshot.market.free_float_pct if snapshot.market else None,
                trend=trend,
                trend_strength=trend_strength,
                support_level=support,
                resistance_level=resistance,
                distance_to_support_pct=dist_support,
                distance_to_resistance_pct=dist_resistance,
                liquidity_avg_volume=snapshot.technical.avg_volume_30d if snapshot.technical else None,
                revenue_growth_pct=revenue_growth,
                earnings_growth_pct=earnings_growth,
                net_margin_pct=net_margin,
                gross_margin_pct=snapshot.financials.gross_margin_pct if snapshot.financials else None,
                return_on_equity_pct=snapshot.financials.roe_pct if snapshot.financials else None,
                return_on_assets_pct=snapshot.financials.roa_pct if snapshot.financials else None,
                debt_to_equity_ratio=snapshot.financials.debt_to_equity if snapshot.financials else None,
                current_ratio=snapshot.financials.current_ratio if snapshot.financials else None,
                interest_coverage_ratio=snapshot.financials.interest_coverage if snapshot.financials else None,
                earnings_quality_ratio=snapshot.financials.ocf_to_pat_ratio if snapshot.financials else None,
                periods_analyzed=periods,
                pe_ratio=pe_ratio,
                pb_ratio=snapshot.valuation.pb_ratio if snapshot.valuation else None,
                dividend_yield_pct=dividend_yield,
                kse_100_level=kse_level,
                kse_100_change_pct=kse_change,
                index_context=index_context,
                recent_event_count=event_count,
                recent_positive_events=positive_events,
                recent_negative_events=negative_events,
                latest_event_date=latest_event.date.isoformat() if latest_event else None,
                latest_event_type=self._extract_event_type(latest_event.body) if latest_event else None,
                data_freshness_days=freshness_days,
                market_data_confidence=snapshot.quality.market_data_confidence if snapshot.quality else "low",
                financial_data_confidence=snapshot.quality.financial_data_confidence if snapshot.quality else "low",
                missing_data_fields=gaps,
                data_gaps_description=gaps_desc,
                sentiment=sentiment,
                confidence_score=confidence,
                key_strengths=strengths,
                key_concerns=concerns,
            )

            self.logger.info(f"Built evidence pack for {snapshot.ticker} (confidence: {confidence}%)")
            return pack

        except Exception as e:
            self.logger.error(f"Error building evidence pack: {e}")
            return None

    @staticmethod
    def _calc_distance_pct(current: Optional[float], level: Optional[float], direction: str) -> Optional[float]:
        """Calculate distance from support/resistance as percentage.

        Args:
            current: Current price
            level: Support or resistance level
            direction: "above" (for support) or "below" (for resistance)

        Returns:
            Distance as percentage or None
        """
        if not current or not level:
            return None

        if direction == "above" and current > level:
            return ((current - level) / level) * 100
        elif direction == "below" and current < level:
            return ((level - current) / level) * 100

        return None

    @staticmethod
    def _build_index_context(
        price: Optional[float],
        price_change: Optional[float],
        kse_level: Optional[float],
        kse_change: Optional[float]
    ) -> str:
        """Build market context narrative.

        Args:
            price: Current price
            price_change: Price change %
            kse_level: KSE-100 level
            kse_change: KSE-100 change %

        Returns:
            Context narrative
        """
        parts = []

        if kse_level:
            parts.append(f"KSE-100 at {kse_level}")
            if kse_change:
                direction = "up" if kse_change > 0 else "down"
                parts.append(f"market {direction} {abs(kse_change):.1f}%")

        if price and price_change:
            direction = "up" if price_change > 0 else "down"
            parts.append(f"stock {direction} {abs(price_change):.1f}%")

        return ", ".join(parts) if parts else "No market context available"

    @staticmethod
    def _assess_sentiment(
        financials: Optional[Any],
        technical: Optional[Any],
        market: Optional[Any]
    ) -> str:
        """Assess overall sentiment from financial and technical metrics.

        Args:
            financials: FinancialMetrics
            technical: TechnicalIndicators
            market: MarketData

        Returns:
            "positive", "negative", "neutral", or "mixed"
        """
        signals = []

        # Financial signals
        if financials:
            if financials.revenue_growth_pct and financials.revenue_growth_pct > 10:
                signals.append("positive")
            elif financials.revenue_growth_pct and financials.revenue_growth_pct < -5:
                signals.append("negative")

            if financials.roe_pct and financials.roe_pct > 20:
                signals.append("positive")
            elif financials.roe_pct and financials.roe_pct < 5:
                signals.append("negative")

        # Technical signals
        if technical:
            if technical.trend == "uptrend":
                signals.append("positive")
            elif technical.trend == "downtrend":
                signals.append("negative")

        # Market signals
        if market and market.change_pct and market.change_pct > 2:
            signals.append("positive")
        elif market and market.change_pct and market.change_pct < -2:
            signals.append("negative")

        if not signals:
            return "neutral"

        positive_count = signals.count("positive")
        negative_count = signals.count("negative")

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "mixed"

    @staticmethod
    def _calc_confidence_score(quality: Optional[Any]) -> float:
        """Calculate overall confidence score for analysis.

        Args:
            quality: DataQuality metadata

        Returns:
            Confidence score 0-100
        """
        if not quality:
            return 40.0  # Low confidence without quality data

        confidence = 50.0  # Base score

        # Data freshness (max +30 points)
        if quality.market_data_freshness_days < 1:
            confidence += 30
        elif quality.market_data_freshness_days < 7:
            confidence += 20
        elif quality.market_data_freshness_days < 30:
            confidence += 10

        # Market confidence (max +20 points)
        if quality.market_data_confidence == "high":
            confidence += 20
        elif quality.market_data_confidence == "medium":
            confidence += 10

        # Missing data penalty (max -30 points)
        if quality.missing_data_fields:
            confidence -= len(quality.missing_data_fields) * 5

        return max(0, min(100, confidence))

    @staticmethod
    def _identify_strengths(financials: Optional[Any], technical: Optional[Any]) -> List[str]:
        """Identify key strengths from analysis.

        Args:
            financials: FinancialMetrics
            technical: TechnicalIndicators

        Returns:
            List of strength descriptions
        """
        strengths = []

        if financials:
            if financials.revenue_growth_pct and financials.revenue_growth_pct > 15:
                strengths.append(f"Strong revenue growth ({financials.revenue_growth_pct:.1f}%)")
            if financials.roe_pct and financials.roe_pct > 20:
                strengths.append(f"High ROE ({financials.roe_pct:.1f}%)")
            if financials.ocf_to_pat_ratio and financials.ocf_to_pat_ratio > 1:
                strengths.append("High earnings quality")

        if technical:
            if technical.trend == "uptrend" and technical.trend_strength and technical.trend_strength > 50:
                strengths.append(f"Strong uptrend ({technical.trend_strength:.0f}% strength)")

        return strengths

    @staticmethod
    def _identify_concerns(financials: Optional[Any], technical: Optional[Any]) -> List[str]:
        """Identify key concerns from analysis.

        Args:
            financials: FinancialMetrics
            technical: TechnicalIndicators

        Returns:
            List of concern descriptions
        """
        concerns = []

        if financials:
            if financials.revenue_growth_pct and financials.revenue_growth_pct < -5:
                concerns.append(f"Declining revenue ({financials.revenue_growth_pct:.1f}%)")
            if financials.debt_to_equity and financials.debt_to_equity > 2:
                concerns.append(f"High leverage ({financials.debt_to_equity:.1f}x)")
            if financials.current_ratio and financials.current_ratio < 1:
                concerns.append("Weak liquidity")

        if technical:
            if technical.trend == "downtrend":
                concerns.append(f"Downtrend ({technical.trend_strength:.0f}% strength)")

        return concerns

    @staticmethod
    def _extract_event_type(body: Optional[str]) -> Optional[str]:
        """Extract event type from normalized announcement body.

        Args:
            body: Announcement body with metadata

        Returns:
            Event type (e.g., "EARNINGS") or None
        """
        if not body:
            return None

        upper_body = body.upper()
        if "[EARNINGS" in upper_body:
            return "EARNINGS"
        elif "[DIVIDEND" in upper_body:
            return "DIVIDEND"
        elif "[ACQUISITION" in upper_body:
            return "ACQUISITION"
        elif "[REGULATORY" in upper_body:
            return "REGULATORY"

        return None
