# PSX Quant Signal Research Platform

The project contains a React dashboard and a Python quant research API. The API currently uses deterministic synthetic development data and labels it accordingly. It must not be treated as live PSX data or investment advice.

## Run locally

Use two terminals:

```powershell
npm.cmd run api
```

```powershell
npm.cmd run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to FastAPI on port 8000.

## Licensed data contract

Set `PSX_DATA_FILE` to a CSV containing one row per trading date and symbol:

| Column | Meaning |
|---|---|
| `date` | Trading date |
| `symbol` | PSX symbol |
| `open`, `high`, `low`, `close` | Corporate-action-adjusted OHLC prices |
| `volume` | Traded shares |
| `benchmark_close` | Adjusted KSE-100 close on the same date |

The current baseline needs at least 336 distinct trading dates. Production history should include delisted and suspended stocks to avoid survivorship bias. Fundamentals must later be joined by their public announcement date, never by reporting-period end.

## Quant baseline

- Five-day benchmark-relative return target: stock return minus benchmark return
- Trading costs applied separately during signal qualification, not to the prediction label
- Technical, relative-strength, volatility, volume and breakout features
- Regularized logistic regression
- Time-ordered walk-forward validation with a 21-day embargo
- Disjoint sigmoid probability calibration
- BUY/SELL precision gate of at least 60%
- `NO SIGNAL` when evidence is insufficient

## Verification

```powershell
npm.cmd run test:quant
npm.cmd run build
```
