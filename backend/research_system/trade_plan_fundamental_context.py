"""
Trade Plan Fundamental Context Integration - Module 6, Sprint R5

Pulls financial fundamentals from Module 1 (Research) to inform trade plan decisions.

Context provided:
- EPS trend (improving, declining, stable)
- Revenue growth (1Y, 3Y)
- Profitability metrics (ROE, ROA, margins)
- Debt trajectory (declining, stable, rising)
- Cash flow status (positive, negative)
- Balance sheet strength
- Latest results date
- Financial momentum

This module bridges fundamental analysis (Module 1) with trade planning (Module 6).
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, date


# ════════════════════════════════════════════════════════════════════════════════
# ENUMS & CONSTANTS
# ════════════════════════════════════════════════════════════════════════════════

class EPSTrend(str, Enum):
    """EPS trajectory."""
    ACCELERATING = "ACCELERATING"        # Growing faster
    IMPROVING = "IMPROVING"              # Growing steadily
    STABLE = "STABLE"                    # Flat earnings
    DECLINING = "DECLINING"              # Falling earnings
    DETERIORATING = "DETERIORATING"      # Falling faster


class DebtTrend(str, Enum):
    """Debt trajectory."""
    IMPROVING = "IMPROVING"              # Debt/Equity falling
    STABLE = "STABLE"                    # Steady leverage
    RISING = "RISING"                    # Debt/Equity rising
    CRITICAL = "CRITICAL"                # Unsustainable leverage


class CashFlowStatus(str, Enum):
    """Free cash flow condition."""
    STRONG = "STRONG"                    # FCF > Net Income
    POSITIVE = "POSITIVE"                # FCF > 0
    WEAK = "WEAK"                        # FCF > 0 but small
    NEGATIVE = "NEGATIVE"                # FCF < 0


class FinancialMomentum(str, Enum):
    """Overall financial trajectory."""
    ACCELERATING = "ACCELERATING"        # Improving across metrics
    IMPROVING = "IMPROVING"              # Most metrics positive
    STABLE = "STABLE"                    # Mixed or flat
    DECLINING = "DECLINING"              # Most metrics negative
    DETERIORATING = "DETERIORATING"      # Deteriorating across metrics


# ════════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ════════════════════════════════════════════════════════════════════════════════

class FundamentalMetrics:
    """Core financial metrics snapshot."""

    def __init__(
        self,
        latest_eps: Optional[float],
        eps_1y_growth: Optional[float],
        eps_3y_growth: Optional[float],
        eps_trend: EPSTrend,
        revenue_1y_growth: Optional[float],
        revenue_3y_growth: Optional[float],
        roe: Optional[float],
        roa: Optional[float],
        roic: Optional[float],
        debt_to_equity: Optional[float],
        debt_trend: DebtTrend,
        fcf: Optional[float],
        fcf_status: CashFlowStatus,
        net_margin: Optional[float],
        operating_margin: Optional[float],
        latest_results_date: Optional[date],
        results_age_days: Optional[int],
    ):
        self.latest_eps = latest_eps
        self.eps_1y_growth = eps_1y_growth
        self.eps_3y_growth = eps_3y_growth
        self.eps_trend = eps_trend
        self.revenue_1y_growth = revenue_1y_growth
        self.revenue_3y_growth = revenue_3y_growth
        self.roe = roe
        self.roa = roa
        self.roic = roic
        self.debt_to_equity = debt_to_equity
        self.debt_trend = debt_trend
        self.fcf = fcf
        self.fcf_status = fcf_status
        self.net_margin = net_margin
        self.operating_margin = operating_margin
        self.latest_results_date = latest_results_date
        self.results_age_days = results_age_days

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response dict."""
        return {
            "earnings": {
                "latest_eps": self.latest_eps,
                "1y_growth": self.eps_1y_growth,
                "3y_growth": self.eps_3y_growth,
                "trend": self.eps_trend.value if self.eps_trend else None,
            },
            "revenue": {
                "1y_growth": self.revenue_1y_growth,
                "3y_growth": self.revenue_3y_growth,
            },
            "profitability": {
                "roe": self.roe,
                "roa": self.roa,
                "roic": self.roic,
                "net_margin": self.net_margin,
                "operating_margin": self.operating_margin,
            },
            "leverage": {
                "debt_to_equity": self.debt_to_equity,
                "trend": self.debt_trend.value if self.debt_trend else None,
            },
            "cash_flow": {
                "fcf": self.fcf,
                "status": self.fcf_status.value if self.fcf_status else None,
            },
            "reporting": {
                "latest_results_date": self.latest_results_date.isoformat() if self.latest_results_date else None,
                "results_age_days": self.results_age_days,
            },
        }


class FundamentalContext:
    """Complete fundamental analysis context."""

    def __init__(
        self,
        ticker: str,
        metrics: FundamentalMetrics,
        momentum: FinancialMomentum,
        financial_health_score: float,
        quality_score: float,
        description: str,
    ):
        self.ticker = ticker
        self.metrics = metrics
        self.momentum = momentum
        self.financial_health_score = financial_health_score  # 0-100
        self.quality_score = quality_score  # 0-100
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response dict."""
        return {
            "ticker": self.ticker,
            "momentum": self.momentum.value,
            "financial_health_score": round(self.financial_health_score, 1),
            "quality_score": round(self.quality_score, 1),
            "metrics": self.metrics.to_dict(),
            "description": self.description,
        }


# ════════════════════════════════════════════════════════════════════════════════
# FUNDAMENTAL CONTEXT EXTRACTION
# ════════════════════════════════════════════════════════════════════════════════

class FundamentalContextExtractor:
    """Extract fundamental context for trade planning."""

    @staticmethod
    def classify_eps_trend(
        eps_1y_growth: Optional[float],
        eps_3y_growth: Optional[float],
    ) -> EPSTrend:
        """
        Classify EPS trend.

        Args:
            eps_1y_growth: 1-year EPS growth (%)
            eps_3y_growth: 3-year EPS growth (%)

        Returns:
            EPSTrend classification
        """
        if eps_1y_growth is None:
            return EPSTrend.STABLE

        # Accelerating: 1Y growth > 3Y growth
        if eps_3y_growth is not None and eps_1y_growth > eps_3y_growth + 5:
            return EPSTrend.ACCELERATING

        # Improving: Positive growth
        if eps_1y_growth > 5:
            return EPSTrend.IMPROVING

        # Stable: -5% to +5%
        if -5 <= eps_1y_growth <= 5:
            return EPSTrend.STABLE

        # Declining: -15% to -5%
        if -15 <= eps_1y_growth <= -5:
            return EPSTrend.DECLINING

        # Deteriorating: < -15%
        return EPSTrend.DETERIORATING

    @staticmethod
    def classify_debt_trend(
        debt_to_equity_current: Optional[float],
        debt_to_equity_3y_avg: Optional[float],
    ) -> DebtTrend:
        """
        Classify debt trajectory.

        Args:
            debt_to_equity_current: Current D/E ratio
            debt_to_equity_3y_avg: 3-year average D/E ratio

        Returns:
            DebtTrend classification
        """
        if debt_to_equity_current is None:
            return DebtTrend.STABLE

        # Critical: D/E > 1.5
        if debt_to_equity_current > 1.5:
            return DebtTrend.CRITICAL

        # Rising: D/E increasing
        if debt_to_equity_3y_avg and debt_to_equity_current > debt_to_equity_3y_avg:
            return DebtTrend.RISING

        # Improving: D/E decreasing
        if debt_to_equity_3y_avg and debt_to_equity_current < debt_to_equity_3y_avg - 0.1:
            return DebtTrend.IMPROVING

        return DebtTrend.STABLE

    @staticmethod
    def classify_fcf_status(
        fcf: Optional[float],
        net_income: Optional[float],
    ) -> CashFlowStatus:
        """
        Classify free cash flow status.

        Args:
            fcf: Free cash flow (PKR)
            net_income: Net income (PKR)

        Returns:
            CashFlowStatus classification
        """
        if fcf is None or fcf <= 0:
            return CashFlowStatus.NEGATIVE

        if net_income is None or net_income <= 0:
            return CashFlowStatus.POSITIVE

        # Strong: FCF > Net Income (quality)
        if fcf > net_income * 1.1:
            return CashFlowStatus.STRONG

        # Positive: FCF > 0 and meaningful
        if fcf > net_income * 0.5:
            return CashFlowStatus.POSITIVE

        # Weak: FCF > 0 but small
        return CashFlowStatus.WEAK

    @staticmethod
    def calculate_financial_health_score(
        roe: Optional[float],
        debt_to_equity: Optional[float],
        fcf_status: CashFlowStatus,
    ) -> float:
        """
        Calculate overall financial health score (0-100).

        Args:
            roe: Return on Equity (%)
            debt_to_equity: Debt to Equity ratio
            fcf_status: Free cash flow status

        Returns:
            Health score (0-100)
        """
        score = 50.0  # Base

        # ROE component (0-30 points)
        if roe:
            if roe > 20:
                score += 30
            elif roe > 15:
                score += 25
            elif roe > 10:
                score += 20
            elif roe > 5:
                score += 10
            else:
                score += 5

        # Debt component (0-30 points)
        if debt_to_equity is not None:
            if debt_to_equity < 0.3:
                score += 30
            elif debt_to_equity < 0.6:
                score += 25
            elif debt_to_equity < 0.9:
                score += 15
            elif debt_to_equity < 1.2:
                score += 5
            else:
                score -= 20

        # FCF component (0-20 points)
        if fcf_status == CashFlowStatus.STRONG:
            score += 20
        elif fcf_status == CashFlowStatus.POSITIVE:
            score += 10
        elif fcf_status == CashFlowStatus.WEAK:
            score += 5
        else:
            score -= 15

        return max(0, min(100, score))

    @staticmethod
    def calculate_quality_score(
        eps_trend: EPSTrend,
        revenue_1y_growth: Optional[float],
        net_margin: Optional[float],
        fcf_status: CashFlowStatus,
    ) -> float:
        """
        Calculate earnings quality score (0-100).

        Args:
            eps_trend: EPS trend
            revenue_1y_growth: Revenue growth (%)
            net_margin: Net profit margin (%)
            fcf_status: Cash flow status

        Returns:
            Quality score (0-100)
        """
        score = 50.0  # Base

        # EPS trend component (0-25 points)
        if eps_trend == EPSTrend.ACCELERATING:
            score += 25
        elif eps_trend == EPSTrend.IMPROVING:
            score += 20
        elif eps_trend == EPSTrend.STABLE:
            score += 10
        elif eps_trend == EPSTrend.DECLINING:
            score -= 10
        else:
            score -= 20

        # Revenue growth component (0-25 points)
        if revenue_1y_growth:
            if revenue_1y_growth > 15:
                score += 25
            elif revenue_1y_growth > 10:
                score += 20
            elif revenue_1y_growth > 5:
                score += 10
            elif revenue_1y_growth > 0:
                score += 5
            else:
                score -= 10

        # Margin component (0-20 points)
        if net_margin:
            if net_margin > 15:
                score += 20
            elif net_margin > 10:
                score += 15
            elif net_margin > 5:
                score += 10
            else:
                score += 5

        # FCF quality (0-10 points)
        if fcf_status == CashFlowStatus.STRONG:
            score += 10
        elif fcf_status == CashFlowStatus.POSITIVE:
            score += 5

        return max(0, min(100, score))

    @staticmethod
    def classify_financial_momentum(
        eps_trend: EPSTrend,
        revenue_growth: Optional[float],
        debt_trend: DebtTrend,
        fcf_status: CashFlowStatus,
    ) -> FinancialMomentum:
        """
        Classify overall financial momentum.

        Args:
            eps_trend: EPS trend
            revenue_growth: Revenue growth (%)
            debt_trend: Debt trend
            fcf_status: Cash flow status

        Returns:
            FinancialMomentum classification
        """
        positive_signals = 0

        # EPS signal
        if eps_trend in [EPSTrend.ACCELERATING, EPSTrend.IMPROVING]:
            positive_signals += 1
        elif eps_trend == EPSTrend.DETERIORATING:
            positive_signals -= 1

        # Revenue signal
        if revenue_growth and revenue_growth > 5:
            positive_signals += 1
        elif revenue_growth and revenue_growth < 0:
            positive_signals -= 1

        # Debt signal
        if debt_trend == DebtTrend.IMPROVING:
            positive_signals += 1
        elif debt_trend == DebtTrend.CRITICAL:
            positive_signals -= 1

        # FCF signal
        if fcf_status in [CashFlowStatus.STRONG, CashFlowStatus.POSITIVE]:
            positive_signals += 1
        elif fcf_status == CashFlowStatus.NEGATIVE:
            positive_signals -= 1

        if positive_signals >= 3:
            return FinancialMomentum.ACCELERATING
        elif positive_signals >= 2:
            return FinancialMomentum.IMPROVING
        elif positive_signals >= 0:
            return FinancialMomentum.STABLE
        elif positive_signals >= -1:
            return FinancialMomentum.DECLINING
        else:
            return FinancialMomentum.DETERIORATING

    @staticmethod
    def extract_fundamental_context(
        ticker: str,
        latest_eps: Optional[float] = None,
        eps_1y_growth: Optional[float] = None,
        eps_3y_growth: Optional[float] = None,
        revenue_1y_growth: Optional[float] = None,
        revenue_3y_growth: Optional[float] = None,
        roe: Optional[float] = None,
        roa: Optional[float] = None,
        roic: Optional[float] = None,
        net_margin: Optional[float] = None,
        operating_margin: Optional[float] = None,
        debt_to_equity: Optional[float] = None,
        debt_to_equity_3y_avg: Optional[float] = None,
        fcf: Optional[float] = None,
        net_income: Optional[float] = None,
        latest_results_date: Optional[date] = None,
    ) -> FundamentalContext:
        """
        Extract complete fundamental context.

        Args:
            ticker: Security ticker
            latest_eps: Latest EPS
            eps_1y_growth: 1-year EPS growth (%)
            eps_3y_growth: 3-year EPS growth (%)
            revenue_1y_growth: 1-year revenue growth (%)
            revenue_3y_growth: 3-year revenue growth (%)
            roe: Return on Equity (%)
            roa: Return on Assets (%)
            roic: Return on Invested Capital (%)
            net_margin: Net profit margin (%)
            operating_margin: Operating margin (%)
            debt_to_equity: Current D/E ratio
            debt_to_equity_3y_avg: 3-year average D/E
            fcf: Free cash flow (PKR)
            net_income: Net income (PKR)
            latest_results_date: Date of latest results

        Returns:
            FundamentalContext object
        """
        # Calculate trends
        eps_trend = FundamentalContextExtractor.classify_eps_trend(eps_1y_growth, eps_3y_growth)
        debt_trend = FundamentalContextExtractor.classify_debt_trend(debt_to_equity, debt_to_equity_3y_avg)
        fcf_status = FundamentalContextExtractor.classify_fcf_status(fcf, net_income)

        # Calculate scores
        health_score = FundamentalContextExtractor.calculate_financial_health_score(
            roe, debt_to_equity, fcf_status
        )
        quality_score = FundamentalContextExtractor.calculate_quality_score(
            eps_trend, revenue_1y_growth, net_margin, fcf_status
        )

        # Classify momentum
        momentum = FundamentalContextExtractor.classify_financial_momentum(
            eps_trend, revenue_1y_growth, debt_trend, fcf_status
        )

        # Calculate results age
        results_age_days = None
        if latest_results_date:
            results_age_days = (datetime.now().date() - latest_results_date).days

        # Build metrics
        metrics = FundamentalMetrics(
            latest_eps=latest_eps,
            eps_1y_growth=eps_1y_growth,
            eps_3y_growth=eps_3y_growth,
            eps_trend=eps_trend,
            revenue_1y_growth=revenue_1y_growth,
            revenue_3y_growth=revenue_3y_growth,
            roe=roe,
            roa=roa,
            roic=roic,
            debt_to_equity=debt_to_equity,
            debt_trend=debt_trend,
            fcf=fcf,
            fcf_status=fcf_status,
            net_margin=net_margin,
            operating_margin=operating_margin,
            latest_results_date=latest_results_date,
            results_age_days=results_age_days,
        )

        # Build description
        descriptions = []
        descriptions.append(f"EPS: {eps_trend.value}")
        if revenue_1y_growth is not None:
            descriptions.append(f"Revenue: {revenue_1y_growth:+.1f}% (1Y)")
        if roe is not None:
            descriptions.append(f"ROE: {roe:.1f}%")
        descriptions.append(f"Debt: {debt_trend.value}")
        descriptions.append(f"FCF: {fcf_status.value}")
        descriptions.append(f"Momentum: {momentum.value}")

        description = " | ".join(descriptions)

        return FundamentalContext(
            ticker=ticker,
            metrics=metrics,
            momentum=momentum,
            financial_health_score=health_score,
            quality_score=quality_score,
            description=description,
        )


# ════════════════════════════════════════════════════════════════════════════════
# TRADE PLAN VALIDATION
# ════════════════════════════════════════════════════════════════════════════════

class FundamentalValidator:
    """Validate trade plans against fundamental context."""

    @staticmethod
    def validate_earnings_quality(
        eps_trend: EPSTrend,
        results_age_days: Optional[int],
    ) -> tuple[bool, Optional[str]]:
        """
        Validate entry based on earnings quality.

        Args:
            eps_trend: EPS trend
            results_age_days: Days since latest results

        Returns:
            (is_acceptable, warning_message)
        """
        if eps_trend == EPSTrend.DETERIORATING:
            return (
                True,
                f"Earnings are DETERIORATING. Enter with caution.",
            )

        if results_age_days and results_age_days > 180:
            return (
                True,
                f"Latest results are {results_age_days} days old. Consider waiting for new results.",
            )

        return True, None

    @staticmethod
    def validate_balance_sheet(
        debt_trend: DebtTrend,
        fcf_status: CashFlowStatus,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate balance sheet strength.

        Args:
            debt_trend: Debt trend
            fcf_status: Free cash flow status

        Returns:
            (is_acceptable, warning_message)
        """
        if debt_trend == DebtTrend.CRITICAL:
            return (
                True,
                "Balance sheet is in CRITICAL condition. High financial risk.",
            )

        if debt_trend == DebtTrend.RISING and fcf_status == CashFlowStatus.NEGATIVE:
            return (
                True,
                "Debt rising with negative FCF. Potential liquidity risk.",
            )

        return True, None


# ════════════════════════════════════════════════════════════════════════════════
# TRADE PLAN ENHANCEMENT
# ════════════════════════════════════════════════════════════════════════════════

def enhance_trade_plan_with_fundamentals(
    trade_plan: Dict[str, Any],
    fundamental_context: FundamentalContext,
) -> Dict[str, Any]:
    """
    Enhance trade plan with fundamental context.

    Args:
        trade_plan: Trade plan dictionary
        fundamental_context: FundamentalContext object

    Returns:
        Enhanced trade plan with fundamental analysis
    """
    # Validate fundamentals
    earnings_valid, earnings_warning = FundamentalValidator.validate_earnings_quality(
        fundamental_context.metrics.eps_trend,
        fundamental_context.metrics.results_age_days,
    )

    balance_sheet_valid, balance_sheet_warning = FundamentalValidator.validate_balance_sheet(
        fundamental_context.metrics.debt_trend,
        fundamental_context.metrics.fcf_status,
    )

    # Compile warnings
    warnings = []
    if earnings_warning:
        warnings.append(earnings_warning)
    if balance_sheet_warning:
        warnings.append(balance_sheet_warning)

    return {
        **trade_plan,
        "fundamental_context": fundamental_context.to_dict(),
        "fundamental_validation": {
            "earnings_quality_valid": earnings_valid,
            "balance_sheet_valid": balance_sheet_valid,
        },
        "fundamental_warnings": warnings,
    }


# ════════════════════════════════════════════════════════════════════════════════
# API INTEGRATION
# ════════════════════════════════════════════════════════════════════════════════

def api_get_fundamental_context(
    ticker: str,
    eps_1y_growth: Optional[float] = None,
    eps_3y_growth: Optional[float] = None,
    revenue_1y_growth: Optional[float] = None,
    roe: Optional[float] = None,
    debt_to_equity: Optional[float] = None,
    fcf_status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    API handler: Get fundamental context.

    GET /api/securities/{ticker}/fundamental-context
    """
    try:
        # Parse FCF status if provided
        fcf_status_enum = None
        if fcf_status:
            try:
                fcf_status_enum = CashFlowStatus[fcf_status]
            except KeyError:
                pass

        context = FundamentalContextExtractor.extract_fundamental_context(
            ticker=ticker,
            eps_1y_growth=eps_1y_growth,
            eps_3y_growth=eps_3y_growth,
            revenue_1y_growth=revenue_1y_growth,
            roe=roe,
            debt_to_equity=debt_to_equity,
        )

        return {
            "success": True,
            "fundamental_context": context.to_dict(),
        }

    except Exception as e:
        return {"error": str(e)}
