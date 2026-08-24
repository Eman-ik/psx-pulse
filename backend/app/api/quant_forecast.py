"""
Bridges the frontend into D:/khronos's real Kronos quant forecast + Signal
Qualification Gate (see D:/khronos/quant_forecast.py and signal_qualification.py) --
the same subprocess-isolation pattern agents/psxagents/agents/utils/quant_forecast_tools.py
already uses (heavy torch/Kronos stack stays in khronos's own dedicated .venv, not
imported into this backend process).

Deliberately on-demand, not eager: one real forecast call costs ~5-30s (an actual
15-sample Kronos ensemble on CPU), so this is a plain synchronous GET the frontend
calls only when a user opens the Quant Forecast tab, not something bundled into the
company page's initial parallel fetch alongside everything else.
"""

from __future__ import annotations

import json
import subprocess

from fastapi import APIRouter

router = APIRouter(prefix="/quant-forecast", tags=["quant-forecast"])

_KRONOS_PYTHON = r"D:\khronos\.venv\Scripts\python.exe"
_KRONOS_SCRIPT = r"D:\khronos\quant_forecast.py"
_SUBPROCESS_TIMEOUT_SECONDS = 120


@router.get("/{ticker}")
def get_quant_forecast(ticker: str, horizon_days: int = 5) -> dict:
    ticker_upper = ticker.upper()

    try:
        result = subprocess.run(
            [_KRONOS_PYTHON, _KRONOS_SCRIPT, ticker_upper, str(horizon_days)],
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "ticker": ticker_upper,
            "reason": f"forecast timed out after {_SUBPROCESS_TIMEOUT_SECONDS}s",
        }
    except Exception as exc:  # noqa: BLE001 -- a subprocess/environment failure must not 500 the page
        return {"ok": False, "ticker": ticker_upper, "reason": f"could not run the forecast ({exc})"}

    if result.returncode != 0:
        return {
            "ok": False,
            "ticker": ticker_upper,
            "reason": f"forecast process failed (exit {result.returncode}): {result.stderr.strip()[-500:]}",
        }

    try:
        return json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"ok": False, "ticker": ticker_upper, "reason": "could not parse forecast output"}
