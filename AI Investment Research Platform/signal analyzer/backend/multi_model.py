from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import brier_score_loss, mean_absolute_error, mean_squared_error, precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .quant_engine import ModelConfig
from .feature_engine import EXTENDED_FEATURE_COLUMNS, build_panel_dataset

MODEL_FEATURES = EXTENDED_FEATURE_COLUMNS


@dataclass(frozen=True)
class MultiModelConfig:
    downside_threshold: float = -0.05
    buy_outperformance_probability: float = 0.60
    maximum_downside_probability: float = 0.20
    minimum_expected_excess_return: float = 0.004
    minimum_direction_precision: float = 0.60
    minimum_risk_precision: float = 0.60


@dataclass
class MultiModelMetrics:
    observations: int
    direction_auc: float
    direction_brier: float
    direction_buy_precision: float
    regression_mae: float
    regression_rmse: float
    regression_spearman_ic: float
    downside_auc: float
    downside_brier: float
    downside_alert_precision: float
    downside_base_rate: float


def _classifier() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(C=0.35, class_weight="balanced", max_iter=2000)),
    ])


def _regressor() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", Ridge(alpha=12.0)),
    ])


def _safe_auc(y: np.ndarray, probability: np.ndarray) -> float:
    return float(roc_auc_score(y, probability)) if len(np.unique(y)) == 2 else 0.5


def walk_forward_three_models(features: pd.DataFrame, config: ModelConfig) -> pd.DataFrame:
    required = ["return_60d", "target_direction", "target_5d_excess_return", "target_5d_return", "target_downside"]
    labelled = features.dropna(subset=required).sort_values("date").copy()
    dates = np.array(sorted(labelled["date"].unique()))
    minimum = config.min_train_days + config.embargo_days + config.test_days
    if len(dates) < minimum:
        raise ValueError(f"Need at least {minimum} dates; received {len(dates)}")
    outputs: list[pd.DataFrame] = []
    cursor = config.min_train_days + config.embargo_days
    while cursor < len(dates):
        cutoff = dates[cursor - config.embargo_days]
        test_dates = dates[cursor:cursor + config.test_days]
        train = labelled[labelled["date"] < cutoff]
        test = labelled[labelled["date"].isin(test_dates)]
        if test.empty or train["target_direction"].nunique() < 2:
            cursor += config.test_days
            continue
        direction = _classifier().fit(train[MODEL_FEATURES], train["target_direction"].astype(int))
        magnitude = _regressor().fit(train[MODEL_FEATURES], train["target_5d_excess_return"])
        train_downside = train["target_downside"].astype(int)
        if train_downside.nunique() < 2:
            cursor += config.test_days
            continue
        risk = _classifier().fit(train[MODEL_FEATURES], train_downside)
        fold = test[["date", "symbol", "target_direction", "target_5d_excess_return", "target_5d_return", "target_downside"]].copy()
        fold = fold.rename(columns={"target_direction":"target", "target_5d_excess_return":"forward_excess_return", "target_5d_return":"forward_stock_return", "target_downside":"downside_target"})
        fold["outperformance_probability"] = direction.predict_proba(test[MODEL_FEATURES])[:, 1]
        fold["expected_excess_return"] = magnitude.predict(test[MODEL_FEATURES])
        fold["downside_probability"] = risk.predict_proba(test[MODEL_FEATURES])[:, 1]
        outputs.append(fold)
        cursor += config.test_days
    if not outputs:
        raise ValueError("No eligible walk-forward folds")
    return pd.concat(outputs, ignore_index=True)


def evaluate_predictions(predictions: pd.DataFrame) -> MultiModelMetrics:
    direction_y = predictions["target"].astype(int).to_numpy()
    direction_p = predictions["outperformance_probability"].to_numpy()
    downside_y = predictions["downside_target"].astype(int).to_numpy()
    downside_p = predictions["downside_probability"].to_numpy()
    buy_mask = direction_p >= 0.60
    risk_mask = downside_p >= 0.60
    ic = spearmanr(predictions["expected_excess_return"], predictions["forward_excess_return"], nan_policy="omit").statistic
    return MultiModelMetrics(
        observations=len(predictions), direction_auc=_safe_auc(direction_y, direction_p),
        direction_brier=float(brier_score_loss(direction_y, direction_p)),
        direction_buy_precision=float(precision_score(direction_y[buy_mask], np.ones(buy_mask.sum()), zero_division=0)) if buy_mask.any() else 0.0,
        regression_mae=float(mean_absolute_error(predictions["forward_excess_return"], predictions["expected_excess_return"])),
        regression_rmse=float(mean_squared_error(predictions["forward_excess_return"], predictions["expected_excess_return"]) ** 0.5),
        regression_spearman_ic=float(ic) if np.isfinite(ic) else 0.0,
        downside_auc=_safe_auc(downside_y, downside_p), downside_brier=float(brier_score_loss(downside_y, downside_p)),
        downside_alert_precision=float(precision_score(downside_y[risk_mask], np.ones(risk_mask.sum()), zero_division=0)) if risk_mask.any() else 0.0,
        downside_base_rate=float(downside_y.mean()),
    )


class ThreeModelSystem:
    def __init__(self, model_config: ModelConfig = ModelConfig(), signal_config: MultiModelConfig = MultiModelConfig()):
        self.model_config, self.signal_config = model_config, signal_config
        self.direction = None; self.magnitude = None; self.risk = None
        self.metrics: MultiModelMetrics | None = None

    @staticmethod
    def _calibrated_fit(base: Pipeline, train: pd.DataFrame, calibration: pd.DataFrame, target: str):
        fitted = base.fit(train[MODEL_FEATURES], train[target].astype(int))
        calibrated = CalibratedClassifierCV(FrozenEstimator(fitted), method="sigmoid")
        calibrated.fit(calibration[MODEL_FEATURES], calibration[target].astype(int))
        return calibrated

    def fit(self, prices: pd.DataFrame) -> "ThreeModelSystem":
        features = build_panel_dataset(prices, self.model_config)
        predictions = walk_forward_three_models(features, self.model_config)
        self.metrics = evaluate_predictions(predictions)
        labelled = features.dropna(subset=["return_60d", "target_direction", "target_5d_excess_return", "target_5d_return", "target_downside"]).sort_values("date").copy()
        dates = np.array(sorted(labelled["date"].unique()))
        split = int(len(dates) * 0.8); train_end = split - self.model_config.embargo_days
        train = labelled[labelled["date"].isin(dates[:train_end])]
        calibration = labelled[labelled["date"].isin(dates[split:])]
        self.direction = self._calibrated_fit(_classifier(), train, calibration, "target_direction")
        self.risk = self._calibrated_fit(_classifier(), train, calibration, "target_downside")
        self.magnitude = _regressor().fit(train[MODEL_FEATURES], train["target_5d_excess_return"])
        return self

    def forecast(self, prices: pd.DataFrame) -> list[dict]:
        if self.metrics is None or self.direction is None or self.magnitude is None or self.risk is None:
            raise RuntimeError("Models must be fitted first")
        features = build_panel_dataset(prices, self.model_config)
        latest = features.dropna(subset=["return_60d"]).sort_values("date").groupby("symbol").tail(1).copy()
        latest["outperformance_probability"] = self.direction.predict_proba(latest[MODEL_FEATURES])[:, 1]
        latest["expected_excess_return"] = self.magnitude.predict(latest[MODEL_FEATURES])
        latest["downside_probability"] = self.risk.predict_proba(latest[MODEL_FEATURES])[:, 1]
        low, high = latest["realized_vol_20d"].quantile([0.33, 0.67])
        qualified_model = (
            self.metrics.direction_buy_precision >= self.signal_config.minimum_direction_precision
            and self.metrics.downside_auc > 0.5
        )
        output = []
        for row in latest.itertuples():
            signal = "NO SIGNAL"
            if qualified_model:
                if (row.outperformance_probability >= self.signal_config.buy_outperformance_probability
                    and row.expected_excess_return >= self.signal_config.minimum_expected_excess_return
                    and row.downside_probability <= self.signal_config.maximum_downside_probability):
                    signal = "BUY"
                else:
                    signal = "HOLD"
            regime = "LOW" if row.realized_vol_20d <= low else "HIGH" if row.realized_vol_20d >= high else "MEDIUM"
            output.append({
                "symbol": row.symbol, "as_of": row.date.date().isoformat(), "signal": signal,
                "outperformance_probability": round(float(row.outperformance_probability), 4),
                "expected_excess_return": round(float(row.expected_excess_return), 4),
                "downside_probability": round(float(row.downside_probability), 4),
                "volatility_regime": regime,
            })
        return sorted(output, key=lambda x: x["outperformance_probability"], reverse=True)

    def save(self, directory: Path) -> None:
        if self.metrics is None: raise RuntimeError("Models must be fitted first")
        directory.mkdir(parents=True, exist_ok=True)
        joblib.dump({"direction": self.direction, "magnitude": self.magnitude, "risk": self.risk}, directory / "three_models.joblib")
        (directory / "three_model_metadata.json").write_text(json.dumps({
            "model_config": asdict(self.model_config), "signal_config": asdict(self.signal_config),
            "metrics": asdict(self.metrics), "features": MODEL_FEATURES,
        }, indent=2), encoding="utf-8")
