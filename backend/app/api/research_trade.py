"""
Module 7: Unified Research-to-Trade Flow API

Integrates research analysis, decision gates, and position sizing into a complete
trade decision-support workflow.

POST /api/research-trade/unified-flow
- Input: ticker, entry, stop, targets, portfolio_value, risk_percent
- Output: evidence_score, gates, thesis, calculator, confidence, ready_to_trade
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add research_system to path so we can import from it
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from research_system.research_trade_unified import ResearchTradeUnifiedFlow, TradeHorizon

router = APIRouter(prefix="/research-trade", tags=["research-trade"])


# ════════════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ════════════════════════════════════════════════════════════════════════════════

class UnifiedFlowRequest(BaseModel):
    """Request for unified research-to-trade analysis"""
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    entry: float = Field(..., gt=0, description="Entry price")
    stop: float = Field(..., gt=0, description="Stop loss price")
    targets: List[float] = Field(..., min_items=1, description="List of target prices")
    portfolio_value: float = Field(..., gt=0, description="Total portfolio value")
    risk_percent: float = Field(default=2.0, ge=0.1, le=10.0, description="Risk per trade as % of portfolio")
    trade_horizon: str = Field(default="MEDIUM_TERM", description="Trade holding period (INTRADAY, SWING, SHORT_TERM, MEDIUM_TERM, LONG_TERM)")

    class Config:
        schema_extra = {
            "example": {
                "ticker": "FFC",
                "entry": 250.0,
                "stop": 240.0,
                "targets": [260.0, 270.0, 280.0],
                "portfolio_value": 100000.0,
                "risk_percent": 2.0,
                "trade_horizon": "MEDIUM_TERM",
            }
        }


class EvidenceCoverageScoreResponse(BaseModel):
    """Evidence coverage assessment (data completeness, not investment quality)"""
    coverage_pct: float = Field(..., ge=0, le=100)
    total_sections: int
    real_sections: int
    missing_evidence: List[str]
    data_freshness_score: float = Field(..., ge=0, le=100)
    source_reliability: float = Field(..., ge=0, le=100)
    overall_evidence_score: float = Field(..., ge=0, le=100)


class DecisionGateResponse(BaseModel):
    """Result of a decision gate"""
    gate_name: str
    passed: bool
    issue: str | None = None


class PillarScoresResponse(BaseModel):
    """Pillar analysis scores"""
    Fundamental: float = Field(..., ge=0, le=100)
    Valuation: float = Field(..., ge=0, le=100)
    Technical: float = Field(..., ge=0, le=100)
    Market: float = Field(..., ge=0, le=100)


class ThesisResponse(BaseModel):
    """Trade thesis synthesis"""
    thesis_valid: bool
    reason: str | None = None
    pillar_scores: PillarScoresResponse | None = None
    confidence_score: float = Field(..., ge=0, le=100)
    evidence_coverage: float = Field(..., ge=0, le=100)
    gates_passed: bool
    bull_case: str
    bear_case: str
    invalidation: str


class CalculatorMetricsResponse(BaseModel):
    """Position sizing metrics"""
    position_size_shares: int
    capital_required: float
    risk_per_share: float
    max_loss: float
    allocation_pct: float
    warnings: List[str] = []


class UnifiedFlowResponse(BaseModel):
    """Complete unified research-to-trade response"""
    ticker: str
    evidence_score: EvidenceCoverageScoreResponse
    gates: List[DecisionGateResponse]
    gates_passed: bool
    thesis: ThesisResponse
    calculator: CalculatorMetricsResponse
    ready_to_trade: bool
    confidence: float = Field(..., ge=0, le=100)
    timestamp: str


# ════════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════════

@router.post("/unified-flow", response_model=UnifiedFlowResponse)
def unified_research_trade_flow(request: UnifiedFlowRequest) -> Dict[str, Any]:
    """
    Run complete research-to-trade analysis.

    **Flow**:
    1. Assess research evidence coverage (data completeness)
    2. Run position sizing calculator
    3. Validate decision gates (Data Integrity, Trade Validity, Hard Risks)
    4. If gates pass: analyze fundamentals, valuation, technical, market, events
    5. Synthesize thesis from all pillars
    6. Return complete decision package

    **Response Fields**:
    - `evidence_score`: Research data completeness (0-100%, separate from investment quality)
    - `gates`: Decision gate results (must all pass to proceed)
    - `gates_passed`: True if all gates passed
    - `thesis`: Trade thesis synthesis with bull/bear/invalidation cases
    - `calculator`: Position sizing metrics (shares, capital, risk)
    - `ready_to_trade`: True if gates passed AND thesis valid
    - `confidence`: Investment confidence score (0-100%, not a buy/sell recommendation)

    **Entry Requirements**:
    - Entry price must be > stop loss
    - At least one target must be > entry price
    - All prices must be positive
    """

    try:
        # Map trade horizon string to enum
        try:
            horizon = TradeHorizon[request.trade_horizon.upper()]
        except KeyError:
            raise ValueError(f"Invalid trade_horizon: {request.trade_horizon}. Must be one of: {', '.join(h.name for h in TradeHorizon)}")

        # Call refactored orchestrator
        result = ResearchTradeUnifiedFlow.orchestrate_full_flow(
            ticker=request.ticker,
            entry=request.entry,
            stop=request.stop,
            targets=request.targets,
            portfolio_value=request.portfolio_value,
            risk_percent=request.risk_percent,
            trade_horizon=horizon,
        )

        # Transform gates to response format
        gates_response = [
            DecisionGateResponse(
                gate_name=gate.gate_name,
                passed=gate.passed,
                issue=gate.issue,
            )
            for gate in result["gates"]
        ]

        # Transform evidence score to response format
        evidence = result["evidence_score"]
        evidence_response = EvidenceCoverageScoreResponse(
            coverage_pct=evidence.coverage_pct,
            total_sections=evidence.total_sections,
            real_sections=evidence.real_sections,
            missing_evidence=evidence.missing_evidence,
            data_freshness_score=evidence.data_freshness_score,
            source_reliability=evidence.source_reliability,
            overall_evidence_score=evidence.overall_evidence_score,
        )

        # Transform thesis to response format
        thesis = result["thesis"]
        thesis_response = ThesisResponse(
            thesis_valid=thesis.get("thesis_valid", False),
            reason=thesis.get("reason"),
            pillar_scores=PillarScoresResponse(**thesis["pillar_scores"]) if thesis.get("pillar_scores") else None,
            confidence_score=thesis.get("confidence_score", 0),
            evidence_coverage=thesis.get("evidence_coverage", 0),
            gates_passed=thesis.get("gates_passed", False),
            bull_case=thesis.get("bull_case", ""),
            bear_case=thesis.get("bear_case", ""),
            invalidation=thesis.get("invalidation", ""),
        )

        # Transform calculator to response format
        calc = result["calculator"]
        calculator_response = CalculatorMetricsResponse(
            position_size_shares=int(calc.position_size_shares),
            capital_required=float(calc.capital_required),
            risk_per_share=float(calc.risk_per_share),
            max_loss=float(calc.max_loss),
            allocation_pct=float(calc.allocation_pct),
            warnings=calc.warnings or [],
        )

        return {
            "ticker": request.ticker,
            "evidence_score": evidence_response,
            "gates": gates_response,
            "gates_passed": result["gates_passed"],
            "thesis": thesis_response,
            "calculator": calculator_response,
            "ready_to_trade": result["ready_to_trade"],
            "confidence": result["confidence"],
            "timestamp": result["timestamp"],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
