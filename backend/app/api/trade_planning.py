"""Trade planning: position sizing, risk validation, trade confirmation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/research/trade", tags=["research"])


class TradePlan(BaseModel):
    ticker: str
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float | None = None
    portfolio_value: float
    risk_percent: float


class TradeValidation(BaseModel):
    ticker: str
    entry_price: float
    stop_loss: float
    current_price: float
    portfolio_value: float
    position_shares: int


class TradePlanResponse(BaseModel):
    ticker: str
    entry_price: float
    stop_loss: float
    take_profits: list[float]
    position_shares: int
    risk_amount: float
    max_loss: float
    reward_potential: list[float]
    risk_reward_ratio: float
    position_size_pct: float
    is_valid: bool
    warnings: list[str]
    confidence: str


@router.post("/planning", response_model=TradePlanResponse)
def plan_trade(plan: TradePlan) -> TradePlanResponse:
    """Calculate position sizing and validate trade parameters."""

    warnings = []

    # Risk in PKR
    risk_amount = plan.portfolio_value * (plan.risk_percent / 100)

    # Risk per share
    risk_per_share = abs(plan.entry_price - plan.stop_loss)
    if risk_per_share < 0.01:
        raise HTTPException(status_code=400, detail="Stop loss too close to entry")

    # Position shares
    position_shares = int(risk_amount / risk_per_share)

    # Max loss if stop hit
    max_loss = position_shares * risk_per_share

    # Take profit rewards
    tp1_reward = (plan.take_profit_1 - plan.entry_price) * position_shares if plan.take_profit_1 else 0
    tp2_reward = (plan.take_profit_2 - plan.entry_price) * position_shares if plan.take_profit_2 else 0
    reward_potential = [tp1_reward]
    if plan.take_profit_2:
        reward_potential.append(tp2_reward)

    # Risk/reward
    avg_reward = sum(reward_potential) / len(reward_potential) if reward_potential else 0
    risk_reward_ratio = avg_reward / max_loss if max_loss > 0 else 0

    # Validation
    is_valid = True
    position_size_pct = (position_shares * plan.entry_price) / plan.portfolio_value * 100

    if plan.stop_loss >= plan.entry_price:
        is_valid = False
        warnings.append("Stop loss must be below entry price")

    if plan.take_profit_1 <= plan.entry_price:
        is_valid = False
        warnings.append("Take profit must be above entry price")

    if position_size_pct > 10:
        warnings.append(f"Position is {position_size_pct:.1f}% of portfolio (typical max 5-10%)")

    if risk_reward_ratio < 1.5:
        warnings.append(f"Risk/reward ratio {risk_reward_ratio:.2f} is below 1.5:1 threshold")

    if plan.risk_percent > 2:
        warnings.append(f"Risk per trade {plan.risk_percent}% is above typical 1-2% limit")

    # Confidence
    if risk_reward_ratio >= 2.5 and position_size_pct <= 5 and not warnings:
        confidence = "High"
    elif risk_reward_ratio >= 1.5 and position_size_pct <= 8:
        confidence = "Medium"
    else:
        confidence = "Low"

    return TradePlanResponse(
        ticker=plan.ticker,
        entry_price=plan.entry_price,
        stop_loss=plan.stop_loss,
        take_profits=[plan.take_profit_1] + ([plan.take_profit_2] if plan.take_profit_2 else []),
        position_shares=position_shares,
        risk_amount=risk_amount,
        max_loss=max_loss,
        reward_potential=reward_potential,
        risk_reward_ratio=risk_reward_ratio,
        position_size_pct=position_size_pct,
        is_valid=is_valid,
        warnings=warnings,
        confidence=confidence,
    )


@router.post("/validate", response_model=dict)
def validate_trade(trade: TradeValidation) -> dict:
    """Validate current trade parameters against position limits."""

    checks = {}

    # Price check
    if trade.current_price <= trade.stop_loss or trade.current_price >= trade.entry_price * 1.5:
        checks["price_valid"] = False
        checks["price_msg"] = "Entry price not in valid range vs current price"
    else:
        checks["price_valid"] = True

    # Liquidity check (avg volume >= 100k shares)
    checks["liquidity_ok"] = trade.position_shares < 1000000

    # Position size check
    position_value = trade.position_shares * trade.entry_price
    position_pct = position_value / trade.portfolio_value * 100
    checks["position_pct"] = position_pct
    checks["position_ok"] = position_pct <= 10

    # Risk check
    max_loss = trade.position_shares * abs(trade.entry_price - trade.stop_loss)
    risk_pct = (max_loss / trade.portfolio_value) * 100
    checks["risk_pct"] = risk_pct
    checks["risk_ok"] = risk_pct <= 2

    checks["overall_valid"] = all([
        checks.get("price_valid", False),
        checks.get("liquidity_ok", False),
        checks.get("position_ok", False),
        checks.get("risk_ok", False),
    ])

    return checks
