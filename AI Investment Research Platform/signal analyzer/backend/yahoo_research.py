from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd
import yfinance as yf

from .quant_engine import ModelConfig, SignalModel, build_features, walk_forward_predictions

DEFAULT_UNIVERSE = [
    "FFC", "MARI", "SYS", "HBL", "LUCK", "OGDC", "EFERT", "MCB", "UBL",
    "NBP", "PPL", "POL", "HUBC", "PSO", "BAHL", "MTL", "INDU", "NESTLE",
    "COLG", "ILP", "FCCL", "DGKC", "MLCF", "TRG",
]


def download_yahoo_psx(
    symbols: list[str] = DEFAULT_UNIVERSE,
    start: str = "2010-01-01",
    end: str | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Download adjusted research OHLCV from Yahoo and build a universe benchmark.

    This is an educational/research source, not a licensed PSX production feed.
    The benchmark is an equal-weight average of available universe returns and
    therefore has survivorship and membership limitations.
    """
    tickers = [f"{symbol}.KA" for symbol in symbols]
    raw = yf.download(
        tickers, start=start, end=end, interval="1d", auto_adjust=True,
        group_by="ticker", threads=True, progress=False,
    )
    frames: list[pd.DataFrame] = []
    coverage: dict[str, dict] = {}
    close_series: dict[str, pd.Series] = {}
    for symbol, ticker in zip(symbols, tickers):
        if ticker not in raw.columns.get_level_values(0):
            coverage[symbol] = {"rows": 0, "status": "missing"}
            continue
        data = raw[ticker].dropna(subset=["Open", "High", "Low", "Close"]).copy()
        if data.empty:
            coverage[symbol] = {"rows": 0, "status": "missing"}
            continue
        data.index = pd.to_datetime(data.index).tz_localize(None)
        close_series[symbol] = data["Close"].astype(float)
        coverage[symbol] = {
            "rows": len(data), "status": "available",
            "first": data.index.min().date().isoformat(), "last": data.index.max().date().isoformat(),
            "zero_volume_days": int((data["Volume"].fillna(0) == 0).sum()),
        }
        frames.append(pd.DataFrame({
            "date": data.index, "symbol": symbol, "open": data["Open"].to_numpy(float),
            "high": data["High"].to_numpy(float), "low": data["Low"].to_numpy(float),
            "close": data["Close"].to_numpy(float), "volume": data["Volume"].fillna(0).to_numpy(float),
        }))
    if len(frames) < 5:
        raise RuntimeError(f"Only {len(frames)} symbols downloaded; insufficient for a market benchmark")
    closes = pd.concat(close_series, axis=1).sort_index()
    returns = closes.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    # Require at least five valid constituents to calculate a daily benchmark return.
    market_return = returns.mean(axis=1, skipna=True).where(returns.notna().sum(axis=1) >= 5)
    benchmark = (1 + market_return.fillna(0)).cumprod() * 100_000
    panel = pd.concat(frames, ignore_index=True)
    panel["benchmark_close"] = panel["date"].map(benchmark)
    panel = panel.dropna(subset=["benchmark_close"]).sort_values(["symbol", "date"]).reset_index(drop=True)
    metadata = {
        "provider": "Yahoo Finance via yfinance", "usage": "research_only",
        "benchmark": "equal_weight_available_downloaded_universe",
        "requested_symbols": len(symbols), "available_symbols": len(frames), "coverage": coverage,
        "limitations": [
            "Not a licensed PSX market-data feed",
            "Current constituent list introduces survivorship bias",
            "Equal-weight universe benchmark is not the KSE-100",
            "Yahoo corporate-action adjustments and data quality require independent verification",
            "No point-in-time fundamentals or delisted-company universe",
        ],
    }
    return panel, metadata


def run_experiment(output: Path, input_file: Path | None = None) -> dict:
    if input_file:
        panel = pd.read_csv(input_file, parse_dates=["date"])
        source = {
            "provider": "Yahoo Finance via yfinance", "usage": "research_only",
            "benchmark": "equal_weight_available_downloaded_universe",
            "available_symbols": int(panel["symbol"].nunique()),
            "cached_input": str(input_file),
            "limitations": ["Cached Yahoo research dataset", "Survivorship bias", "Benchmark is not KSE-100"],
        }
    else:
        panel, source = download_yahoo_psx()
    config = ModelConfig()
    model = SignalModel(config).fit(panel)
    features = build_features(panel, config)
    oos = walk_forward_predictions(features, config)
    oos["predicted_class"] = (oos["probability"] >= 0.5).astype(int)
    yearly = []
    for year, group in oos.groupby(oos["date"].dt.year):
        yearly.append({
            "year": int(year), "observations": len(group),
            "accuracy": round(float((group["predicted_class"] == group["target"]).mean()), 4),
            "mean_probability": round(float(group["probability"].mean()), 4),
            "realized_positive_rate": round(float(group["target"].mean()), 4),
        })
    report = {
        "experiment": "five_day_psx_relative_return_baseline",
        "generated_at": pd.Timestamp.now(tz="Asia/Karachi").isoformat(),
        "source": source, "config": asdict(config), "validation": asdict(model.metrics),
        "yearly_out_of_sample": yearly, "latest_signals": model.rank(panel),
        "target_definition": "stock adjusted 5-day return minus equal-weight research benchmark 5-day return; positive class is excess return > 0",
        "interpretation": "Research baseline. Signal qualification is evaluated separately from the raw market-outperformance target. SELL is intentionally withheld until a separately validated downside model exists. Do not use for investment decisions.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    panel.to_csv(output.with_name("yahoo_psx_panel.csv"), index=False)
    model.save(output.with_name("model_artifacts"))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/yahoo_5d_report.json"))
    parser.add_argument("--input", type=Path, default=None, help="Use an existing normalized panel instead of downloading")
    args = parser.parse_args()
    report = run_experiment(args.output, args.input)
    print(json.dumps({
        "available_symbols": report["source"]["available_symbols"],
        "validation": report["validation"], "latest_signals": report["latest_signals"][:5],
        "report": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
