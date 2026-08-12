from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

import joblib
import numpy as np
import pandas as pd

from .calibration_analysis import _logit
from .feature_engine import EXTENDED_FEATURE_COLUMNS, build_panel_dataset


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()


def _calibrate(probability: float, artifacts: dict) -> float:
    method = artifacts["selected_method"]
    if method == "platt": return float(artifacts["platt"].predict_proba(_logit(np.array([probability])))[:, 1][0])
    if method == "isotonic": return float(artifacts["isotonic"].predict([probability])[0])
    return probability


def generate_passports() -> list[dict]:
    report_path = Path("research/three_model_report.json"); data_path = Path("research/yahoo_psx_panel.csv")
    artifact_path = Path("research/model_artifacts/three_models.joblib"); calibrator_path = Path("research/model_artifacts/probability_calibrators.joblib")
    report = json.loads(report_path.read_text(encoding="utf-8")); calibrators = joblib.load(calibrator_path)
    raw = pd.read_csv(data_path, parse_dates=["date"]); panel = build_panel_dataset(raw)
    latest = panel.sort_values("date").groupby("symbol").tail(1).set_index("symbol")
    train = panel.dropna(subset=["target_direction"])
    low = train[EXTENDED_FEATURE_COLUMNS].quantile(.01); high = train[EXTENDED_FEATURE_COLUMNS].quantile(.99)
    dataset_version, model_version = _sha256(data_path), _sha256(artifact_path)
    passports = []
    for forecast in report["forecasts"]:
        symbol = forecast["symbol"]; row = latest.loc[symbol]
        values = row[EXTENDED_FEATURE_COLUMNS]
        completeness = float(values.notna().mean())
        comparable = values.notna() & low.notna() & high.notna()
        ood_score = float(((values[comparable] < low[comparable]) | (values[comparable] > high[comparable])).mean()) if comparable.any() else 1.0
        calibrated = _calibrate(float(forecast["outperformance_probability"]), calibrators)
        agreement = [calibrated > .5, forecast["expected_excess_return"] > 0, forecast["downside_probability"] < .20]
        payload = {
            "stock": symbol, "as_of": forecast["as_of"], "horizon_trading_days": 5,
            "model_version": model_version, "dataset_version": dataset_version,
            "raw_outperformance_probability": forecast["outperformance_probability"],
            "outperformance_probability": round(calibrated, 4), "calibration_method": calibrators["selected_method"],
            "expected_excess_return": forecast["expected_excess_return"], "downside_probability": forecast["downside_probability"],
            "market_regime": "BULLISH" if row["benchmark_close"] / panel.drop_duplicates("date").sort_values("date")["benchmark_close"].iloc[-21] - 1 > 0 else "BEARISH",
            "sector": row["sector"], "sector_regime": "STRONG" if row["sector_relative_strength"] > 0 else "WEAK",
            "liquidity_regime": "HIGH" if row["liquidity_percentile"] >= .67 else "LOW" if row["liquidity_percentile"] <= .33 else "MEDIUM",
            "volatility_regime": forecast["volatility_regime"], "fundamental_assessment":"UNAVAILABLE", "sentiment_assessment":"UNAVAILABLE",
            "model_agreement": f"{sum(agreement)}/{len(agreement)}", "data_completeness": round(completeness, 4), "ood_score": round(ood_score, 4),
            "signal": forecast["signal"], "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        identity = json.dumps({k:payload[k] for k in ["stock","as_of","horizon_trading_days","model_version","dataset_version"]}, sort_keys=True)
        payload["prediction_id"] = hashlib.sha256(identity.encode()).hexdigest()[:24]
        passports.append(payload)
    ledger = Path("research/prediction_passports.jsonl"); existing = set()
    if ledger.exists():
        existing = {json.loads(line)["prediction_id"] for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()}
    with ledger.open("a", encoding="utf-8") as handle:
        for passport in passports:
            if passport["prediction_id"] not in existing: handle.write(json.dumps(passport) + "\n")
    Path("research/latest_prediction_passports.json").write_text(json.dumps(passports, indent=2), encoding="utf-8")
    return passports


if __name__ == "__main__": print(json.dumps(generate_passports(), indent=2))
