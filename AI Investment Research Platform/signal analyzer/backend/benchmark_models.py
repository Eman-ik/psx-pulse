from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, f1_score, log_loss, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .feature_engine import EXTENDED_FEATURE_COLUMNS, build_panel_dataset


@dataclass
class BenchmarkMetrics:
    model: str
    observations: int
    accuracy: float
    auc: float
    brier: float
    buy_precision: float
    coverage: float
    pr_auc: float
    recall: float
    f1: float
    log_loss: float


def _metrics(name: str, frame: pd.DataFrame) -> BenchmarkMetrics:
    y = frame["target"].astype(int).to_numpy()
    p = frame["probability"].clip(0.001, 0.999).to_numpy()
    buy = p >= 0.60
    return BenchmarkMetrics(
        model=name, observations=len(frame), accuracy=float(accuracy_score(y, p >= 0.5)),
        auc=float(roc_auc_score(y, p)), brier=float(brier_score_loss(y, p)),
        buy_precision=float(precision_score(y[buy], np.ones(buy.sum()), zero_division=0)) if buy.any() else 0.0,
        coverage=float(buy.mean()), pr_auc=float(average_precision_score(y, p)),
        recall=float(recall_score(y, p >= 0.5, zero_division=0)),
        f1=float(f1_score(y, p >= 0.5, zero_division=0)), log_loss=float(log_loss(y, p)),
    )


def _models() -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline([
            ("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler()),
            ("model", LogisticRegression(C=0.35, class_weight="balanced", max_iter=2000)),
        ]),
        "random_forest": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", RandomForestClassifier(
                n_estimators=160, max_depth=9, min_samples_leaf=80, max_features="sqrt",
                class_weight="balanced_subsample", n_jobs=-1, random_state=42,
            )),
        ]),
    }


def benchmark(panel: pd.DataFrame, first_test_year: int = 2018) -> dict:
    features = build_panel_dataset(panel)
    labelled = features.dropna(subset=["return_60d", "target_direction"]).sort_values("date")
    predictions: dict[str, list[pd.DataFrame]] = {
        "always_positive": [], "previous_5d_momentum": [], "sector_momentum": [],
        "logistic_regression": [], "random_forest": [],
    }
    years = sorted(y for y in labelled["date"].dt.year.unique() if y >= first_test_year)
    fold_audit = []
    for year in years:
        test_start = pd.Timestamp(year=year, month=1, day=1)
        embargo_cutoff = test_start - pd.offsets.BDay(5)
        train = labelled[labelled["date"] < embargo_cutoff]
        test = labelled[labelled["date"].dt.year == year]
        if train.empty or test.empty: continue
        fold_audit.append({
            "test_year": int(year), "train_last_feature_date": train["date"].max().date().isoformat(),
            "test_first_feature_date": test["date"].min().date().isoformat(),
            "purge_business_days": 5, "target_horizon_days": 5,
        })
        truth = test[["date", "symbol", "target_direction"]].rename(columns={"target_direction":"target"})
        base_rate = float(train["target_direction"].mean())
        naive = truth.copy(); naive["probability"] = base_rate
        predictions["always_positive"].append(naive)
        momentum = truth.copy(); momentum["probability"] = np.where(test["market_relative_5d"] > 0, 0.65, 0.35)
        predictions["previous_5d_momentum"].append(momentum)
        sector = truth.copy(); sector["probability"] = np.where(test["sector_relative_strength"] > 0, 0.65, 0.35)
        predictions["sector_momentum"].append(sector)
        for name, model in _models().items():
            model.fit(train[EXTENDED_FEATURE_COLUMNS], train["target_direction"].astype(int))
            result = truth.copy(); result["probability"] = model.predict_proba(test[EXTENDED_FEATURE_COLUMNS])[:, 1]
            predictions[name].append(result)
    metrics = []
    for name, folds in predictions.items():
        if folds: metrics.append(asdict(_metrics(name, pd.concat(folds, ignore_index=True))))
    metrics.sort(key=lambda x: x["auc"], reverse=True)
    oos = {name: pd.concat(folds, ignore_index=True) for name, folds in predictions.items() if folds}
    return {
        "evaluation": "annual expanding-window with five-business-day embargo",
        "first_test_year": int(first_test_year), "last_test_year": int(max(years)),
        "feature_count": len(EXTENDED_FEATURE_COLUMNS), "metrics": metrics,
        "winner_by_auc": metrics[0]["model"] if metrics else None, "fold_audit": fold_audit,
        "_oos_predictions": oos,
    }


def main():
    panel = pd.read_csv("research/yahoo_psx_panel.csv", parse_dates=["date"])
    report = benchmark(panel)
    predictions = report.pop("_oos_predictions")
    prediction_dir = Path("research/oos_predictions"); prediction_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in predictions.items(): frame.to_csv(prediction_dir / f"{name}.csv", index=False)
    path = Path("research/model_benchmark_report.json")
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
