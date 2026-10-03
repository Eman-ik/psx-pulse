"""Step 23: Valuation Comparator — Deep valuation analysis.

Fair value and multiple analysis:
- Historical P/E ranges (1-year, 3-year, 5-year)
- Forward vs trailing multiples
- Fair value estimation via regression
- Valuation range and discount/premium

Input: Historical valuation data + current metrics
Output: ValuationAnalysis (fair value + multiples)
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class ValuationAnalysis:
    """Deep valuation analysis result."""

    ticker: str
    current_price: float
    current_eps: float

    # Current multiples
    pe_ratio_current: Optional[float] = None
    pb_ratio_current: Optional[float] = None
    dividend_yield_pct: Optional[float] = None

    # Historical multiples
    pe_ratio_1y_avg: Optional[float] = None
    pe_ratio_3y_avg: Optional[float] = None
    pe_ratio_5y_avg: Optional[float] = None

    pe_ratio_1y_min: Optional[float] = None
    pe_ratio_1y_max: Optional[float] = None

    # Peer comparison
    pe_ratio_peer_median: Optional[float] = None
    pb_ratio_peer_median: Optional[float] = None

    # Fair value
    fair_value_estimate: Optional[float] = None
    valuation_range_min: Optional[float] = None
    valuation_range_max: Optional[float] = None

    # Assessment
    discount_premium_pct: Optional[float] = None  # vs fair value
    valuation_assessment: str = "Neutral"  # Undervalued, Fair, Overvalued

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "current_price": round(self.current_price, 2),
            "current_eps": round(self.current_eps, 2),
            "pe_current": round(self.pe_ratio_current, 1) if self.pe_ratio_current else None,
            "pb_current": round(self.pb_ratio_current, 2) if self.pb_ratio_current else None,
            "pe_1y_avg": round(self.pe_ratio_1y_avg, 1) if self.pe_ratio_1y_avg else None,
            "pe_peer_median": round(self.pe_ratio_peer_median, 1) if self.pe_ratio_peer_median else None,
            "fair_value": round(self.fair_value_estimate, 2) if self.fair_value_estimate else None,
            "valuation_range": {
                "min": round(self.valuation_range_min, 2) if self.valuation_range_min else None,
                "max": round(self.valuation_range_max, 2) if self.valuation_range_max else None,
            },
            "discount_premium_pct": round(self.discount_premium_pct, 1) if self.discount_premium_pct else None,
            "assessment": self.valuation_assessment,
        }


class ValuationComparator:
    """Analyzes valuation and fair value."""

    def __init__(self):
        """Initialize valuation comparator."""
        self.logger = logging.getLogger(__name__)

    def analyze_valuation(
        self,
        ticker: str,
        current_price: float,
        current_eps: float,
        current_book_value: Optional[float] = None,
        dividend_per_share: Optional[float] = None,
        historical_pe_ratios: Optional[List[float]] = None,
        peer_pe_median: Optional[float] = None,
    ) -> ValuationAnalysis:
        """Analyze valuation metrics.

        Args:
            ticker: Company ticker
            current_price: Current stock price
            current_eps: Current earnings per share
            current_book_value: Current book value per share
            dividend_per_share: Annual dividend per share
            historical_pe_ratios: List of historical P/E ratios (sorted by date)
            peer_pe_median: Median P/E of peer group

        Returns:
            ValuationAnalysis with fair value
        """
        try:
            analysis = ValuationAnalysis(
                ticker=ticker,
                current_price=current_price,
                current_eps=current_eps,
            )

            # Current multiples
            analysis.pe_ratio_current = (
                current_price / current_eps if current_eps > 0 else None
            )

            if current_book_value and current_book_value > 0:
                analysis.pb_ratio_current = current_price / current_book_value

            if dividend_per_share:
                analysis.dividend_yield_pct = (
                    (dividend_per_share / current_price) * 100
                    if current_price > 0
                    else 0
                )

            # Historical PE analysis
            if historical_pe_ratios and len(historical_pe_ratios) > 0:
                analysis.pe_ratio_1y_avg = sum(
                    historical_pe_ratios[-4:]
                ) / min(4, len(historical_pe_ratios))
                if len(historical_pe_ratios) >= 12:
                    analysis.pe_ratio_3y_avg = sum(
                        historical_pe_ratios[-12:]
                    ) / min(12, len(historical_pe_ratios))
                if len(historical_pe_ratios) >= 20:
                    analysis.pe_ratio_5y_avg = sum(
                        historical_pe_ratios[-20:]
                    ) / min(20, len(historical_pe_ratios))

                analysis.pe_ratio_1y_min = min(historical_pe_ratios[-4:]) if len(historical_pe_ratios) >= 4 else min(historical_pe_ratios)
                analysis.pe_ratio_1y_max = max(historical_pe_ratios[-4:]) if len(historical_pe_ratios) >= 4 else max(historical_pe_ratios)

            # Peer comparison
            analysis.pe_ratio_peer_median = peer_pe_median

            # Fair value estimation
            analysis.fair_value_estimate = self._estimate_fair_value(
                current_eps,
                analysis.pe_ratio_1y_avg,
                analysis.pe_ratio_peer_median,
            )

            # Valuation range
            if analysis.fair_value_estimate:
                analysis.valuation_range_min = (
                    analysis.fair_value_estimate * 0.85
                )
                analysis.valuation_range_max = (
                    analysis.fair_value_estimate * 1.15
                )

                analysis.discount_premium_pct = (
                    ((current_price - analysis.fair_value_estimate)
                    / analysis.fair_value_estimate) * 100
                )

                # Assessment
                if analysis.discount_premium_pct < -10:
                    analysis.valuation_assessment = "Undervalued"
                elif analysis.discount_premium_pct > 10:
                    analysis.valuation_assessment = "Overvalued"
                else:
                    analysis.valuation_assessment = "Fair Value"

            pe_str = f"{analysis.pe_ratio_current:.1f}x" if analysis.pe_ratio_current else "N/A"
            fv_str = f"{analysis.fair_value_estimate:.2f}" if analysis.fair_value_estimate else "N/A"
            self.logger.info(
                f"Valued {ticker}: PE {pe_str}, "
                f"FV {fv_str}, "
                f"assessment: {analysis.valuation_assessment}"
            )
            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing valuation: {e}")
            return ValuationAnalysis(
                ticker=ticker,
                current_price=current_price,
                current_eps=current_eps,
            )

    @staticmethod
    def _estimate_fair_value(
        eps: float,
        historical_pe: Optional[float],
        peer_pe: Optional[float],
    ) -> Optional[float]:
        """Estimate fair value using PE multiples."""
        if eps <= 0:
            return None

        # Use weighted average of available PE multiples
        pe_estimate = None
        weight_sum = 0

        if historical_pe:
            pe_estimate = (pe_estimate or 0) + historical_pe * 0.6
            weight_sum += 0.6

        if peer_pe:
            pe_estimate = (pe_estimate or 0) + peer_pe * 0.4
            weight_sum += 0.4

        if weight_sum == 0:
            return None

        pe_estimate /= weight_sum

        return eps * pe_estimate
