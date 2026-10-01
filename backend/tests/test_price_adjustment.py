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
        source="test",
    )


def _dividend(effective_date: date, pct: float) -> CorporateAction:
    return CorporateAction(
        security_id=1,
        action_type="dividend",
        effective_date=effective_date,
        ratio_or_amount=pct,
        currency="PKR_PCT",
    )


def _split(effective_date: date, ratio: float, verified: bool = False) -> CorporateAction:
    return CorporateAction(
        security_id=1,
        action_type="split",
        effective_date=effective_date,
        ratio_or_amount=ratio,
        currency=None,
        verified=verified,
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


def test_split_scales_prior_bars_by_the_observed_price_ratio():
    # KOHC's real 2025-08-25 split: close went 549.99 -> 108.18, ratio ~0.1967 -- see
    # scripts/verify_and_repair_discontinuities.py. A pre-split PKR 549.99 bar should
    # come out comparable to the post-split price level once adjusted.
    bars = [_bar(date(2025, 8, 22), 549.99), _bar(date(2025, 8, 25), 108.18)]
    actions = [_split(date(2025, 8, 25), 0.1967)]

    factors = compute_adjustment_factors(bars, actions)

    assert factors[date(2025, 8, 25)] == pytest.approx(1.0)
    assert factors[date(2025, 8, 22)] == pytest.approx(0.1967)

    adjusted = apply_adjustment(bars, actions)
    by_date = {b["date"]: b for b in adjusted}
    assert by_date["2025-08-22"]["close"] == pytest.approx(549.99 * 0.1967, rel=1e-6)
    assert by_date["2025-08-25"]["close"] == pytest.approx(108.18)


def test_split_and_dividend_compound_on_the_same_prior_bar():
    bars = [_bar(date(2026, 1, 1), 100.0), _bar(date(2026, 1, 5), 100.0), _bar(date(2026, 1, 10), 20.0)]
    actions = [
        _dividend(date(2026, 1, 5), 10.0),  # PKR 1/share, prior close (01-01) = 100
        _split(date(2026, 1, 10), 0.2),  # 5-for-1-shaped, applies to every bar before it
    ]

    factors = compute_adjustment_factors(bars, actions)

    assert factors[date(2026, 1, 10)] == pytest.approx(1.0)
    # 01-05 is before the split only
    assert factors[date(2026, 1, 5)] == pytest.approx(0.2)
    # 01-01 is before both the dividend and the split -- both factors compound
    assert factors[date(2026, 1, 1)] == pytest.approx((1 - 1 / 100) * 0.2)


def test_split_with_null_ratio_is_skipped_not_treated_as_zero():
    bars = [_bar(date(2026, 1, 1), 100.0), _bar(date(2026, 1, 2), 100.0)]
    bad_split = CorporateAction(
        security_id=1, action_type="split", effective_date=date(2026, 1, 2),
        ratio_or_amount=None, currency=None, verified=False,
    )

    factors = compute_adjustment_factors(bars, [bad_split])

    assert factors[date(2026, 1, 1)] == pytest.approx(1.0)
