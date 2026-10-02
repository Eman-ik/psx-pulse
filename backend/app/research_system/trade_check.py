"""Pre-trade checks on a proposed entry/stop/targets, computed only from stored data.

Each gate is PASS, FAIL or UNAVAILABLE with the numbers behind it. There is deliberately no
overall "ready to trade" flag or confidence score: the gates measure different things, and
collapsing them into one yes/no would claim a certainty the evidence doesn't support.
"""

import math
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.data_status import freshness
from app.db.models import FinancialFact, PriceOHLCV, Security, SourceDocument
from app.research_system.technical_screener import TechnicalScreener

MIN_REWARD_RISK = 1.5
MAX_ADV_PARTICIPATION = 0.10  # position at most 10% of 20-day average daily volume
ATR_PERIOD = 14

PASS, FAIL, UNAVAILABLE = "PASS", "FAIL", "UNAVAILABLE"


def _gate(name: str, status: str, detail: str, **evidence) -> dict:
    return {"name": name, "status": status, "detail": detail, "evidence": evidence}


def position_size(entry: float, stop: float, targets: list[float], portfolio_value: float, risk_percent: float) -> dict:
    risk_per_share = entry - stop
    risk_budget = portfolio_value * risk_percent / 100
    shares = math.floor(risk_budget / risk_per_share) if risk_per_share > 0 else 0
    return {
        "risk_budget": round(risk_budget, 2),
        "risk_per_share": round(risk_per_share, 4),
        "shares": shares,
        "capital_required": round(shares * entry, 2),
        "max_loss": round(shares * risk_per_share, 2),
        "allocation_pct": round(shares * entry / portfolio_value * 100, 2),
        "reward_risk": [
            {"target": t, "ratio": round((t - entry) / risk_per_share, 2) if risk_per_share > 0 else None} for t in targets
        ],
    }


def average_true_range(bars: list[PriceOHLCV], period: int = ATR_PERIOD) -> float | None:
    if len(bars) < period + 1:
        return None
    ranges = [
        max(float(b.high) - float(b.low), abs(float(b.high) - float(p.close)), abs(float(b.low) - float(p.close)))
        for p, b in zip(bars[-period - 1:-1], bars[-period:])
    ]
    return sum(ranges) / period


def fundamental_evidence(db: Session, issuer_id: int) -> dict:
    facts = db.execute(
        select(FinancialFact.period_end, FinancialFact.source_document_id)
        .where(FinancialFact.issuer_id == issuer_id, FinancialFact.superseded_by_id.is_(None))
    ).all()
    periods = sorted({f.period_end for f in facts})
    documents = db.execute(
        select(SourceDocument.url, SourceDocument.local_path)
        .where(SourceDocument.id.in_({f.source_document_id for f in facts}))
    ).all()
    latest = periods[-1] if periods else None
    months_old = None if latest is None else (date.today() - latest).days // 30
    if not facts:
        level = "NONE"
    elif len(periods) >= 3 and months_old <= 15:
        level = "HIGH"
    elif len(periods) >= 2 and months_old <= 27:
        level = "MEDIUM"
    else:
        level = "LOW"
    return {
        "level": level,
        "rule": "HIGH: 3+ annual periods, latest within 15 months; MEDIUM: 2+, within 27 months; LOW: anything else on file",
        "facts": len(facts),
        "periods": [p.isoformat() for p in periods],
        "latest_period_months_old": months_old,
        "sources": [d.url or d.local_path for d in documents],
    }


def run_trade_check(
    db: Session, ticker: str, entry: float, stop: float, targets: list[float], portfolio_value: float, risk_percent: float
) -> dict:
    security = db.execute(select(Security).where(Security.symbol == ticker.upper())).scalar_one_or_none()
    if security is None:
        raise LookupError(f"Unknown ticker {ticker}")

    sizing = position_size(entry, stop, targets, portfolio_value, risk_percent)
    data = freshness(db, PriceOHLCV, PriceOHLCV.security_id == security.id)
    bars = list(reversed(db.execute(
        select(PriceOHLCV).where(PriceOHLCV.security_id == security.id).order_by(PriceOHLCV.trade_date.desc()).limit(30)
    ).scalars().all()))
    last_close = float(bars[-1].close) if bars else None

    gates = []

    if not bars:
        gates.append(_gate("DATA", FAIL, "No price history on file.", **data))
    elif data["stale"]:
        gates.append(_gate("DATA", FAIL, f"Latest close is from {data['as_of']}; prices are stale.", **data))
    else:
        gates.append(_gate("DATA", PASS, f"Latest close {last_close} on {data['as_of']}.", last_close=last_close, **data))

    ratios = [r["ratio"] for r in sizing["reward_risk"] if r["ratio"] is not None]
    best = max(ratios) if ratios else None
    if stop >= entry:
        gates.append(_gate("TRADE_STRUCTURE", FAIL, "Stop must be below entry for a long trade."))
    elif not any(t > entry for t in targets):
        gates.append(_gate("TRADE_STRUCTURE", FAIL, "No target is above entry."))
    else:
        status = PASS if best >= MIN_REWARD_RISK else FAIL
        gates.append(_gate("TRADE_STRUCTURE", status, f"Best reward/risk {best}:1 (minimum {MIN_REWARD_RISK}:1).",
                           best_reward_risk=best, minimum=MIN_REWARD_RISK))

    atr = average_true_range(bars)
    if atr is None or stop >= entry:
        gates.append(_gate("STOP_VS_NOISE", UNAVAILABLE, f"Needs {ATR_PERIOD + 1} bars and a stop below entry."))
    else:
        status = PASS if entry - stop >= atr else FAIL
        gates.append(_gate("STOP_VS_NOISE", status,
                           f"Stop is {entry - stop:.2f} below entry; ATR({ATR_PERIOD}) is {atr:.2f}. "
                           + ("A stop inside one day's typical range is likely to be hit by noise." if status == FAIL else ""),
                           stop_distance=round(entry - stop, 4), atr=round(atr, 4)))

    volumes = [b.volume for b in bars[-20:] if b.volume is not None]
    if len(volumes) < 20 or not sum(volumes):
        gates.append(_gate("LIQUIDITY", UNAVAILABLE, "Needs 20 days of reported volume."))
    else:
        adv = sum(volumes) / 20
        participation = sizing["shares"] / adv
        status = PASS if participation <= MAX_ADV_PARTICIPATION else FAIL
        gates.append(_gate("LIQUIDITY", status,
                           f"{sizing['shares']:,} shares is {participation:.1%} of the 20-day average volume ({adv:,.0f}); "
                           f"limit {MAX_ADV_PARTICIPATION:.0%}.",
                           shares=sizing["shares"], average_daily_volume=round(adv), participation=round(participation, 4)))

    if sizing["shares"] == 0:
        gates.append(_gate("RISK_BUDGET", FAIL, "Risk budget is smaller than the risk on one share."))
    elif sizing["capital_required"] > portfolio_value:
        gates.append(_gate("RISK_BUDGET", FAIL, f"Needs {sizing['capital_required']:,.0f}, more than the portfolio value.",
                           **sizing))
    else:
        gates.append(_gate("RISK_BUDGET", PASS,
                           f"Max loss {sizing['max_loss']:,.0f} within a {risk_percent}% budget; uses "
                           f"{sizing['allocation_pct']}% of the portfolio."))

    latest_date = db.execute(select(func.max(PriceOHLCV.trade_date))).scalar()
    technical = TechnicalScreener.screen_security(db, security, latest_date) if latest_date else None

    return {
        "ticker": security.symbol,
        "issuer": security.issuer.name if security.issuer else security.symbol,
        "inputs": {"entry": entry, "stop": stop, "targets": targets, "portfolio_value": portfolio_value,
                   "risk_percent": risk_percent},
        "last_close": last_close,
        "entry_vs_last_close_pct": round((entry - last_close) / last_close * 100, 2) if last_close else None,
        "gates": gates,
        "position_sizing": sizing,
        "technical_context": None if technical is None else {
            "above_20dma": technical.above_20dma, "above_50dma": technical.above_50dma,
            "above_200dma": technical.above_200dma, "rsi": technical.rsi,
            "lookback_high": technical.lookback_high, "lookback_low": technical.lookback_low,
            "lookback_days": technical.lookback_days,
        },
        "fundamental_evidence": fundamental_evidence(db, security.issuer_id),
    }
