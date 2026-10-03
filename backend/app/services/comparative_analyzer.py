"""Step 17: Comparative Analyzer — Compare metrics across multiple companies.

Multi-company financial comparison:
- Side-by-side growth metrics
- Peer-relative valuation (percentile ranking vs peers)
- Sector benchmarking
- Relative strength ranking (best to worst per metric)

Input: List of companies + list of metrics to compare
Output: ComparisonResult (side-by-side metrics with percentile ranks)
"""

import logging
import statistics
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class MetricCategory(str, Enum):
    """Metric categories for comparison."""

    GROWTH = "Growth"
    VALUATION = "Valuation"
    PROFITABILITY = "Profitability"
    EFFICIENCY = "Efficiency"
    LEVERAGE = "Leverage"
    TECHNICAL = "Technical"


@dataclass
class ComparisonMetric:
    """Single metric compared across companies."""

    metric_name: str
    category: MetricCategory
    company_values: Dict[str, Optional[float]] = field(default_factory=dict)  # ticker -> value
    peer_median: Optional[float] = None
    peer_mean: Optional[float] = None
    peer_stdev: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "category": self.category.value,
            "peer_median": round(self.peer_median, 2) if self.peer_median else None,
            "peer_mean": round(self.peer_mean, 2) if self.peer_mean else None,
            "company_count": len([v for v in self.company_values.values() if v is not None]),
        }


@dataclass
class CompanyRanking:
    """Ranking of a company for a specific metric."""

    ticker: str
    rank: int  # 1 = best, N = worst
    value: Optional[float]
    percentile: float  # 0-100%, where 100 = best


@dataclass
class ComparisonResult:
    """Complete comparison across multiple companies."""

    tickers_compared: List[str]
    metrics: List[ComparisonMetric]
    rankings: Dict[str, List[CompanyRanking]]  # metric_name -> [rankings]

    # Summary stats
    company_scores: Dict[str, float]  # ticker -> overall score (0-100)
    leader: str  # Best overall performer
    laggard: str  # Worst overall performer

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tickers_compared": self.tickers_compared,
            "company_count": len(self.tickers_compared),
            "metrics_count": len(self.metrics),
            "leader": self.leader,
            "laggard": self.laggard,
            "metrics": [m.to_dict() for m in self.metrics],
            "company_scores": {t: round(s, 1) for t, s in self.company_scores.items()},
        }


class ComparativeAnalyzer:
    """Compares financial metrics across multiple companies."""

    def __init__(self):
        """Initialize analyzer."""
        self.logger = logging.getLogger(__name__)

    def compare(
        self,
        companies: Dict[str, Dict[str, Any]],
        metric_names: Optional[List[str]] = None,
    ) -> Optional[ComparisonResult]:
        """Compare companies across specified metrics.

        Args:
            companies: Dict mapping ticker -> company data (from FinancialContextService)
            metric_names: List of metric names to compare (None = default set)

        Returns:
            ComparisonResult or None on error
        """
        try:
            if not companies or len(companies) < 2:
                self.logger.warning(f"Need at least 2 companies, got {len(companies)}")
                return None

            tickers = list(companies.keys())

            # Use default metrics if not specified
            if not metric_names:
                metric_names = [
                    "revenue_growth_pct",
                    "profit_growth_pct",
                    "pe_ratio",
                    "pb_ratio",
                    "roe_pct",
                    "net_margin_pct",
                    "debt_to_equity",
                ]

            # Build comparison metrics
            comparison_metrics = []
            for metric in metric_names:
                comp_metric = self._build_comparison_metric(
                    metric, companies, tickers
                )
                if comp_metric:
                    comparison_metrics.append(comp_metric)

            # Build rankings
            rankings = {}
            for metric in comparison_metrics:
                rankings[metric.metric_name] = self._rank_companies(
                    metric, tickers
                )

            # Calculate company scores
            company_scores = self._calculate_company_scores(
                rankings, tickers
            )

            # Find leader and laggard
            leader = max(company_scores, key=company_scores.get) if company_scores else tickers[0]
            laggard = min(company_scores, key=company_scores.get) if company_scores else tickers[-1]

            result = ComparisonResult(
                tickers_compared=tickers,
                metrics=comparison_metrics,
                rankings=rankings,
                company_scores=company_scores,
                leader=leader,
                laggard=laggard,
            )

            self.logger.info(
                f"Compared {len(tickers)} companies across {len(comparison_metrics)} metrics. "
                f"Leader: {leader} ({company_scores.get(leader, 0):.0f}%)"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error comparing companies: {e}")
            return None

    @staticmethod
    def _build_comparison_metric(
        metric_name: str,
        companies: Dict[str, Dict[str, Any]],
        tickers: List[str],
    ) -> Optional[ComparisonMetric]:
        """Build a single comparison metric across all companies."""
        company_values = {}
        for ticker in tickers:
            company = companies.get(ticker, {})
            value = company.get(metric_name)
            company_values[ticker] = value

        # Calculate peer statistics
        valid_values = [v for v in company_values.values() if v is not None and isinstance(v, (int, float))]

        if not valid_values:
            return None

        peer_median = statistics.median(valid_values) if len(valid_values) > 0 else None
        peer_mean = statistics.mean(valid_values) if len(valid_values) > 0 else None
        peer_stdev = statistics.stdev(valid_values) if len(valid_values) > 1 else None

        # Determine category
        category = ComparativeAnalyzer._get_metric_category(metric_name)

        return ComparisonMetric(
            metric_name=metric_name,
            category=category,
            company_values=company_values,
            peer_median=peer_median,
            peer_mean=peer_mean,
            peer_stdev=peer_stdev,
        )

    @staticmethod
    def _rank_companies(
        metric: ComparisonMetric,
        tickers: List[str],
    ) -> List[CompanyRanking]:
        """Rank companies for a specific metric."""
        rankings = []

        # Determine if higher or lower is better
        is_inverse = ComparativeAnalyzer._is_inverse_metric(metric.metric_name)

        # Build ranking list with values
        ranking_data = []
        for ticker in tickers:
            value = metric.company_values.get(ticker)
            if value is not None:
                ranking_data.append((ticker, value))

        if not ranking_data:
            return []

        # Sort (inverse = ascending, normal = descending)
        ranking_data.sort(key=lambda x: x[1], reverse=not is_inverse)

        # Assign ranks and calculate percentiles
        total = len(ranking_data)
        for rank, (ticker, value) in enumerate(ranking_data, 1):
            percentile = ((total - rank) / total) * 100  # 100 = best, 0 = worst

            rankings.append(
                CompanyRanking(
                    ticker=ticker,
                    rank=rank,
                    value=value,
                    percentile=percentile,
                )
            )

        return rankings

    @staticmethod
    def _calculate_company_scores(
        rankings: Dict[str, List[CompanyRanking]],
        tickers: List[str],
    ) -> Dict[str, float]:
        """Calculate overall score for each company (0-100%)."""
        company_scores = {ticker: 0.0 for ticker in tickers}

        if not rankings:
            return company_scores

        # Average percentiles across all metrics
        metric_count = len(rankings)
        for ticker in tickers:
            total_percentile = 0.0
            count = 0

            for metric_name, company_rankings in rankings.items():
                for ranking in company_rankings:
                    if ranking.ticker == ticker:
                        total_percentile += ranking.percentile
                        count += 1
                        break

            if count > 0:
                company_scores[ticker] = total_percentile / count
            else:
                company_scores[ticker] = 50.0  # Default if missing data

        return company_scores

    @staticmethod
    def _get_metric_category(metric_name: str) -> MetricCategory:
        """Determine metric category."""
        metric_lower = metric_name.lower()

        if "growth" in metric_lower:
            return MetricCategory.GROWTH
        elif "pe" in metric_lower or "pb" in metric_lower or "multiple" in metric_lower:
            return MetricCategory.VALUATION
        elif "margin" in metric_lower or "roe" in metric_lower or "roa" in metric_lower:
            return MetricCategory.PROFITABILITY
        elif "asset" in metric_lower or "turnover" in metric_lower:
            return MetricCategory.EFFICIENCY
        elif "debt" in metric_lower or "leverage" in metric_lower or "equity" in metric_lower:
            return MetricCategory.LEVERAGE
        elif "trend" in metric_lower or "momentum" in metric_lower:
            return MetricCategory.TECHNICAL
        else:
            return MetricCategory.PROFITABILITY

    @staticmethod
    def _is_inverse_metric(metric_name: str) -> bool:
        """Return True if lower values are better (e.g., P/E, debt)."""
        metric_lower = metric_name.lower()
        return any(
            inv in metric_lower
            for inv in ["pe", "pb", "debt", "leverage", "multiple"]
        )
