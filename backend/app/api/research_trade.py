"""Pre-trade checks for a proposed long trade. Returns individual gates, never a single
"ready to trade" verdict; see app/research_system/trade_check.py."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.research_system.trade_check import run_trade_check

router = APIRouter(prefix="/api/research-trade", tags=["research-trade"])


class TradeCheckRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    entry: float = Field(..., gt=0)
    stop: float = Field(..., gt=0)
    targets: list[float] = Field(..., min_length=1)
    portfolio_value: float = Field(..., gt=0)
    risk_percent: float = Field(default=1.0, ge=0.1, le=10.0)


@router.post("/check")
def trade_check(request: TradeCheckRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return run_trade_check(db, request.ticker, request.entry, request.stop, request.targets,
                               request.portfolio_value, request.risk_percent)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
