"""Unified Research Intelligence API — brings all intelligence engines together.

Serves a complete institutional-grade research report with:
- Business health diagnosis
- What changed analysis
- Earnings quality assessment
- Bull/bear case
- Red flags
- Risk engine
- Catalysts
- Valuation context
- What to watch
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
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

router = APIRouter(prefix="/api/v1/research", tags=["research"])


@router.get("/{ticker}/analysis")
def unified_research_intelligence(ticker: str, db: Session = Depends(get_db)) -> dict:
    """Complete research intelligence for a stock — the Insight Engine.

    Returns all intelligence engines combined into a comprehensive analysis:
    - Business health diagnosis
    - What's changed since last period
    - Earnings quality assessment
    - Bull/bear case with critical debate
    - Financial red flags
    - Risk assessment
    - Upcoming catalysts
    - Valuation context
    - What to watch
    """
    symbol = ticker.strip().upper()
    security = db.execute(
        select(Security).where(Security.symbol == symbol, Security.is_active.is_(True))
    ).scalar_one_or_none()

    if security is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {symbol}")

    issuer_id = security.issuer_id
    if issuer_id is None:
        raise HTTPException(status_code=404, detail=f"No issuer data for {symbol}")

    try:
        # Create evidence context once per request
        context = ResearchContext(db, issuer_id)

        # Run all intelligence engines with shared ResearchContext (single database scan)
        business_health = BusinessHealthEngine.analyze(context)
        what_changed = WhatChangedEngine.analyze(context)
        earnings_quality = EarningsQualityEngine.analyze(context)
        bull_bear = BullBearCaseEngine.analyze(context)
        red_flags = RedFlagEngine.detect(context)
        risks = RiskEngine.analyze(context)
        catalysts = CatalystEngine.analyze(context)
        valuation = ValuationContextEngine.analyze(context)
        watch_list = WhatToWatchEngine.analyze(context)

        # Build output map for consistency validator
        all_outputs = {
            "business_health": business_health,
            "what_changed": what_changed,
            "earnings_quality": earnings_quality,
            "bull_bear_case": bull_bear,
            "red_flags": red_flags,
            "risk_engine": risks,
            "catalyst_engine": catalysts,
            "valuation_context": valuation,
            "watch_list": watch_list,
        }

        # Validate logical consistency across engines
        validator = ConsistencyValidator(context, all_outputs)
        validation_report = validator.validate_all()

        # Composite confidence score based on actual data coverage + consistency
        # Use weighted average of engine confidences + validation status
        engine_confidences = {
            "business_health": business_health.get("data_coverage_pct", 0),
            "what_changed": what_changed.get("data_coverage_pct", 0),
            "earnings_quality": earnings_quality.get("data_coverage_pct", 0),
            "valuation": valuation.get("data_coverage_pct", 0),
        }
        avg_coverage = int(sum(engine_confidences.values()) / len(engine_confidences))
        # Penalize if validation found contradictions
        consistency_penalty = 0 if validation_report.get("overall_valid") else 20
        confidence_score = max(0, min(100, avg_coverage - consistency_penalty))

        return {
            "ticker": symbol,
            "issuer_id": issuer_id,
            "status": "complete",
            "confidence_score": confidence_score,
            "generated_at": None,  # Add timestamp in production
            # The 30-second view
            "executive_summary": {
                "business_health": business_health.get("assessment", "Unknown"),
                "earnings_trend": business_health.get("components", {}).get("profitability", "Unknown"),
                "earnings_quality": earnings_quality.get("assessment", "Unknown"),
                "valuation_assessment": valuation.get("assessment", "Unknown"),
                "risk_level": risks.get("summary", {}).get("high", 0),
                "key_insight": bull_bear.get("critical_debate", ""),
            },
            # Full intelligence engines
            "intelligence": {
                "business_health": business_health,
                "what_changed": what_changed,
                "earnings_quality": earnings_quality,
                "investment_case": {
                    "bull": bull_bear.get("bull_case", {}),
                    "bear": bull_bear.get("bear_case", {}),
                    "critical_debate": bull_bear.get("critical_debate", ""),
                },
                "red_flags": red_flags,
                "risk_assessment": risks,
                "catalysts": catalysts,
                "valuation": valuation,
                "watch_list": watch_list,
            },
            # Thesis framework
            "thesis": {
                "bull_case": bull_bear.get("bull_case", {}).get("thesis", ""),
                "bear_case": bull_bear.get("bear_case", {}).get("thesis", ""),
                "confirmation_triggers": watch_list.get("thesis_invalidation_triggers", []),
                "major_risks": [r for r in risks.get("all_risks", [])[:3]],
            },
            # Actionable monitoring
            "before_you_buy": watch_list.get("watch_metrics", []),
            # Cross-engine consistency validation
            "validation": validation_report,
        }

    except Exception as e:
        # Log but don't expose internal errors
        return {
            "ticker": symbol,
            "status": "error",
            "error": str(e),
            "message": "Unable to generate complete intelligence analysis. Check that fundamental data is available.",
        }


@router.get("/{ticker}/quick-view")
def quick_view(ticker: str, db: Session = Depends(get_db)) -> dict:
    """30-second research view — the essential context only."""
    symbol = ticker.strip().upper()
    security = db.execute(
        select(Security).where(Security.symbol == symbol, Security.is_active.is_(True))
    ).scalar_one_or_none()

    if security is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {symbol}")

    issuer_id = security.issuer_id
    if issuer_id is None:
        raise HTTPException(status_code=404, detail=f"No issuer data for {symbol}")

    business_health = BusinessHealthEngine.analyze(db, issuer_id)
    bull_bear = BullBearCaseEngine.analyze(db, issuer_id)
    valuation = ValuationContextEngine.analyze(db, issuer_id)
    risks = RiskEngine.analyze(db, issuer_id)

    return {
        "ticker": symbol,
        "business_health": business_health.get("assessment", "Unknown"),
        "trend": business_health.get("narrative", ""),
        "valuation": valuation.get("assessment", ""),
        "bull_thesis": bull_bear.get("bull_case", {}).get("thesis", ""),
        "bear_thesis": bull_bear.get("bear_case", {}).get("thesis", ""),
        "key_debate": bull_bear.get("critical_debate", ""),
        "major_risks": risks.get("summary", {}).get("high", 0),
        "watchlist": [r.get("title") for r in risks.get("high_priority_risks", [])],
    }
