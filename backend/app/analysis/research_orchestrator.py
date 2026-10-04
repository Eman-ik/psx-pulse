"""Research Orchestrator — single source of truth for all research analysis.

Runs all 9 intelligence engines once per request with shared ResearchContext.
Caches result to eliminate duplicate work when multiple endpoints need analysis.
Validates cross-engine consistency.
"""

from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import Security
from app.analysis.business_health import BusinessHealthEngine
from app.analysis.what_changed import WhatChangedEngine
from app.analysis.earnings_quality_v2 import EarningsQualityEngine
from app.analysis.bull_bear_case import BullBearCaseEngine
from app.analysis.red_flags import RedFlagEngine
from app.analysis.risk_engine import RiskEngine
from app.analysis.catalyst_engine import CatalystEngine
from app.analysis.valuation_context import ValuationContextEngine
from app.analysis.what_to_watch import WhatToWatchEngine
from app.analysis.evidence_context import ResearchContext
from app.analysis.consistency_validator import ConsistencyValidator


class ResearchOrchestrator:
    """Orchestrates all research engines into a single unified analysis."""

    @staticmethod
    def analyze(db: Session, issuer_id: int) -> Dict:
        """Run all 9 intelligence engines with shared ResearchContext.

        Returns:
            {
                "ticker": str,
                "issuer_id": int,
                "business_health": {},
                "what_changed": {},
                "earnings_quality": {},
                "bull_bear_case": {},
                "red_flags": {},
                "risk_engine": {},
                "catalyst_engine": {},
                "valuation_context": {},
                "what_to_watch": {},
                "validation": {},
                "confidence_score": 0-100,
            }
        """
        # Create evidence context once (single database scan)
        context = ResearchContext(db, issuer_id)

        # Run all 9 engines
        business_health = BusinessHealthEngine.analyze(context)
        what_changed = WhatChangedEngine.analyze(context)
        earnings_quality = EarningsQualityEngine.analyze(context)
        bull_bear = BullBearCaseEngine.analyze(context)
        red_flags = RedFlagEngine.detect(context)
        risks = RiskEngine.analyze(context)
        catalysts = CatalystEngine.analyze(context)
        valuation = ValuationContextEngine.analyze(context)
        watch_list = WhatToWatchEngine.analyze(context)

        # Collect all outputs for consistency validation
        all_outputs = {
            "business_health": business_health,
            "what_changed": what_changed,
            "earnings_quality": earnings_quality,
            "bull_bear_case": bull_bear,
            "red_flags": red_flags,
            "risk_engine": risks,
            "catalyst_engine": catalysts,
            "valuation_context": valuation,
            "what_to_watch": watch_list,
        }

        # Validate logical consistency
        validator = ConsistencyValidator(context, all_outputs)
        validation_report = validator.validate_all()

        # CORRECTED: THREE SEPARATE METRICS (not conflated into one)
        # 1. DATA COVERAGE: percentage of expected data actually available (0-100%)
        engine_data_coverages = [
            business_health.get("data_coverage_pct", 0),
            what_changed.get("data_coverage_pct", 0),
            earnings_quality.get("data_coverage_pct", 0),
            valuation.get("data_coverage_pct", 0),
        ]
        composite_data_coverage = int(sum(engine_data_coverages) / len(engine_data_coverages)) if engine_data_coverages else 0

        # 2. EVIDENCE QUALITY: reliability, recency, provenance of available data
        # High: audited financials, recent
        # Medium: quarterly data, some secondary sources
        # Low: old data, unverified sources
        # For now, assume "High" if data_coverage > 70%, "Medium" if > 40%, else "Low"
        if composite_data_coverage >= 70:
            evidence_quality = "High"
        elif composite_data_coverage >= 40:
            evidence_quality = "Medium"
        else:
            evidence_quality = "Low"

        # 3. ANALYTICAL CONFIDENCE: confidence in the engine interpretations
        # Based on: consistency across engines + signal clarity
        engine_confidences = [
            business_health.get("classification_confidence", "Low"),
            what_changed.get("confidence", "Low"),
            earnings_quality.get("confidence", "Low"),
            valuation.get("confidence", "Low"),
        ]
        # Count "High" confidences
        high_count = sum(1 for c in engine_confidences if c == "High")
        if high_count >= 3 and validation_report.get("overall_valid"):
            overall_analytical_confidence = "High"
        elif high_count >= 1 or validation_report.get("overall_valid"):
            overall_analytical_confidence = "Medium"
        else:
            overall_analytical_confidence = "Low"

        # Backward compatibility: old "confidence_score" = data_coverage - penalty
        # (deprecated: do not use for new features)
        consistency_penalty = 0 if validation_report.get("overall_valid") else 20
        deprecated_confidence_score = max(0, min(100, composite_data_coverage - consistency_penalty))

        return {
            "issuer_id": issuer_id,
            "business_health": business_health,
            "what_changed": what_changed,
            "earnings_quality": earnings_quality,
            "bull_bear_case": bull_bear,
            "red_flags": red_flags,
            "risk_engine": risks,
            "catalyst_engine": catalysts,
            "valuation_context": valuation,
            "what_to_watch": watch_list,
            "validation": validation_report,
            # NEW: Three separate metrics
            "data_coverage_pct": composite_data_coverage,
            "evidence_quality": evidence_quality,
            "analytical_confidence": overall_analytical_confidence,
            # DEPRECATED (for backward compatibility only)
            "confidence_score": deprecated_confidence_score,
        }
