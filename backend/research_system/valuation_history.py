"""
Historical Valuation Analysis

Sprint V2: Historical valuation snapshots, trends, and percentile analysis.

Features:
- Historical valuation bands (1Y, 3Y, 5Y medians)
- Percentile rankings (25th, 75th)
- Trend analysis (increasing/decreasing multiples)
- Valuation score based on historical context
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from .schema import ValuationSnapshot, Security


class ValuationHistoryAnalyzer:
    """Analyze historical valuation patterns and trends."""

    def __init__(self, session: Session):
        self.session = session

    def get_valuation_series(
        self,
        security_id: int,
        metric: str,
        days: int = 365
    ) -> List[Tuple[date, Optional[Decimal]]]:
        """
        Get time series of valuation metric.

        Returns: [(date, value), ...]
        """
        cutoff_date = date.today() - timedelta(days=days)

        snapshots = self.session.query(ValuationSnapshot).filter(
            ValuationSnapshot.security_id == security_id,
            ValuationSnapshot.snapshot_date >= cutoff_date
        ).order_by(ValuationSnapshot.snapshot_date).all()

        return [
            (s.snapshot_date, getattr(s, metric, None))
            for s in snapshots
        ]

    def calculate_percentiles(
        self,
        security_id: int,
        metric: str,
        days: int = 365
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate percentiles for valuation metric.
        Returns: {p0 (min), p25, p50 (median), p75, p100 (max), count}
        """
        series = self.get_valuation_series(security_id, metric, days)

        values = [v for _, v in series if v is not None]

        if not values:
            return {
                "min": None,
                "p25": None,
                "median": None,
                "p75": None,
                "max": None,
                "count": 0,
                "current": None,
            }

        values_sorted = sorted([float(v) for v in values])
        count = len(values_sorted)

        # Get current value (most recent)
        current = Decimal(str(values_sorted[-1])) if values_sorted else None

        # Calculate indices for percentiles
        p25_idx = max(0, (count - 1) * 25 // 100)
        p50_idx = (count - 1) * 50 // 100
        p75_idx = min(count - 1, (count - 1) * 75 // 100)

        return {
            "min": Decimal(str(values_sorted[0])),
            "p25": Decimal(str(values_sorted[p25_idx])),
            "median": Decimal(str(values_sorted[p50_idx])),
            "p75": Decimal(str(values_sorted[p75_idx])),
            "max": Decimal(str(values_sorted[-1])),
            "current": current,
            "count": count,
        }

    def get_multi_period_analysis(
        self,
        security_id: int,
        metric: str
    ) -> Dict[str, Dict]:
        """
        Get valuation metric across multiple time periods.

        Returns analysis for 1Y, 3Y, 5Y, and all-time.
        """
        return {
            "ytd": self.calculate_percentiles(security_id, metric, days=365),
            "3y": self.calculate_percentiles(security_id, metric, days=365*3),
            "5y": self.calculate_percentiles(security_id, metric, days=365*5),
            "all_time": self.calculate_percentiles(security_id, metric, days=365*10),
        }

    def calculate_trend(
        self,
        security_id: int,
        metric: str,
        days: int = 365
    ) -> Dict[str, float]:
        """
        Calculate valuation trend (is multiple expanding or contracting?).

        Returns: {
            direction: "increasing" | "decreasing" | "stable",
            change_pct: percentage change over period,
            recent_vs_historic: current vs period median,
            slope: rate of change
        }
        """
        series = self.get_valuation_series(security_id, metric, days)

        if len(series) < 2:
            return {
                "direction": "unknown",
                "change_pct": 0.0,
                "recent_vs_historic": 0.0,
                "slope": 0.0,
                "data_points": len(series),
            }

        values = [float(v) for _, v in series if v is not None]

        if len(values) < 2:
            return {
                "direction": "unknown",
                "change_pct": 0.0,
                "recent_vs_historic": 0.0,
                "slope": 0.0,
                "data_points": len(values),
            }

        first_value = values[0]
        last_value = values[-1]
        median_value = sorted(values)[len(values) // 2]

        # Calculate change
        change_pct = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0

        # Determine direction
        if abs(change_pct) < 2:
            direction = "stable"
        elif change_pct > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        # Recent vs historic
        recent_vs_historic = ((last_value - median_value) / median_value * 100) if median_value != 0 else 0

        # Calculate slope (simple linear regression)
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))

        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum) if (n * x2_sum - x_sum * x_sum) != 0 else 0

        return {
            "direction": direction,
            "change_pct": round(change_pct, 2),
            "recent_vs_historic": round(recent_vs_historic, 2),
            "slope": round(slope, 4),
            "data_points": len(values),
        }

    def get_valuation_percentile_rank(
        self,
        security_id: int,
        metric: str,
        current_value: Decimal,
        days: int = 365
    ) -> int:
        """
        Calculate percentile rank of current valuation within historical range.

        Returns: 0-100 (0 = lowest, 100 = highest in period)
        """
        percentiles = self.calculate_percentiles(security_id, metric, days)

        min_val = percentiles.get("min")
        max_val = percentiles.get("max")

        if not min_val or not max_val or min_val == max_val:
            return 50  # Default to median

        range_val = max_val - min_val
        position = current_value - min_val

        if range_val == 0:
            return 50

        percentile = int((position / range_val) * 100)
        return max(0, min(100, percentile))

    def generate_valuation_band_data(
        self,
        security_id: int,
        metric: str = "pe_ratio",
        days: int = 365
    ) -> Dict:
        """
        Generate data for valuation bands visualization.

        Returns data suitable for charting valuation bands over time.
        """
        series = self.get_valuation_series(security_id, metric, days)
        percentiles = self.calculate_percentiles(security_id, metric, days)

        # Prepare time series with bands
        timeline_data = []
        for snap_date, value in series:
            timeline_data.append({
                "date": snap_date.isoformat(),
                "value": float(value) if value else None,
            })

        return {
            "ticker_id": security_id,
            "metric": metric,
            "period_days": days,
            "timeline": timeline_data,
            "bands": {
                "min": float(percentiles["min"]) if percentiles["min"] else None,
                "p25": float(percentiles["p25"]) if percentiles["p25"] else None,
                "median": float(percentiles["median"]) if percentiles["median"] else None,
                "p75": float(percentiles["p75"]) if percentiles["p75"] else None,
                "max": float(percentiles["max"]) if percentiles["max"] else None,
            },
            "current": float(percentiles["current"]) if percentiles["current"] else None,
            "data_points": percentiles["count"],
        }

    def get_comprehensive_historical_report(
        self,
        security_id: int
    ) -> Dict:
        """
        Generate comprehensive historical valuation report.

        Includes: P/E, P/B, EV/EBITDA trends and percentiles.
        """
        metrics_to_analyze = ["pe_ratio", "pb_ratio", "ev_ebitda_ratio"]

        report = {
            "security_id": security_id,
            "analysis_date": date.today().isoformat(),
            "metrics": {},
        }

        for metric in metrics_to_analyze:
            report["metrics"][metric] = {
                "periods": self.get_multi_period_analysis(security_id, metric),
                "trend": self.calculate_trend(security_id, metric, days=365),
                "band_data": self.generate_valuation_band_data(security_id, metric),
            }

        return report


class ValuationComparator:
    """Compare valuation across peers and sector."""

    def __init__(self, session: Session):
        self.session = session
        self.analyzer = ValuationHistoryAnalyzer(session)

    def compare_to_peers(
        self,
        ticker: str,
        peer_tickers: List[str],
        metric: str = "pe_ratio"
    ) -> Dict:
        """
        Compare one company's valuation metric to peers.

        Returns: relative positioning and percentile within peer group.
        """
        # Get security ID for ticker
        security = self.session.query(Security).filter(
            Security.ticker == ticker
        ).first()

        if not security:
            return {"error": f"Company {ticker} not found"}

        # Get latest valuation for this company
        latest = self.session.query(ValuationSnapshot).filter(
            ValuationSnapshot.security_id == security.security_id
        ).order_by(desc(ValuationSnapshot.snapshot_date)).first()

        if not latest:
            return {"error": f"No valuation data for {ticker}"}

        current_value = getattr(latest, metric, None)

        if not current_value:
            return {"error": f"No {metric} data for {ticker}"}

        # Get peer values
        peer_values = {}
        for peer_ticker in peer_tickers:
            peer_security = self.session.query(Security).filter(
                Security.ticker == peer_ticker
            ).first()

            if not peer_security:
                continue

            peer_latest = self.session.query(ValuationSnapshot).filter(
                ValuationSnapshot.security_id == peer_security.security_id
            ).order_by(desc(ValuationSnapshot.snapshot_date)).first()

            if peer_latest:
                peer_value = getattr(peer_latest, metric, None)
                if peer_value:
                    peer_values[peer_ticker] = float(peer_value)

        # Calculate statistics
        all_values = [current_value] + [Decimal(str(v)) for v in peer_values.values()]
        all_values_sorted = sorted([float(v) for v in all_values])

        rank = all_values_sorted.index(float(current_value)) + 1
        percentile = int((rank / len(all_values_sorted)) * 100)

        return {
            "ticker": ticker,
            "metric": metric,
            "current_value": float(current_value),
            "peer_count": len(peer_values),
            "rank": rank,
            "out_of": len(all_values_sorted),
            "percentile": percentile,
            "peer_values": peer_values,
            "peer_median": float(Decimal(str(all_values_sorted[len(all_values_sorted) // 2]))),
            "peer_min": float(Decimal(str(all_values_sorted[0]))),
            "peer_max": float(Decimal(str(all_values_sorted[-1]))),
            "vs_median": round(
                ((float(current_value) - all_values_sorted[len(all_values_sorted) // 2]) /
                 all_values_sorted[len(all_values_sorted) // 2] * 100) if all_values_sorted[len(all_values_sorted) // 2] != 0 else 0,
                2
            ),
        }

    def compare_to_sector_median(
        self,
        ticker: str,
        sector_id: int,
        metric: str = "pe_ratio"
    ) -> Dict:
        """
        Compare company valuation to sector median.
        """
        # Get company value
        security = self.session.query(Security).filter(
            Security.ticker == ticker
        ).first()

        if not security:
            return {"error": f"Company {ticker} not found"}

        latest = self.session.query(ValuationSnapshot).filter(
            ValuationSnapshot.security_id == security.security_id
        ).order_by(desc(ValuationSnapshot.snapshot_date)).first()

        if not latest:
            return {"error": f"No valuation data for {ticker}"}

        company_value = getattr(latest, metric, None)

        if not company_value:
            return {"error": f"No {metric} data for {ticker}"}

        # Get sector values
        sector_securities = self.session.query(Security).filter(
            Security.sector_id == sector_id
        ).all()

        sector_values = []
        for sec in sector_securities:
            sec_latest = self.session.query(ValuationSnapshot).filter(
                ValuationSnapshot.security_id == sec.security_id
            ).order_by(desc(ValuationSnapshot.snapshot_date)).first()

            if sec_latest:
                val = getattr(sec_latest, metric, None)
                if val:
                    sector_values.append((sec.ticker, float(val)))

        if not sector_values:
            return {"error": "No sector valuation data"}

        sector_values_only = [v for _, v in sector_values]
        sector_median = Decimal(str(sorted(sector_values_only)[len(sector_values_only) // 2]))

        # Calculate percentile within sector
        sector_sorted = sorted(sector_values_only)
        company_percentile = int(
            (len([v for v in sector_sorted if v <= float(company_value)]) / len(sector_sorted)) * 100
        )

        return {
            "ticker": ticker,
            "metric": metric,
            "company_value": float(company_value),
            "sector_median": float(sector_median),
            "sector_count": len(sector_values),
            "percentile": company_percentile,
            "vs_median_pct": round(
                ((float(company_value) - float(sector_median)) / float(sector_median) * 100)
                if sector_median != 0 else 0,
                2
            ),
            "sector_min": float(Decimal(str(min(sector_values_only)))),
            "sector_max": float(Decimal(str(max(sector_values_only)))),
            "direction": "above" if float(company_value) > float(sector_median) else "below",
        }
