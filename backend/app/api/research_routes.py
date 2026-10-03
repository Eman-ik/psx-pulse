"""Research API routes — Integrate evidence, analysis, and decisions.

Endpoints:
- GET /api/research/{ticker}/snapshot — Build evidence pack
- POST /api/research/{ticker}/analyze — LLM analysis
- POST /api/research/{ticker}/decide — Investment decision
- POST /api/research/{ticker}/unified-flow — End-to-end research

Input: Ticker symbol
Output: JSON with evidence, analysis, or decision
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["research"])


class AnalysisRequest(BaseModel):
    """Request for LLM analysis."""

    ticker: str
    mode: str = "quick"  # quick, deep, forecast
    months: Optional[int] = 12  # For forecast mode


class DecisionRequest(BaseModel):
    """Request for investment decision."""

    ticker: str
    portfolio_size_thousands: int = 100


class UnifiedFlowRequest(BaseModel):
    """Request for end-to-end research flow."""

    ticker: str
    analysis_mode: str = "quick"
    portfolio_size_thousands: int = 100


class SnapshotResponse(BaseModel):
    """Evidence pack response."""

    ticker: str
    company_name: Optional[str]
    current_price: float
    market_cap_bracket: str
    sentiment: str
    confidence_score: float
    data_freshness_days: int
    data: dict


class AnalysisResponse(BaseModel):
    """LLM analysis response."""

    ticker: str
    overall_thesis: str
    confidence: float
    investment_rating: str
    bull_case: str
    bear_case: str
    key_catalysts: list
    key_risks: list
    tokens_used: int
    time_horizon: str


class DecisionResponse(BaseModel):
    """Investment decision response."""

    ticker: str
    recommendation: str
    confidence_pct: float
    conviction_level: str
    suggested_entry_price: float
    target_exit_price: float
    stop_loss_price: float
    position_size_pct: float
    position_size_category: str
    suggested_quantity: Optional[int]
    bull_case: dict
    base_case: dict
    bear_case: dict
    expected_return_pct: float
    key_upside_catalysts: list
    key_downside_risks: list
    time_horizon: str


class UnifiedFlowResponse(BaseModel):
    """Complete research flow response."""

    ticker: str
    snapshot: dict
    analysis: dict
    decision: dict
    flow_status: str  # "complete", "partial", "failed"


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "research-api"}


@router.get("/{ticker}/snapshot")
async def get_snapshot(ticker: str) -> SnapshotResponse:
    """Build evidence pack for ticker.

    Args:
        ticker: Company ticker symbol

    Returns:
        SnapshotResponse with evidence pack data
    """
    try:
        from app.services.snapshot_builder import SnapshotBuilder
        from app.services.evidence_pack_builder import EvidencePackBuilder

        # Build snapshot
        builder = SnapshotBuilder()
        snapshot = builder.build(ticker)

        if not snapshot:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        # Build evidence pack
        evidence_builder = EvidencePackBuilder()
        evidence_pack = evidence_builder.build(snapshot)

        if not evidence_pack:
            raise HTTPException(status_code=500, detail="Failed to build evidence pack")

        return SnapshotResponse(
            ticker=ticker,
            company_name=evidence_pack.company_name,
            current_price=evidence_pack.current_price or 0.0,
            market_cap_bracket=evidence_pack.market_cap_bracket or "unknown",
            sentiment=evidence_pack.sentiment or "neutral",
            confidence_score=evidence_pack.confidence_score or 0.0,
            data_freshness_days=evidence_pack.data_freshness_days or 0,
            data=evidence_pack.to_dict(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building snapshot for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{ticker}/analyze")
async def analyze(
    ticker: str,
    mode: str = Query("quick", description="Analysis mode: quick, deep, forecast"),
    months: int = Query(12, description="Forecast months (for forecast mode)"),
) -> AnalysisResponse:
    """Run LLM analysis for ticker.

    Args:
        ticker: Company ticker
        mode: Analysis mode (quick/deep/forecast)
        months: Months for forecast mode

    Returns:
        AnalysisResponse with LLM analysis
    """
    try:
        from app.services.snapshot_builder import SnapshotBuilder
        from app.services.evidence_pack_builder import EvidencePackBuilder
        from app.services.llm_client import LLMClient

        # Build evidence pack
        builder = SnapshotBuilder()
        snapshot = builder.build(ticker)
        if not snapshot:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        evidence_builder = EvidencePackBuilder()
        evidence_pack = evidence_builder.build(snapshot)
        if not evidence_pack:
            raise HTTPException(status_code=500, detail="Failed to build evidence pack")

        # Run LLM analysis
        llm = LLMClient()
        if mode == "quick":
            result = llm.analyze_quick(evidence_pack)
        elif mode == "deep":
            result = llm.analyze_deep(evidence_pack)
        elif mode == "forecast":
            result = llm.analyze_forecast(evidence_pack, months=months)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown mode: {mode}")

        if not result:
            raise HTTPException(status_code=500, detail="Analysis failed")

        return AnalysisResponse(
            ticker=result.ticker,
            overall_thesis=result.overall_thesis,
            confidence=result.confidence,
            investment_rating=result.investment_rating,
            bull_case=result.bull_case,
            bear_case=result.bear_case,
            key_catalysts=result.key_catalysts,
            key_risks=result.key_risks,
            tokens_used=result.tokens_used,
            time_horizon=result.time_horizon,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{ticker}/decide")
async def decide(
    ticker: str,
    portfolio_size_thousands: int = Query(100, description="Portfolio size in thousands PKR"),
) -> DecisionResponse:
    """Generate investment decision for ticker.

    Args:
        ticker: Company ticker
        portfolio_size_thousands: Portfolio size in thousands

    Returns:
        DecisionResponse with investment decision
    """
    try:
        from app.services.snapshot_builder import SnapshotBuilder
        from app.services.evidence_pack_builder import EvidencePackBuilder
        from app.services.llm_client import LLMClient
        from app.services.analyst_engine import AnalystEngine

        # Build evidence pack
        builder = SnapshotBuilder()
        snapshot = builder.build(ticker)
        if not snapshot:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        evidence_builder = EvidencePackBuilder()
        evidence_pack = evidence_builder.build(snapshot)
        if not evidence_pack:
            raise HTTPException(status_code=500, detail="Failed to build evidence pack")

        # Run LLM analysis
        llm = LLMClient()
        llm_result = llm.analyze_quick(evidence_pack)
        if not llm_result:
            raise HTTPException(status_code=500, detail="Analysis failed")

        # Generate decision
        analyst = AnalystEngine()
        decision = analyst.decide(llm_result, evidence_pack, portfolio_size_thousands)
        if not decision:
            raise HTTPException(status_code=500, detail="Decision generation failed")

        return DecisionResponse(
            ticker=decision.ticker,
            recommendation=decision.recommendation.value,
            confidence_pct=decision.confidence_pct,
            conviction_level=decision.conviction_level,
            suggested_entry_price=decision.suggested_entry_price,
            target_exit_price=decision.target_exit_price,
            stop_loss_price=decision.stop_loss_price,
            position_size_pct=decision.position_size_pct,
            position_size_category=decision.position_size_category.value,
            suggested_quantity=decision.suggested_quantity,
            bull_case={
                "target_price": decision.bull_case_projection.target_price,
                "upside_pct": decision.bull_case_projection.upside_pct,
                "probability_pct": decision.bull_case_projection.probability_pct,
            },
            base_case={
                "target_price": decision.base_case_projection.target_price,
                "upside_pct": decision.base_case_projection.upside_pct,
                "probability_pct": decision.base_case_projection.probability_pct,
            },
            bear_case={
                "target_price": decision.bear_case_projection.target_price,
                "upside_pct": decision.bear_case_projection.upside_pct,
                "probability_pct": decision.bear_case_projection.probability_pct,
            },
            expected_return_pct=decision.expected_return_pct,
            key_upside_catalysts=decision.key_upside_catalysts,
            key_downside_risks=decision.key_downside_risks,
            time_horizon=decision.time_horizon,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deciding on {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{ticker}/unified-flow")
async def unified_flow(
    ticker: str,
    analysis_mode: str = Query("quick", description="Analysis mode"),
    portfolio_size_thousands: int = Query(100, description="Portfolio size in thousands"),
) -> UnifiedFlowResponse:
    """End-to-end research flow: snapshot → analyze → decide.

    Args:
        ticker: Company ticker
        analysis_mode: Analysis mode (quick/deep/forecast)
        portfolio_size_thousands: Portfolio size in thousands

    Returns:
        UnifiedFlowResponse with all stages
    """
    try:
        from app.services.snapshot_builder import SnapshotBuilder
        from app.services.evidence_pack_builder import EvidencePackBuilder
        from app.services.llm_client import LLMClient
        from app.services.analyst_engine import AnalystEngine

        flow_status = "complete"
        snapshot_data = {}
        analysis_data = {}
        decision_data = {}

        # Stage 1: Build snapshot
        try:
            builder = SnapshotBuilder()
            snapshot = builder.build(ticker)
            if not snapshot:
                raise Exception(f"No data for {ticker}")

            evidence_builder = EvidencePackBuilder()
            evidence_pack = evidence_builder.build(snapshot)
            if not evidence_pack:
                raise Exception("Failed to build evidence pack")

            snapshot_data = evidence_pack.to_dict()
        except Exception as e:
            logger.error(f"Snapshot stage failed: {e}")
            flow_status = "partial"
            snapshot_data = {"error": str(e)}

        # Stage 2: Run analysis
        try:
            if not evidence_pack:
                raise Exception("No evidence pack from stage 1")

            llm = LLMClient()
            if analysis_mode == "quick":
                llm_result = llm.analyze_quick(evidence_pack)
            elif analysis_mode == "deep":
                llm_result = llm.analyze_deep(evidence_pack)
            elif analysis_mode == "forecast":
                llm_result = llm.analyze_forecast(evidence_pack, months=12)
            else:
                raise Exception(f"Unknown analysis mode: {analysis_mode}")

            if not llm_result:
                raise Exception("Analysis failed")

            analysis_data = llm_result.to_dict()
        except Exception as e:
            logger.error(f"Analysis stage failed: {e}")
            if flow_status == "complete":
                flow_status = "partial"
            analysis_data = {"error": str(e)}

        # Stage 3: Generate decision
        try:
            if not llm_result or not evidence_pack:
                raise Exception("Missing data from previous stages")

            analyst = AnalystEngine()
            decision = analyst.decide(llm_result, evidence_pack, portfolio_size_thousands)
            if not decision:
                raise Exception("Decision generation failed")

            decision_data = decision.to_dict()
        except Exception as e:
            logger.error(f"Decision stage failed: {e}")
            if flow_status == "complete":
                flow_status = "partial"
            decision_data = {"error": str(e)}

        return UnifiedFlowResponse(
            ticker=ticker,
            snapshot=snapshot_data,
            analysis=analysis_data,
            decision=decision_data,
            flow_status=flow_status,
        )

    except Exception as e:
        logger.error(f"Unified flow failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
