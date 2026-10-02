"""Technical and momentum screeners. Indicators without enough history are null, and
filters never treat null as a match."""

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.data_status import freshness
from app.db.models import PriceOHLCV
from app.db.session import get_db
from app.research_system.momentum_screener import MAX_ANCHOR_GAP_DAYS, MomentumScreener
from app.research_system.technical_screener import TechnicalScreener

router = APIRouter(prefix="/screeners", tags=["screeners"])


def _rounded(signal) -> dict:
    return {k: round(v, 2) if isinstance(v, float) else v for k, v in asdict(signal).items()}


def _response(db: Session, session, signals, **extra) -> dict:
    return {
        "timestamp": session.created_at.isoformat(),
        "freshness": freshness(db, PriceOHLCV),
        "total_screened": session.total_screened,
        "results_count": len(signals),
        **extra,
        "signals": [_rounded(s) for s in signals],
    }


@router.get("/technical")
def run_technical_screener(db: Session = Depends(get_db)) -> dict:
    session = TechnicalScreener.run_screening(db)
    return _response(db, session, session.signals)


@router.get("/technical/filter")
def filter_technical_signals(
    above_200dma: bool = True,
    rsi_oversold: bool = False,
    volume_spike: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    session = TechnicalScreener.run_screening(db)
    filtered = [
        s for s in session.signals
        if (not above_200dma or s.above_200dma is True)
        and (not rsi_oversold or (s.rsi is not None and s.rsi < 30))
        and (not volume_spike or s.volume_spike is True)
    ]
    return _response(db, session, filtered, passed_filters=len(filtered))


@router.get("/momentum")
def run_momentum_screener(db: Session = Depends(get_db)) -> dict:
    session = MomentumScreener.run_screening(db)
    return _response(db, session, session.signals, max_anchor_gap_days=MAX_ANCHOR_GAP_DAYS)


@router.get("/momentum/filter")
def filter_momentum_signals(
    min_1m_return: float | None = None,
    min_12_1_momentum: float | None = None,
    db: Session = Depends(get_db),
) -> dict:
    session = MomentumScreener.run_screening(db)
    filtered = [
        s for s in session.signals
        if (min_1m_return is None or (s.return_1m is not None and s.return_1m >= min_1m_return))
        and (min_12_1_momentum is None or (s.momentum_12_1 is not None and s.momentum_12_1 >= min_12_1_momentum))
    ]
    return _response(db, session, filtered, passed_filters=len(filtered), max_anchor_gap_days=MAX_ANCHOR_GAP_DAYS)
