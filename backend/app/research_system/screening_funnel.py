"""Fundamental analysis screening funnel for PSX companies.

Implements 5-stage screening as described in the investment funnel:
  Screen 1: Basic Quality (removes suspended, weak balance sheet, persistent losses)
  Screen 2: Financial Quality (growth, margins, returns, cash flow, debt)
  Screen 3: Valuation (P/E, P/B, EV/EBITDA, FCF yield, dividend yield)
  Screen 4: Industry Analysis (peer comparison)
  Screen 5: Deep Research (already in Research Studio)

Each stage outputs pass/fail per company, with a composite watchlist score.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScreeningResult:
    """Result of one company passing/failing a screening stage."""
    symbol: str
    name: str
    sector: str
    screen_1_basic_quality: Optional[bool]  # None = tradable, but no statements to check
    screen_1_reasons: list[str] = field(default_factory=list)

    screen_2_financial_quality: Optional[bool] = None
    screen_2_score: float = 0.0  # 0-100
    screen_2_reasons: list[str] = field(default_factory=list)

    screen_3_valuation: Optional[bool] = None
    screen_3_score: float = 0.0  # 0-100
    screen_3_reasons: list[str] = field(default_factory=list)

    screen_4_peer_comparison: Optional[bool] = None
    screen_4_score: float = 0.0  # 0-100
    screen_4_reasons: list[str] = field(default_factory=list)

    tier: str = "price_only"  # watchlist | deep_research | price_only

    @property
    def passes_all_screens(self) -> bool:
        """True if company passes screens 1-4 and qualifies for watchlist."""
        return all(s is True for s in self._stages)

    @property
    def stage_reached(self) -> int:
        """How far through the funnel: 1=basic, 2=financial, 3=valuation, 4=peer, 5=watchlist."""
        # First stage that did not pass, whether it failed or could not be evaluated.
        return next((i for i, s in enumerate(self._stages, start=1) if s is not True), 5)

    @property
    def _stages(self) -> list[Optional[bool]]:
        return [self.screen_1_basic_quality, self.screen_2_financial_quality,
                self.screen_3_valuation, self.screen_4_peer_comparison]


@dataclass
class ScreeningSession:
    """One run of the screening funnel across all companies."""
    created_at: datetime
    ticker_count: int
    passed_screen_1: int = 0
    passed_screen_2: int = 0
    passed_screen_3: int = 0
    passed_screen_4: int = 0
    watchlist_companies: list[str] = field(default_factory=list)
    results: list[ScreeningResult] = field(default_factory=list)


class ScreeningFunnel:
    """Implements the 5-stage fundamental analysis screening funnel."""

    @staticmethod
    def screen_1_basic_quality(
        company_data: dict,
        is_active: bool,
        has_recent_prices: bool,
        balance_sheet_health: Optional[dict] = None,
    ) -> tuple[Optional[bool], list[str]]:
        """Screen 1: Basic Quality

        Removes:
        - Suspended/inactive companies
        - Companies with no recent price data
        - Extremely weak balance sheets (D/E > 3.0, current ratio < 0.5)
        - Persistent losses (negative earnings last 2 years)

        Returns: (passes, reasons_for_failure)
        """
        reasons = []

        if not is_active:
            reasons.append("Company is inactive/suspended")

        if not has_recent_prices:
            reasons.append("No recent price data")

        if balance_sheet_health:
            debt_to_equity = balance_sheet_health.get("debt_to_equity", 0)
            current_ratio = balance_sheet_health.get("current_ratio", 0)

            if debt_to_equity and debt_to_equity > 3.0:
                reasons.append(f"Total liabilities/equity too high: {debt_to_equity:.1f}x (max 3.0x)")

            if current_ratio and current_ratio < 0.5:
                reasons.append(f"Current ratio too low: {current_ratio:.2f}x (min 0.5x)")

            # Check for persistent losses
            net_income_trend = balance_sheet_health.get("net_income_trend", [])
            if len(net_income_trend) >= 2 and all(ni < 0 for ni in net_income_trend[-2:]):
                reasons.append("Negative earnings in last 2 years")

        if reasons:
            return False, reasons
        if not balance_sheet_health or all(v is None for v in balance_sheet_health.values()):
            return None, ["Balance-sheet checks not run: no source-linked statements on file"]
        return True, reasons

    @staticmethod
    def screen_2_financial_quality(
        company_data: dict,
        financials: Optional[dict] = None,
    ) -> tuple[Optional[bool], float, list[str]]:
        """Screen 2: Financial Quality

        Scores on 5 dimensions (each 0-100):
        - Revenue growth: Target >10% YoY (0-100 score)
        - EPS growth: Target >10% YoY (0-100 score)
        - Net margin: Target >5% (0-100 score)
        - ROE: Target >10% (0-100 score)
        - ROIC: Target >8% (0-100 score)
        - Cash flow health: OCF > Net Income? (0-100 score)
        - Debt trend: Declining or stable D/E (0-100 score)

        Composite score = average of 7 dimensions
        Pass threshold: >= 50/100

        Returns: (passes, composite_score, reasons)
        """
        reasons = []
        scores = []

        if not financials or all(v is None for v in financials.values()):
            return None, 0.0, ["No financial data available"]

        # Revenue growth
        rev_growth = financials.get("revenue_growth_yoy", 0)
        if rev_growth is not None:
            rev_score = min(100, (rev_growth / 10) * 100) if rev_growth > 0 else 0
            scores.append(rev_score)
            if rev_growth < 5:
                reasons.append(f"Revenue growth weak: {rev_growth:.1f}% (target >10%)")

        # EPS growth
        eps_growth = financials.get("eps_growth_yoy", 0)
        if eps_growth is not None:
            eps_score = min(100, (eps_growth / 10) * 100) if eps_growth > 0 else 0
            scores.append(eps_score)
            if eps_growth < 5:
                reasons.append(f"EPS growth weak: {eps_growth:.1f}% (target >10%)")

        # Net margin
        net_margin = financials.get("net_profit_margin", 0)
        if net_margin is not None:
            margin_score = min(100, net_margin / 5 * 100) if net_margin > 0 else 0
            scores.append(margin_score)
            if net_margin < 2:
                reasons.append(f"Net margin low: {net_margin:.1f}% (target >5%)")

        # ROE
        roe = financials.get("roe", 0)
        if roe is not None:
            roe_score = min(100, roe / 10 * 100) if roe > 0 else 0
            scores.append(roe_score)
            if roe < 8:
                reasons.append(f"ROE weak: {roe:.1f}% (target >10%)")

        # ROIC (if available)
        roic = financials.get("roic", 0)
        if roic is not None:
            roic_score = min(100, roic / 8 * 100) if roic > 0 else 0
            scores.append(roic_score)
            if roic < 6:
                reasons.append(f"ROIC weak: {roic:.1f}% (target >8%)")

        # Cash flow health
        ocf = financials.get("operating_cash_flow", 0)
        net_income = financials.get("net_income", 0)
        if ocf is not None and net_income is not None and net_income > 0:
            cf_score = 100 if ocf >= net_income else 50
            scores.append(cf_score)
            if ocf < net_income:
                reasons.append("OCF < Net Income (quality concern)")

        # Debt trend (stable or declining D/E)
        de_current = financials.get("debt_to_equity", 0)
        de_prior = financials.get("debt_to_equity_prior_year", de_current)
        if de_current is not None and de_prior is not None:
            if de_current <= de_prior:
                debt_score = 100
            else:
                debt_score = max(0, 100 - ((de_current - de_prior) / de_prior * 100))
            scores.append(debt_score)
            if de_current > de_prior:
                reasons.append(f"D/E increasing: {de_current:.1f}x vs {de_prior:.1f}x")

        if not scores:
            return None, 0.0, ["No scorable financial metrics"]
        composite = sum(scores) / len(scores)
        passes = composite >= 50

        return passes, composite, reasons

    @staticmethod
    def screen_3_valuation(
        company_data: dict,
        valuation_metrics: Optional[dict] = None,
    ) -> tuple[Optional[bool], float, list[str]]:
        """Screen 3: Valuation

        Scores on 5 multiples (each 0-100):
        - P/E: Cheaper than sector median = 100, median = 50, expensive = 0
        - P/B: Cheaper than sector = 100, at sector = 50, expensive = 0
        - EV/EBITDA: Cheaper than sector = 100, at sector = 50, expensive = 0
        - FCF Yield: Higher than sector = 100, at sector = 50, lower = 0
        - Dividend Yield: Higher than 3% = 100, at 3% = 50, lower = 0

        Composite score = average of available multiples
        Pass threshold: >= 40/100 (valuation is not a dealbreaker, but matters)

        Returns: (passes, composite_score, reasons)
        """
        reasons = []
        scores = []

        if not valuation_metrics:
            return None, 0.0, ["No valuation data available"]

        # P/E
        pe = valuation_metrics.get("pe_ratio")
        pe_sector_median = valuation_metrics.get("pe_sector_median")
        if pe is not None:
            if pe_sector_median:
                if pe < pe_sector_median:
                    pe_score = min(100, (1 - (pe / pe_sector_median - 0.7)) * 100)
                else:
                    pe_score = max(0, (1 - (pe / pe_sector_median - 1)) * 100)
                scores.append(pe_score)
            if pe_sector_median and pe > pe_sector_median * 1.2:
                reasons.append(f"P/E expensive: {pe:.1f}x vs sector {pe_sector_median:.1f}x")

        # P/B
        pb = valuation_metrics.get("pb_ratio")
        pb_sector_median = valuation_metrics.get("pb_sector_median")
        if pb is not None:
            if pb_sector_median:
                if pb < pb_sector_median:
                    pb_score = min(100, (1 - (pb / pb_sector_median - 0.7)) * 100)
                else:
                    pb_score = max(0, (1 - (pb / pb_sector_median - 1)) * 100)
                scores.append(pb_score)
            if pb_sector_median and pb > pb_sector_median * 1.3:
                reasons.append(f"P/B expensive: {pb:.1f}x vs sector {pb_sector_median:.1f}x")

        # FCF Yield
        fcf_yield = valuation_metrics.get("fcf_yield")
        fcf_yield_sector = valuation_metrics.get("fcf_yield_sector")
        if fcf_yield is not None:
            if fcf_yield_sector:
                scores.append(min(100, (fcf_yield / fcf_yield_sector) * 100))
            if fcf_yield and fcf_yield < 1.5:
                reasons.append(f"FCF yield low: {fcf_yield:.1f}% (target >2%)")

        # Dividend Yield
        div_yield = valuation_metrics.get("dividend_yield")
        if div_yield is not None:
            div_score = min(100, (div_yield / 3) * 100) if div_yield > 0 else 0
            scores.append(div_score)

        if not scores:
            return None, 0.0, ["No valuation multiples with a sector comparison on file"]
        composite = sum(scores) / len(scores)
        passes = composite >= 40  # More lenient than screen 2

        return passes, composite, reasons

    @staticmethod
    def screen_4_peer_comparison(
        company_data: dict,
        peer_metrics: Optional[dict] = None,
    ) -> tuple[Optional[bool], float, list[str]]:
        """Screen 4: Industry Analysis (Peer Comparison)

        Scores vs peers (0-100):
        - ROE rank vs peers (top quartile = 100)
        - Revenue growth rank vs peers (top quartile = 100)
        - Margin rank vs peers (top quartile = 100)
        - Valuation rank vs peers (bottom quartile = 100, top quartile = 0)

        Composite = average rank score
        Pass threshold: >= 40/100 (better than below-average peer)

        Returns: (passes, composite_score, reasons)
        """
        reasons = []
        scores = []

        if not peer_metrics:
            return None, 0.0, ["No peer data available"]

        # ROE rank
        roe_rank = peer_metrics.get("roe_percentile")
        if roe_rank is not None:
            scores.append(roe_rank)
            if roe_rank < 25:
                reasons.append(f"ROE in bottom quartile of peers ({roe_rank}th percentile)")

        # Revenue growth rank
        rev_rank = peer_metrics.get("revenue_growth_percentile")
        if rev_rank is not None:
            scores.append(rev_rank)
            if rev_rank < 25:
                reasons.append(f"Revenue growth in bottom quartile ({rev_rank}th percentile)")

        # Margin rank
        margin_rank = peer_metrics.get("margin_percentile")
        if margin_rank is not None:
            scores.append(margin_rank)
            if margin_rank < 25:
                reasons.append(f"Margins in bottom quartile ({margin_rank}th percentile)")

        # Valuation rank (inverted: cheaper is better)
        valuation_rank = peer_metrics.get("valuation_percentile")
        if valuation_rank is not None:
            valuation_score = 100 - valuation_rank  # Invert so cheaper = higher
            scores.append(valuation_score)
            if valuation_rank > 75:
                reasons.append(f"Valuation expensive vs peers ({valuation_rank}th percentile)")

        if not scores:
            return None, 0.0, ["No peer percentiles available"]
        composite = sum(scores) / len(scores)
        passes = composite >= 40  # Better than median peer

        return passes, composite, reasons

