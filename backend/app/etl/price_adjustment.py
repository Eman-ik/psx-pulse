"""Corporate-action-adjusted price series.

Backward multiplicative adjustment — the same "adjusted close" methodology most price vendors
use: for each corporate action, every bar strictly before its effective date is scaled by a
factor derived from the actual (raw) close on the last trading day before that date, so a chart
of adjusted prices shows total return instead of an artificial cliff on the ex-date.

v1 only handles cash dividends with currency == "PKR_PCT" (PSX's own convention: percentage of
the PKR 10 ordinary-share face value) since that's the only corporate-action type actually
ingested so far (app/ingestion/psx_payouts.py — no bonus/rights/split rows exist in this pilot's
data yet). Bonus/rights/split events use a different formula entirely (they change share count,
not just cash-out value); an unsupported action type is skipped with a warning rather than
adjusted for using the wrong math, so a future bonus issue doesn't get silently mishandled.
"""

import logging
from datetime import date
from typing import Sequence

from app.db.models import CorporateAction, PriceOHLCV

logger = logging.getLogger(__name__)

FACE_VALUE_PKR = 10.0  # standard PSX ordinary-share face/par value; dividends are quoted as a % of this


def _dividend_adjustment_factor(action: CorporateAction, prev_close: float) -> float | None:
    if action.ratio_or_amount is None or prev_close <= 0:
        return None
    dividend_per_share = float(action.ratio_or_amount) * FACE_VALUE_PKR / 100
    if dividend_per_share >= prev_close:
        logger.warning(
            "Dividend PKR %.2f on %s exceeds/equals prior close PKR %.2f for security %s — skipping "
            "adjustment for this event rather than producing a negative/zero factor",
            dividend_per_share,
            action.effective_date,
            prev_close,
            action.security_id,
        )
        return None
    return 1 - dividend_per_share / prev_close


def compute_adjustment_factors(
    bars: Sequence[PriceOHLCV], actions: Sequence[CorporateAction]
) -> dict[date, float]:
    """Per trade_date, the cumulative multiplier to apply to that bar's raw OHLC.

    A bar dated on or after an action's effective_date is unaffected by that action (it's
    already "ex"); only strictly earlier bars get scaled. Multiple events compound: an old bar
    is multiplied by the factor of every dividend that happened after it.
    """
    sorted_bars = sorted(bars, key=lambda b: b.trade_date)
    factors_by_date: dict[date, float] = {b.trade_date: 1.0 for b in sorted_bars}

    for action in sorted(actions, key=lambda a: a.effective_date):
        if action.action_type != "dividend" or action.currency != "PKR_PCT":
            logger.info(
                "Skipping unsupported corporate action for price adjustment: %s on %s "
                "(only PKR_PCT dividends are handled in v1)",
                action.action_type,
                action.effective_date,
            )
            continue

        prior_bars = [b for b in sorted_bars if b.trade_date < action.effective_date]
        if not prior_bars:
            continue
        prev_close = float(prior_bars[-1].close)

        factor = _dividend_adjustment_factor(action, prev_close)
        if factor is None:
            continue

        for b in prior_bars:
            factors_by_date[b.trade_date] *= factor

    return factors_by_date


def apply_adjustment(bars: Sequence[PriceOHLCV], actions: Sequence[CorporateAction]) -> list[dict]:
    """Returns adjusted bars as plain dicts, one per input bar, each carrying its own factor
    so a caller can tell exactly how much (if any) adjustment was applied to that date.
    """
    factors = compute_adjustment_factors(bars, actions)
    result = []
    for b in sorted(bars, key=lambda x: x.trade_date):
        factor = factors[b.trade_date]
        result.append(
            {
                "date": b.trade_date.isoformat(),
                "open": float(b.open) * factor,
                "high": float(b.high) * factor,
                "low": float(b.low) * factor,
                "close": float(b.close) * factor,
                "volume": b.volume,
                "is_delayed": b.is_delayed,
                "adjustment_factor": factor,
            }
        )
    return result
