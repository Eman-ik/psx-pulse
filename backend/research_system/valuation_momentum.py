"""
Valuation Momentum & Relative Value Index

Sprint V5: Track how valuation attractiveness is changing, and measure valuation
relative to peers and sector.

Features:
- Historical valuation momentum (is valuation improving/deteriorating?)
- Relative value index (1-100 score vs peers/sector)
- Momentum driver analysis (fundamentals vs speculation)
- Peer and sector comparison
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, stdev
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .schema import Security, ValuationSnapshot, FinancialMetric


class RelativeValueIndex:
    """Composite index measuring valuation attractiveness vs peers and sector."""

    def __init__(self, session: Session):
        self.session = session

    def calculate_relative_value_index(
        self,
        ticker: str,
        peer_tickers: List[str],
        weights: Optional[Dict[str, float]] = None,
        analysis_date: Optional[datetime] = None,
    ) -> float:
        """
        Calculate relative value index score (1-100 scale).

        Score measures how attractive this stock's valuation is relative to peers.
        50 = peer median
        > 50 = more attractive (better valued)
        < 50 = less attractive (more expensive)

        Args:
            ticker: Company ticker
            peer_tickers: List of peer company tickers
            weights: Valuation metric weights (default: equal weight)
            analysis_date: Date for valuation snapshot (default: today)

        Returns:
            Relative value index score (1-100)

        Example:
            >>> rvi.calculate_relative_value_index(
            ...     "FFC",
            ...     peer_tickers=["EFERT", "FATIMA", "LUCK"],
            ...     weights={
            ...         "dividend_yield": 0.25,
            ...         "fcf_yield": 0.25,
            ...         "pe_discount": 0.20,
            ...         "pb_discount": 0.15,
            ...         "ev_ebitda_discount": 0.15
            ...     }
            ... )
            75.2
        """
        if weights is None:
            weights = {
                "dividend_yield": 0.25,
                "fcf_yield": 0.25,
                "pe_discount": 0.20,
                "pb_discount": 0.15,
                "ev_ebitda_discount": 0.15,
            }

        if analysis_date is None:
            analysis_date = datetime.now()

        # Get all securities
        all_tickers = [ticker] + peer_tickers
        all_securities = (
            self.session.query(Security).filter(Security.ticker.in_(all_tickers)).all()
        )
        security_map = {s.ticker: s for s in all_securities}

        if ticker not in security_map:
            raise ValueError(f"Security not found: {ticker}")

        # Get latest valuation snapshot for each
        valuations = {}
        for t in all_tickers:
            if t not in security_map:
                continue

            sec = security_map[t]
            snapshot = (
                self.session.query(ValuationSnapshot)
                .filter(
                    ValuationSnapshot.security_id == sec.security_id,
                    ValuationSnapshot.snapshot_date <= analysis_date,
                )
                .order_by(desc(ValuationSnapshot.snapshot_date))
                .first()
            )

            if snapshot:
                valuations[t] = {
                    "dividend_yield": float(snapshot.dividend_yield or 0),
                    "fcf_yield": float(snapshot.fcf_yield or 0),
                    "pe_ratio": float(snapshot.pe_ratio or 0),
                    "pb_ratio": float(snapshot.pb_ratio or 0),
                    "ev_ebitda": float(snapshot.ev_ebitda or 0),
                }

        if not valuations:
            raise ValueError("No valuation data available")

        # Calculate peer medians
        div_yields = [v["dividend_yield"] for v in valuations.values() if v["dividend_yield"] > 0]
        fcf_yields = [v["fcf_yield"] for v in valuations.values() if v["fcf_yield"] > 0]
        pe_ratios = [v["pe_ratio"] for v in valuations.values() if v["pe_ratio"] > 0]
        pb_ratios = [v["pb_ratio"] for v in valuations.values() if v["pb_ratio"] > 0]
        ev_ebitdas = [v["ev_ebitda"] for v in valuations.values() if v["ev_ebitda"] > 0]

        peer_medians = {
            "dividend_yield": self._median(div_yields) if div_yields else 0,
            "fcf_yield": self._median(fcf_yields) if fcf_yields else 0,
            "pe_ratio": self._median(pe_ratios) if pe_ratios else 0,
            "pb_ratio": self._median(pb_ratios) if pb_ratios else 0,
            "ev_ebitda": self._median(ev_ebitdas) if ev_ebitdas else 0,
        }

        # Calculate percentile scores for target company
        target_vals = valuations.get(ticker, {})
        score_components = {}

        # Dividend yield: higher is better
        if target_vals.get("dividend_yield", 0) > 0 and peer_medians["dividend_yield"] > 0:
            div_percentile = self._calculate_percentile(
                target_vals["dividend_yield"],
                div_yields if div_yields else [peer_medians["dividend_yield"]],
            )
            score_components["dividend_yield"] = div_percentile * weights["dividend_yield"]
        else:
            score_components["dividend_yield"] = 50 * weights["dividend_yield"]

        # FCF yield: higher is better
        if target_vals.get("fcf_yield", 0) > 0 and peer_medians["fcf_yield"] > 0:
            fcf_percentile = self._calculate_percentile(
                target_vals["fcf_yield"],
                fcf_yields if fcf_yields else [peer_medians["fcf_yield"]],
            )
            score_components["fcf_yield"] = fcf_percentile * weights["fcf_yield"]
        else:
            score_components["fcf_yield"] = 50 * weights["fcf_yield"]

        # P/E discount: lower is better (higher percentile when lower)
        if target_vals.get("pe_ratio", 0) > 0 and peer_medians["pe_ratio"] > 0:
            pe_percentile = 100 - self._calculate_percentile(
                target_vals["pe_ratio"],
                pe_ratios if pe_ratios else [peer_medians["pe_ratio"]],
            )
            score_components["pe_discount"] = pe_percentile * weights["pe_discount"]
        else:
            score_components["pe_discount"] = 50 * weights["pe_discount"]

        # P/B discount: lower is better
        if target_vals.get("pb_ratio", 0) > 0 and peer_medians["pb_ratio"] > 0:
            pb_percentile = 100 - self._calculate_percentile(
                target_vals["pb_ratio"],
                pb_ratios if pb_ratios else [peer_medians["pb_ratio"]],
            )
            score_components["pb_discount"] = pb_percentile * weights["pb_discount"]
        else:
            score_components["pb_discount"] = 50 * weights["pb_discount"]

        # EV/EBITDA discount: lower is better
        if target_vals.get("ev_ebitda", 0) > 0 and peer_medians["ev_ebitda"] > 0:
            ev_percentile = 100 - self._calculate_percentile(
                target_vals["ev_ebitda"],
                ev_ebitdas if ev_ebitdas else [peer_medians["ev_ebitda"]],
            )
            score_components["ev_ebitda_discount"] = ev_percentile * weights["ev_ebitda_discount"]
        else:
            score_components["ev_ebitda_discount"] = 50 * weights["ev_ebitda_discount"]

        total_score = sum(score_components.values())
        return round(min(100, max(1, total_score)), 1)

    def get_peer_and_sector_comparison(
        self,
        ticker: str,
        peer_tickers: List[str],
        sector_name: Optional[str] = None,
    ) -> Dict:
        """
        Compare valuation position vs peers and sector.

        Args:
            ticker: Company ticker
            peer_tickers: List of peer tickers
            sector_name: Sector name for sector-level comparison

        Returns:
            Comparison analysis with percentiles and ratings
        """
        # Calculate RVI for all (including target)
        all_tickers = [ticker] + peer_tickers
        rvi_scores = {}

        for t in all_tickers:
            try:
                score = self.calculate_relative_value_index(t, [pt for pt in all_tickers if pt != t])
                rvi_scores[t] = score
            except Exception:
                continue

        if ticker not in rvi_scores:
            raise ValueError(f"Could not calculate RVI for {ticker}")

        target_score = rvi_scores[ticker]
        peer_scores = sorted(
            [v for k, v in rvi_scores.items() if k in peer_tickers],
            reverse=True,
        )

        # Percentile among peers
        better_count = sum(1 for s in peer_scores if s >= target_score)
        percentile_vs_peers = (better_count / len(peer_scores) * 100) if peer_scores else 50

        # Rating
        if percentile_vs_peers >= 75:
            rating = "Excellent"
        elif percentile_vs_peers >= 60:
            rating = "Above Average"
        elif percentile_vs_peers >= 40:
            rating = "Average"
        elif percentile_vs_peers >= 25:
            rating = "Below Average"
        else:
            rating = "Poor"

        # Rank among peers
        rank = 1 + sum(1 for s in peer_scores if s > target_score)

        result = {
            "ticker": ticker,
            "relative_value_index": target_score,
            "vs_peers": {
                "percentile": round(percentile_vs_peers, 1),
                "rank": rank,
                "total_peers": len(peer_scores),
                "rating": rating,
                "peer_scores": {t: rvi_scores[t] for t in peer_tickers if t in rvi_scores},
            },
        }

        # Sector comparison if requested
        if sector_name:
            try:
                sector_companies = (
                    self.session.query(Security)
                    .filter(
                        Security.sector.name == sector_name,
                        Security.listing_status == "ACTIVE",
                    )
                    .all()
                )

                sector_rvi_scores = {}
                for sec in sector_companies:
                    if sec.ticker != ticker:
                        try:
                            score = self.calculate_relative_value_index(
                                sec.ticker,
                                [s.ticker for s in sector_companies if s.ticker != sec.ticker],
                            )
                            sector_rvi_scores[sec.ticker] = score
                        except Exception:
                            continue

                if sector_rvi_scores:
                    sector_better = sum(1 for s in sector_rvi_scores.values() if s >= target_score)
                    sector_percentile = (sector_better / len(sector_rvi_scores) * 100)

                    if sector_percentile >= 75:
                        sector_rating = "Excellent"
                    elif sector_percentile >= 60:
                        sector_rating = "Above Average"
                    elif sector_percentile >= 40:
                        sector_rating = "Average"
                    elif sector_percentile >= 25:
                        sector_rating = "Below Average"
                    else:
                        sector_rating = "Poor"

                    result["vs_sector"] = {
                        "percentile": round(sector_percentile, 1),
                        "rating": sector_rating,
                        "total_companies": len(sector_rvi_scores),
                    }
            except Exception:
                pass

        return result

    @staticmethod
    def _median(values: List[float]) -> float:
        """Calculate median of list."""
        if not values:
            return 0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        if n % 2 == 1:
            return sorted_vals[n // 2]
        else:
            return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

    @staticmethod
    def _calculate_percentile(value: float, all_values: List[float]) -> float:
        """Calculate percentile rank of value within all_values (0-100)."""
        if not all_values:
            return 50
        sorted_vals = sorted(all_values)
        count_less = sum(1 for v in sorted_vals if v < value)
        count_equal = sum(1 for v in sorted_vals if v == value)
        percentile = ((count_less + count_equal * 0.5) / len(sorted_vals)) * 100
        return min(100, max(0, percentile))


class ValuationMomentumAnalyzer:
    """Analyze how valuation attractiveness changes over time."""

    def __init__(self, session: Session):
        self.session = session

    def calculate_valuation_momentum(
        self,
        ticker: str,
        periods: int = 12,
        metric: str = "composite_score",
    ) -> Dict:
        """
        Calculate valuation momentum over historical periods.

        Args:
            ticker: Company ticker
            periods: Number of periods to analyze (typically months)
            metric: Which metric to track
                   - "composite_score": Overall valuation score
                   - "pe_ratio": Price-to-earnings ratio
                   - "dividend_yield": Dividend yield

        Returns:
            Momentum analysis with trend and acceleration
        """
        security = self.session.query(Security).filter_by(ticker=ticker).first()
        if not security:
            raise ValueError(f"Security not found: {ticker}")

        # Get historical snapshots
        cutoff_date = datetime.now() - timedelta(days=365 * (periods // 12 + 1))
        snapshots = (
            self.session.query(ValuationSnapshot)
            .filter(
                ValuationSnapshot.security_id == security.security_id,
                ValuationSnapshot.snapshot_date >= cutoff_date,
            )
            .order_by(ValuationSnapshot.snapshot_date)
            .all()
        )

        if not snapshots:
            raise ValueError("Insufficient historical data")

        # Extract values based on metric
        if metric == "composite_score":
            values = [
                (s.snapshot_date, s.composite_score)
                for s in snapshots
                if s.composite_score is not None
            ]
        elif metric == "pe_ratio":
            values = [(s.snapshot_date, s.pe_ratio) for s in snapshots if s.pe_ratio is not None]
        elif metric == "dividend_yield":
            values = [
                (s.snapshot_date, s.dividend_yield)
                for s in snapshots
                if s.dividend_yield is not None
            ]
        else:
            raise ValueError(f"Unknown metric: {metric}")

        if len(values) < 2:
            raise ValueError(f"Insufficient data points for metric: {metric}")

        # Extract numeric values
        dates = [v[0] for v in values]
        numeric_vals = [float(v[1]) for v in values]

        current = numeric_vals[-1]
        previous = numeric_vals[-2] if len(numeric_vals) > 1 else numeric_vals[0]
        oldest = numeric_vals[0]

        # Calculate momentum
        change = current - previous
        momentum_direction = "improving" if change > 0 else "deteriorating" if change < 0 else "flat"

        # Trend slope (linear regression)
        trend_slope = self._calculate_trend_slope(numeric_vals)

        # Recent acceleration
        if len(numeric_vals) >= 3:
            recent_change = numeric_vals[-1] - numeric_vals[-3]
            earlier_change = numeric_vals[-3] - numeric_vals[-6] if len(numeric_vals) >= 6 else recent_change
            recent_acceleration = recent_change > earlier_change
        else:
            recent_change = change
            recent_acceleration = False

        # Percentile (where current ranks in historical range)
        percentile = (
            sum(1 for v in numeric_vals if v <= current) / len(numeric_vals) * 100
            if numeric_vals
            else 50
        )

        return {
            "ticker": ticker,
            "metric": metric,
            "current_value": round(current, 2),
            "previous_value": round(previous, 2),
            "change": round(change, 2),
            "momentum_direction": momentum_direction,
            "momentum_strength": round(abs(change), 2),
            "trend_slope": round(trend_slope, 4),
            "recent_acceleration": recent_acceleration,
            "historical_range": [round(min(numeric_vals), 2), round(max(numeric_vals), 2)],
            "percentile": round(percentile, 1),
            "period_analysis": periods,
            "data_points": len(numeric_vals),
        }

    def analyze_momentum_drivers(
        self,
        ticker: str,
        periods: int = 12,
    ) -> Dict:
        """
        Determine what's driving valuation momentum (fundamentals vs speculation).

        Args:
            ticker: Company ticker
            periods: Number of periods to analyze

        Returns:
            Analysis of momentum drivers
        """
        security = self.session.query(Security).filter_by(ticker=ticker).first()
        if not security:
            raise ValueError(f"Security not found: {ticker}")

        # Get momentum data
        try:
            valuation_momentum = self.calculate_valuation_momentum(
                ticker, periods, metric="composite_score"
            )
        except Exception as e:
            return {"error": str(e)}

        # Get earnings/FCF growth data
        cutoff_date = datetime.now() - timedelta(days=365 * (periods // 12 + 1))
        metrics = (
            self.session.query(FinancialMetric)
            .filter(
                FinancialMetric.security_id == security.security_id,
                FinancialMetric.recorded_date >= cutoff_date,
            )
            .all()
        )

        # Extract EPS and FCF
        eps_values = [
            (m.recorded_date, m.earnings_per_share)
            for m in metrics
            if m.earnings_per_share is not None
        ]
        fcf_values = [
            (m.recorded_date, m.free_cash_flow)
            for m in metrics
            if m.free_cash_flow is not None
        ]

        # Calculate earnings growth
        eps_numeric = [float(v[1]) for v in eps_values]
        fcf_numeric = [float(v[1]) for v in fcf_values]

        eps_growth = (
            ((eps_numeric[-1] - eps_numeric[0]) / abs(eps_numeric[0]) * 100)
            if eps_numeric and eps_numeric[0] != 0
            else 0
        )
        fcf_growth = (
            ((fcf_numeric[-1] - fcf_numeric[0]) / abs(fcf_numeric[0]) * 100)
            if fcf_numeric and fcf_numeric[0] != 0
            else 0
        )

        # Classify driver
        val_improving = valuation_momentum["momentum_direction"] == "improving"
        earnings_strong = eps_growth > 5
        fcf_strong = fcf_growth > 5

        if val_improving and earnings_strong:
            driver = "fundamentals"
            insight = "Valuation improving alongside earnings growth; fundamentally justified"
            confidence = 0.85
        elif val_improving and not earnings_strong:
            driver = "speculation"
            insight = "Valuation improving despite weak earnings; multiple expansion"
            confidence = 0.70
        elif not val_improving and earnings_strong:
            driver = "mean_reversion"
            insight = "Valuation deteriorating despite earnings growth; mean reversion"
            confidence = 0.75
        else:
            driver = "neutral"
            insight = "Valuation flat alongside flat earnings"
            confidence = 0.50

        return {
            "ticker": ticker,
            "valuation_momentum": valuation_momentum["momentum_direction"],
            "valuation_strength": valuation_momentum["momentum_strength"],
            "earnings_growth": round(eps_growth, 2),
            "fcf_growth": round(fcf_growth, 2),
            "momentum_driver": driver,
            "confidence": confidence,
            "insights": insight,
        }

    @staticmethod
    def _calculate_trend_slope(values: List[float]) -> float:
        """Calculate linear trend slope using simple linear regression."""
        if len(values) < 2:
            return 0

        n = len(values)
        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = sum(values) / n

        numerator = sum((x_vals[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0

        return numerator / denominator
