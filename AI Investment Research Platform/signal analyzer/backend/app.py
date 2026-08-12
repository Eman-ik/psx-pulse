from functools import lru_cache
from pathlib import Path
import os
import json

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .quant_engine import ModelConfig, SignalModel, synthetic_market
from .multi_model import ThreeModelSystem

app = FastAPI(title="PSX Quant Signal API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["GET"], allow_headers=["*"])


def _load_prices() -> tuple[pd.DataFrame, str]:
    configured = os.getenv("PSX_DATA_FILE")
    if configured:
        path = Path(configured)
        if not path.exists():
            raise FileNotFoundError(f"PSX_DATA_FILE does not exist: {path}")
        return pd.read_csv(path), "licensed_file"
    return synthetic_market(), "synthetic_development"


@lru_cache(maxsize=1)
def _model_bundle():
    prices, source = _load_prices()
    model = SignalModel(ModelConfig()).fit(prices)
    return prices, source, model


@lru_cache(maxsize=1)
def _three_model_bundle():
    prices, source = _load_prices()
    return prices, source, ThreeModelSystem().fit(prices)


@app.get("/api/health")
def health():
    _, source, model = _model_bundle()
    return {"status": "ok", "data_source": source, "model": "calibrated_logistic_regression", "metrics": model.metrics}


@app.get("/api/signals")
def signals():
    try:
        prices, source, model = _model_bundle()
        return {"data_source": source, "is_live": False, "signals": model.rank(prices), "metrics": model.metrics}
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/forecasts")
def forecasts():
    try:
        prices, source, system = _three_model_bundle()
        return {
            "data_source": source, "is_live": False, "horizon_trading_days": 5,
            "metrics": system.metrics, "forecasts": system.forecast(prices),
        }
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/prediction-passports/latest")
def latest_prediction_passports():
    path = Path("research/latest_prediction_passports.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="No prediction passports have been generated")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/prediction-passports/{prediction_id}")
def prediction_passport(prediction_id: str):
    ledger = Path("research/prediction_passports.jsonl")
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if record.get("prediction_id") == prediction_id:
                return record
    raise HTTPException(status_code=404, detail="Prediction passport not found")


@app.get("/api/research/summary")
def research_summary():
    files = {
        "benchmark": Path("research/model_benchmark_report.json"),
        "alpha": Path("research/alpha_evaluation_report.json"),
        "calibration": Path("research/calibration_report.json"),
        "passports": Path("research/latest_prediction_passports.json"),
    }
    missing = [name for name, path in files.items() if not path.exists()]
    if missing: raise HTTPException(status_code=404, detail=f"Missing research reports: {missing}")
    return {name: json.loads(path.read_text(encoding="utf-8")) for name, path in files.items()}
