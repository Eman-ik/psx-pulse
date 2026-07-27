import pytest

from app.etl.signal_engine import compose_signal, peer_relative_score


def test_peer_relative_score_at_peer_mean_is_neutral():
    assert peer_relative_score(value=10.0, peer_mean=10.0, higher_is_better=True) == pytest.approx(50.0)
    assert peer_relative_score(value=10.0, peer_mean=10.0, higher_is_better=False) == pytest.approx(50.0)


def test_peer_relative_score_above_mean_scores_higher_when_higher_is_better():
    # 20% above the peer mean, capped deviation of 0.2 -> 50 + 0.2*50 = 60
    assert peer_relative_score(value=12.0, peer_mean=10.0, higher_is_better=True) == pytest.approx(60.0)


def test_peer_relative_score_direction_flips_for_lower_is_better_metrics():
    # Same 20%-above-mean value, but for a metric where lower is better (e.g. P/E): should
    # score BELOW 50, not above -- being expensive relative to peers is bearish, not bullish.
    assert peer_relative_score(value=12.0, peer_mean=10.0, higher_is_better=False) == pytest.approx(40.0)


def test_peer_relative_score_deviation_is_capped_at_100_percent():
    # 10x the peer mean would naively blow past the 0-100 scale; must clamp instead.
    assert peer_relative_score(value=100.0, peer_mean=10.0, higher_is_better=True) == pytest.approx(100.0)
    assert peer_relative_score(value=-100.0, peer_mean=10.0, higher_is_better=True) == pytest.approx(0.0)


def test_compose_signal_averages_only_available_dimensions():
    # 3 of 5 dimensions present, well above the mandatory-suppressor floor.
    dims = {"quality": 80.0, "growth": 80.0, "financial_health": 80.0, "valuation": None, "catalyst_risk": None}
    result = compose_signal(dims, is_delisted=False)
    assert result["suppressed"] is False
    assert result["composite_score"] == pytest.approx(80.0)
    assert result["composite_signal"] == "strong_buy"


def test_compose_signal_suppressed_when_too_few_dimensions():
    dims = {"quality": 90.0, "growth": None, "financial_health": None, "valuation": None, "catalyst_risk": None}
    result = compose_signal(dims, is_delisted=False)
    assert result["suppressed"] is True
    assert result["composite_signal"] == "no_signal"
    assert "score dimensions" in result["suppression_reasons"][0]


def test_compose_signal_suppressed_when_delisted_even_with_full_data():
    dims = {"quality": 90.0, "growth": 90.0, "financial_health": 90.0, "valuation": 90.0, "catalyst_risk": 90.0}
    result = compose_signal(dims, is_delisted=True)
    assert result["suppressed"] is True
    assert result["composite_signal"] == "no_signal"
    assert any("delisted" in r for r in result["suppression_reasons"])


@pytest.mark.parametrize(
    "score,expected_label",
    [(90, "strong_buy"), (65, "buy"), (50, "hold"), (30, "sell"), (10, "strong_sell")],
)
def test_compose_signal_thresholds(score, expected_label):
    dims = {"quality": score, "growth": score, "financial_health": None, "valuation": None, "catalyst_risk": None}
    result = compose_signal(dims, is_delisted=False)
    assert result["composite_signal"] == expected_label
