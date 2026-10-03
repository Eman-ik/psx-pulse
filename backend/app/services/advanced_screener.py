"""Step 16: Advanced Screener — Filter companies by fundamental criteria.

Multi-stage screening funnel:
- Stage 1: Market cap filters (micro/small/mid/large)
- Stage 2: Growth filters (revenue growth, profitability)
- Stage 3: Valuation filters (P/E, P/B ratios)
- Stage 4: Quality filters (ROE, margins, debt ratios)
- Stage 5: Technical filters (trend, momentum, support)

Input: List of companies with financial data
Output: ScreeningResult (passed/failed companies + stage breakdown)
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ScreeningStage(str, Enum):
    """Screening pipeline stages."""

    MARKET_CAP = "Market Cap"
    GROWTH = "Growth"
    VALUATION = "Valuation"
    QUALITY = "Quality"
    TECHNICAL = "Technical"


class FilterResult(str, Enum):
    """Filter result status."""

    PASS = "Pass"
    FAIL = "Fail"
    BORDERLINE = "Borderline"
    INSUFFICIENT_DATA = "Insufficient Data"


@dataclass
class StageResult:
    """Result for one screening stage."""

    stage: ScreeningStage
    companies_passed: int
    companies_failed: int
    companies_borderline: int
    filters_applied: List[str]


@dataclass
class CompanyFilterResult:
    """Screening result for one company."""

    ticker: str
    company_name: str
    passed_all_stages: bool
    failed_at_stage: Optional[ScreeningStage]
    stage_results: Dict[str, FilterResult]
    score: float  # 0-100% based on how many criteria met


@dataclass
class ScreeningResult:
    """Complete screening run results."""

    total_companies: int
    passed_companies: int
    failed_companies: int
    borderline_companies: int

    stage_results: List[StageResult]
    company_results: List[CompanyFilterResult]

    top_scorers: List[CompanyFilterResult]  # Top 10 by score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_companies": self.total_companies,
            "passed_companies": self.passed_companies,
            "failed_companies": self.failed_companies,
            "borderline_companies": self.borderline_companies,
            "pass_rate_pct": (self.passed_companies / self.total_companies * 100) if self.total_companies > 0 else 0,
            "top_scorers_count": len(self.top_scorers),
            "stage_results": [
                {
                    "stage": r.stage.value,
                    "passed": r.companies_passed,
                    "failed": r.companies_failed,
                }
                for r in self.stage_results
            ],
        }


@dataclass
class ScreeningCriteria:
    """Screening filter criteria."""

    # Market cap filters
    min_market_cap_millions: Optional[float] = None
    max_market_cap_millions: Optional[float] = None

    # Growth filters
    min_revenue_growth_pct: Optional[float] = None
    min_profit_growth_pct: Optional[float] = None

    # Valuation filters
    max_pe_ratio: Optional[float] = None
    max_pb_ratio: Optional[float] = None

    # Quality filters
    min_roe_pct: Optional[float] = None
    min_net_margin_pct: Optional[float] = None
    max_debt_to_equity: Optional[float] = None

    # Technical filters
    required_trend: Optional[str] = None  # "uptrend", "stable"
    min_trend_strength_pct: Optional[float] = None


class AdvancedScreener:
    """Advanced multi-stage screening for stock selection."""

    def __init__(self):
        """Initialize screener."""
        self.logger = logging.getLogger(__name__)

    def screen(
        self,
        companies: List[Dict[str, Any]],
        criteria: ScreeningCriteria,
    ) -> Optional[ScreeningResult]:
        """Run multi-stage screening.

        Args:
            companies: List of companies with financial data
            criteria: Screening criteria

        Returns:
            ScreeningResult or None on error
        """
        try:
            if not companies:
                return None

            # Stage 1: Market Cap
            stage1_results = []
            for company in companies:
                result = self._filter_market_cap(company, criteria)
                stage1_results.append((company, result))

            passed_stage1 = [c for c, r in stage1_results if r == FilterResult.PASS]

            # Stage 2: Growth
            stage2_results = []
            for company in passed_stage1:
                result = self._filter_growth(company, criteria)
                stage2_results.append((company, result))

            passed_stage2 = [c for c, r in stage2_results if r == FilterResult.PASS]

            # Stage 3: Valuation
            stage3_results = []
            for company in passed_stage2:
                result = self._filter_valuation(company, criteria)
                stage3_results.append((company, result))

            passed_stage3 = [c for c, r in stage3_results if r == FilterResult.PASS]

            # Stage 4: Quality
            stage4_results = []
            for company in passed_stage3:
                result = self._filter_quality(company, criteria)
                stage4_results.append((company, result))

            passed_stage4 = [c for c, r in stage4_results if r == FilterResult.PASS]

            # Stage 5: Technical
            stage5_results = []
            for company in passed_stage4:
                result = self._filter_technical(company, criteria)
                stage5_results.append((company, result))

            passed_stage5 = [c for c, r in stage5_results if r == FilterResult.PASS]

            # Calculate scores for all companies
            company_results = []
            for company in companies:
                score = self._calculate_screening_score(company, criteria)
                failed_stage = self._determine_failed_stage(company, criteria)

                result = CompanyFilterResult(
                    ticker=company.get("ticker", ""),
                    company_name=company.get("company_name", ""),
                    passed_all_stages=company in passed_stage5,
                    failed_at_stage=failed_stage,
                    stage_results={
                        "market_cap": self._filter_market_cap(company, criteria).value,
                        "growth": self._filter_growth(company, criteria).value,
                        "valuation": self._filter_valuation(company, criteria).value,
                        "quality": self._filter_quality(company, criteria).value,
                        "technical": self._filter_technical(company, criteria).value,
                    },
                    score=score,
                )
                company_results.append(result)

            # Sort by score and get top scorers
            company_results.sort(key=lambda x: x.score, reverse=True)
            top_scorers = company_results[:10]

            # Create stage results
            stage_results = [
                StageResult(
                    stage=ScreeningStage.MARKET_CAP,
                    companies_passed=len(passed_stage1),
                    companies_failed=len(companies) - len(passed_stage1),
                    companies_borderline=0,
                    filters_applied=self._get_filters_applied(ScreeningStage.MARKET_CAP, criteria),
                ),
                StageResult(
                    stage=ScreeningStage.GROWTH,
                    companies_passed=len(passed_stage2),
                    companies_failed=len(passed_stage1) - len(passed_stage2),
                    companies_borderline=0,
                    filters_applied=self._get_filters_applied(ScreeningStage.GROWTH, criteria),
                ),
                StageResult(
                    stage=ScreeningStage.VALUATION,
                    companies_passed=len(passed_stage3),
                    companies_failed=len(passed_stage2) - len(passed_stage3),
                    companies_borderline=0,
                    filters_applied=self._get_filters_applied(ScreeningStage.VALUATION, criteria),
                ),
                StageResult(
                    stage=ScreeningStage.QUALITY,
                    companies_passed=len(passed_stage4),
                    companies_failed=len(passed_stage3) - len(passed_stage4),
                    companies_borderline=0,
                    filters_applied=self._get_filters_applied(ScreeningStage.QUALITY, criteria),
                ),
                StageResult(
                    stage=ScreeningStage.TECHNICAL,
                    companies_passed=len(passed_stage5),
                    companies_failed=len(passed_stage4) - len(passed_stage5),
                    companies_borderline=0,
                    filters_applied=self._get_filters_applied(ScreeningStage.TECHNICAL, criteria),
                ),
            ]

            result = ScreeningResult(
                total_companies=len(companies),
                passed_companies=len(passed_stage5),
                failed_companies=len(companies) - len(passed_stage5),
                borderline_companies=0,
                stage_results=stage_results,
                company_results=company_results,
                top_scorers=top_scorers,
            )

            self.logger.info(
                f"Screening complete: {len(passed_stage5)}/{len(companies)} "
                f"passed ({result.to_dict()['pass_rate_pct']:.1f}%)"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error running screening: {e}")
            return None

    @staticmethod
    def _filter_market_cap(company: Dict, criteria: ScreeningCriteria) -> FilterResult:
        """Filter by market cap."""
        market_cap = company.get("market_cap_millions")
        if market_cap is None:
            return FilterResult.INSUFFICIENT_DATA

        if criteria.min_market_cap_millions and market_cap < criteria.min_market_cap_millions:
            return FilterResult.FAIL
        if criteria.max_market_cap_millions and market_cap > criteria.max_market_cap_millions:
            return FilterResult.FAIL

        return FilterResult.PASS

    @staticmethod
    def _filter_growth(company: Dict, criteria: ScreeningCriteria) -> FilterResult:
        """Filter by growth rates."""
        revenue_growth = company.get("revenue_growth_pct")
        profit_growth = company.get("profit_growth_pct")

        if criteria.min_revenue_growth_pct and revenue_growth:
            if revenue_growth < criteria.min_revenue_growth_pct:
                return FilterResult.FAIL

        if criteria.min_profit_growth_pct and profit_growth:
            if profit_growth < criteria.min_profit_growth_pct:
                return FilterResult.FAIL

        return FilterResult.PASS

    @staticmethod
    def _filter_valuation(company: Dict, criteria: ScreeningCriteria) -> FilterResult:
        """Filter by valuation multiples."""
        pe_ratio = company.get("pe_ratio")
        pb_ratio = company.get("pb_ratio")

        if criteria.max_pe_ratio and pe_ratio and pe_ratio > criteria.max_pe_ratio:
            return FilterResult.FAIL
        if criteria.max_pb_ratio and pb_ratio and pb_ratio > criteria.max_pb_ratio:
            return FilterResult.FAIL

        return FilterResult.PASS

    @staticmethod
    def _filter_quality(company: Dict, criteria: ScreeningCriteria) -> FilterResult:
        """Filter by quality metrics."""
        roe = company.get("roe_pct")
        net_margin = company.get("net_margin_pct")
        debt_to_equity = company.get("debt_to_equity")

        if criteria.min_roe_pct and roe and roe < criteria.min_roe_pct:
            return FilterResult.FAIL
        if criteria.min_net_margin_pct and net_margin and net_margin < criteria.min_net_margin_pct:
            return FilterResult.FAIL
        if criteria.max_debt_to_equity and debt_to_equity and debt_to_equity > criteria.max_debt_to_equity:
            return FilterResult.FAIL

        return FilterResult.PASS

    @staticmethod
    def _filter_technical(company: Dict, criteria: ScreeningCriteria) -> FilterResult:
        """Filter by technical indicators."""
        trend = company.get("trend")
        trend_strength = company.get("trend_strength_pct")

        if criteria.required_trend and trend != criteria.required_trend:
            return FilterResult.FAIL
        if criteria.min_trend_strength_pct and trend_strength:
            if trend_strength < criteria.min_trend_strength_pct:
                return FilterResult.FAIL

        return FilterResult.PASS

    @staticmethod
    def _calculate_screening_score(company: Dict, criteria: ScreeningCriteria) -> float:
        """Calculate overall screening score (0-100)."""
        score = 50.0  # Base score

        # Add points for criteria met
        if criteria.min_revenue_growth_pct:
            revenue_growth = company.get("revenue_growth_pct", 0)
            if revenue_growth >= criteria.min_revenue_growth_pct:
                score += 10

        if criteria.min_roe_pct:
            roe = company.get("roe_pct", 0)
            if roe >= criteria.min_roe_pct:
                score += 10

        if criteria.max_pe_ratio:
            pe = company.get("pe_ratio", 999)
            if pe <= criteria.max_pe_ratio:
                score += 10

        return min(100, score)

    @staticmethod
    def _determine_failed_stage(company: Dict, criteria: ScreeningCriteria) -> Optional[ScreeningStage]:
        """Determine which stage company failed at."""
        if AdvancedScreener._filter_market_cap(company, criteria) == FilterResult.FAIL:
            return ScreeningStage.MARKET_CAP
        if AdvancedScreener._filter_growth(company, criteria) == FilterResult.FAIL:
            return ScreeningStage.GROWTH
        if AdvancedScreener._filter_valuation(company, criteria) == FilterResult.FAIL:
            return ScreeningStage.VALUATION
        if AdvancedScreener._filter_quality(company, criteria) == FilterResult.FAIL:
            return ScreeningStage.QUALITY
        if AdvancedScreener._filter_technical(company, criteria) == FilterResult.FAIL:
            return ScreeningStage.TECHNICAL
        return None

    @staticmethod
    def _get_filters_applied(stage: ScreeningStage, criteria: ScreeningCriteria) -> List[str]:
        """Get list of filters applied at a stage."""
        filters = []

        if stage == ScreeningStage.MARKET_CAP:
            if criteria.min_market_cap_millions:
                filters.append(f"Min Market Cap: {criteria.min_market_cap_millions}M")
            if criteria.max_market_cap_millions:
                filters.append(f"Max Market Cap: {criteria.max_market_cap_millions}M")

        elif stage == ScreeningStage.GROWTH:
            if criteria.min_revenue_growth_pct:
                filters.append(f"Min Revenue Growth: {criteria.min_revenue_growth_pct}%")
            if criteria.min_profit_growth_pct:
                filters.append(f"Min Profit Growth: {criteria.min_profit_growth_pct}%")

        elif stage == ScreeningStage.VALUATION:
            if criteria.max_pe_ratio:
                filters.append(f"Max P/E: {criteria.max_pe_ratio}")
            if criteria.max_pb_ratio:
                filters.append(f"Max P/B: {criteria.max_pb_ratio}")

        elif stage == ScreeningStage.QUALITY:
            if criteria.min_roe_pct:
                filters.append(f"Min ROE: {criteria.min_roe_pct}%")
            if criteria.min_net_margin_pct:
                filters.append(f"Min Net Margin: {criteria.min_net_margin_pct}%")
            if criteria.max_debt_to_equity:
                filters.append(f"Max D/E: {criteria.max_debt_to_equity}")

        elif stage == ScreeningStage.TECHNICAL:
            if criteria.required_trend:
                filters.append(f"Trend: {criteria.required_trend}")
            if criteria.min_trend_strength_pct:
                filters.append(f"Min Trend Strength: {criteria.min_trend_strength_pct}%")

        return filters
