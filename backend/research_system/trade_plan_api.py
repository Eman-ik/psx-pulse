"""
Trade Plan API - Module 6, Sprint R2

REST API for trade plan CRUD operations and risk calculations.

Endpoints:
- POST /api/trade-plans                    Create new plan
- GET /api/trade-plans/{id}               Get specific plan
- GET /api/trade-plans?user_id=X          List user's plans
- PATCH /api/trade-plans/{id}             Update plan
- DELETE /api/trade-plans/{id}            Delete plan
- POST /api/trade-plans/calculate         Calculate risks (no persistence)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .schema import TradePlan, TradeStatus, Security
from .database import get_session
from .trade_plan_engine import (
    TradePlanCalculator,
    CalculatorInput,
    CalculatorOutput,
)


# ════════════════════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ════════════════════════════════════════════════════════════════════════════════

def trade_plan_to_dict(plan: TradePlan) -> Dict[str, Any]:
    """Convert TradePlan to API response dict."""
    return {
        "trade_plan_id": plan.trade_plan_id,
        "user_id": plan.user_id,
        "ticker": plan.ticker,
        "security_id": plan.security_id,
        "status": plan.status.value if plan.status else None,
        "trade_type": plan.trade_type.value if plan.trade_type else None,
        "time_horizon": plan.time_horizon.value if plan.time_horizon else None,
        # Entry
        "entry_price": float(plan.entry_price) if plan.entry_price else None,
        "entry_zone_low": float(plan.entry_zone_low) if plan.entry_zone_low else None,
        "entry_zone_high": float(plan.entry_zone_high) if plan.entry_zone_high else None,
        # Exit
        "stop_price": float(plan.stop_price) if plan.stop_price else None,
        "stop_type": plan.stop_type.value if plan.stop_type else None,
        "target_1": float(plan.target_1) if plan.target_1 else None,
        "target_2": float(plan.target_2) if plan.target_2 else None,
        "target_3": float(plan.target_3) if plan.target_3 else None,
        # Risk
        "portfolio_value": float(plan.portfolio_value) if plan.portfolio_value else None,
        "risk_percent": float(plan.risk_percent) if plan.risk_percent else None,
        "max_loss_amount": float(plan.max_loss_amount) if plan.max_loss_amount else None,
        "max_position_percent": float(plan.max_position_percent) if plan.max_position_percent else None,
        # Position sizing
        "position_size": plan.position_size,
        "capital_required": float(plan.capital_required) if plan.capital_required else None,
        "allocation_pct": float(plan.allocation_pct) if plan.allocation_pct else None,
        # Risk/Reward
        "risk_reward_1": float(plan.risk_reward_1) if plan.risk_reward_1 else None,
        "risk_reward_2": float(plan.risk_reward_2) if plan.risk_reward_2 else None,
        "risk_reward_3": float(plan.risk_reward_3) if plan.risk_reward_3 else None,
        # Thesis
        "entry_thesis": plan.entry_thesis,
        "invalidation_thesis": plan.invalidation_thesis,
        "notes": plan.notes,
        # Execution
        "entered_at": plan.entered_at.isoformat() if plan.entered_at else None,
        "actual_entry_price": float(plan.actual_entry_price) if plan.actual_entry_price else None,
        "closed_at": plan.closed_at.isoformat() if plan.closed_at else None,
        "exit_reason": plan.exit_reason,
        # Audit
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


# ════════════════════════════════════════════════════════════════════════════════
# CRUD OPERATIONS
# ════════════════════════════════════════════════════════════════════════════════

class TradePlanRepository:
    """Data access layer for trade plans."""

    @staticmethod
    def create(
        session: Session,
        user_id: str,
        ticker: str,
        security_id: int,
        entry_price: float,
        stop_price: float,
        portfolio_value: float,
        risk_percent: float,
        trade_type: Optional[str] = None,
        time_horizon: Optional[str] = None,
        target_1: Optional[float] = None,
        target_2: Optional[float] = None,
        target_3: Optional[float] = None,
        entry_zone_low: Optional[float] = None,
        entry_zone_high: Optional[float] = None,
        stop_type: Optional[str] = None,
        max_position_percent: float = 20.0,
        entry_thesis: Optional[str] = None,
        invalidation_thesis: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> TradePlan:
        """
        Create new trade plan.

        Args:
            session: Database session
            user_id: User identifier
            ticker: Security ticker
            security_id: Security ID
            entry_price: Planned entry price
            stop_price: Stop-loss price
            portfolio_value: Total portfolio (PKR)
            risk_percent: Risk per trade (%)
            ... (optional parameters)

        Returns:
            Created TradePlan object
        """
        plan = TradePlan(
            user_id=user_id,
            ticker=ticker,
            security_id=security_id,
            entry_price=Decimal(str(entry_price)),
            stop_price=Decimal(str(stop_price)),
            portfolio_value=Decimal(str(int(portfolio_value))),
            risk_percent=Decimal(str(risk_percent)),
            trade_type=trade_type,
            time_horizon=time_horizon,
            target_1=Decimal(str(target_1)) if target_1 else None,
            target_2=Decimal(str(target_2)) if target_2 else None,
            target_3=Decimal(str(target_3)) if target_3 else None,
            entry_zone_low=Decimal(str(entry_zone_low)) if entry_zone_low else None,
            entry_zone_high=Decimal(str(entry_zone_high)) if entry_zone_high else None,
            stop_type=stop_type,
            max_position_percent=Decimal(str(max_position_percent)),
            entry_thesis=entry_thesis,
            invalidation_thesis=invalidation_thesis,
            notes=notes,
            status=TradeStatus.DRAFT,
        )

        session.add(plan)
        session.commit()
        session.refresh(plan)
        return plan

    @staticmethod
    def get_by_id(session: Session, trade_plan_id: int) -> Optional[TradePlan]:
        """Get trade plan by ID."""
        return session.query(TradePlan).filter(
            TradePlan.trade_plan_id == trade_plan_id
        ).first()

    @staticmethod
    def list_by_user(
        session: Session,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TradePlan]:
        """
        List all trade plans for a user.

        Args:
            session: Database session
            user_id: User identifier
            status: Filter by status (optional)
            limit: Result limit
            offset: Pagination offset

        Returns:
            List of TradePlan objects
        """
        query = session.query(TradePlan).filter(TradePlan.user_id == user_id)

        if status:
            query = query.filter(TradePlan.status == status)

        return query.order_by(TradePlan.created_at.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def update(
        session: Session,
        trade_plan_id: int,
        **kwargs
    ) -> Optional[TradePlan]:
        """
        Update trade plan fields.

        Args:
            session: Database session
            trade_plan_id: Plan ID
            **kwargs: Fields to update (entry_price, stop_price, etc.)

        Returns:
            Updated TradePlan or None if not found
        """
        plan = TradePlanRepository.get_by_id(session, trade_plan_id)
        if not plan:
            return None

        # Convert Decimals if needed
        for key, value in kwargs.items():
            if key in ['entry_price', 'stop_price', 'target_1', 'target_2', 'target_3',
                      'portfolio_value', 'risk_percent', 'entry_zone_low', 'entry_zone_high',
                      'max_position_percent', 'capital_required', 'allocation_pct',
                      'risk_reward_1', 'risk_reward_2', 'risk_reward_3', 'actual_entry_price']:
                if value is not None:
                    value = Decimal(str(value))

            if hasattr(plan, key):
                setattr(plan, key, value)

        plan.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(plan)
        return plan

    @staticmethod
    def delete(session: Session, trade_plan_id: int) -> bool:
        """
        Delete trade plan.

        Args:
            session: Database session
            trade_plan_id: Plan ID

        Returns:
            True if deleted, False if not found
        """
        plan = TradePlanRepository.get_by_id(session, trade_plan_id)
        if not plan:
            return False

        session.delete(plan)
        session.commit()
        return True


# ════════════════════════════════════════════════════════════════════════════════
# CALCULATION & PERSISTENCE
# ════════════════════════════════════════════════════════════════════════════════

def calculate_and_save(
    session: Session,
    trade_plan_id: int,
    adv20_value: Optional[float] = None,
    atr: Optional[float] = None
) -> tuple[Optional[TradePlan], Optional[CalculatorOutput], List[str]]:
    """
    Run trade plan calculator and save results to database.

    Args:
        session: Database session
        trade_plan_id: Trade plan ID
        adv20_value: Average daily value (optional)
        atr: ATR for stop calculation (optional)

    Returns:
        (updated_plan, calculator_output, errors)
    """
    plan = TradePlanRepository.get_by_id(session, trade_plan_id)
    if not plan:
        return None, None, ["Trade plan not found"]

    # Build calculator input from plan
    targets = []
    if plan.target_1:
        targets.append(float(plan.target_1))
    if plan.target_2:
        targets.append(float(plan.target_2))
    if plan.target_3:
        targets.append(float(plan.target_3))

    if not targets:
        return None, None, ["No targets defined"]

    calculator_input = CalculatorInput(
        entry_price=float(plan.entry_price),
        stop_price=float(plan.stop_price),
        target_prices=targets,
        portfolio_value=float(plan.portfolio_value),
        risk_percent=float(plan.risk_percent),
        max_position_percent=float(plan.max_position_percent),
        adv20_value=adv20_value,
        atr=atr
    )

    # Run calculator
    try:
        output = TradePlanCalculator.calculate(calculator_input)
    except ValueError as e:
        return None, None, [str(e)]

    # Save results to database
    update_data = {
        "position_size": output.risk_metrics.position_size,
        "capital_required": output.risk_metrics.capital_required,
        "allocation_pct": output.risk_metrics.allocation_pct,
        "max_loss_amount": output.risk_metrics.max_loss,
    }

    # Save R/R ratios
    for i, rr in enumerate(output.risk_reward_ratios, 1):
        key = f"risk_reward_{i}"
        if hasattr(plan, key):
            update_data[key] = rr.ratio

    plan = TradePlanRepository.update(session, trade_plan_id, **update_data)

    return plan, output, []


# ════════════════════════════════════════════════════════════════════════════════
# API HANDLERS
# ════════════════════════════════════════════════════════════════════════════════

def api_create_trade_plan(
    user_id: str,
    ticker: str,
    entry_price: float,
    stop_price: float,
    portfolio_value: float,
    risk_percent: float,
    security_id: Optional[int] = None,
    target_1: Optional[float] = None,
    target_2: Optional[float] = None,
    target_3: Optional[float] = None,
    trade_type: Optional[str] = None,
    time_horizon: Optional[str] = None,
    entry_thesis: Optional[str] = None,
    invalidation_thesis: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    API handler: Create new trade plan.

    POST /api/trade-plans
    {
        "user_id": "user@example.com",
        "ticker": "DGKC",
        "security_id": 123,
        "entry_price": 200,
        "stop_price": 188,
        "portfolio_value": 2000000,
        "risk_percent": 1.0,
        "target_1": 220,
        "target_2": 240,
        ...
    }
    """
    session = get_session()
    try:
        if security_id is None:
            # Lookup security by ticker
            security = session.query(Security).filter(
                Security.ticker == ticker
            ).first()
            if not security:
                return {"error": f"Security not found: {ticker}"}
            security_id = security.security_id

        plan = TradePlanRepository.create(
            session,
            user_id=user_id,
            ticker=ticker,
            security_id=security_id,
            entry_price=entry_price,
            stop_price=stop_price,
            portfolio_value=portfolio_value,
            risk_percent=risk_percent,
            trade_type=trade_type,
            time_horizon=time_horizon,
            target_1=target_1,
            target_2=target_2,
            target_3=target_3,
            entry_thesis=entry_thesis,
            invalidation_thesis=invalidation_thesis,
            notes=notes,
        )

        return {
            "success": True,
            "trade_plan": trade_plan_to_dict(plan)
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()


def api_get_trade_plan(trade_plan_id: int) -> Dict[str, Any]:
    """
    API handler: Get trade plan by ID.

    GET /api/trade-plans/{id}
    """
    session = get_session()
    try:
        plan = TradePlanRepository.get_by_id(session, trade_plan_id)
        if not plan:
            return {"error": f"Trade plan not found: {trade_plan_id}"}

        return {
            "success": True,
            "trade_plan": trade_plan_to_dict(plan)
        }

    finally:
        session.close()


def api_list_trade_plans(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    API handler: List trade plans for user.

    GET /api/trade-plans?user_id=X&status=WATCHING&limit=50
    """
    session = get_session()
    try:
        plans = TradePlanRepository.list_by_user(
            session,
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )

        return {
            "success": True,
            "count": len(plans),
            "trade_plans": [trade_plan_to_dict(p) for p in plans]
        }

    finally:
        session.close()


def api_update_trade_plan(
    trade_plan_id: int,
    **kwargs
) -> Dict[str, Any]:
    """
    API handler: Update trade plan.

    PATCH /api/trade-plans/{id}
    {
        "status": "READY",
        "entry_price": 202,
        ...
    }
    """
    session = get_session()
    try:
        plan = TradePlanRepository.update(session, trade_plan_id, **kwargs)
        if not plan:
            return {"error": f"Trade plan not found: {trade_plan_id}"}

        return {
            "success": True,
            "trade_plan": trade_plan_to_dict(plan)
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()


def api_delete_trade_plan(trade_plan_id: int) -> Dict[str, Any]:
    """
    API handler: Delete trade plan.

    DELETE /api/trade-plans/{id}
    """
    session = get_session()
    try:
        deleted = TradePlanRepository.delete(session, trade_plan_id)
        if not deleted:
            return {"error": f"Trade plan not found: {trade_plan_id}"}

        return {"success": True, "message": "Trade plan deleted"}

    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()


def api_calculate_trade_plan(
    trade_plan_id: int,
    adv20_value: Optional[float] = None,
    atr: Optional[float] = None
) -> Dict[str, Any]:
    """
    API handler: Calculate risks and save to plan.

    POST /api/trade-plans/{id}/calculate
    {
        "adv20_value": 20000000,
        "atr": 6.5
    }
    """
    session = get_session()
    try:
        plan, output, errors = calculate_and_save(
            session,
            trade_plan_id,
            adv20_value=adv20_value,
            atr=atr
        )

        if errors:
            return {"error": errors[0]}

        if not plan or not output:
            return {"error": "Calculation failed"}

        return {
            "success": True,
            "trade_plan": trade_plan_to_dict(plan),
            "calculation": {
                "risk_per_share": output.risk_metrics.risk_per_share,
                "max_loss": output.risk_metrics.max_loss,
                "position_size": output.risk_metrics.position_size,
                "capital_required": output.risk_metrics.capital_required,
                "allocation_pct": output.risk_metrics.allocation_pct,
                "risk_reward_ratios": [
                    {"target": rr.target_price, "ratio": rr.ratio}
                    for rr in output.risk_reward_ratios
                ],
                "liquidity_category": output.liquidity_category.value if output.liquidity_category else None,
                "warnings": output.warnings,
            }
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()


def api_unified_research_trade_flow(
    ticker: str,
    entry: float,
    stop: float,
    targets: List[float],
    portfolio_value: float,
    risk_percent: float,
    research_report: Optional[Dict[str, Any]] = None,
    security_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    API handler: Complete unified research-to-trade flow (Module 7).

    Orchestrates: Research Report → Position Sizing → All Contexts → Unified Scoring

    POST /api/research-trade/unified-flow
    {
        "ticker": "FFC",
        "entry": 250,
        "stop": 240,
        "targets": [260, 270, 280],
        "portfolio_value": 100000,
        "risk_percent": 2,
        "research_report": {...}  # Optional, will be fetched if not provided
    }

    Returns:
    {
        "success": true,
        "unified_response": {
            "ticker": "FFC",
            "research_quality_score": {...},
            "calculator_output": {...},
            "contexts": {
                "technical": {...},
                "market": {...},
                "fundamental": {...},
                "valuation": {...},
                "events": {...}
            },
            "unified_confidence_score": 78,
            "entry_recommendation": "ENTER",
            "key_reasons": [...]
        }
    }
    """
    from .research_trade_unified import ResearchTradeUnifiedFlow

    try:
        # Validate inputs
        if entry <= stop:
            raise ValueError(f"Entry ({entry}) must be > stop ({stop})")
        if not targets or all(t <= entry for t in targets):
            raise ValueError(f"At least one target ({targets}) must be > entry ({entry})")

        # Run unified flow
        unified_response = ResearchTradeUnifiedFlow.orchestrate_full_flow(
            ticker=ticker,
            entry=entry,
            stop=stop,
            targets=targets,
            portfolio_value=portfolio_value,
            risk_percent=risk_percent,
            research_report=research_report,
            security_id=security_id,
        )

        # Convert to dict for JSON serialization
        return {
            "success": True,
            "unified_response": {
                "ticker": unified_response.ticker,
                "security_id": unified_response.security_id,
                # Research component
                "research_quality_score": {
                    "overall_score": unified_response.research_quality_score.overall_score,
                    "total_sections": unified_response.research_quality_score.total_sections,
                    "real_content_sections": unified_response.research_quality_score.real_content_sections,
                    "missing_evidence_count": unified_response.research_quality_score.missing_evidence_count,
                    "confidence_adjustment": unified_response.research_quality_score.confidence_adjustment,
                },
                "research_report": unified_response.research_report,
                # Calculator component
                "calculator_output": {
                    "risk_metrics": {
                        "risk_per_share": float(unified_response.calculator_output.risk_metrics.risk_per_share),
                        "max_loss": float(unified_response.calculator_output.risk_metrics.max_loss),
                        "position_size": unified_response.calculator_output.risk_metrics.position_size,
                        "capital_required": float(unified_response.calculator_output.risk_metrics.capital_required),
                        "allocation_pct": float(unified_response.calculator_output.risk_metrics.allocation_pct),
                    },
                    "risk_reward_ratios": [
                        {"target": float(rr.target_price), "reward": float(rr.reward_per_share), "ratio": float(rr.ratio)}
                        for rr in unified_response.calculator_output.risk_reward_ratios
                    ],
                    "liquidity_category": unified_response.calculator_output.liquidity_category.value if unified_response.calculator_output.liquidity_category else None,
                    "warnings": unified_response.calculator_output.warnings,
                },
                # Contexts
                "contexts": {
                    "technical": {
                        "zones": getattr(unified_response.technical_context, "zones", []),
                        "atr": getattr(unified_response.technical_context, "atr", None),
                        "volatility_pct": getattr(unified_response.technical_context, "volatility_pct", None),
                        "trend_state": getattr(unified_response.technical_context, "trend_state", None),
                    },
                    "market": {
                        "regime": getattr(unified_response.market_context, "regime", None),
                        "regime_confidence": getattr(unified_response.market_context, "regime_confidence", None),
                        "market_health": getattr(unified_response.market_context, "market_health", None),
                        "sector_trend": getattr(unified_response.market_context, "sector_trend", None),
                        "breadth_pct": getattr(unified_response.market_context, "breadth_pct", None),
                    },
                    "fundamental": {
                        "momentum": getattr(unified_response.fundamental_context, "momentum", None),
                        "financial_health_score": getattr(unified_response.fundamental_context, "financial_health_score", None),
                        "quality_score": getattr(unified_response.fundamental_context, "quality_score", None),
                        "eps_trend": getattr(unified_response.fundamental_context, "eps_trend", None),
                    },
                    "valuation": {
                        "status": getattr(unified_response.valuation_context, "status", None),
                        "pe_ratio": float(getattr(unified_response.valuation_context, "pe_ratio", 0)) if getattr(unified_response.valuation_context, "pe_ratio", None) else None,
                        "margin_of_safety": getattr(unified_response.valuation_context, "margin_of_safety", None),
                        "valuation_score": getattr(unified_response.valuation_context, "valuation_score", None),
                    },
                    "events": {
                        "upcoming_events": getattr(unified_response.events_context, "upcoming_events", []),
                        "entry_recommendation": getattr(unified_response.events_context, "entry_recommendation", None),
                        "days_to_nearest_event": getattr(unified_response.events_context, "days_to_nearest_event", None),
                    },
                },
                # Unified scoring
                "confidence_breakdown": {
                    "research_quality_score": unified_response.confidence_breakdown.research_quality_score,
                    "technical_score": unified_response.confidence_breakdown.technical_score,
                    "market_score": unified_response.confidence_breakdown.market_score,
                    "fundamental_score": unified_response.confidence_breakdown.fundamental_score,
                    "valuation_score": unified_response.confidence_breakdown.valuation_score,
                    "events_score": unified_response.confidence_breakdown.events_score,
                    "overall_confidence": unified_response.confidence_breakdown.overall_confidence,
                    "key_reasons": unified_response.confidence_breakdown.key_reasons(top_n=3),
                },
                "unified_confidence_score": unified_response.unified_confidence_score,
                "entry_recommendation": unified_response.entry_recommendation.value,
            }
        }

    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Internal error: {str(e)}"}
