from __future__ import annotations

from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss


def _logit(probability: np.ndarray) -> np.ndarray:
    p = np.clip(probability, 1e-5, 1 - 1e-5)
    return np.log(p / (1 - p)).reshape(-1, 1)


def _ece(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1); total = len(y); error = 0.0
    for low, high in zip(edges[:-1], edges[1:]):
        mask = (p >= low) & (p < high if high < 1 else p <= high)
        if mask.any(): error += mask.sum() / total * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return float(error)


def _reliability(y: np.ndarray, p: np.ndarray, bins: int = 10) -> list[dict]:
    groups = pd.DataFrame({"target": y, "probability": p})
    groups["bin"] = pd.cut(groups["probability"], np.linspace(0, 1, bins + 1), include_lowest=True)
    result = groups.groupby("bin", observed=True).agg(count=("target", "size"), predicted=("probability", "mean"), realized=("target", "mean")).reset_index()
    return [{"range": str(r.bin), "count": int(r.count), "mean_probability": float(r.predicted), "realized_rate": float(r.realized)} for r in result.itertuples()]


def chronological_calibration(predictions: pd.DataFrame, minimum_history: int = 5000) -> tuple[dict, dict]:
    data = predictions.copy(); data["date"] = pd.to_datetime(data["date"]); data = data.sort_values("date")
    outputs = {"raw": [], "platt": [], "isotonic": []}; fold_audit = []
    for year in sorted(data["date"].dt.year.unique()):
        test = data[data["date"].dt.year == year]
        if test.empty: continue
        calibration_cutoff = test["date"].min() - pd.offsets.BDay(5)
        train = data[data["date"] < calibration_cutoff]
        if len(train) < minimum_history or test.empty: continue
        y_train, p_train = train["target"].astype(int).to_numpy(), train["probability"].to_numpy()
        platt = LogisticRegression(C=1e6).fit(_logit(p_train), y_train)
        isotonic = IsotonicRegression(out_of_bounds="clip").fit(p_train, y_train)
        raw_p = test["probability"].to_numpy(); y_test = test["target"].astype(int).to_numpy()
        calibrated = {"raw": raw_p, "platt": platt.predict_proba(_logit(raw_p))[:, 1], "isotonic": isotonic.predict(raw_p)}
        for method, values in calibrated.items():
            frame = test[["date", "symbol", "target"]].copy(); frame["probability"] = values; outputs[method].append(frame)
        fold_audit.append({"test_year": int(year), "calibration_rows": len(train), "test_rows": len(test), "calibration_last_date": train["date"].max().date().isoformat(), "test_first_date": test["date"].min().date().isoformat(), "purge_business_days": 5})
    metrics = []
    combined = {}
    for method, folds in outputs.items():
        frame = pd.concat(folds, ignore_index=True); combined[method] = frame
        y, p = frame["target"].astype(int).to_numpy(), frame["probability"].to_numpy()
        metrics.append({"method": method, "observations": len(frame), "brier": float(brier_score_loss(y, p)), "log_loss": float(log_loss(y, np.clip(p, 1e-6, 1-1e-6))), "ece_10_bin": _ece(y, p), "reliability": _reliability(y, p)})
    metrics.sort(key=lambda x: x["brier"])
    # Final production calibrators use all genuinely out-of-sample predictions.
    y_all, p_all = data["target"].astype(int).to_numpy(), data["probability"].to_numpy()
    artifacts = {
        "platt": LogisticRegression(C=1e6).fit(_logit(p_all), y_all),
        "isotonic": IsotonicRegression(out_of_bounds="clip").fit(p_all, y_all),
        "selected_method": metrics[0]["method"],
    }
    return {"selection_metric":"lowest out-of-sample Brier score", "metrics":metrics, "fold_audit":fold_audit}, artifacts


def main():
    predictions = pd.read_csv("research/oos_predictions/logistic_regression.csv", parse_dates=["date"])
    report, artifacts = chronological_calibration(predictions)
    Path("research/calibration_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    joblib.dump(artifacts, "research/model_artifacts/probability_calibrators.joblib")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
