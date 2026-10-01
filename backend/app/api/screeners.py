"""API endpoints for technical and momentum screeners."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.data_status import freshness
from app.db.models import PriceOHLCV
from app.db.session import get_db
from app.research_system.technical_screener import TechnicalScreener
from app.research_system.momentum_screener import MomentumScreener

router = APIRouter(prefix="/screeners", tags=["screeners"])


@router.get("/technical")
def run_technical_screener(db: Session = Depends(get_db)) -> dict:
    """Run technical analysis screener on all PSX securities."""
    session = TechnicalScreener.run_screening(db)

    return {
        "timestamp": session.created_at.isoformat(),
        "freshness": freshness(db, PriceOHLCV),
        "total_screened": session.total_screened,
        "results_count": len(session.signals),
        "signals": [
            {
                "symbol": signal.symbol,
                "name": signal.name,
                "sector": signal.sector,
                "price": signal.price,
                "change_pct": round(signal.change_pct, 2),
                "price_vs_20dma": round(signal.price_vs_20dma, 2),
                "price_vs_50dma": round(signal.price_vs_50dma, 2),
                "price_vs_200dma": round(signal.price_vs_200dma, 2),
                "rsi": round(signal.rsi, 2) if signal.rsi else None,
                "volume_vs_avg": round(signal.volume_vs_avg, 2),
                "above_200dma": signal.above_200dma,
                "price_near_52week_high": signal.price_near_52week_high,
                "price_near_52week_low": signal.price_near_52week_low,
                "volume_spike": signal.volume_spike,
                "technical_score": round(signal.technical_score, 2),
            }
            for signal in session.signals
        ],
    }


@router.get("/momentum")
def run_momentum_screener(db: Session = Depends(get_db)) -> dict:
    """Run momentum screener on all PSX securities."""
    session = MomentumScreener.run_screening(db)

    return {
        "timestamp": session.created_at.isoformat(),
        "freshness": freshness(db, PriceOHLCV),
        "total_screened": session.total_screened,
        "results_count": len(session.signals),
        "signals": [
            {
                "symbol": signal.symbol,
                "name": signal.name,
                "sector": signal.sector,
                "price": signal.price,
                "return_1m": round(signal.return_1m, 2) if signal.return_1m else None,
                "return_3m": round(signal.return_3m, 2) if signal.return_3m else None,
                "return_6m": round(signal.return_6m, 2) if signal.return_6m else None,
                "return_12m": round(signal.return_12m, 2) if signal.return_12m else None,
                "momentum_score": round(signal.momentum_score, 2),
                "strongest_period": signal.strongest_period,
                "trend": signal.trend,
            }
            for signal in session.signals
        ],
    }


@router.get("/technical/filter")
def filter_technical_signals(
    min_score: float = 60,
    above_200dma: bool = True,
    rsi_oversold: bool = False,
    volume_spike: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    """Filter technical signals by criteria."""
    session = TechnicalScreener.run_screening(db)

    filtered = session.signals

    if min_score:
        filtered = [s for s in filtered if s.technical_score >= min_score]

    if above_200dma:
        filtered = [s for s in filtered if s.above_200dma]

    if rsi_oversold:
        filtered = [s for s in filtered if s.rsi and s.rsi < 30]

    if volume_spike:
        filtered = [s for s in filtered if s.volume_spike]

    return {
        "timestamp": session.created_at.isoformat(),
        "freshness": freshness(db, PriceOHLCV),
        "total_screened": session.total_screened,
        "passed_filters": len(filtered),
        "signals": [
            {
                "symbol": signal.symbol,
                "name": signal.name,
                "sector": signal.sector,
                "price": signal.price,
                "change_pct": round(signal.change_pct, 2),
                "price_vs_20dma": round(signal.price_vs_20dma, 2),
                "price_vs_50dma": round(signal.price_vs_50dma, 2),
                "price_vs_200dma": round(signal.price_vs_200dma, 2),
                "rsi": round(signal.rsi, 2) if signal.rsi else None,
                "volume_vs_avg": round(signal.volume_vs_avg, 2),
                "above_200dma": signal.above_200dma,
                "price_near_52week_high": signal.price_near_52week_high,
                "price_near_52week_low": signal.price_near_52week_low,
                "volume_spike": signal.volume_spike,
                "technical_score": round(signal.technical_score, 2),
            }
            for signal in filtered
        ],
    }


@router.get("/momentum/filter")
def filter_momentum_signals(
    min_score: float = 60,
    min_1m_return: float = 0,
    trend: str = None,
    db: Session = Depends(get_db),
) -> dict:
    """Filter momentum signals by criteria."""
    session = MomentumScreener.run_screening(db)

    filtered = session.signals

    if min_score:
        filtered = [s for s in filtered if s.momentum_score >= min_score]

    if min_1m_return:
        filtered = [s for s in filtered if s.return_1m and s.return_1m >= min_1m_return]

    if trend:
        filtered = [s for s in filtered if s.trend == trend]

    return {
        "timestamp": session.created_at.isoformat(),
        "freshness": freshness(db, PriceOHLCV),
        "total_screened": session.total_screened,
        "passed_filters": len(filtered),
        "signals": [
            {
                "symbol": signal.symbol,
                "name": signal.name,
                "sector": signal.sector,
                "price": signal.price,
                "return_1m": round(signal.return_1m, 2) if signal.return_1m else None,
                "return_3m": round(signal.return_3m, 2) if signal.return_3m else None,
                "return_6m": round(signal.return_6m, 2) if signal.return_6m else None,
                "return_12m": round(signal.return_12m, 2) if signal.return_12m else None,
                "momentum_score": round(signal.momentum_score, 2),
                "trend": signal.trend,
            }
            for signal in filtered
        ],
    }
