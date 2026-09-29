"""
Composite Valuation Score & Peer Quality Analysis

Sprint V4: Combined valuation metrics, peer quality comparison, and weighted scoring.

Features:
- Composite valuation score (combines multiple metrics)
- Weighted valuation assessment
- Peer quality ranking
- Terminal value estimation (Gordon growth model)
- Historical quality trends
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .schema import Security, ValuationSnapshot, FinancialMetric


class CompositeValuationScore:
    """
    Weighted combination of valuation metrics.

    Metrics included:
    - P/E attractiveness (inverse P/E vs median)
    - P/B attractiveness (inverse P/B vs median)
    - Dividend yield
    - FCF yield
    - EV/EBITDA attractiveness
    """

    def __init__(self, session: Session):
        self.session = session

    def calculate_valuation_score(
        self,
        pe_ratio: Decimal,
        pb_ratio: Decimal,
        dividend_yield: Optional[Decimal],
        fcf_yield: Optional[Decimal],
        ev_ebitda: Decimal,
        peer_median_pe: Decimal,
        peer_median_pb: Decimal,
        peer_median_ev_ebitda: Decimal,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate composite valuation score (0-100).

        Higher score = more attractive valuation.

        Weights (default):
        - P/E discount to peers: 25%
        - P/B discount to peers: 20%
        - Dividend yield: 15%
        - FCF yield: 15%
        - EV/EBITDA discount: 25%
        """
        if weights is None:
            weights = {
                "pe": 0.25,
                "pb": 0.20,
                "dividend": 0.15,
                "fcf": 0.15,
                "ev_ebitda": 0.25,
            }

        score = 0

        # P/E component (0-25 points)
        # Lower P/E relative to peers is better
        if peer_median_pe > 0:
            pe_ratio_float = float(pe_ratio)
            peer_median_float = float(peer_median_pe)

            if pe_ratio_float < peer_median_float * 0.8:
                # Very cheap (<20% below median)
                pe_score = 25
            elif pe_ratio_float < peer_median_float:
                # Moderately cheap
                pe_score = 20 - ((peer_median_float - pe_ratio_float) / peer_median_float) * 5
            elif pe_ratio_float < peer_median_float * 1.2:
                # Moderately expensive
                pe_score = 15 - ((pe_ratio_float - peer_median_float) / peer_median_float) * 5
            else:
                # Very expensive
                pe_score = max(0, 10)
        else:
            pe_score = 12.5

        score += pe_score * weights["pe"]

        # P/B component (0-20 points)
        if peer_median_pb > 0:
            pb_ratio_float = float(pb_ratio)
            peer_median_pb_float = float(peer_median_pb)

            if pb_ratio_float < peer_median_pb_float * 0.8:
                pb_score = 20
            elif pb_ratio_float < peer_median_pb_float:
                pb_score = 16 - ((peer_median_pb_float - pb_ratio_float) / peer_median_pb_float) * 4
            elif pb_ratio_float < peer_median_pb_float * 1.2:
                pb_score = 12 - ((pb_ratio_float - peer_median_pb_float) / peer_median_pb_float) * 4
            else:
                pb_score = max(0, 8)
        else:
            pb_score = 10

        score += pb_score * weights["pb"]

        # Dividend yield component (0-15 points)
        if dividend_yield:
            div_yield_float = float(dividend_yield)
            if div_yield_float >= 8:
                dividend_score = 15
            elif div_yield_float >= 6:
                dividend_score = 12
            elif div_yield_float >= 4:
                dividend_score = 9
            elif div_yield_float >= 2:
                dividend_score = 6
            else:
                dividend_score = 3
        else:
            dividend_score = 0

        score += dividend_score * weights["dividend"]

        # FCF yield component (0-15 points)
        if fcf_yield:
            fcf_yield_float = float(fcf_yield)
            if fcf_yield_float >= 8:
                fcf_score = 15
            elif fcf_yield_float >= 6:
                fcf_score = 12
            elif fcf_yield_float >= 4:
                fcf_score = 9
            elif fcf_yield_float >= 2:
                fcf_score = 6
            else:
                fcf_score = 3
        else:
            fcf_score = 0

        score += fcf_score * weights["fcf"]

        # EV/EBITDA component (0-25 points)
        if peer_median_ev_ebitda > 0:
            ev_ebitda_float = float(ev_ebitda)
            peer_median_ev_float = float(peer_median_ev_ebitda)

            if ev_ebitda_float < peer_median_ev_float * 0.8:
                ev_score = 25
            elif ev_ebitda_float < peer_median_ev_float:
                ev_score = 20 - ((peer_median_ev_float - ev_ebitda_float) / peer_median_ev_float) * 5
            elif ev_ebitda_float < peer_median_ev_float * 1.2:
                ev_score = 15 - ((ev_ebitda_float - peer_median_ev_float) / peer_median_ev_float) * 5
            else:
                ev_score = max(0, 10)
        else:
            ev_score = 12.5

        score += ev_score * weights["ev_ebitda"]

        return round(float(score), 1)

    def get_valuation_rating(self, score: float) -> str:
        """Convert score to rating."""
        if score >= 80:
            return "Extremely Attractive"
        elif score >= 70:
            return "Very Attractive"
        elif score >= 60:
            return "Attractive"
        elif score >= 50:
            return "Fair Value"
        elif score >= 40:
            return "Moderately Expensive"
        elif score >= 30:
            return "Expensive"
        else:
            return "Very Expensive"


class PeerQualityComparison:
    """Compare quality scores across peer group."""

    def __init__(self, session: Session):
        self.session = session

    def get_peer_quality_ranking(
        self,
        peer_tickers: List[str],
        quality_scores: Dict[str, float]
    ) -> List[Tuple[str, float, int]]:
        """
        Rank peers by quality score.

        Returns: [(ticker, score, rank), ...]
        """
        # Sort by quality score (descending)
        ranked = sorted(
            quality_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            (ticker, score, rank + 1)
            for rank, (ticker, score) in enumerate(ranked)
        ]

    def generate_peer_quality_matrix(
        self,
        peer_tickers: List[str],
        quality_scores: Dict[str, float],
        valuation_scores: Dict[str, float]
    ) -> Dict:
        """
        Generate quality vs valuation matrix for peer group.

        Shows where each peer stands in 2D space.
        """
        matrix = {
            "peers": [],
            "group_stats": {
                "avg_quality": 0,
                "avg_valuation": 0,
                "quality_range": (0, 0),
                "valuation_range": (0, 0),
            }
        }

        quality_values = []
        valuation_values = []

        for ticker in peer_tickers:
            quality = quality_scores.get(ticker, 50)
            valuation = valuation_scores.get(ticker, 50)

            quality_values.append(quality)
            valuation_values.append(valuation)

            # Determine quadrant
            if quality >= 70 and valuation >= 70:
                quadrant = "High_Quality_Attractive_Valuation"
            elif quality >= 70:
                quadrant = "High_Quality_Expensive_Valuation"
            elif valuation >= 70:
                quadrant = "Lower_Quality_Attractive_Valuation"
            else:
                quadrant = "Lower_Quality_Expensive_Valuation"

            matrix["peers"].append({
                "ticker": ticker,
                "quality_score": quality,
                "valuation_score": valuation,
                "quadrant": quadrant,
                "position": {
                    "x": valuation,
                    "y": quality,
                }
            })

        # Calculate group statistics
        if quality_values:
            matrix["group_stats"]["avg_quality"] = sum(quality_values) / len(quality_values)
            matrix["group_stats"]["quality_range"] = (min(quality_values), max(quality_values))

        if valuation_values:
            matrix["group_stats"]["avg_valuation"] = sum(valuation_values) / len(valuation_values)
            matrix["group_stats"]["valuation_range"] = (min(valuation_values), max(valuation_values))

        return matrix

    def identify_best_value(
        self,
        peer_tickers: List[str],
        quality_scores: Dict[str, float],
        valuation_scores: Dict[str, float]
    ) -> str:
        """Identify best value stock (high quality, attractive valuation)."""
        best_ticker = None
        best_score = -1

        for ticker in peer_tickers:
            quality = quality_scores.get(ticker, 0)
            valuation = valuation_scores.get(ticker, 0)

            # Combined score favoring high quality + attractive valuation
            combined = (quality * 0.6) + (valuation * 0.4)

            if combined > best_score:
                best_score = combined
                best_ticker = ticker

        return best_ticker


class TerminalValueEstimator:
    """Estimate terminal value using Gordon growth model."""

    def __init__(self, session: Session):
        self.session = session

    def calculate_terminal_value_gordon_growth(
        self,
        fcf_current: Decimal,
        fcf_growth_rate: Decimal,
        wacc: Decimal,
        terminal_growth_rate: Decimal = Decimal("3")
    ) -> Decimal:
        """
        Calculate terminal value using Gordon Growth Model.

        TV = FCF(terminal) × (1 + g) / (WACC - g)

        Args:
            fcf_current: Current FCF
            fcf_growth_rate: Growth rate to terminal year (%)
            wacc: Weighted average cost of capital (%)
            terminal_growth_rate: Perpetual growth rate (%)
        """
        # Validate inputs
        wacc_decimal = Decimal(wacc) / Decimal("100")
        terminal_growth_decimal = Decimal(terminal_growth_rate) / Decimal("100")
        fcf_growth_decimal = Decimal(fcf_growth_rate) / Decimal("100")

        if wacc_decimal <= terminal_growth_decimal:
            return Decimal("0")  # Invalid WACC/growth combination

        # Project FCF to terminal year
        fcf_terminal = Decimal(fcf_current) * (Decimal("1") + fcf_growth_decimal)

        # Calculate terminal value
        tv = (fcf_terminal * (Decimal("1") + terminal_growth_decimal)) / (
            wacc_decimal - terminal_growth_decimal
        )

        return tv

    def calculate_intrinsic_value(
        self,
        fcf_projections: List[Decimal],  # Years 1-5
        terminal_fcf: Decimal,
        wacc: Decimal,
        shares_outstanding: Decimal,
        terminal_growth_rate: Decimal = Decimal("3")
    ) -> Decimal:
        """
        Calculate intrinsic value per share using FCF discounting.

        Process:
        1. Discount FCF projections to present value
        2. Calculate terminal value (Gordon growth)
        3. Sum PV of projections + PV of terminal value
        4. Divide by shares outstanding
        """
        wacc_decimal = Decimal(wacc) / Decimal("100")
        terminal_growth_decimal = Decimal(terminal_growth_rate) / Decimal("100")

        # Calculate terminal value
        tv = (terminal_fcf * (Decimal("1") + terminal_growth_decimal)) / (
            wacc_decimal - terminal_growth_decimal
        )

        # Discount FCF projections
        pv_fcf = Decimal("0")
        for year, fcf in enumerate(fcf_projections, 1):
            discount_factor = (Decimal("1") + wacc_decimal) ** year
            pv_fcf += fcf / discount_factor

        # Discount terminal value (at end of projection period)
        discount_factor_tv = (Decimal("1") + wacc_decimal) ** len(fcf_projections)
        pv_tv = tv / discount_factor_tv

        # Total enterprise value
        enterprise_value = pv_fcf + pv_tv

        # Equity value per share
        intrinsic_value_per_share = enterprise_value / Decimal(shares_outstanding)

        return intrinsic_value_per_share

    def generate_valuation_range(
        self,
        base_case_fcf: Decimal,
        base_case_wacc: Decimal,
        shares_outstanding: Decimal,
        growth_rate: Decimal,
        sensitivity_wacc_range: Tuple[Decimal, Decimal],
        sensitivity_growth_range: Tuple[Decimal, Decimal]
    ) -> Dict:
        """
        Generate valuation range using sensitivity analysis.

        Varies WACC and terminal growth rate to show range.
        """
        wacc_low, wacc_high = sensitivity_wacc_range
        growth_low, growth_high = sensitivity_growth_range

        values = []

        for wacc in [wacc_low, base_case_wacc, wacc_high]:
            for terminal_growth in [growth_low, growth_high]:
                if wacc <= terminal_growth:
                    continue

                tv = self.calculate_terminal_value_gordon_growth(
                    base_case_fcf,
                    float(growth_rate),
                    float(wacc),
                    float(terminal_growth)
                )

                value_per_share = tv / Decimal(shares_outstanding)
                values.append(float(value_per_share))

        if not values:
            return {"error": "Invalid WACC/growth assumptions"}

        return {
            "low": min(values),
            "high": max(values),
            "midpoint": sum(values) / len(values),
            "base_case": float(
                self.calculate_terminal_value_gordon_growth(
                    base_case_fcf,
                    float(growth_rate),
                    float(base_case_wacc),
                    Decimal("3")
                ) / Decimal(shares_outstanding)
            ),
        }


class QualityTrendAnalyzer:
    """Analyze how quality metrics change over time."""

    def __init__(self, session: Session):
        self.session = session

    def calculate_roe_trend(
        self,
        security_id: int,
        years: int = 5
    ) -> Dict:
        """
        Calculate ROE trend over time.

        Shows whether profitability is improving or deteriorating.
        """
        cutoff_date = date.today() - timedelta(days=365 * years)

        # Query financial metrics for ROE
        metrics = self.session.query(FinancialMetric).filter(
            FinancialMetric.security_id == security_id,
            FinancialMetric.metric_code == "ROE"
        ).filter(
            FinancialMetric.calculated_at >= cutoff_date
        ).order_by(FinancialMetric.calculated_at).all()

        if not metrics:
            return {"error": "No ROE data available"}

        values = [float(m.value) for m in metrics]
        trend = "stable"

        if len(values) >= 2:
            # Simple trend: compare first vs last
            if values[-1] > values[0] * 1.1:
                trend = "improving"
            elif values[-1] < values[0] * 0.9:
                trend = "deteriorating"

        return {
            "trend": trend,
            "values": values,
            "latest": values[-1] if values else None,
            "highest": max(values) if values else None,
            "lowest": min(values) if values else None,
            "average": sum(values) / len(values) if values else None,
        }

    def calculate_margin_trend(
        self,
        security_id: int,
        metric_code: str = "NET_PROFIT_MARGIN",
        years: int = 5
    ) -> Dict:
        """Calculate trend for margin metrics (NPM, OPM, etc)."""
        cutoff_date = date.today() - timedelta(days=365 * years)

        metrics = self.session.query(FinancialMetric).filter(
            FinancialMetric.security_id == security_id,
            FinancialMetric.metric_code == metric_code
        ).filter(
            FinancialMetric.calculated_at >= cutoff_date
        ).order_by(FinancialMetric.calculated_at).all()

        if not metrics:
            return {"error": f"No {metric_code} data available"}

        values = [float(m.value) for m in metrics]
        trend = "stable"

        if len(values) >= 2:
            if values[-1] > values[0] * 1.05:
                trend = "improving"
            elif values[-1] < values[0] * 0.95:
                trend = "deteriorating"

        return {
            "metric": metric_code,
            "trend": trend,
            "values": values,
            "latest": values[-1] if values else None,
            "highest": max(values) if values else None,
            "lowest": min(values) if values else None,
            "average": sum(values) / len(values) if values else None,
        }

    def generate_quality_trend_report(
        self,
        security_id: int
    ) -> Dict:
        """Generate comprehensive quality trend report."""
        return {
            "security_id": security_id,
            "analysis_date": date.today().isoformat(),
            "roe_trend": self.calculate_roe_trend(security_id),
            "npm_trend": self.calculate_margin_trend(security_id, "NET_PROFIT_MARGIN"),
            "opm_trend": self.calculate_margin_trend(security_id, "OPERATING_MARGIN"),
        }
