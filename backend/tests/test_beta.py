from datetime import date, timedelta

import pytest

from app.etl.beta import MIN_OVERLAPPING_DAYS, compute_beta_from_bars, daily_returns

# A varied return sequence (not constant, so variance is non-degenerate), long enough to clear
# MIN_OVERLAPPING_DAYS after the first bar is consumed as the "previous close" baseline.
_MARKET_RETURNS = [0.01, -0.008, 0.015, -0.02, 0.005, 0.012, -0.011, 0.003, -0.004, 0.018] * 7


def _prices_from_returns(start_price: float, returns: list[float], start_date: date) -> list[tuple[date, float]]:
    bars = [(start_date, start_price)]
    price = start_price
    for i, r in enumerate(returns, start=1):
        price = price * (1 + r)
        bars.append((start_date + timedelta(days=i), price))
    return bars


def test_daily_returns_basic():
    bars = [(date(2024, 1, 1), 100.0), (date(2024, 1, 2), 110.0), (date(2024, 1, 3), 99.0)]
    returns = daily_returns(bars)
    assert returns[date(2024, 1, 2)] == pytest.approx(0.10)
    assert returns[date(2024, 1, 3)] == pytest.approx(-0.10)


def test_beta_of_two_when_company_moves_exactly_double_the_market():
    market_bars = _prices_from_returns(100.0, _MARKET_RETURNS, date(2024, 1, 1))
    company_returns = [2 * r for r in _MARKET_RETURNS]
    company_bars = _prices_from_returns(50.0, company_returns, date(2024, 1, 1))

    result = compute_beta_from_bars(company_bars, market_bars)

    assert result is not None
    assert result["beta"] == pytest.approx(2.0, abs=1e-9)
    assert result["n_days"] == len(_MARKET_RETURNS)


def test_beta_of_one_when_company_tracks_market_exactly():
    market_bars = _prices_from_returns(100.0, _MARKET_RETURNS, date(2024, 1, 1))
    company_bars = _prices_from_returns(25.0, _MARKET_RETURNS, date(2024, 1, 1))

    result = compute_beta_from_bars(company_bars, market_bars)

    assert result is not None
    assert result["beta"] == pytest.approx(1.0, abs=1e-9)


def test_negative_beta_when_company_moves_inversely():
    market_bars = _prices_from_returns(100.0, _MARKET_RETURNS, date(2024, 1, 1))
    inverse_returns = [-r for r in _MARKET_RETURNS]
    company_bars = _prices_from_returns(75.0, inverse_returns, date(2024, 1, 1))

    result = compute_beta_from_bars(company_bars, market_bars)

    assert result is not None
    assert result["beta"] == pytest.approx(-1.0, abs=1e-9)


def test_insufficient_overlapping_history_returns_none():
    short_returns = _MARKET_RETURNS[: MIN_OVERLAPPING_DAYS - 1]
    market_bars = _prices_from_returns(100.0, short_returns, date(2024, 1, 1))
    company_bars = _prices_from_returns(50.0, short_returns, date(2024, 1, 1))

    assert compute_beta_from_bars(company_bars, market_bars) is None


def test_no_date_overlap_returns_none():
    market_bars = _prices_from_returns(100.0, _MARKET_RETURNS, date(2024, 1, 1))
    # Company history from a completely different, non-overlapping calendar period.
    company_bars = _prices_from_returns(50.0, _MARKET_RETURNS, date(2020, 1, 1))

    assert compute_beta_from_bars(company_bars, market_bars) is None
