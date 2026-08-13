import pandas as pd
import pytest

from app.etl.ml_signal_engine import (
    FEATURE_COLUMNS,
    ModelConfig,
    SignalModel,
    build_features,
    synthetic_benchmark,
    synthetic_market,
    validate_prices,
)


@pytest.fixture(scope="module")
def prices() -> pd.DataFrame:
    return synthetic_market(days=800)


def test_validate_prices_rejects_duplicate_observations(prices):
    bad = pd.concat([prices, prices.iloc[[0]]])
    with pytest.raises(ValueError, match="Duplicate"):
        validate_prices(bad)


def test_validate_prices_rejects_non_positive_prices(prices):
    bad = prices.copy()
    bad.loc[0, "close"] = 0
    with pytest.raises(ValueError, match="positive"):
        validate_prices(bad)


def test_validate_prices_rejects_missing_columns(prices):
    with pytest.raises(ValueError, match="Missing required price columns"):
        validate_prices(prices.drop(columns=["benchmark_close"]))


def test_features_use_past_and_labels_use_future(prices):
    features = build_features(prices)
    row = features[features["symbol"] == "MARI"].dropna(subset=FEATURE_COLUMNS + ["target"]).iloc[100]
    symbol_prices = prices[prices["symbol"] == "MARI"].reset_index(drop=True)
    idx = symbol_prices.index[symbol_prices["date"] == row["date"]][0]
    expected_5d = symbol_prices.loc[idx, "close"] / symbol_prices.loc[idx - 5, "close"] - 1
    assert row["return_5d"] == pytest.approx(expected_5d)


def test_signal_gate_never_issues_unvalidated_trade(prices):
    # An impossible-to-clear accuracy bar (0.99) should always fall back to HOLD/NO SIGNAL,
    # never fabricate a BUY the walk-forward validation didn't actually earn.
    config = ModelConfig(min_train_days=252, test_days=63, embargo_days=5, minimum_validated_accuracy=0.99)
    model = SignalModel(config).fit(prices)
    assert all(x["signal"] in {"HOLD", "NO SIGNAL"} for x in model.rank(prices))


def test_signal_never_sell(prices):
    # This classifier only estimates upside probability -- SELL must never appear.
    model = SignalModel().fit(prices)
    assert all(x["signal"] != "SELL" for x in model.rank(prices))


def test_probabilities_are_valid(prices):
    model = SignalModel().fit(prices)
    values = [x["outperformance_probability"] for x in model.rank(prices)]
    assert all(0 <= x <= 1 for x in values)


def test_walk_forward_raises_on_insufficient_history():
    short_prices = synthetic_market(days=100)
    with pytest.raises(ValueError, match="trading dates"):
        SignalModel().fit(short_prices)


def test_synthetic_benchmark_is_positive_and_starts_at_base_level():
    prices = synthetic_market(days=100)
    benchmark = synthetic_benchmark(prices, base_level=100_000.0)
    assert (benchmark > 0).all()
    assert benchmark.iloc[0] == pytest.approx(100_000.0)


def test_synthetic_benchmark_averages_across_symbols_not_one_dominant_name():
    # Build two symbols with opposite trends; the benchmark should land between them, not track
    # either one exactly -- proof it's actually averaging, not silently picking one symbol.
    dates = pd.bdate_range("2024-01-01", periods=30)
    up = pd.DataFrame({
        "date": dates, "symbol": "UP", "open": 100, "high": 101, "low": 99,
        "close": [100 * (1.01 ** i) for i in range(30)], "volume": 1000, "benchmark_close": 1,
    })
    down = pd.DataFrame({
        "date": dates, "symbol": "DOWN", "open": 100, "high": 101, "low": 99,
        "close": [100 * (0.99 ** i) for i in range(30)], "volume": 1000, "benchmark_close": 1,
    })
    combined = pd.concat([up, down], ignore_index=True)
    benchmark = synthetic_benchmark(combined)
    assert benchmark.iloc[-1] != pytest.approx(up.iloc[-1]["close"] / up.iloc[0]["close"] * 100_000.0, rel=1e-3)
    assert benchmark.iloc[-1] != pytest.approx(down.iloc[-1]["close"] / down.iloc[0]["close"] * 100_000.0, rel=1e-3)
