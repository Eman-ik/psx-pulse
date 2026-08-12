from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd


def _portfolio_metrics(returns: pd.Series, periods_per_year: float = 252 / 5) -> dict:
    returns = returns.dropna().astype(float)
    if returns.empty: return {}
    equity = (1 + returns).cumprod()
    drawdown = equity / equity.cummax() - 1
    downside = returns[returns < 0].std(ddof=1)
    gross_profit, gross_loss = returns[returns > 0].sum(), -returns[returns < 0].sum()
    return {
        "observations": len(returns), "mean_5d_return": float(returns.mean()),
        "annualized_return": float(equity.iloc[-1] ** (periods_per_year / len(returns)) - 1),
        "annualized_volatility": float(returns.std(ddof=1) * np.sqrt(periods_per_year)),
        "sharpe": float(returns.mean() / returns.std(ddof=1) * np.sqrt(periods_per_year)) if returns.std(ddof=1) else 0.0,
        "sortino": float(returns.mean() / downside * np.sqrt(periods_per_year)) if downside and np.isfinite(downside) else 0.0,
        "maximum_drawdown": float(drawdown.min()), "hit_rate": float((returns > 0).mean()),
        "profit_factor": float(gross_profit / gross_loss) if gross_loss else None,
    }


def evaluate_alpha(predictions: pd.DataFrame, panel: pd.DataFrame, round_trip_cost: float = 0.004) -> dict:
    targets = panel[["date", "symbol", "close", "benchmark_close"]].copy()
    targets["date"] = pd.to_datetime(targets["date"])
    targets = targets.sort_values(["symbol", "date"])
    targets["stock_forward_5d"] = targets.groupby("symbol")["close"].shift(-5) / targets["close"] - 1
    targets["benchmark_forward_5d"] = targets.groupby("symbol")["benchmark_close"].shift(-5) / targets["benchmark_close"] - 1
    targets["excess_forward_5d"] = targets["stock_forward_5d"] - targets["benchmark_forward_5d"]
    merged = predictions.merge(targets[["date", "symbol", "stock_forward_5d", "excess_forward_5d"]], on=["date", "symbol"], how="inner").dropna()
    merged["rank_pct"] = merged.groupby("date")["probability"].rank(pct=True, method="first")
    merged["decile"] = np.ceil(merged["rank_pct"] * 10).clip(1, 10).astype(int)
    deciles = merged.groupby("decile").agg(
        observations=("excess_forward_5d", "size"), avg_5d_excess_return=("excess_forward_5d", "mean"),
        median_5d_excess_return=("excess_forward_5d", "median"), hit_rate=("excess_forward_5d", lambda x: float((x > 0).mean())),
    ).reset_index().to_dict("records")
    daily = merged.groupby(["date", "decile"])["excess_forward_5d"].mean().unstack()
    # Sample one cohort every five trading dates to avoid counting overlapping
    # five-day target windows as independent portfolio observations.
    non_overlapping = daily.iloc[::5].copy()
    top_gross = non_overlapping.get(10, pd.Series(dtype=float))
    bottom_gross = non_overlapping.get(1, pd.Series(dtype=float))
    top_net = top_gross - round_trip_cost
    long_short_net = top_gross - bottom_gross - 2 * round_trip_cost
    benchmark = panel.drop_duplicates("date").sort_values("date")[["date", "benchmark_close"]]
    benchmark["return_20d"] = benchmark["benchmark_close"].pct_change(20)
    benchmark["volatility_20d"] = benchmark["benchmark_close"].pct_change().rolling(20).std() * np.sqrt(252)
    benchmark["trend_regime"] = np.where(benchmark["return_20d"] >= 0, "BULL", "BEAR")
    benchmark["volatility_regime"] = np.where(benchmark["volatility_20d"] >= benchmark["volatility_20d"].median(), "HIGH_VOL", "LOW_VOL")
    regime_data = merged.merge(benchmark[["date", "trend_regime", "volatility_regime"]], on="date", how="left")
    regime_rows = []
    for (trend, volatility), group in regime_data.groupby(["trend_regime", "volatility_regime"]):
        top = group[group["decile"] == 10]["excess_forward_5d"]
        bottom = group[group["decile"] == 1]["excess_forward_5d"]
        regime_rows.append({"trend": trend, "volatility": volatility, "top_decile_mean_excess": float(top.mean()), "bottom_decile_mean_excess": float(bottom.mean()), "spread": float(top.mean() - bottom.mean()), "observations": len(group)})
    return {
        "methodology": "Daily cross-sectional deciles; portfolio metrics use every fifth trading-date cohort to avoid overlapping target windows.",
        "round_trip_cost": round_trip_cost, "long_short_cost": 2 * round_trip_cost,
        "deciles": deciles, "top_decile_long_only_net": _portfolio_metrics(top_net),
        "top_minus_bottom_net": _portfolio_metrics(long_short_net), "regimes": regime_rows,
        "execution_warning": "Long-short is an alpha diagnostic; short availability and borrow costs are not modeled for PSX.",
    }


def main():
    predictions = pd.read_csv("research/oos_predictions/logistic_regression.csv", parse_dates=["date"])
    panel = pd.read_csv("research/yahoo_psx_panel.csv", parse_dates=["date"])
    report = evaluate_alpha(predictions, panel)
    path = Path("research/alpha_evaluation_report.json")
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
