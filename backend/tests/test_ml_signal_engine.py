import pandas as pd
import pytest

from app.etl.ml_signal_engine import (
    FEATURE_COLUMNS,
    FUNDAMENTAL_FEATURE_COLUMNS,
    TECHNICAL_FEATURE_COLUMNS,
    ModelConfig,
    SignalModel,
    build_features,
    load_fundamental_panel,
    load_price_panel,
    synthetic_benchmark,
    synthetic_market,
    validate_prices,
    validation_metrics,
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
    row = features[features["symbol"] == "MARI"].dropna(subset=TECHNICAL_FEATURE_COLUMNS + ["target"]).iloc[100]
    symbol_prices = prices[prices["symbol"] == "MARI"].reset_index(drop=True)
    idx = symbol_prices.index[symbol_prices["date"] == row["date"]][0]
    expected_5d = symbol_prices.loc[idx, "close"] / symbol_prices.loc[idx - 5, "close"] - 1
    assert row["return_5d"] == pytest.approx(expected_5d)


def test_build_features_fundamentals_never_leak_before_known_as_of(prices):
    # The whole point of the point-in-time join: a price bar dated BEFORE a fundamental
    # fact's known_as_of must never see that fact's value, only bars on/after it.
    mari_dates = sorted(prices.loc[prices["symbol"] == "MARI", "date"].unique())
    known_as_of = mari_dates[400]
    fundamentals = pd.DataFrame({
        "symbol": ["MARI"],
        "known_as_of": [known_as_of],
        **{col: [42.0] for col in FUNDAMENTAL_FEATURE_COLUMNS},
    })
    features = build_features(prices, fundamentals=fundamentals)
    mari = features[features["symbol"] == "MARI"].sort_values("date")

    before = mari[mari["date"] < known_as_of]
    on_or_after = mari[mari["date"] >= known_as_of]
    assert before["eps_growth_yoy"].isna().all(), "fundamental leaked into a bar before its known_as_of date"
    assert (on_or_after["eps_growth_yoy"] == 42.0).all()


def test_build_features_symbol_with_no_fundamental_coverage_gets_real_nan(prices):
    # Only MARI has a fundamentals row; every other pooled symbol must get real NaN, not a
    # fabricated value or another symbol's data bleeding across via the merge.
    fundamentals = pd.DataFrame({
        "symbol": ["MARI"],
        "known_as_of": [prices["date"].min()],
        **{col: [10.0] for col in FUNDAMENTAL_FEATURE_COLUMNS},
    })
    features = build_features(prices, fundamentals=fundamentals)
    other_symbols = features[features["symbol"] != "MARI"]
    assert other_symbols["roe"].isna().all()


def test_signal_model_fits_with_partial_fundamental_coverage(prices):
    # Real production shape: most pooled symbols have no fundamental coverage at all, one
    # or two do. The imputer must handle that mix without the pipeline crashing or silently
    # dropping the majority of the pool (see TECHNICAL_FEATURE_COLUMNS' role in dropna).
    fundamentals = pd.DataFrame({
        "symbol": ["MARI", "FFC"],
        "known_as_of": [prices["date"].min(), prices["date"].min()],
        **{col: [5.0, -2.0] for col in FUNDAMENTAL_FEATURE_COLUMNS},
    })
    model = SignalModel(fundamentals=fundamentals).fit(prices)
    rankings = model.rank(prices)
    assert len(rankings) == prices["symbol"].nunique()
    assert model.metrics.observations > 0


@pytest.mark.requires_seeded_data
def test_load_price_panel_drops_zero_open_rows_real_data():
    # Real, confirmed artifact (2026-08-27): some illiquid symbols have open=0 on thin-
    # trading days (high/low/close are real, open just wasn't reported). validate_prices()
    # requires every OHLC column strictly positive, so these must never reach build_features.
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        panel = load_price_panel(db)

    assert not panel.empty
    assert (panel["open"] > 0).all()
    assert (panel["high"] > 0).all()
    assert (panel["low"] > 0).all()
    assert (panel["close"] > 0).all()


@pytest.mark.requires_seeded_data
def test_load_fundamental_panel_returns_point_in_time_anchored_real_data():
    # Hits the real dev DB (same convention as test_api_endpoints.py) -- proves the actual
    # ratio_value -> announcement join works against real rows, not just synthetic ones.
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        panel = load_fundamental_panel(db)

    assert not panel.empty
    assert set(panel.columns) == {"symbol", "known_as_of", *FUNDAMENTAL_FEATURE_COLUMNS}
    assert panel["symbol"].nunique() > 0
    # known_as_of must be a real, populated timestamp for every row -- an unanchored ratio
    # should never have made it past load_fundamental_panel's inner-join filtering.
    assert panel["known_as_of"].notna().all()


def test_signal_gate_never_issues_unvalidated_trade(prices):
    # An impossible-to-clear accuracy bar (0.99) should always fall back to HOLD/NO SIGNAL,
    # never fabricate a BUY the walk-forward validation didn't actually earn.
    config = ModelConfig(min_train_days=252, test_days=63, embargo_days=5, minimum_validated_accuracy=0.99)
    model = SignalModel(config).fit(prices)
    assert all(x["signal"] in {"HOLD", "NO SIGNAL"} for x in model.rank(prices))


def test_validation_metrics_flags_precision_that_only_matches_base_rate():
    # 70% of this population beats the benchmark (target=1). A "confident" (p>=0.6) subset
    # of 20 rows with 13 true positives has 65% precision -- clears the engine's old fixed
    # 60% floor, but a random 20-row subset of this same imbalanced population would score
    # 70% by construction. That subset has learned nothing; same trap Kronos's EFERT case
    # caught (60.8% accuracy, "significant" vs. chance, still below its 68.9% naive
    # baseline), one layer down at the precision-vs-base-rate level instead of
    # accuracy-vs-random.
    buy_target = [1] * 13 + [0] * 7          # 20 rows, p>=0.6 -> buy_precision = 13/20 = 0.65
    rest_target = [1] * 57 + [0] * 23         # 80 rows, p=0.5 -> excluded from buy/sell masks
    predictions = pd.DataFrame({
        "target": buy_target + rest_target,
        "probability": [0.65] * 20 + [0.5] * 80,
    })
    metrics = validation_metrics(predictions)
    assert metrics.buy_precision == pytest.approx(0.65)
    assert metrics.positive_rate == pytest.approx(0.70)
    assert metrics.beats_naive_baseline is False


def test_validation_metrics_accepts_precision_genuinely_above_base_rate():
    # Same 70% overall base rate, but the confident subset is 90% precision -- real
    # concentration of true positives above what a random size-matched subset would get.
    buy_target = [1] * 18 + [0] * 2           # 20 rows -> buy_precision = 18/20 = 0.90
    rest_target = [1] * 52 + [0] * 28          # 80 rows, total positives = 70/100 = 0.70
    predictions = pd.DataFrame({
        "target": buy_target + rest_target,
        "probability": [0.65] * 20 + [0.5] * 80,
    })
    metrics = validation_metrics(predictions)
    assert metrics.beats_naive_baseline is True


def test_signal_gate_rejects_precision_that_only_matches_base_rate(prices):
    # Integration-level check: even with buy_precision clearing minimum_validated_accuracy
    # and enough observations, a metrics object that fails beats_naive_baseline must never
    # produce a BUY -- the fix belongs in SignalModel.rank(), not just validation_metrics().
    model = SignalModel().fit(prices)
    model.metrics.buy_precision = 0.65
    model.metrics.positive_rate = 0.70
    model.metrics.beats_naive_baseline = False
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
