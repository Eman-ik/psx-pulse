"""Horizon sweep for the ML signal engine's pooled classifier.

Same pooled universe, same features (return/momentum/relative-strength/RSI/ATR/
volatility/volume-z/drawdown/breakout -- see FEATURE_COLUMNS in ml_signal_engine.py,
this was never a raw-OHLCV baseline), same walk-forward methodology and model
(calibrated logistic regression) -- only horizon_days varies. This is the cheapest,
highest-signal experiment before reaching for better features or a bigger model:
if 5-day has no real edge, a different horizon might, or none will -- either way
it's a real answer instead of a guess.

Read-only: computes validation metrics only, never writes MlSignalScore rows.

Run with: backend/.venv/Scripts/python.exe scripts/horizon_sweep.py
"""

import logging
from dataclasses import replace
from datetime import date

from app.db.session import SessionLocal
from app.etl.ml_signal_engine import (
    ModelConfig,
    attach_benchmark,
    build_features,
    load_price_panel,
    validation_metrics,
    walk_forward_predictions,
)

logging.basicConfig(level=logging.WARNING)

HORIZONS_DAYS = [1, 3, 5, 10, 20]


def main() -> None:
    with SessionLocal() as db:
        base_config = ModelConfig()
        # Eligibility (min_train_days+embargo+test_days) doesn't depend on horizon_days,
        # so one panel load and one benchmark attach covers every horizon in the sweep.
        panel = load_price_panel(db, config=base_config, as_of=date.today())
        if panel.empty:
            print("No securities met the history/staleness thresholds -- nothing to sweep.")
            return
        print(f"Loaded price panel: {panel['symbol'].nunique()} symbols, {len(panel)} rows\n")
        priced = attach_benchmark(panel)

        print(f"{'Horizon':>8} {'N':>7} {'Accuracy':>9} {'BuyPrec':>8} {'SellPrec':>9} {'Brier':>7} {'ROC AUC':>8}")
        for h in HORIZONS_DAYS:
            config = replace(base_config, horizon_days=h)
            try:
                features = build_features(priced, config)
                predictions = walk_forward_predictions(features, config)
                metrics = validation_metrics(predictions)
            except ValueError as exc:
                print(f"{h:>7}d  -- could not fit: {exc}")
                continue
            auc = f"{metrics.roc_auc:.3f}" if metrics.roc_auc is not None else "n/a"
            print(
                f"{h:>7}d {metrics.observations:>7} {metrics.accuracy * 100:>8.1f}% "
                f"{metrics.buy_precision * 100:>7.1f}% {metrics.sell_precision * 100:>8.1f}% "
                f"{metrics.brier_score:>7.4f} {auc:>8}"
            )


if __name__ == "__main__":
    main()
