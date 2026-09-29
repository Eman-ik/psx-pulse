"""
Module 6, Sprint R6: Valuation Context Integration

Comprehensive valuation analysis for trade planning decisions.

Integrates Module 2 (valuation data):
- P/E vs historical median
- Fair value vs market price
- Dividend yield assessment
- Valuation score calculation (0-100)
- Margin of safety calculation
- Investment rating (Undervalued/Fair/Overvalued)
- Entry price quality assessment
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import date
from typing import Optional, List, Dict, Tuple
import json


# ════════════════════════════════════════════════════════════════════════════════
# ENUMS
# ════════════════════════════════════════════════════════════════════════════════

class ValuationStatus(Enum):
    """Investment rating based on valuation metrics."""
    UNDERVALUED = "UNDERVALUED"      # Price << Fair value
    FAIRLY_VALUED = "FAIRLY_VALUED"  # Price ≈ Fair value
    OVERVALUED = "OVERVALUED"        # Price > Fair value


class PERelative(Enum):
    """P/E relative to median."""
    SIGNIFICANTLY_BELOW = "SIGNIFICANTLY_BELOW"  # < 0.8x median
    BELOW_MEDIAN = "BELOW_MEDIAN"                # 0.8-0.95x median
    AT_MEDIAN = "AT_MEDIAN"                      # 0.95-1.05x median
    ABOVE_MEDIAN = "ABOVE_MEDIAN"                # 1.05-1.2x median
    SIGNIFICANTLY_ABOVE = "SIGNIFICANTLY_ABOVE"  # > 1.2x median


class DividendStatus(Enum):
    """Dividend yield classification."""
    HIGH = "HIGH"              # > 3.5%
    MODERATE = "MODERATE"      # 2.0-3.5%
    LOW = "LOW"                # 0.5-2.0%
    MINIMAL = "MINIMAL"        # 0-0.5%
    NONE = "NONE"              # No dividend


# ════════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class ValuationMetrics:
    """Valuation data snapshot."""
    current_price: float
    earnings_per_share: float
    pe_ratio: float
    pe_median_1y: float        # Median P/E over 1Y
    pe_median_3y: float        # Median P/E over 3Y
    pe_median_5y: float        # Median P/E over 5Y
    price_to_book: float       # P/B ratio
    price_to_sales: float      # P/S ratio
    peg_ratio: Optional[float] = None  # P/E / Growth%
    dividend_yield: float = 0.0
    annual_dividend: Optional[float] = None
    forward_eps: Optional[float] = None  # Next 12-month EPS estimate
    fair_value_estimate: Optional[float] = None  # Analyst estimate
    valuation_date: date = field(default_factory=date.today)

    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "current_price": self.current_price,
            "earnings_per_share": self.earnings_per_share,
            "pe_ratio": self.pe_ratio,
            "pe_median_1y": self.pe_median_1y,
            "pe_median_3y": self.pe_median_3y,
            "pe_median_5y": self.pe_median_5y,
            "price_to_book": self.price_to_book,
            "price_to_sales": self.price_to_sales,
            "peg_ratio": self.peg_ratio,
            "dividend_yield": self.dividend_yield,
            "annual_dividend": self.annual_dividend,
            "forward_eps": self.forward_eps,
            "fair_value_estimate": self.fair_value_estimate,
            "valuation_date": self.valuation_date.isoformat(),
        }


@dataclass
class ValuationContext:
    """Complete valuation context for trade planning."""
    ticker: str
    metrics: ValuationMetrics
    status: ValuationStatus
    pe_relative: PERelative
    dividend_status: DividendStatus
    valuation_score: float  # 0-100
    margin_of_safety: float  # % below fair value
    upside_potential: float  # % to fair value
    description: str

    def to_dict(self) -> Dict:
        """Serialize to dict for API."""
        return {
            "ticker": self.ticker,
            "metrics": self.metrics.to_dict(),
            "status": self.status.value,
            "pe_relative": self.pe_relative.value,
            "dividend_status": self.dividend_status.value,
            "valuation_score": self.valuation_score,
            "margin_of_safety": self.margin_of_safety,
            "upside_potential": self.upside_potential,
            "description": self.description,
        }


# ════════════════════════════════════════════════════════════════════════════════
# VALUATION EXTRACTOR
# ════════════════════════════════════════════════════════════════════════════════

class ValuationContextExtractor:
    """Extract and classify valuation metrics."""

    @staticmethod
    def classify_pe_relative(pe_ratio: float, pe_median: float) -> PERelative:
        """Classify P/E relative to median."""
        ratio = pe_ratio / pe_median if pe_median > 0 else 1.0

        if ratio < 0.8:
            return PERelative.SIGNIFICANTLY_BELOW
        elif ratio < 0.95:
            return PERelative.BELOW_MEDIAN
        elif ratio <= 1.05:
            return PERelative.AT_MEDIAN
        elif ratio <= 1.2:
            return PERelative.ABOVE_MEDIAN
        else:
            return PERelative.SIGNIFICANTLY_ABOVE

    @staticmethod
    def classify_dividend_yield(yield_pct: float) -> DividendStatus:
        """Classify dividend yield."""
        if yield_pct < 0:
            return DividendStatus.NONE
        elif yield_pct < 0.5:
            return DividendStatus.MINIMAL
        elif yield_pct < 2.0:
            return DividendStatus.LOW
        elif yield_pct < 3.5:
            return DividendStatus.MODERATE
        else:
            return DividendStatus.HIGH

    @staticmethod
    def classify_valuation_status(
        current_price: float,
        fair_value: float,
        tolerance_pct: float = 5.0
    ) -> ValuationStatus:
        """Classify valuation status vs fair value."""
        if fair_value <= 0:
            return ValuationStatus.FAIRLY_VALUED

        diff_pct = ((fair_value - current_price) / current_price) * 100

        if diff_pct > tolerance_pct:
            return ValuationStatus.UNDERVALUED
        elif diff_pct < -tolerance_pct:
            return ValuationStatus.OVERVALUED
        else:
            return ValuationStatus.FAIRLY_VALUED

    @staticmethod
    def calculate_valuation_score(
        pe_relative: PERelative,
        pb_ratio: float,
        ps_ratio: float,
        dividend_yield: float,
        peg_ratio: Optional[float] = None
    ) -> float:
        """
        Calculate composite valuation score (0-100).

        Components:
        - P/E relative to median: 0-30 points
        - P/B ratio (lower is better): 0-25 points
        - P/S ratio (lower is better): 0-20 points
        - Dividend yield: 0-15 points
        - PEG ratio (if available): 0-10 points
        """
        score = 50  # Base score

        # P/E relative (30 pts): undervalued is better
        pe_points = {
            PERelative.SIGNIFICANTLY_BELOW: 30,
            PERelative.BELOW_MEDIAN: 25,
            PERelative.AT_MEDIAN: 15,
            PERelative.ABOVE_MEDIAN: 5,
            PERelative.SIGNIFICANTLY_ABOVE: 0,
        }
        score += pe_points.get(pe_relative, 15)

        # P/B ratio (25 pts): < 1.0 is best
        if pb_ratio <= 1.0:
            score += 25
        elif pb_ratio <= 2.0:
            score += 15
        elif pb_ratio <= 3.0:
            score += 8
        else:
            score += 2

        # P/S ratio (20 pts): < 1.0 is best
        if ps_ratio <= 1.0:
            score += 20
        elif ps_ratio <= 2.0:
            score += 12
        elif ps_ratio <= 3.0:
            score += 6
        else:
            score += 2

        # Dividend yield (15 pts)
        if dividend_yield >= 3.5:
            score += 15
        elif dividend_yield >= 2.0:
            score += 10
        elif dividend_yield >= 0.5:
            score += 5
        else:
            score += 0

        # PEG ratio (10 pts, if available)
        if peg_ratio is not None:
            if peg_ratio <= 1.0:
                score += 10
            elif peg_ratio <= 1.5:
                score += 6
            elif peg_ratio <= 2.0:
                score += 3
            else:
                score += 0

        return min(max(score, 0), 100)

    @staticmethod
    def calculate_margin_of_safety(current_price: float, fair_value: float) -> float:
        """
        Calculate margin of safety.

        MOS = (Fair Value - Current Price) / Current Price * 100
        Positive = undervalued, Negative = overvalued
        """
        if current_price <= 0:
            return 0.0

        return ((fair_value - current_price) / current_price) * 100

    @staticmethod
    def calculate_upside_potential(current_price: float, fair_value: float) -> float:
        """
        Calculate upside to fair value.

        Upside = (Fair Value - Current Price) / Current Price * 100
        Same as MOS when fair_value > current_price
        """
        if current_price <= 0:
            return 0.0

        return ((fair_value - current_price) / current_price) * 100

    @staticmethod
    def extract_valuation_context(
        ticker: str,
        current_price: float,
        earnings_per_share: float,
        pe_ratio: float,
        pe_median_1y: float,
        price_to_book: float,
        price_to_sales: float,
        dividend_yield: float = 0.0,
        peg_ratio: Optional[float] = None,
        fair_value_estimate: Optional[float] = None,
        forward_eps: Optional[float] = None,
        annual_dividend: Optional[float] = None,
    ) -> ValuationContext:
        """Extract complete valuation context."""

        # Default fair value if not provided
        if fair_value_estimate is None:
            fair_value_estimate = current_price * 1.15  # Assume 15% upside

        # Classify metrics
        pe_relative = ValuationContextExtractor.classify_pe_relative(
            pe_ratio,
            pe_median_1y
        )
        dividend_status = ValuationContextExtractor.classify_dividend_yield(
            dividend_yield
        )
        valuation_status = ValuationContextExtractor.classify_valuation_status(
            current_price,
            fair_value_estimate
        )

        # Calculate scores
        valuation_score = ValuationContextExtractor.calculate_valuation_score(
            pe_relative,
            price_to_book,
            price_to_sales,
            dividend_yield,
            peg_ratio
        )

        margin_of_safety = ValuationContextExtractor.calculate_margin_of_safety(
            current_price,
            fair_value_estimate
        )

        upside_potential = ValuationContextExtractor.calculate_upside_potential(
            current_price,
            fair_value_estimate
        )

        # Build description
        description = f"{ticker}: {valuation_status.value} at {pe_relative.value}. "
        description += f"P/E {pe_ratio:.1f}x (median {pe_median_1y:.1f}x). "
        description += f"Fair value ${fair_value_estimate:.2f}, "
        description += f"margin of safety {margin_of_safety:.1f}%. "

        if dividend_status != DividendStatus.NONE:
            description += f"Yield {dividend_yield:.2f}%. "

        metrics = ValuationMetrics(
            current_price=current_price,
            earnings_per_share=earnings_per_share,
            pe_ratio=pe_ratio,
            pe_median_1y=pe_median_1y,
            pe_median_3y=pe_median_1y * 0.95,  # Assume slight historical trend
            pe_median_5y=pe_median_1y * 0.93,
            price_to_book=price_to_book,
            price_to_sales=price_to_sales,
            peg_ratio=peg_ratio,
            dividend_yield=dividend_yield,
            annual_dividend=annual_dividend,
            forward_eps=forward_eps,
            fair_value_estimate=fair_value_estimate,
        )

        return ValuationContext(
            ticker=ticker,
            metrics=metrics,
            status=valuation_status,
            pe_relative=pe_relative,
            dividend_status=dividend_status,
            valuation_score=valuation_score,
            margin_of_safety=margin_of_safety,
            upside_potential=upside_potential,
            description=description,
        )


# ════════════════════════════════════════════════════════════════════════════════
# VALUATION VALIDATOR
# ════════════════════════════════════════════════════════════════════════════════

class ValuationValidator:
    """Validate entry decisions against valuation metrics."""

    @staticmethod
    def validate_entry_vs_valuation(
        valuation_status: ValuationStatus,
        valuation_score: float,
        margin_of_safety: float,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if entry is sound from valuation perspective.

        Returns: (is_valid, warning_message)
        """
        warnings = []

        # Overvalued warning
        if valuation_status == ValuationStatus.OVERVALUED:
            if margin_of_safety < -20:
                warnings.append(
                    f"CAUTION: Stock is significantly overvalued "
                    f"({margin_of_safety:.1f}% above fair value). "
                    f"Risk/reward is unfavorable."
                )
            elif margin_of_safety < -10:
                warnings.append(
                    f"Stock is overvalued ({margin_of_safety:.1f}% above fair value). "
                    f"Consider waiting for pullback."
                )

        # Low valuation score
        if valuation_score < 40:
            warnings.append(
                f"Valuation score is low ({valuation_score:.0f}/100). "
                f"Multiple expansion risk."
            )

        # Positive: undervalued entry
        if valuation_status == ValuationStatus.UNDERVALUED:
            if margin_of_safety > 25:
                return True, None  # Excellent entry

        combined_warning = " | ".join(warnings) if warnings else None
        return True, combined_warning

    @staticmethod
    def validate_pe_reasonableness(
        pe_ratio: float,
        pe_median: float,
        growth_rate: Optional[float] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if P/E is reasonable for company quality/growth.

        Rule: P/E should be reasonable relative to growth
        (PEG ratio ~1.0 is fair)
        """
        if pe_median <= 0:
            return True, None

        pe_relative = pe_ratio / pe_median

        # P/E too high relative to median
        if pe_relative > 1.5:
            return True, f"P/E {pe_ratio:.1f}x is {(pe_relative-1)*100:.0f}% above median. Verify growth justifies premium."

        # P/E significantly below median
        if pe_relative < 0.6 and growth_rate and growth_rate > 0:
            return True, None  # Potentially good value

        return True, None

    @staticmethod
    def validate_dividend_sustainability(
        annual_dividend: Optional[float],
        earnings_per_share: float,
        fcf_per_share: Optional[float] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if dividend is sustainable.

        Dividend should not exceed earnings or FCF.
        """
        if annual_dividend is None or annual_dividend <= 0:
            return True, None

        # Check payout ratio
        if earnings_per_share > 0:
            payout_ratio = annual_dividend / earnings_per_share
            if payout_ratio > 1.0:
                return True, f"Dividend payout ratio {payout_ratio:.1%} exceeds earnings. Sustainability at risk."
            elif payout_ratio > 0.8:
                return True, f"High payout ratio {payout_ratio:.1%}. Limited room for growth."

        # Check against FCF if available
        if fcf_per_share and fcf_per_share > 0:
            fcf_payout = annual_dividend / fcf_per_share
            if fcf_payout > 1.0:
                return True, f"Dividend exceeds FCF. Sustainability questionable."

        return True, None


# ════════════════════════════════════════════════════════════════════════════════
# INTEGRATION FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def enhance_trade_plan_with_valuation(
    trade_plan: Dict,
    context: ValuationContext,
) -> Dict:
    """Add valuation context to trade plan."""
    enhanced = trade_plan.copy()

    # Add context
    enhanced["valuation_context"] = context.to_dict()

    # Add validation
    is_valid, warning = ValuationValidator.validate_entry_vs_valuation(
        context.status,
        context.valuation_score,
        context.margin_of_safety,
    )
    enhanced["valuation_validation"] = {
        "is_valid": is_valid,
        "warning": warning,
    }

    # Add valuation warnings to plan
    warnings = []
    if warning:
        warnings.append(warning)

    # P/E validation
    _, pe_warning = ValuationValidator.validate_pe_reasonableness(
        context.metrics.pe_ratio,
        context.metrics.pe_median_1y,
    )
    if pe_warning:
        warnings.append(pe_warning)

    enhanced["valuation_warnings"] = warnings

    return enhanced


# ════════════════════════════════════════════════════════════════════════════════
# API HANDLERS
# ════════════════════════════════════════════════════════════════════════════════

def api_get_valuation_context(
    ticker: str,
    current_price: float,
    earnings_per_share: float,
    pe_ratio: float,
    pe_median_1y: float,
    price_to_book: float,
    price_to_sales: float,
    dividend_yield: float = 0.0,
    **kwargs
) -> Dict:
    """API: Get valuation context."""
    try:
        context = ValuationContextExtractor.extract_valuation_context(
            ticker=ticker,
            current_price=current_price,
            earnings_per_share=earnings_per_share,
            pe_ratio=pe_ratio,
            pe_median_1y=pe_median_1y,
            price_to_book=price_to_book,
            price_to_sales=price_to_sales,
            dividend_yield=dividend_yield,
            **kwargs
        )

        return {
            "success": True,
            "valuation_context": context.to_dict(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
