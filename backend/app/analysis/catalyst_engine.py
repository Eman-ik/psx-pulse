"""Catalyst Engine — identify things capable of changing the stock thesis.

Categorize: Known+Dated, Known+Undated, Possible, Speculative.
Examples: earnings, dividend, debt reduction, rate cuts, commodity changes, etc.

NOTE: Catalyst data will be integrated from announcement database in Phase 2.
For now, this engine returns a gate indicating data unavailability.
"""

from typing import Dict

from app.analysis.period_alignment import PeriodAlignedAnalyzer
from app.analysis.evidence_context import ResearchContext, ContextualizedOutput


class CatalystEngine:
    """Identify and categorize catalysts that could move the thesis."""

    @staticmethod
    def analyze(context: ResearchContext) -> Dict:
        """Gate: Catalyst data not yet available. Awaiting announcement database integration."""
        output = ContextualizedOutput("catalyst_engine", context)

        output.set_assessment(
            assessment="Unavailable",
            score=0,
            narrative="Catalyst analysis requires integration with the announcement database, which is scheduled for Phase 2.",
            confidence="None",
            data_coverage=0,
        )

        result = output.to_dict()
        result["status"] = "mock_data_gated"
        result["reason"] = "Catalyst data not yet integrated from announcement database"
        result["expected_catalysts"] = [
            "Quarterly earnings announcements",
            "Dividend policy announcements",
            "Capacity expansion commissioning",
            "Rate/policy announcements",
            "Commodity price movements",
        ]
        result["integration_note"] = "Complete integration in Phase 2 (months 3-4)"
        result["validation"] = output.validate()

        return result
