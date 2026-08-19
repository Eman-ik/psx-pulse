"""
Real Quant Forecast tool, backed by the Kronos foundation model (D:/khronos) -- the
"Not an LLM... Quant Forecast... the Quant Analyst interprets that" tool the original
PSX TradingAgents plan called for.

Invoked as a subprocess into khronos's own dedicated .venv rather than importing
torch/einops/Kronos directly into psxagents: keeps the heavy ML stack isolated from
every other analyst's process, which matters on this machine (7.8GB RAM total, already
found a real out-of-memory crash loading a full-size Kronos model during fine-tuning
setup -- see khronos session notes). khronos/quant_forecast.py auto-upgrades to the
real fine-tuned checkpoint once available; this tool has no knowledge of that and
just reports whatever model_source the subprocess used.
"""

from __future__ import annotations

import json
import subprocess
from typing import Annotated

from langchain_core.tools import tool

_KRONOS_PYTHON = r"D:\khronos\.venv\Scripts\python.exe"
_KRONOS_SCRIPT = r"D:\khronos\quant_forecast.py"
_SUBPROCESS_TIMEOUT_SECONDS = 600


@tool
def get_quant_forecast(
    ticker: Annotated[str, "PSX ticker symbol, e.g. FFC"],
    horizon_days: Annotated[int, "forecast horizon in trading days, default 5"] = 5,
) -> str:
    """
    Real probabilistic price forecast from the Kronos foundation model, run against
    real PSX price history. NOT an LLM -- a genuine quantitative model producing an
    ensemble of independent stochastic forecasts (see khronos/quant_forecast.py for
    why a single averaged path isn't enough for these statistics). Interpret this
    output; do not restate it as your own reasoning or override its numbers.
    Args:
        ticker (str): PSX ticker symbol, e.g. FFC
        horizon_days (int): forecast horizon in trading days, default 5
    Returns:
        str: A formatted real forecast summary (probability of positive return,
        expected return, downside VaR, volatility, trend regime, model confidence),
        or a clear unavailable message if the model/data couldn't produce one.
    """
    try:
        result = subprocess.run(
            [_KRONOS_PYTHON, _KRONOS_SCRIPT, ticker, str(horizon_days)],
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return (
            f"QUANT_FORECAST_UNAVAILABLE: Kronos forecast for '{ticker.upper()}' timed "
            f"out after {_SUBPROCESS_TIMEOUT_SECONDS}s. Do not fabricate a substitute forecast."
        )
    except Exception as exc:  # noqa: BLE001 -- a subprocess/environment failure must not crash the graph
        return (
            f"QUANT_FORECAST_UNAVAILABLE: could not run the Kronos forecast for "
            f"'{ticker.upper()}' ({exc}). Do not fabricate a substitute forecast."
        )

    if result.returncode != 0:
        return (
            f"QUANT_FORECAST_UNAVAILABLE: the Kronos forecast process for "
            f"'{ticker.upper()}' failed (exit {result.returncode}): "
            f"{result.stderr.strip()[-500:]}. Do not fabricate a substitute forecast."
        )

    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return (
            f"QUANT_FORECAST_UNAVAILABLE: could not parse the Kronos forecast output "
            f"for '{ticker.upper()}'. Do not fabricate a substitute forecast."
        )

    if not payload.get("ok"):
        return (
            f"QUANT_FORECAST_UNAVAILABLE for '{ticker.upper()}': "
            f"{payload.get('reason', 'unknown reason')}. Do not fabricate a substitute forecast."
        )

    return (
        f"# Quant Forecast for {payload['ticker']} ({payload.get('issuer_name', 'unknown issuer')})\n"
        f"# As of real close on {payload['as_of_date']} (PKR {payload['last_real_close']})\n"
        f"# Model: {payload['model_source']}, {payload['n_samples']} independent real stochastic samples\n\n"
        f"Horizon: {payload['horizon_days']} trading days\n"
        f"P(positive return): {payload['p_positive_return'] * 100:.0f}%\n"
        f"Expected {payload['horizon_days']}D return: {payload['expected_return_pct']:+.2f}%\n"
        f"Expected downside VaR (5th percentile): {payload['downside_var_pct']:+.2f}%\n"
        f"Expected volatility: {payload['expected_volatility_pct']:.2f}%\n"
        f"Trend regime: {payload['trend_regime']}\n"
        f"Model confidence: {payload['model_confidence']}\n"
    )
