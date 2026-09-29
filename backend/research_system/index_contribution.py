"""
Index Contribution Engine - Sprint M7

Analyze how individual securities contribute to index movement.
Identify which stocks drive index performance and momentum.

Features:
- Index contribution calculation (weight × return)
- Top contributors identification (positive and negative)
- Contribution ranking over periods
- Key driver identification
- Sector contribution analysis
- Cumulative contribution tracking
- Momentum driver analysis
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta


class IndexContributionEngine:
    """Analyze security contributions to index movement."""

    # ════════════════════════════════════════════════════════════════════════════
    # CONTRIBUTION CALCULATION
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def calculate_security_contribution(
        security_return: float,
        security_weight: float,
    ) -> float:
        """
        Calculate a security's contribution to index.

        Contribution = Security Return % × Security Weight %

        Args:
            security_return: Security's return percentage
            security_weight: Security's weight in index (as %)

        Returns:
            Contribution in basis points
        """
        return security_return * security_weight / 100

    @staticmethod
    def calculate_index_contributions(
        securities_returns: Dict[str, float],
        securities_weights: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Calculate all securities' contributions to index.

        Args:
            securities_returns: Dict of {security_id: return_pct}
            securities_weights: Dict of {security_id: weight_%}

        Returns:
            Dict of {security_id: contribution_bps}
        """
        contributions = {}

        for sec_id, ret in securities_returns.items():
            weight = securities_weights.get(sec_id, 0)
            contribution = IndexContributionEngine.calculate_security_contribution(ret, weight)
            contributions[sec_id] = contribution

        return contributions

    # ════════════════════════════════════════════════════════════════════════════
    # TOP CONTRIBUTORS IDENTIFICATION
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def identify_positive_contributors(
        contributions: Dict[str, float],
        limit: int = 10,
    ) -> List[Dict]:
        """
        Identify top positive contributors to index.

        Args:
            contributions: Dict of {security_id: contribution_bps}
            limit: Number of contributors to return

        Returns:
            List of positive contributors ranked by contribution
        """
        positive = [
            {
                "security_id": sec_id,
                "contribution_bps": round(contrib, 2),
                "contribution_pct": round(contrib / 100, 4),
                "rank": 0,
            }
            for sec_id, contrib in contributions.items()
            if contrib > 0
        ]

        # Sort by contribution (highest first)
        positive.sort(key=lambda x: x["contribution_bps"], reverse=True)

        # Add ranking
        for i, contributor in enumerate(positive[:limit]):
            contributor["rank"] = i + 1

        return positive[:limit]

    @staticmethod
    def identify_negative_contributors(
        contributions: Dict[str, float],
        limit: int = 10,
    ) -> List[Dict]:
        """
        Identify top negative contributors (drags on index).

        Args:
            contributions: Dict of {security_id: contribution_bps}
            limit: Number of contributors to return

        Returns:
            List of negative contributors ranked by drag
        """
        negative = [
            {
                "security_id": sec_id,
                "contribution_bps": round(contrib, 2),
                "contribution_pct": round(contrib / 100, 4),
                "rank": 0,
            }
            for sec_id, contrib in contributions.items()
            if contrib < 0
        ]

        # Sort by contribution (most negative first = biggest drag)
        negative.sort(key=lambda x: x["contribution_bps"])

        # Add ranking
        for i, contributor in enumerate(negative[:limit]):
            contributor["rank"] = i + 1

        return negative[:limit]

    # ════════════════════════════════════════════════════════════════════════════
    # CONTRIBUTION ANALYSIS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_contribution_breakdown(
        contributions: Dict[str, float],
    ) -> Dict:
        """
        Get breakdown of contributions (positive vs negative).

        Args:
            contributions: Dict of {security_id: contribution_bps}

        Returns:
            Breakdown statistics
        """
        if not contributions:
            return {"error": "No data"}

        positive_contribs = [c for c in contributions.values() if c > 0]
        negative_contribs = [c for c in contributions.values() if c < 0]
        neutral = [c for c in contributions.values() if c == 0]

        total_positive = sum(positive_contribs)
        total_negative = sum(negative_contribs)
        total_contribution = sum(contributions.values())

        return {
            "total_contribution_bps": round(total_contribution, 2),
            "total_contribution_pct": round(total_contribution / 100, 4),
            "positive_contributors": len(positive_contribs),
            "negative_contributors": len(negative_contribs),
            "neutral_securities": len(neutral),
            "total_positive_contribution_bps": round(total_positive, 2),
            "total_negative_contribution_bps": round(total_negative, 2),
            "avg_positive_contribution": round(total_positive / len(positive_contribs), 2) if positive_contribs else 0,
            "avg_negative_contribution": round(total_negative / len(negative_contribs), 2) if negative_contribs else 0,
            "top_positive_rank": positive_contribs[0] if positive_contribs else 0,
            "top_negative_rank": negative_contribs[0] if negative_contribs else 0,
        }

    @staticmethod
    def get_concentration_analysis(
        contributions: Dict[str, float],
    ) -> Dict:
        """
        Analyze concentration of index contribution.

        Shows if index move driven by few stocks (concentrated)
        or many stocks (broad-based).

        Args:
            contributions: Dict of {security_id: contribution_bps}

        Returns:
            Concentration metrics
        """
        if not contributions:
            return {"error": "No data"}

        sorted_contribs = sorted(
            contributions.values(),
            key=abs,
            reverse=True
        )

        total_contribution = sum(abs(c) for c in contributions.values())

        if total_contribution == 0:
            return {
                "concentration": "NO_MOVEMENT",
                "top_5_pct_of_total": 0,
                "top_10_pct_of_total": 0,
            }

        # Calculate what % of total contribution comes from top 5 and top 10
        top_5_contribution = sum(abs(c) for c in sorted_contribs[:5])
        top_10_contribution = sum(abs(c) for c in sorted_contribs[:10])

        top_5_pct = (top_5_contribution / total_contribution * 100) if total_contribution else 0
        top_10_pct = (top_10_contribution / total_contribution * 100) if total_contribution else 0

        # Classify concentration
        if top_5_pct > 70:
            concentration = "HIGHLY_CONCENTRATED"
        elif top_5_pct > 50:
            concentration = "CONCENTRATED"
        elif top_10_pct > 60:
            concentration = "MODERATE"
        else:
            concentration = "BROAD_BASED"

        return {
            "concentration": concentration,
            "top_5_pct_of_total": round(top_5_pct, 1),
            "top_10_pct_of_total": round(top_10_pct, 1),
            "interpretation": f"Index move is {concentration.lower()} - "
                            f"top 5 stocks account for {round(top_5_pct, 1)}% of movement",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # SECTOR CONTRIBUTION ANALYSIS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def analyze_sector_contributions(
        contributions: Dict[str, float],
        security_to_sector: Dict[str, str],
    ) -> Dict[str, Dict]:
        """
        Analyze contributions by sector.

        Args:
            contributions: Dict of {security_id: contribution_bps}
            security_to_sector: Dict mapping security_id to sector_name

        Returns:
            Dict with sector contribution analysis
        """
        sector_contributions = {}

        for sec_id, contrib in contributions.items():
            sector = security_to_sector.get(sec_id, "Unknown")

            if sector not in sector_contributions:
                sector_contributions[sector] = {
                    "total_contribution_bps": 0,
                    "securities": 0,
                    "positive_contributors": 0,
                    "negative_contributors": 0,
                }

            sector_contributions[sector]["total_contribution_bps"] += contrib
            sector_contributions[sector]["securities"] += 1

            if contrib > 0:
                sector_contributions[sector]["positive_contributors"] += 1
            elif contrib < 0:
                sector_contributions[sector]["negative_contributors"] += 1

        # Format and rank
        result = {}
        for sector, data in sector_contributions.items():
            result[sector] = {
                "total_contribution_bps": round(data["total_contribution_bps"], 2),
                "total_contribution_pct": round(data["total_contribution_bps"] / 100, 4),
                "securities_count": data["securities"],
                "positive_contributors": data["positive_contributors"],
                "negative_contributors": data["negative_contributors"],
                "avg_contribution_bps": round(
                    data["total_contribution_bps"] / data["securities"], 2
                ) if data["securities"] > 0 else 0,
            }

        # Sort by total contribution
        sorted_result = dict(sorted(
            result.items(),
            key=lambda x: abs(x[1]["total_contribution_bps"]),
            reverse=True
        ))

        return sorted_result

    # ════════════════════════════════════════════════════════════════════════════
    # MOMENTUM DRIVER ANALYSIS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def identify_momentum_drivers(
        contributions: Dict[str, float],
        securities_weights: Dict[str, float],
    ) -> List[Dict]:
        """
        Identify key momentum drivers.

        These are high-weight securities that significantly moved.

        Args:
            contributions: Dict of {security_id: contribution_bps}
            securities_weights: Dict of {security_id: weight_%}

        Returns:
            List of momentum drivers ranked by impact
        """
        drivers = []

        for sec_id, contrib in contributions.items():
            weight = securities_weights.get(sec_id, 0)

            if abs(contrib) > 0.05:  # Meaningful contribution (at least 5 bps)
                drivers.append({
                    "security_id": sec_id,
                    "weight_pct": round(weight, 2),
                    "contribution_bps": round(contrib, 2),
                    "contribution_pct": round(contrib / 100, 4),
                    "impact_level": "HIGH" if abs(contrib) > 20 else "MEDIUM" if abs(contrib) > 10 else "NOTABLE",
                    "direction": "UP" if contrib > 0 else "DOWN",
                })

        # Sort by absolute contribution
        drivers.sort(key=lambda x: abs(x["contribution_bps"]), reverse=True)

        return drivers

    @staticmethod
    def get_contribution_trend(
        daily_contributions_list: List[Dict[str, float]],
        security_id: str,
    ) -> Dict:
        """
        Analyze contribution trend for a security over time.

        Args:
            daily_contributions_list: List of daily contribution dicts
            security_id: Security to analyze

        Returns:
            Trend analysis
        """
        if not daily_contributions_list:
            return {"error": "No data"}

        contributions = [
            d.get(security_id, 0) for d in daily_contributions_list
        ]

        if not contributions:
            return {"error": "Security not found"}

        avg_contribution = sum(contributions) / len(contributions)
        total_contribution = sum(contributions)
        max_contrib = max(contributions)
        min_contrib = min(contributions)

        # Trend direction
        if len(contributions) > 1:
            recent_avg = sum(contributions[-3:]) / 3 if len(contributions) >= 3 else contributions[-1]
            older_avg = sum(contributions[:3]) / 3 if len(contributions) >= 3 else contributions[0]
            trend = "IMPROVING" if recent_avg > older_avg else "DETERIORATING" if recent_avg < older_avg else "STABLE"
        else:
            trend = "INSUFFICIENT_DATA"

        return {
            "security_id": security_id,
            "days_tracked": len(contributions),
            "total_contribution_bps": round(total_contribution, 2),
            "avg_contribution_bps": round(avg_contribution, 2),
            "max_contribution_bps": round(max_contrib, 2),
            "min_contribution_bps": round(min_contrib, 2),
            "contribution_volatility": round(
                (max(contributions) - min(contributions)) / 2, 2
            ) if contributions else 0,
            "trend": trend,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # CONTRIBUTION REPORTS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_index_contribution_report(
        securities_returns: Dict[str, float],
        securities_weights: Dict[str, float],
        securities_to_sector: Optional[Dict[str, str]] = None,
        limit: int = 10,
    ) -> Dict:
        """
        Generate comprehensive index contribution report.

        Args:
            securities_returns: Dict of {security_id: return_pct}
            securities_weights: Dict of {security_id: weight_%}
            securities_to_sector: Optional sector mapping
            limit: Number of top contributors to show

        Returns:
            Comprehensive contribution report
        """
        engine = IndexContributionEngine()

        contributions = engine.calculate_index_contributions(
            securities_returns, securities_weights
        )

        return {
            "date": date.today().isoformat(),
            "total_index_contribution_bps": round(sum(contributions.values()), 2),
            "top_positive_contributors": engine.identify_positive_contributors(
                contributions, limit
            ),
            "top_negative_contributors": engine.identify_negative_contributors(
                contributions, limit
            ),
            "contribution_breakdown": engine.get_contribution_breakdown(contributions),
            "concentration_analysis": engine.get_concentration_analysis(contributions),
            "momentum_drivers": engine.identify_momentum_drivers(
                contributions, securities_weights
            ),
            "sector_contributions": engine.analyze_sector_contributions(
                contributions, securities_to_sector or {}
            ) if securities_to_sector else None,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # CONTRIBUTION COMPARISON
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def compare_contribution_periods(
        period1_contributions: Dict[str, float],
        period2_contributions: Dict[str, float],
    ) -> Dict:
        """
        Compare contributions between two periods.

        Shows which securities are becoming more/less important to index.

        Args:
            period1_contributions: Dict from earlier period
            period2_contributions: Dict from later period

        Returns:
            Comparison analysis
        """
        comparison = []

        # Get all securities from both periods
        all_securities = set(period1_contributions.keys()) | set(period2_contributions.keys())

        for sec_id in all_securities:
            p1_contrib = period1_contributions.get(sec_id, 0)
            p2_contrib = period2_contributions.get(sec_id, 0)
            change = p2_contrib - p1_contrib

            comparison.append({
                "security_id": sec_id,
                "period1_contribution_bps": round(p1_contrib, 2),
                "period2_contribution_bps": round(p2_contrib, 2),
                "change_bps": round(change, 2),
                "change_pct": round((change / abs(p1_contrib) * 100), 2) if p1_contrib != 0 else float('inf'),
                "trend": "INCREASED" if change > 0 else "DECREASED" if change < 0 else "UNCHANGED",
            })

        # Sort by absolute change
        comparison.sort(key=lambda x: abs(x["change_bps"]), reverse=True)

        return {
            "securities_analyzed": len(comparison),
            "top_changes": comparison[:10],
            "summary": {
                "increased_count": len([c for c in comparison if c["trend"] == "INCREASED"]),
                "decreased_count": len([c for c in comparison if c["trend"] == "DECREASED"]),
            },
        }
