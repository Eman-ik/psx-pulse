"""
Market Movers Engine - Sprint M6

Identify and analyze market movers: top gainers, losers, volume leaders,
and stocks with significant price/volume activity.

Features:
- Top gainers/losers identification (% return based)
- Volume leaders detection (absolute volume)
- Value movers (largest PKR value traded)
- Momentum classification for movers
- Sector distribution of movers
- Price/volume momentum analysis
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from enum import Enum


class MoverCategory(str, Enum):
    """Categories for market movers."""
    STRONG_GAINER = "STRONG_GAINER"       # Top 10% gainers
    GAINER = "GAINER"                     # 10-50% gainers
    LOSER = "LOSER"                       # 50-90% losers
    STRONG_LOSER = "STRONG_LOSER"         # Bottom 10% losers
    HIGH_VOLUME = "HIGH_VOLUME"           # Top 10% by volume
    ACCUMULATION = "ACCUMULATION"        # High volume + price up
    DISTRIBUTION = "DISTRIBUTION"        # High volume + price down


class MarketMoversEngine:
    """Analyze and identify market movers."""

    # ════════════════════════════════════════════════════════════════════════════
    # TOP MOVERS IDENTIFICATION
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def identify_top_gainers(
        securities_returns: Dict[str, float],
        limit: int = 10,
    ) -> List[Dict]:
        """
        Identify top gaining securities.

        Args:
            securities_returns: Dict of {security_id: return_pct}
            limit: Number of top gainers to return

        Returns:
            List of top gainers ranked by return
        """
        gainers = [
            {
                "security_id": sec_id,
                "return_pct": round(ret, 2),
                "rank": 0,
            }
            for sec_id, ret in securities_returns.items()
            if ret > 0
        ]

        # Sort by return (highest first)
        gainers.sort(key=lambda x: x["return_pct"], reverse=True)

        # Add ranking
        for i, gainer in enumerate(gainers[:limit]):
            gainer["rank"] = i + 1

        return gainers[:limit]

    @staticmethod
    def identify_top_losers(
        securities_returns: Dict[str, float],
        limit: int = 10,
    ) -> List[Dict]:
        """
        Identify top losing securities.

        Args:
            securities_returns: Dict of {security_id: return_pct}
            limit: Number of top losers to return

        Returns:
            List of top losers ranked by return (most negative first)
        """
        losers = [
            {
                "security_id": sec_id,
                "return_pct": round(ret, 2),
                "rank": 0,
            }
            for sec_id, ret in securities_returns.items()
            if ret < 0
        ]

        # Sort by return (lowest first = most negative)
        losers.sort(key=lambda x: x["return_pct"])

        # Add ranking
        for i, loser in enumerate(losers[:limit]):
            loser["rank"] = i + 1

        return losers[:limit]

    @staticmethod
    def identify_volume_leaders(
        securities_volume: Dict[str, int],
        limit: int = 10,
    ) -> List[Dict]:
        """
        Identify top volume leaders.

        Args:
            securities_volume: Dict of {security_id: volume_shares}
            limit: Number of volume leaders to return

        Returns:
            List of volume leaders ranked by volume
        """
        leaders = [
            {
                "security_id": sec_id,
                "volume": vol,
                "rank": 0,
            }
            for sec_id, vol in securities_volume.items()
        ]

        # Sort by volume (highest first)
        leaders.sort(key=lambda x: x["volume"], reverse=True)

        # Add ranking
        for i, leader in enumerate(leaders[:limit]):
            leader["rank"] = i + 1

        return leaders[:limit]

    @staticmethod
    def identify_value_movers(
        securities_value: Dict[str, float],
        limit: int = 10,
    ) -> List[Dict]:
        """
        Identify top value movers (PKR value traded).

        Args:
            securities_value: Dict of {security_id: value_pkr}
            limit: Number of value movers to return

        Returns:
            List of value movers ranked by PKR value
        """
        movers = [
            {
                "security_id": sec_id,
                "value_pkr": round(val, 2),
                "rank": 0,
            }
            for sec_id, val in securities_value.items()
        ]

        # Sort by value (highest first)
        movers.sort(key=lambda x: x["value_pkr"], reverse=True)

        # Add ranking
        for i, mover in enumerate(movers[:limit]):
            mover["rank"] = i + 1

        return movers[:limit]

    # ════════════════════════════════════════════════════════════════════════════
    # MOVER ANALYSIS AND CLASSIFICATION
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def classify_movers(
        securities_returns: Dict[str, float],
        securities_volume: Dict[str, int],
    ) -> Dict[str, List[Dict]]:
        """
        Classify securities into mover categories.

        Args:
            securities_returns: Dict of {security_id: return_pct}
            securities_volume: Dict of {security_id: volume_shares}

        Returns:
            Dict grouped by mover category
        """
        if not securities_returns:
            return {}

        movers_by_category = {
            "STRONG_GAINER": [],
            "GAINER": [],
            "LOSER": [],
            "STRONG_LOSER": [],
            "HIGH_VOLUME": [],
            "ACCUMULATION": [],
            "DISTRIBUTION": [],
        }

        # Calculate percentiles for returns and volume
        returns_list = sorted(securities_returns.values())
        volume_list = sorted(securities_volume.values())

        if len(returns_list) > 0:
            p90_return = returns_list[int(len(returns_list) * 0.9)]
            p10_return = returns_list[int(len(returns_list) * 0.1)]
        else:
            p90_return = p10_return = 0

        if len(volume_list) > 0:
            p90_volume = volume_list[int(len(volume_list) * 0.9)]
        else:
            p90_volume = 0

        # Classify each security
        for sec_id, ret in securities_returns.items():
            vol = securities_volume.get(sec_id, 0)
            is_high_volume = vol >= p90_volume

            if ret >= p90_return:
                category = "STRONG_GAINER"
                if is_high_volume:
                    category = "ACCUMULATION"
            elif ret > 0:
                category = "GAINER"
            elif ret <= p10_return:
                category = "STRONG_LOSER"
                if is_high_volume:
                    category = "DISTRIBUTION"
            else:
                category = "LOSER"

            if category == "HIGH_VOLUME" and ret >= 0:
                # Don't double-count accumulation
                if category not in movers_by_category:
                    continue

            movers_by_category[category].append({
                "security_id": sec_id,
                "return_pct": round(ret, 2),
                "volume": vol,
            })

        return movers_by_category

    # ════════════════════════════════════════════════════════════════════════════
    # MOMENTUM AND MOVER PROFILES
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def analyze_mover_momentum(
        return_pct: float,
        volume: int,
        avg_volume: int,
    ) -> Dict:
        """
        Analyze momentum profile of a mover.

        Args:
            return_pct: Return percentage
            volume: Current volume
            avg_volume: Average volume

        Returns:
            Momentum profile
        """
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

        # Classify momentum
        if return_pct > 0 and volume_ratio > 1.5:
            momentum = "STRONG_BUY"
            signal = "Bullish volume breakout"
        elif return_pct > 0 and volume_ratio > 1.0:
            momentum = "BUY"
            signal = "Positive momentum with volume support"
        elif return_pct > 0 and volume_ratio < 1.0:
            momentum = "WEAK_BUY"
            signal = "Price up but low conviction (low volume)"
        elif return_pct < 0 and volume_ratio > 1.5:
            momentum = "STRONG_SELL"
            signal = "Bearish volume breakdown"
        elif return_pct < 0 and volume_ratio > 1.0:
            momentum = "SELL"
            signal = "Negative momentum with volume support"
        elif return_pct < 0 and volume_ratio < 1.0:
            momentum = "WEAK_SELL"
            signal = "Price down but low conviction (low volume)"
        else:
            momentum = "NEUTRAL"
            signal = "Balanced activity"

        return {
            "return_pct": round(return_pct, 2),
            "volume": volume,
            "volume_ratio": round(volume_ratio, 2),
            "momentum": momentum,
            "signal": signal,
            "strength": "STRONG" if abs(volume_ratio - 1.0) > 1.0 else "MODERATE",
        }

    @staticmethod
    def get_mover_statistics(
        securities_returns: Dict[str, float],
        securities_volume: Dict[str, int],
    ) -> Dict:
        """
        Calculate statistics about market movers.

        Args:
            securities_returns: Dict of {security_id: return_pct}
            securities_volume: Dict of {security_id: volume_shares}

        Returns:
            Statistics about mover activity
        """
        if not securities_returns:
            return {"error": "No data"}

        returns = list(securities_returns.values())
        volumes = list(securities_volume.values())

        gainers = [r for r in returns if r > 0]
        losers = [r for r in returns if r < 0]
        unchanged = [r for r in returns if r == 0]

        avg_gainer_return = sum(gainers) / len(gainers) if gainers else 0
        avg_loser_return = sum(losers) / len(losers) if losers else 0
        avg_volume = sum(volumes) / len(volumes) if volumes else 0

        return {
            "total_securities": len(securities_returns),
            "gainers": len(gainers),
            "losers": len(losers),
            "unchanged": len(unchanged),
            "gainer_pct": round(len(gainers) / len(securities_returns) * 100, 1) if securities_returns else 0,
            "loser_pct": round(len(losers) / len(securities_returns) * 100, 1) if securities_returns else 0,
            "avg_gainer_return": round(avg_gainer_return, 2),
            "avg_loser_return": round(avg_loser_return, 2),
            "best_performer_return": round(max(returns), 2) if returns else 0,
            "worst_performer_return": round(min(returns), 2) if returns else 0,
            "avg_volume": int(avg_volume),
            "total_volume": int(sum(volumes)),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # SECTOR ANALYSIS OF MOVERS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def analyze_movers_by_sector(
        securities_to_sector: Dict[str, str],
        securities_returns: Dict[str, float],
    ) -> Dict[str, Dict]:
        """
        Analyze top movers by sector.

        Args:
            securities_to_sector: Dict mapping security_id to sector_name
            securities_returns: Dict of {security_id: return_pct}

        Returns:
            Dict with top mover per sector
        """
        sector_movers = {}

        for sec_id, ret in securities_returns.items():
            sector = securities_to_sector.get(sec_id, "Unknown")

            if sector not in sector_movers:
                sector_movers[sector] = {
                    "security_id": sec_id,
                    "return_pct": ret,
                }
            elif ret > sector_movers[sector]["return_pct"]:
                # Update if this security has higher return
                sector_movers[sector] = {
                    "security_id": sec_id,
                    "return_pct": ret,
                }

        # Format output
        result = {}
        for sector, mover in sector_movers.items():
            result[sector] = {
                "top_mover": mover["security_id"],
                "return_pct": round(mover["return_pct"], 2),
                "direction": "UP" if mover["return_pct"] > 0 else "DOWN" if mover["return_pct"] < 0 else "FLAT",
            }

        return result

    # ════════════════════════════════════════════════════════════════════════════
    # MARKET MOVERS REPORT
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_market_movers_report(
        securities_returns: Dict[str, float],
        securities_volume: Dict[str, int],
        securities_to_sector: Optional[Dict[str, str]] = None,
        limit: int = 10,
    ) -> Dict:
        """
        Generate comprehensive market movers report.

        Args:
            securities_returns: Dict of {security_id: return_pct}
            securities_volume: Dict of {security_id: volume_shares}
            securities_to_sector: Optional sector mapping
            limit: Number of top movers to show

        Returns:
            Comprehensive movers report
        """
        engine = MarketMoversEngine()

        return {
            "date": date.today().isoformat(),
            "top_gainers": engine.identify_top_gainers(securities_returns, limit),
            "top_losers": engine.identify_top_losers(securities_returns, limit),
            "volume_leaders": engine.identify_volume_leaders(securities_volume, limit),
            "mover_categories": engine.classify_movers(securities_returns, securities_volume),
            "statistics": engine.get_mover_statistics(securities_returns, securities_volume),
            "sector_movers": engine.analyze_movers_by_sector(
                securities_to_sector or {}, securities_returns
            ) if securities_to_sector else None,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # MOVER ALERTS AND SIGNALS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_unusual_activity_alerts(
        securities_returns: Dict[str, float],
        securities_volume: Dict[str, int],
        volume_threshold: float = 1.5,
    ) -> List[Dict]:
        """
        Identify unusual trading activity.

        Args:
            securities_returns: Dict of {security_id: return_pct}
            securities_volume: Dict of {security_id: volume_shares}
            volume_threshold: Volume multiplier threshold (default 1.5x average)

        Returns:
            List of unusual activity alerts
        """
        if not securities_volume:
            return []

        avg_volume = sum(securities_volume.values()) / len(securities_volume)
        threshold_volume = avg_volume * volume_threshold

        alerts = []

        for sec_id, vol in securities_volume.items():
            if vol >= threshold_volume:
                ret = securities_returns.get(sec_id, 0)

                alert_type = "VOLUME_SURGE"
                if abs(ret) > 5:
                    alert_type = "VOLATILE_BREAKOUT"
                elif ret > 2:
                    alert_type = "VOLUME_ACCUMULATION"
                elif ret < -2:
                    alert_type = "VOLUME_DISTRIBUTION"

                alerts.append({
                    "security_id": sec_id,
                    "alert_type": alert_type,
                    "return_pct": round(ret, 2),
                    "volume": vol,
                    "volume_ratio": round(vol / avg_volume, 2),
                    "signal_strength": "HIGH" if vol >= threshold_volume * 2 else "MEDIUM",
                })

        # Sort by volume ratio (highest first)
        alerts.sort(key=lambda x: x["volume_ratio"], reverse=True)

        return alerts
