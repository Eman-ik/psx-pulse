"""
Market Terminal UI - Sprint M9

Unified dashboard orchestrating all market intelligence engines.
Provides comprehensive market, sector, and macro analysis in one integrated view.

Integrates:
- M1-M2: Market foundation & snapshots
- M3: Breadth analysis & regimes
- M4: Sector performance
- M5: Relative strength
- M6: Market movers
- M7: Index contributions
- M8: Macro variables
"""

from typing import Dict, List, Optional
from datetime import date


class MarketTerminalUI:
    """Unified market intelligence terminal."""

    # ════════════════════════════════════════════════════════════════════════════
    # TERMINAL SECTIONS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_market_overview_section(
        index_code: str,
        index_level: float,
        daily_return: float,
        breadth_pct: float,
        market_health: str,
        regime: str,
    ) -> Dict:
        """
        Create market overview section for terminal.

        Shows top-level market status.
        """
        return {
            "section": "MARKET OVERVIEW",
            "index_code": index_code,
            "index_level": round(index_level, 2),
            "daily_return_pct": round(daily_return, 2),
            "market_status": {
                "breadth_pct": round(breadth_pct, 1),
                "health_score": market_health,
                "regime": regime,
                "signal": "HEALTHY" if breadth_pct > 55 and market_health == "GOOD" else "CAUTION" if breadth_pct < 45 else "NEUTRAL",
            },
        }

    @staticmethod
    def create_breadth_analysis_section(
        breadth_metrics: Dict,
        regime_info: Dict,
        divergence: Optional[Dict] = None,
    ) -> Dict:
        """
        Create breadth analysis section.

        Shows market breadth, regime, and divergences.
        """
        return {
            "section": "MARKET BREADTH ANALYSIS",
            "breadth": {
                "percent_above_50dma": breadth_metrics.get("pct_above_50dma"),
                "strength_rating": breadth_metrics.get("strength_rating"),
                "trend": breadth_metrics.get("trend"),
            },
            "regime": {
                "classification": regime_info.get("classification"),
                "confidence": regime_info.get("confidence"),
                "interpretation": regime_info.get("interpretation"),
            },
            "price_breadth_divergence": divergence or {"status": "aligned"},
        }

    @staticmethod
    def create_sector_performance_section(
        top_gainers: List[Dict],
        top_losers: List[Dict],
        sector_contributions: Dict,
    ) -> Dict:
        """
        Create sector performance section.

        Shows top performing and lagging sectors.
        """
        return {
            "section": "SECTOR PERFORMANCE",
            "top_gainers": top_gainers[:5],
            "top_losers": top_losers[:5],
            "sector_contributions": {
                sector: {
                    "contribution_pct": data.get("total_contribution_pct"),
                    "securities_count": data.get("securities_count"),
                }
                for sector, data in list(sector_contributions.items())[:5]
            },
        }

    @staticmethod
    def create_market_movers_section(
        top_gainers: List[Dict],
        top_losers: List[Dict],
        volume_leaders: List[Dict],
        unusual_alerts: List[Dict],
    ) -> Dict:
        """
        Create market movers section.

        Shows top gainers, losers, and volume leaders.
        """
        return {
            "section": "MARKET MOVERS",
            "top_gainers": top_gainers[:10],
            "top_losers": top_losers[:10],
            "volume_leaders": volume_leaders[:10],
            "unusual_activity": {
                "alerts_count": len(unusual_alerts),
                "top_alerts": unusual_alerts[:5],
            },
        }

    @staticmethod
    def create_relative_strength_section(
        ranked_securities: List[Dict],
        distribution_quality: str,
        outperformer_pct: float,
    ) -> Dict:
        """
        Create relative strength section.

        Shows outperformers and underperformers vs market.
        """
        outperformers = [s for s in ranked_securities if s.get("outperforming")]
        underperformers = [s for s in ranked_securities if not s.get("outperforming")]

        return {
            "section": "RELATIVE STRENGTH",
            "distribution": {
                "quality": distribution_quality,
                "outperformer_pct": round(outperformer_pct, 1),
                "outperformers_count": len(outperformers),
                "underperformers_count": len(underperformers),
            },
            "top_outperformers": outperformers[:5],
            "top_underperformers": underperformers[:5],
        }

    @staticmethod
    def create_contribution_analysis_section(
        top_positive_contributors: List[Dict],
        top_negative_contributors: List[Dict],
        concentration: str,
    ) -> Dict:
        """
        Create index contribution section.

        Shows which securities drove index movement.
        """
        return {
            "section": "INDEX CONTRIBUTION ANALYSIS",
            "concentration": concentration,
            "key_drivers": {
                "positive": top_positive_contributors[:5],
                "negative": top_negative_contributors[:5],
            },
            "interpretation": "Index driven by large-cap concentrated moves" if concentration in ["HIGHLY_CONCENTRATED", "CONCENTRATED"] else "Broad-based participation across securities",
        }

    @staticmethod
    def create_macro_section(
        macro_trends: Dict[str, Dict],
        macro_drivers: List[Dict],
        macro_regime: str,
        sector_macro_impacts: Dict,
    ) -> Dict:
        """
        Create macro analysis section.

        Shows economic variables and sector sensitivity.
        """
        return {
            "section": "MACRO ENVIRONMENT",
            "economic_regime": macro_regime,
            "key_variables": {
                var: {
                    "latest": trend.get("latest_value"),
                    "trend": trend.get("trend"),
                }
                for var, trend in list(macro_trends.items())[:5]
            },
            "macro_drivers": macro_drivers[:5],
            "sector_sensitivity": {
                sector: {
                    "expected_impact": impact.get("expected_sector_impact"),
                    "direction": impact.get("impact_direction"),
                }
                for sector, impact in list(sector_macro_impacts.items())[:5]
            },
        }

    # ════════════════════════════════════════════════════════════════════════════
    # TERMINAL DASHBOARD
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def build_market_terminal_dashboard(
        market_overview: Dict,
        breadth_analysis: Dict,
        sector_performance: Dict,
        market_movers: Dict,
        relative_strength: Dict,
        contribution_analysis: Dict,
        macro_section: Dict,
    ) -> Dict:
        """
        Build complete market terminal dashboard.

        Orchestrates all analysis sections.
        """
        return {
            "terminal_name": "KHRONOS RESEARCH TERMINAL",
            "timestamp": date.today().isoformat(),
            "dashboard_sections": [
                market_overview,
                breadth_analysis,
                sector_performance,
                market_movers,
                relative_strength,
                contribution_analysis,
                macro_section,
            ],
            "quick_stats": {
                "market_status": market_overview.get("market_status", {}).get("signal"),
                "breadth_health": breadth_analysis.get("breadth", {}).get("strength_rating"),
                "top_sector": sector_performance.get("top_gainers", [{}])[0].get("sector_name") if sector_performance.get("top_gainers") else None,
                "total_movers": len(market_movers.get("unusual_activity", {}).get("top_alerts", [])),
                "macro_regime": macro_section.get("economic_regime"),
            },
        }

    # ════════════════════════════════════════════════════════════════════════════
    # TERMINAL VIEWS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_executive_summary(dashboard: Dict) -> Dict:
        """
        Get executive summary view of terminal.

        High-level one-page summary.
        """
        return {
            "view": "EXECUTIVE_SUMMARY",
            "timestamp": dashboard.get("timestamp"),
            "market_overview": {
                "status": dashboard.get("quick_stats", {}).get("market_status"),
                "breadth": dashboard.get("quick_stats", {}).get("breadth_health"),
            },
            "key_themes": [
                {
                    "theme": "Market Structure",
                    "insight": f"Breadth: {dashboard.get('quick_stats', {}).get('breadth_health')}",
                },
                {
                    "theme": "Sector Leadership",
                    "insight": f"Top sector: {dashboard.get('quick_stats', {}).get('top_sector')}",
                },
                {
                    "theme": "Economic Environment",
                    "insight": f"Regime: {dashboard.get('quick_stats', {}).get('macro_regime')}",
                },
            ],
        }

    @staticmethod
    def get_technical_view(dashboard: Dict) -> Dict:
        """
        Get technical analysis view.

        Focused on price action, breadth, and momentum.
        """
        sections = dashboard.get("dashboard_sections", [])

        return {
            "view": "TECHNICAL_VIEW",
            "timestamp": dashboard.get("timestamp"),
            "price_structure": next(
                (s for s in sections if s.get("section") == "MARKET OVERVIEW"), {}
            ),
            "breadth_analysis": next(
                (s for s in sections if s.get("section") == "MARKET BREADTH ANALYSIS"), {}
            ),
            "momentum": next(
                (s for s in sections if s.get("section") == "RELATIVE STRENGTH"), {}
            ),
        }

    @staticmethod
    def get_fundamental_view(dashboard: Dict) -> Dict:
        """
        Get fundamental/valuation view.

        Focused on sector relative value and macro impact.
        """
        sections = dashboard.get("dashboard_sections", [])

        return {
            "view": "FUNDAMENTAL_VIEW",
            "timestamp": dashboard.get("timestamp"),
            "sector_performance": next(
                (s for s in sections if s.get("section") == "SECTOR PERFORMANCE"), {}
            ),
            "contribution_analysis": next(
                (s for s in sections if s.get("section") == "INDEX CONTRIBUTION ANALYSIS"), {}
            ),
            "macro_environment": next(
                (s for s in sections if s.get("section") == "MACRO ENVIRONMENT"), {}
            ),
        }

    @staticmethod
    def get_trading_view(dashboard: Dict) -> Dict:
        """
        Get trading/opportunity view.

        Focused on movers, divergences, and alerts.
        """
        sections = dashboard.get("dashboard_sections", [])

        return {
            "view": "TRADING_VIEW",
            "timestamp": dashboard.get("timestamp"),
            "market_movers": next(
                (s for s in sections if s.get("section") == "MARKET MOVERS"), {}
            ),
            "relative_strength": next(
                (s for s in sections if s.get("section") == "RELATIVE STRENGTH"), {}
            ),
            "breadth_divergence": next(
                (s for s in sections if s.get("section") == "MARKET BREADTH ANALYSIS"), {}
            ).get("price_breadth_divergence", {}),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ALERTS AND SIGNALS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def generate_terminal_alerts(dashboard: Dict) -> List[Dict]:
        """
        Generate actionable alerts from dashboard.

        Identifies key signal levels and anomalies.
        """
        alerts = []
        sections = dashboard.get("dashboard_sections", [])

        # Market structure alert
        market_section = next(
            (s for s in sections if s.get("section") == "MARKET OVERVIEW"), {}
        )
        if market_section.get("market_status", {}).get("signal") == "HEALTHY":
            alerts.append({
                "severity": "INFO",
                "alert_type": "MARKET_STRUCTURE",
                "message": "Market breadth and health are aligned - healthy rally conditions",
            })

        # Sector rotation alert
        sector_section = next(
            (s for s in sections if s.get("section") == "SECTOR PERFORMANCE"), {}
        )
        if sector_section.get("top_gainers"):
            alerts.append({
                "severity": "INFO",
                "alert_type": "SECTOR_ROTATION",
                "message": f"Sector rotation detected: {sector_section.get('top_gainers', [{}])[0].get('sector_name')} leading",
            })

        # Divergence alert
        breadth_section = next(
            (s for s in sections if s.get("section") == "MARKET BREADTH ANALYSIS"), {}
        )
        divergence = breadth_section.get("price_breadth_divergence", {})
        if divergence.get("divergence"):
            alerts.append({
                "severity": "WARNING",
                "alert_type": "DIVERGENCE",
                "message": f"{divergence.get('divergence')} divergence detected between price and breadth",
            })

        # Unusual activity alert
        movers_section = next(
            (s for s in sections if s.get("section") == "MARKET MOVERS"), {}
        )
        unusual_count = movers_section.get("unusual_activity", {}).get("alerts_count", 0)
        if unusual_count > 5:
            alerts.append({
                "severity": "NOTICE",
                "alert_type": "UNUSUAL_ACTIVITY",
                "message": f"{unusual_count} securities showing unusual volume/price activity",
            })

        return alerts

    @staticmethod
    def get_terminal_recommendations(dashboard: Dict) -> Dict:
        """
        Generate terminal recommendations based on dashboard analysis.

        Synthesizes insights across all modules.
        """
        sections = dashboard.get("dashboard_sections", [])
        alerts = MarketTerminalUI.generate_terminal_alerts(dashboard)

        market_section = next(
            (s for s in sections if s.get("section") == "MARKET OVERVIEW"), {}
        )
        breadth_section = next(
            (s for s in sections if s.get("section") == "MARKET BREADTH ANALYSIS"), {}
        )
        macro_section = next(
            (s for s in sections if s.get("section") == "MACRO ENVIRONMENT"), {}
        )

        recommendation = "NEUTRAL"
        if market_section.get("market_status", {}).get("signal") == "HEALTHY" and breadth_section.get("breadth", {}).get("strength_rating") in ["VERY_STRONG", "STRONG"]:
            recommendation = "BULLISH"
        elif market_section.get("market_status", {}).get("signal") == "CAUTION" or breadth_section.get("breadth", {}).get("trend") == "DETERIORATING":
            recommendation = "BEARISH"

        return {
            "overall_recommendation": recommendation,
            "confidence_level": "HIGH" if len([a for a in alerts if a.get("severity") == "WARNING"]) == 0 else "MEDIUM" if len([a for a in alerts if a.get("severity") == "WARNING"]) < 3 else "LOW",
            "key_drivers": [
                f"Market regime: {breadth_section.get('regime', {}).get('classification')}",
                f"Macro environment: {macro_section.get('economic_regime')}",
            ],
            "risk_factors": [a.get("message") for a in alerts if a.get("severity") in ["WARNING", "CAUTION"]],
            "opportunities": [a.get("message") for a in alerts if a.get("severity") == "INFO"],
        }
