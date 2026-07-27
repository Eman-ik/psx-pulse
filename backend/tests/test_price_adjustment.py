from datetime import date

import pytest

from app.db.models import CorporateAction, PriceOHLCV
from app.etl.price_adjustment import apply_adjustment, compute_adjustment_factors


def _bar(trade_date: date, close: float) -> PriceOHLCV:
    return PriceOHLCV(
        security_id=1,
        trade_date=trade_date,
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1000,
        is_delayed=True,
    )


def _dividend(effective_date: date, pct: float) -> CorporateAction:
    return CorporateAction(
        security_id=1,
        action_type="dividend",
        effective_date=effective_date,
        ratio_or_amount=pct,
        currency="PKR_PCT",
    )


def test_single_dividend_scales_only_prior_bars():
    bars = [
        _bar(date(2026, 1, 1), 100.0),
        _bar(date(2026, 1, 2), 102.0),
        _bar(date(2026, 1, 3), 105.0),
    ]
    # 20% of PKR 10 face value = PKR 2/share, ex-dated 2026-01-03; prior close (01-02) is 102.
    actions = [_dividend(date(2026, 1, 3), 20.0)]

    factors = compute_adjustment_factors(bars, actions)

    assert factors[date(2026, 1, 3)] == pytest.approx(1.0)
    assert factors[date(2026, 1, 2)] == pytest.approx(1 - 2 / 102)
    assert factors[date(2026, 1, 1)] == pytest.approx(1 - 2 / 102)

    adjusted = apply_adjustment(bars, actions)
    by_date = {b["date"]: b for b in adjusted}
    assert by_date["2026-01-03"]["close"] == pytest.approx(105.0)
    assert by_date["2026-01-02"]["close"] == pytest.approx(100.0)  # 102 * (100/102)
    assert by_date["2026-01-01"]["close"] == pytest.approx(100 * (1 - 2 / 102))


def test_multiple_dividends_compound_on_earlier_bars():
    bars = [_bar(date(2026, 1, 1), 100.0), _bar(date(2026, 1, 2), 100.0), _bar(date(2026, 1, 3), 105.0)]
    actions = [
        _dividend(date(2026, 1, 2), 10.0),  # PKR 1/share, prior close (01-01) = 100
        _dividend(date(2026, 1, 3), 20.0),  # PKR 2/share, prior close (01-02) = 100
    ]

    factors = compute_adjustment_factors(bars, actions)

    assert factors[date(2026, 1, 3)] == pytest.approx(1.0)
    assert factors[date(2026, 1, 2)] == pytest.approx(1 - 2 / 100)
    # 01-01 is before both ex-dates, so both factors compound
    assert factors[date(2026, 1, 1)] == pytest.approx((1 - 1 / 100) * (1 - 2 / 100))


def test_unsupported_action_type_is_skipped_not_fabricated():
    bars = [_bar(date(2026, 1, 1), 100.0), _bar(date(2026, 1, 2), 100.0)]
    bonus = CorporateAction(
        security_id=1,
        action_type="bonus",
        effective_date=date(2026, 1, 2),
        ratio_or_amount=10.0,
        currency="PKR_PCT",
    )

    factors = compute_adjustment_factors(bars, [bonus])

    assert factors[date(2026, 1, 1)] == pytest.approx(1.0)
    assert factors[date(2026, 1, 2)] == pytest.approx(1.0)


def test_dividend_exceeding_prior_close_is_skipped():
    bars = [_bar(date(2026, 1, 1), 5.0), _bar(date(2026, 1, 2), 5.0)]
    # 100% of PKR 10 face value = PKR 10/share dividend > the PKR 5 prior close: nonsensical, skip.
    actions = [_dividend(date(2026, 1, 2), 100.0)]

    factors = compute_adjustment_factors(bars, actions)

    assert factors[date(2026, 1, 1)] == pytest.approx(1.0)
