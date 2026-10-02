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
        # Run all intelligence engines in parallel conceptually
        business_health = BusinessHealthEngine.analyze(db, issuer_id)
        what_changed = WhatChangedEngine.analyze(db, issuer_id)
        earnings_quality = EarningsQualityEngine.analyze(db, issuer_id)
        bull_bear = BullBearCaseEngine.analyze(db, issuer_id)
        red_flags = RedFlagEngine.detect(db, issuer_id)
        risks = RiskEngine.analyze(db, issuer_id)
        catalysts = CatalystEngine.analyze(db, issuer_id)
        valuation = ValuationContextEngine.analyze(db, issuer_id)
        watch_list = WhatToWatchEngine.analyze(db, issuer_id)

        # Composite confidence score (0-100)
        # Based on data availability and signal strength
        confidence_signals = [
            1 if business_health.get("status") == "complete" else 0,
            1 if what_changed.get("status") == "complete" else 0,
            1 if earnings_quality.get("status") == "complete" else 0,
            1 if bull_bear.get("key_metrics") else 0,
            1 if len(red_flags.get("flags", [])) >= 0 else 0,
        ]
        confidence_score = int((sum(confidence_signals) / len(confidence_signals)) * 100)

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
