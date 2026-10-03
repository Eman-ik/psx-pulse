"""Step 22: Peer Comparison Engine — Compare against sector peers.

Sector-relative analysis:
- Identify peer group by sector
- Compare key metrics vs peers
- Percentile rankings (1-100%)
- Identify leader and laggard

Input: Company ticker + list of all companies
Output: PeerComparison (relative strength analysis)
"""

import logging
import statistics
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class PeerMetricComparison:
    """Single metric comparison vs peers."""

    metric_name: str
    company_value: Optional[float]
    peer_values: List[Optional[float]] = field(default_factory=list)
    peer_median: Optional[float] = None
    peer_mean: Optional[float] = None
    company_percentile: float = 50.0  # 0-100%, 100 = best


@dataclass
class PeerComparison:
    """Complete peer comparison result."""

    ticker: str
    company_name: str
    sector: str

    peer_tickers: List[str] = field(default_factory=list)
    peer_metrics: List[PeerMetricComparison] = field(default_factory=list)

    leader_ticker: Optional[str] = None  # Best performer
    laggard_ticker: Optional[str] = None  # Worst performer

    overall_percentile: float = 50.0  # 0-100%
    peers_outperformed: int = 0  # Count of peers company beats
    peer_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "sector": self.sector,
            "peer_count": self.peer_count,
            "overall_percentile": round(self.overall_percentile, 1),
            "peers_outperformed": self.peers_outperformed,
            "leader": self.leader_ticker,
            "laggard": self.laggard_ticker,
            "peer_metrics": [
                {
                    "metric": m.metric_name,
                    "company_value": round(m.company_value, 2) if m.company_value else None,
                    "peer_median": round(m.peer_median, 2) if m.peer_median else None,
                    "percentile": round(m.company_percentile, 1),
                }
                for m in self.peer_metrics
            ],
        }


class PeerComparisonEngine:
    """Compares company against sector peers."""

    def __init__(self):
        """Initialize peer comparison engine."""
        self.logger = logging.getLogger(__name__)

    def compare_to_peers(
        self,
        ticker: str,
        company_name: str,
        sector: str,
        company_data: Dict[str, Any],
        all_companies: Dict[str, Dict[str, Any]],  # ticker -> data
        metric_names: Optional[List[str]] = None,
    ) -> Optional[PeerComparison]:
        """Compare company against sector peers.

        Args:
            ticker: Company ticker
            company_name: Company name
            sector: Sector name
            company_data: Company financial data
            all_companies: All companies data
            metric_names: Metrics to compare (None = default)

        Returns:
            PeerComparison with peer analysis
        """
        try:
            # Filter peers by sector
            peers = self._get_peers_by_sector(
                ticker, sector, all_companies
            )

            if len(peers) < 2:
                self.logger.warning(f"Less than 2 peers found for {sector}")
                return None

            # Default metrics
            if not metric_names:
                metric_names = [
                    "revenue_growth_pct",
                    "profit_growth_pct",
                    "roe_pct",
                    "pe_ratio",
                    "pb_ratio",
                    "net_margin_pct",
                ]

            # Build peer metrics
            peer_metrics = []
            outperform_count = 0

            for metric in metric_names:
                comp = self._compare_metric_to_peers(
                    metric, company_data, peers
                )
                if comp:
                    peer_metrics.append(comp)
                    # Count how many peers company beats
                    if comp.company_value and comp.peer_median:
                        is_inverse = self._is_inverse_metric(metric)
                        if is_inverse:
                            # Lower is better
                            if comp.company_value < comp.peer_median:
                                outperform_count += 1
                        else:
                            # Higher is better
                            if comp.company_value > comp.peer_median:
                                outperform_count += 1

            # Calculate overall percentile
            percentiles = [m.company_percentile for m in peer_metrics]
            overall_pct = (
                statistics.mean(percentiles) if percentiles else 50.0
            )

            # Find leader and laggard
            leader, laggard = self._find_leader_laggard(peer_metrics, peers)

            result = PeerComparison(
                ticker=ticker,
                company_name=company_name,
                sector=sector,
                peer_tickers=list(peers.keys()),
                peer_metrics=peer_metrics,
                leader_ticker=leader,
                laggard_ticker=laggard,
                overall_percentile=overall_pct,
                peers_outperformed=outperform_count,
                peer_count=len(peers),
            )

            self.logger.info(
                f"Compared {ticker} to {len(peers)} peers in {sector}: "
                f"percentile {overall_pct:.0f}%, outperforms {outperform_count} peers"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error comparing to peers: {e}")
            return None

    @staticmethod
    def _get_peers_by_sector(
        ticker: str,
        sector: str,
        all_companies: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """Get all peers in same sector (excluding self)."""
        peers = {}
        for t, data in all_companies.items():
            if t != ticker and data.get("sector") == sector:
                peers[t] = data
        return peers

    @staticmethod
    def _compare_metric_to_peers(
        metric_name: str,
        company_data: Dict[str, Any],
        peers: Dict[str, Dict[str, Any]],
    ) -> Optional[PeerMetricComparison]:
        """Compare single metric to peers."""
        company_value = company_data.get(metric_name)

        # Get peer values
        peer_values = [
            p.get(metric_name) for p in peers.values()
        ]
        valid_peer_values = [v for v in peer_values if v is not None]

        if not valid_peer_values:
            return None

        peer_median = statistics.median(valid_peer_values)
        peer_mean = statistics.mean(valid_peer_values)

        # Calculate percentile
        percentile = PeerComparisonEngine._calculate_percentile(
            company_value, valid_peer_values, metric_name
        )

        return PeerMetricComparison(
            metric_name=metric_name,
            company_value=company_value,
            peer_values=valid_peer_values,
            peer_median=peer_median,
            peer_mean=peer_mean,
            company_percentile=percentile,
        )

    @staticmethod
    def _calculate_percentile(
        company_value: Optional[float],
        peer_values: List[float],
        metric_name: str,
    ) -> float:
        """Calculate company percentile vs peers."""
        if company_value is None:
            return 50.0

        is_inverse = PeerComparisonEngine._is_inverse_metric(metric_name)
        all_values = peer_values + [company_value]
        all_values.sort()

        if is_inverse:
            # Lower is better (P/E, debt)
            rank = all_values.index(company_value) + 1
            percentile = ((len(all_values) - rank) / len(all_values)) * 100
        else:
            # Higher is better (growth, ROE)
            rank = all_values.index(company_value) + 1
            percentile = ((rank - 1) / len(all_values)) * 100

        return max(0, min(100, percentile))

    @staticmethod
    def _find_leader_laggard(
        peer_metrics: List[PeerMetricComparison],
        peers: Dict[str, Dict[str, Any]],
    ) -> tuple:
        """Find best and worst performing peers."""
        if not peers or not peer_metrics:
            return None, None

        # Score each peer
        peer_scores = {ticker: 0.0 for ticker in peers.keys()}

        for metric in peer_metrics:
            for i, peer_value in enumerate(metric.peer_values):
                peer_ticker = list(peers.keys())[i]
                if peer_value is not None:
                    pct = PeerComparisonEngine._calculate_percentile(
                        peer_value, metric.peer_values, metric.metric_name
                    )
                    peer_scores[peer_ticker] += pct

        # Average scores
        for ticker in peer_scores:
            peer_scores[ticker] /= len(peer_metrics) if peer_metrics else 1

        leader = max(peer_scores, key=peer_scores.get) if peer_scores else None
        laggard = min(peer_scores, key=peer_scores.get) if peer_scores else None

        return leader, laggard

    @staticmethod
    def _is_inverse_metric(metric_name: str) -> bool:
        """Return True if lower values are better."""
        metric_lower = metric_name.lower()
        return any(
            inv in metric_lower
            for inv in ["pe", "pb", "debt", "leverage"]
        )
