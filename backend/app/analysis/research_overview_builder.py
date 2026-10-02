"""Research Overview Builder — transforms detailed analysis into concise presentation.

Takes the full ResearchOrchestrator output and creates a 30-second summary.
Both Overview and Intelligence tabs use the same underlying analysis — this just formats it.
"""

from typing import Dict


class ResearchOverviewBuilder:
    """Summarizes detailed intelligence analysis into concise Overview format."""

    @staticmethod
    def build(analysis: Dict) -> Dict:
        """Transform detailed research analysis into 30-second overview.

        Args:
            analysis: Output from ResearchOrchestrator.analyze()

        Returns:
            {
                "business_health": "Improving|Stable|Weakening",
                "business_health_confidence": "High|Medium|Low",
                "earnings_quality": "High|Strong|Moderate|Provisional",
                "earnings_quality_confidence": "High|Medium|Low",
                "valuation": "Overvalued|Fair|Undervalued|Unavailable",
                "valuation_confidence": "High|Medium|Low",
                "technical_condition": "Positive|Neutral|Negative",
                "risk_level": "High|Medium|Low",
                "what_changed": "description of latest changes",
                "bull_thesis": "one line bull case",
                "bear_thesis": "one line bear case",
                "key_debate": "critical disagreement point",
                "watch_metrics": ["metric1", "metric2"],
                "data_availability": 0-100,
            }
        """
        business_health = analysis.get("business_health", {})
        earnings_quality = analysis.get("earnings_quality", {})
        valuation = analysis.get("valuation_context", {})
        red_flags = analysis.get("red_flags", {})
        bull_bear = analysis.get("bull_bear_case", {})
        what_watch = analysis.get("what_to_watch", {})
        what_changed = analysis.get("what_changed", {})
        risks = analysis.get("risk_engine", {})

        # Map confidence strings to display levels
        def confidence_level(conf_str):
            if conf_str == "High":
                return "High"
            elif conf_str == "Medium":
                return "Medium"
            else:
                return "Low"

        return {
            # Business metrics (30-second snapshot)
            "business_health": business_health.get("assessment", "Unknown"),
            "business_health_confidence": confidence_level(business_health.get("confidence", "Low")),
            "earnings_quality": earnings_quality.get("assessment", "Provisional"),
            "earnings_quality_confidence": confidence_level(earnings_quality.get("confidence", "Low")),
            "valuation": valuation.get("assessment", "Unavailable"),
            "valuation_confidence": confidence_level(valuation.get("confidence", "Low")),

            # Technical/risk summary
            "risk_level": "High" if risks.get("summary", {}).get("high", 0) > 2 else "Medium" if risks.get("summary", {}).get("medium", 0) > 0 else "Low",

            # Narrative summaries
            "what_changed": what_changed.get("interpretation", ""),
            "bull_thesis": bull_bear.get("bull_case", {}).get("thesis", ""),
            "bear_thesis": bull_bear.get("bear_case", {}).get("thesis", ""),
            "key_debate": bull_bear.get("critical_debate", ""),

            # Red flags
            "red_flags": red_flags.get("flags", [])[:3],  # Top 3 flags only for overview

            # Actionable watch list
            "watch_metrics": [m.get("metric") for m in what_watch.get("watch_metrics", [])][:5],

            # Data quality
            "data_availability": int(analysis.get("confidence_score", 0)),
        }

    @staticmethod
    def to_company_overview_format(symbol: str, analysis: Dict, company_price: Dict = None) -> Dict:
        """Format as /api/v1/companies/{ticker}/overview response.

        Args:
            symbol: Stock ticker
            analysis: ResearchOrchestrator output
            company_price: Current price data (optional)

        Returns:
            {
                "company": {...},
                "price": {...},
                "research_overview": {...},
                "latest_events": [],
            }
        """
        overview = ResearchOverviewBuilder.build(analysis)

        return {
            "company": {
                "symbol": symbol,
                "issuer_id": analysis.get("issuer_id"),
            },
            "price": company_price or {},
            "research_overview": overview,
            "latest_events": analysis.get("catalyst_engine", {}).get("catalysts", [])[:5],
        }
