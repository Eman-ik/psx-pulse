from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

REQUIRED_COLUMNS = {"date", "symbol", "open", "high", "low", "close", "volume", "benchmark_close"}
FEATURE_COLUMNS = [
    "return_5d", "return_21d", "return_63d", "relative_21d", "relative_63d",
    "ma_gap_20", "ma_gap_50", "rsi_14", "atr_pct", "volatility_21d",
    "volume_z_21d", "drawdown_63d", "breakout_63d",
]


@dataclass(frozen=True)
class ModelConfig:
    horizon_days: int = 5
    excess_return_threshold: float = 0.0
    transaction_cost: float = 0.004
    min_train_days: int = 504
    test_days: int = 126
    embargo_days: int = 5
    buy_probability: float = 0.60
    sell_probability: float = 0.40
    minimum_validated_accuracy: float = 0.60
    minimum_observations: int = 30


@dataclass
class ValidationMetrics:
    observations: int
    accuracy: float
    buy_precision: float
    sell_precision: float
    brier_score: float
    roc_auc: float | None


def validate_prices(frame: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required price columns: {sorted(missing)}")
    out = frame.copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise")
    out["symbol"] = out["symbol"].astype(str).str.upper().str.strip()
    numeric = ["open", "high", "low", "close", "volume", "benchmark_close"]
    out[numeric] = out[numeric].apply(pd.to_numeric, errors="coerce")
    if out[numeric].isna().any().any():
        raise ValueError("OHLCV and benchmark values must be numeric and non-null")
    if (out[["open", "high", "low", "close", "benchmark_close"]] <= 0).any().any():
        raise ValueError("Prices must be positive")
    if (out["volume"] < 0).any():
        raise ValueError("Volume cannot be negative")
    if out.duplicated(["date", "symbol"]).any():
        raise ValueError("Duplicate date/symbol rows found")
    return out.sort_values(["symbol", "date"]).reset_index(drop=True)


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    return 100 - 100 / (1 + gain / loss.replace(0, np.nan))


def build_features(prices: pd.DataFrame, config: ModelConfig = ModelConfig()) -> pd.DataFrame:
    """Build backward-looking features and forward excess-return labels.

    Fundamental fields can be joined before this call only when keyed by their
    public announcement date. They are deliberately excluded from the first
    baseline until a licensed point-in-time dataset is supplied.
    """
    df = validate_prices(prices)
    groups: list[pd.DataFrame] = []
    for _, g in df.groupby("symbol", sort=False):
        g = g.copy().sort_values("date")
        close, bench = g["close"], g["benchmark_close"]
        previous = close.shift(1)
        true_range = pd.concat([
            g["high"] - g["low"],
            (g["high"] - previous).abs(),
            (g["low"] - previous).abs(),
        ], axis=1).max(axis=1)
        returns = close.pct_change()
        for days in (5, 21, 63):
            g[f"return_{days}d"] = close.pct_change(days)
        g["relative_21d"] = g["return_21d"] - bench.pct_change(21)
        g["relative_63d"] = g["return_63d"] - bench.pct_change(63)
        g["ma_gap_20"] = close / close.rolling(20).mean() - 1
        g["ma_gap_50"] = close / close.rolling(50).mean() - 1
        g["rsi_14"] = _rsi(close) / 100
        g["atr_pct"] = true_range.rolling(14).mean() / close
        g["volatility_21d"] = returns.rolling(21).std() * np.sqrt(252)
        volume_mean = g["volume"].rolling(21).mean()
        volume_std = g["volume"].rolling(21).std().replace(0, np.nan)
        g["volume_z_21d"] = (g["volume"] - volume_mean) / volume_std
        g["drawdown_63d"] = close / close.rolling(63).max() - 1
        g["breakout_63d"] = close / close.shift(1).rolling(63).max() - 1
        stock_forward = close.shift(-config.horizon_days) / close - 1
        bench_forward = bench.shift(-config.horizon_days) / bench - 1
        g["forward_stock_return"] = stock_forward
        g["forward_benchmark_return"] = bench_forward
        # The research target answers one clean question: did the stock beat
        # the benchmark over the next five sessions? Trading costs remain a
        # separate signal-qualification constraint and do not redefine truth.
        g["forward_excess_return"] = stock_forward - bench_forward
        g["net_forward_excess_return"] = g["forward_excess_return"] - config.transaction_cost
        g["target"] = (g["forward_excess_return"] > config.excess_return_threshold).astype(float)
        g.loc[g["forward_excess_return"].isna(), "target"] = np.nan
        groups.append(g)
    return pd.concat(groups, ignore_index=True).replace([np.inf, -np.inf], np.nan)


def _base_model() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(C=0.35, class_weight="balanced", max_iter=2000)),
    ])


def walk_forward_predictions(features: pd.DataFrame, config: ModelConfig = ModelConfig()) -> pd.DataFrame:
    labelled = features.dropna(subset=FEATURE_COLUMNS + ["target"]).sort_values("date")
    dates = np.array(sorted(labelled["date"].unique()))
    if len(dates) < config.min_train_days + config.embargo_days + config.test_days:
        raise ValueError(
            f"Need at least {config.min_train_days + config.embargo_days + config.test_days} "
            f"trading dates; received {len(dates)}"
        )
    outputs: list[pd.DataFrame] = []
    cursor = config.min_train_days + config.embargo_days
    while cursor < len(dates):
        test_dates = dates[cursor: cursor + config.test_days]
        cutoff = dates[cursor - config.embargo_days]
        train = labelled[labelled["date"] < cutoff]
        test = labelled[labelled["date"].isin(test_dates)]
        if train["target"].nunique() < 2 or test.empty:
            cursor += config.test_days
            continue
        model = _base_model().fit(train[FEATURE_COLUMNS], train["target"].astype(int))
        fold = test[["date", "symbol", "target", "forward_excess_return", "net_forward_excess_return"]].copy()
        fold["probability"] = model.predict_proba(test[FEATURE_COLUMNS])[:, 1]
        outputs.append(fold)
        cursor += config.test_days
    if not outputs:
        raise ValueError("Walk-forward validation produced no eligible folds")
    return pd.concat(outputs, ignore_index=True)


def validation_metrics(predictions: pd.DataFrame) -> ValidationMetrics:
    y = predictions["target"].astype(int).to_numpy()
    p = predictions["probability"].to_numpy()
    predicted = (p >= 0.5).astype(int)
    auc = float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None
    buy_mask, sell_mask = p >= 0.6, p <= 0.4
    buy_precision = precision_score(y[buy_mask], np.ones(buy_mask.sum()), zero_division=0) if buy_mask.any() else 0.0
    sell_precision = precision_score(1 - y[sell_mask], np.ones(sell_mask.sum()), zero_division=0) if sell_mask.any() else 0.0
    return ValidationMetrics(
        observations=len(y), accuracy=float(accuracy_score(y, predicted)),
        buy_precision=float(buy_precision), sell_precision=float(sell_precision),
        brier_score=float(brier_score_loss(y, p)), roc_auc=auc,
    )


class SignalModel:
    def __init__(self, config: ModelConfig = ModelConfig()):
        self.config = config
        self.model: CalibratedClassifierCV | None = None
        self.metrics: ValidationMetrics | None = None

    def fit(self, prices: pd.DataFrame) -> "SignalModel":
        features = build_features(prices, self.config)
        predictions = walk_forward_predictions(features, self.config)
        self.metrics = validation_metrics(predictions)
        labelled = features.dropna(subset=FEATURE_COLUMNS + ["target"])
        # Calibration uses a later, disjoint time block. The embargo prevents
        # overlapping forward-return labels from leaking into calibration.
        dates = np.array(sorted(labelled["date"].unique()))
        calibration_start = int(len(dates) * 0.8)
        train_end = calibration_start - self.config.embargo_days
        train = labelled[labelled["date"].isin(dates[:train_end])]
        calibration = labelled[labelled["date"].isin(dates[calibration_start:])]
        if train["target"].nunique() < 2 or calibration["target"].nunique() < 2:
            raise ValueError("Training and calibration periods must contain both target classes")
        fitted = _base_model().fit(train[FEATURE_COLUMNS], train["target"].astype(int))
        self.model = CalibratedClassifierCV(FrozenEstimator(fitted), method="sigmoid")
        self.model.fit(calibration[FEATURE_COLUMNS], calibration["target"].astype(int))
        return self

    def rank(self, prices: pd.DataFrame) -> list[dict]:
        if self.model is None or self.metrics is None:
            raise RuntimeError("Model must be fitted before ranking")
        features = build_features(prices, self.config)
        latest = features.dropna(subset=FEATURE_COLUMNS).sort_values("date").groupby("symbol").tail(1).copy()
        latest["probability"] = self.model.predict_proba(latest[FEATURE_COLUMNS])[:, 1]
        eligible = self.metrics.observations >= self.config.minimum_observations
        # This first classifier estimates only the probability of clearing the
        # positive excess-return hurdle. A low probability is not evidence of a
        # negative return, so SELL is withheld until a separate downside model
        # is fitted and validated.
        validated_accuracy = self.metrics.buy_precision
        records = []
        for row in latest.itertuples():
            probability = float(row.probability)
            signal = "NO SIGNAL"
            if eligible and validated_accuracy >= self.config.minimum_validated_accuracy:
                if probability >= self.config.buy_probability and self.metrics.buy_precision >= self.config.minimum_validated_accuracy:
                    signal = "BUY"
                else:
                    signal = "HOLD"
            auc_confidence = 0.5 if self.metrics.roc_auc is None else 0.5 + max(0.0, self.metrics.roc_auc - 0.5) * 2
            records.append({
                "symbol": row.symbol, "as_of": row.date.date().isoformat(), "price": round(float(row.close), 2),
                "signal": signal, "outperformance_probability": round(probability, 4),
                "evidence_confidence": round(float(min(0.95, auc_confidence)), 4),
                "validated_buy_precision": round(self.metrics.buy_precision, 4),
                "validated_sell_precision": round(self.metrics.sell_precision, 4),
                "validation_observations": self.metrics.observations,
            })
        return sorted(records, key=lambda x: x["outperformance_probability"], reverse=True)

    def save(self, directory: str | Path) -> None:
        if self.model is None or self.metrics is None:
            raise RuntimeError("Cannot save an unfitted model")
        path = Path(directory); path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path / "signal_model.joblib")
        (path / "metadata.json").write_text(json.dumps({
            "config": asdict(self.config), "metrics": asdict(self.metrics),
            "features": FEATURE_COLUMNS, "model_type": "calibrated_logistic_regression",
        }, indent=2), encoding="utf-8")


def synthetic_market(symbols: Iterable[str] = ("MARI", "SYS", "FFC", "HBL", "LUCK", "OGDC"), days: int = 720, seed: int = 42) -> pd.DataFrame:
    """Deterministic development data. Never presented as live market data."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    benchmark_returns = rng.normal(0.00035, 0.011, days)
    benchmark = 100_000 * np.cumprod(1 + benchmark_returns)
    rows = []
    for index, symbol in enumerate(symbols):
        factor = (index - 2.5) * 0.00008
        returns = 0.65 * benchmark_returns + rng.normal(0.00025 + factor, 0.014 + index * 0.0004, days)
        close = (80 + index * 35) * np.cumprod(1 + returns)
        open_ = close * (1 + rng.normal(0, 0.004, days))
        spread = np.abs(rng.normal(0.01, 0.004, days))
        volume = rng.lognormal(14.2 + index * 0.08, 0.45, days).astype(int)
        for i, date in enumerate(dates):
            rows.append({"date": date, "symbol": symbol, "open": open_[i], "high": max(open_[i], close[i]) * (1 + spread[i]), "low": min(open_[i], close[i]) * (1 - spread[i]), "close": close[i], "volume": volume[i], "benchmark_close": benchmark[i]})
    return pd.DataFrame(rows)
