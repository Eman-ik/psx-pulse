"""Multi-factor exposure model (Blueprint Section 8).

Correctly labelled: this is a multi_factor_exposure_model, NOT an APT expected-return
model. The distinction (Blueprint Section 2 and 8.4) is that APT requires estimated
factor risk premia (λ_k) from cross-sectional Fama-MacBeth estimation or factor-mimicking
portfolios. With only 5 pilot issuers and ~30 monthly observations we cannot satisfy the
cross-sectional premium gates (Blueprint Section 8.4). The output clearly states:
  model_classification = "multi_factor_exposure_model"
  apt_expected_return_status = "unavailable"

What this does compute:
  R_excess_i = α + β_m F_market + β_π F_inflation + β_r F_rates + β_fx F_fx + ε

Using monthly data from:
  - Market factor: KSE-100 monthly excess return (from daily IndexOHLCV resampled to month-end)
  - Inflation: month-over-month change in National CPI YoY series (SBP/PBS)
  - Policy rate: month-over-month change in SBP Policy Rate
  - FX: month-over-month PKR/USD return

The regression uses pure Python OLS (numpy not required for this simple case with n<100).
For a more robust implementation with HAC standard errors use numpy/scipy; this version
uses standard OLS SE with a clear disclosure.
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import date
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import IndexOHLCV, Issuer, MacroObservation, MacroSeries, MarketIndex, PriceOHLCV, Security

logger = logging.getLogger(__name__)

MIN_MONTHLY_OBS = 24    # ~2 years minimum for reliable regression
PREFERRED_OBS = 36
BENCHMARK_CODE = "KSE100"

FACTOR_CODES = {
    "market": None,                 # computed from KSE-100
    "inflation": "NATIONAL_CPI_YOY",
    "rate": "SBP_POLICY_RATE",
    "fx": "PKR_USD_RATE",
}


@dataclass
class FactorExposure:
    factor_name: str
    beta: float | None
    beta_se: float | None
    t_stat: float | None
    p_value: float | None
    ci_low: float | None
    ci_high: float | None
    interpretation: str
    data_available: bool


@dataclass
class FactorModelResult:
    issuer_id: int
    symbol: str
    model_classification: str   # always "multi_factor_exposure_model"
    apt_expected_return_status: str  # always "unavailable" until premia are estimated
    window_start: str
    window_end: str
    n_monthly_obs: int
    alpha: float | None
    r_squared: float | None
    residual_vol_monthly: float | None
    factors: list[FactorExposure]
    missing_factors: list[str]
    confidence: str             # high | medium | low | insufficient_data
    notes: list[str]


def _month_end_key(d: date) -> tuple[int, int]:
    return (d.year, d.month)


def _to_monthly_returns(daily_bars: list[tuple[date, float]]) -> dict[tuple[int, int], float]:
    """Resample daily close bars to month-end, compute month-over-month returns."""
    buckets: dict[tuple[int, int], list[tuple[date, float]]] = defaultdict(list)
    for d, close in daily_bars:
        buckets[_month_end_key(d)].append((d, close))
    monthly: dict[tuple[int, int], float] = {}
    for key in sorted(buckets):
        week_bars = sorted(buckets[key], key=lambda x: x[0])
        monthly[key] = week_bars[-1][1]  # last close of month
    keys = sorted(monthly)
    returns: dict[tuple[int, int], float] = {}
    for i in range(1, len(keys)):
        prev_close = monthly[keys[i - 1]]
        curr_close = monthly[keys[i]]
        if prev_close > 0:
            returns[keys[i]] = (curr_close - prev_close) / prev_close
    return returns


def _get_macro_monthly(db: Session, series_code: str) -> dict[tuple[int, int], float]:
    """Return {(year, month): value} for a macro series."""
    series = db.execute(select(MacroSeries).where(MacroSeries.code == series_code)).scalar_one_or_none()
    if series is None:
        return {}
    obs = db.execute(select(MacroObservation).where(MacroObservation.macro_series_id == series.id)).scalars().all()
    result: dict[tuple[int, int], float] = {}
    for o in obs:
        result[_month_end_key(o.period)] = float(o.value)
    return result


def _macro_to_changes(monthly_vals: dict[tuple[int, int], float]) -> dict[tuple[int, int], float]:
    """Convert level series to month-over-month changes."""
    keys = sorted(monthly_vals)
    changes: dict[tuple[int, int], float] = {}
    for i in range(1, len(keys)):
        changes[keys[i]] = monthly_vals[keys[i]] - monthly_vals[keys[i - 1]]
    return changes


def _ols_multivariate(X: list[list[float]], y: list[float]) -> dict:
    """Pure-Python OLS for small matrices. X has intercept column prepended."""
    n = len(y)
    k = len(X[0])
    if n < k + 5:
        return {}

    # X'X
    xtx = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    # X'y
    xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]

    # Gauss-Jordan inversion
    def _inv(mat: list[list[float]]) -> list[list[float]] | None:
        m = len(mat)
        aug = [mat[i][:] + [1.0 if i == j else 0.0 for j in range(m)] for i in range(m)]
        for col in range(m):
            pivot = None
            for row in range(col, m):
                if abs(aug[row][col]) > 1e-12:
                    pivot = row
                    break
            if pivot is None:
                return None
            aug[col], aug[pivot] = aug[pivot], aug[col]
            factor = aug[col][col]
            aug[col] = [v / factor for v in aug[col]]
            for row in range(m):
                if row != col:
                    f = aug[row][col]
                    aug[row] = [aug[row][j] - f * aug[col][j] for j in range(2 * m)]
        return [aug[i][m:] for i in range(m)]

    xtx_inv = _inv(xtx)
    if xtx_inv is None:
        return {}

    # beta = (X'X)^{-1} X'y
    beta = [sum(xtx_inv[i][j] * xty[j] for j in range(k)) for i in range(k)]
    y_hat = [sum(beta[j] * X[i][j] for j in range(k)) for i in range(n)]
    residuals = [y[i] - y_hat[i] for i in range(n)]
    ss_res = sum(r ** 2 for r in residuals)
    ss_tot = sum((yi - sum(y) / n) ** 2 for yi in y)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    df = n - k
    mse = ss_res / df if df > 0 else 0.0
    # Var(beta) = MSE * (X'X)^{-1}
    se = [math.sqrt(mse * xtx_inv[i][i]) if mse * xtx_inv[i][i] >= 0 else None for i in range(k)]
    t_stats = [beta[i] / se[i] if se[i] and se[i] > 0 else None for i in range(k)]
    p_values = [math.erfc(abs(t) / math.sqrt(2)) if t is not None else None for t in t_stats]
    t_crit = 1.96 if df > 120 else (2.042 if df > 30 else (2.228 if df > 10 else 2.571))
    ci_low = [beta[i] - t_crit * se[i] if se[i] is not None else None for i in range(k)]
    ci_high = [beta[i] + t_crit * se[i] if se[i] is not None else None for i in range(k)]
    resid_vol = math.sqrt(ss_res / max(n - 1, 1))

    return {
        "beta": beta, "r_squared": r_squared, "se": se,
        "t_stats": t_stats, "p_values": p_values,
        "ci_low": ci_low, "ci_high": ci_high, "resid_vol": resid_vol,
        "n": n, "df": df,
    }


def _interp(factor: str, beta: float | None, p: float | None) -> str:
    """Generate a plain-language interpretation of a factor beta."""
    if beta is None:
        return "Factor not available."
    sig = "statistically significant" if (p is not None and p < 0.10) else "not statistically significant"
    if factor == "market":
        if beta > 1.2:
            return f"High market sensitivity ({beta:.2f}x) — stock amplifies broad market moves. {sig}."
        elif beta < 0.7:
            return f"Defensive ({beta:.2f}x beta) — less sensitive to broad market than average. {sig}."
        else:
            return f"Market-like sensitivity ({beta:.2f}x beta). {sig}."
    elif factor == "inflation":
        direction = "benefits" if beta > 0 else "is hurt"
        return f"Stock {direction} from rising inflation (beta {beta:.2f}). {sig}."
    elif factor == "rate":
        direction = "benefits from lower rates" if beta < 0 else "is interest-rate sensitive"
        return f"Stock {direction} (beta {beta:.2f}). {sig}."
    elif factor == "fx":
        direction = "benefits from PKR depreciation" if beta > 0 else "is hurt by PKR depreciation"
        return f"Stock {direction} (beta {beta:.2f}). {sig}."
    return f"Beta {beta:.2f}. {sig}."


def compute_factor_model(db: Session, issuer_id: int) -> FactorModelResult:
    issuer = db.get(Issuer, issuer_id)
    security = next((s for s in issuer.securities if s.is_active), None) if issuer else None
    if security is None and issuer and issuer.securities:
        security = issuer.securities[0]
    symbol = security.symbol if security else str(issuer_id)

    notes: list[str] = []
    missing_factors: list[str] = []

    # Market returns (monthly, from daily KSE-100)
    index = db.execute(select(MarketIndex).where(MarketIndex.code == BENCHMARK_CODE)).scalar_one_or_none()
    if index is None:
        return FactorModelResult(
            issuer_id=issuer_id, symbol=symbol,
            model_classification="multi_factor_exposure_model",
            apt_expected_return_status="unavailable",
            window_start="", window_end="", n_monthly_obs=0,
            alpha=None, r_squared=None, residual_vol_monthly=None,
            factors=[], missing_factors=["market"], confidence="insufficient_data",
            notes=["KSE-100 index data not ingested. Run app/ingestion/psx_index.py first."],
        )

    if security is None:
        return FactorModelResult(
            issuer_id=issuer_id, symbol=symbol,
            model_classification="multi_factor_exposure_model",
            apt_expected_return_status="unavailable",
            window_start="", window_end="", n_monthly_obs=0,
            alpha=None, r_squared=None, residual_vol_monthly=None,
            factors=[], missing_factors=["market"], confidence="insufficient_data",
            notes=["No security found for issuer."],
        )

    co_daily = sorted(
        [(b.trade_date, float(b.close)) for b in db.execute(select(PriceOHLCV).where(PriceOHLCV.security_id == security.id)).scalars()],
        key=lambda x: x[0],
    )
    mk_daily = sorted(
        [(b.trade_date, float(b.close)) for b in db.execute(select(IndexOHLCV).where(IndexOHLCV.market_index_id == index.id)).scalars()],
        key=lambda x: x[0],
    )

    co_monthly = _to_monthly_returns(co_daily)
    mk_monthly = _to_monthly_returns(mk_daily)

    # Macro factor monthly changes
    cpi_levels = _get_macro_monthly(db, "NATIONAL_CPI_YOY")   # already YoY, take MoM change
    rate_levels = _get_macro_monthly(db, "SBP_POLICY_RATE")
    fx_levels = _get_macro_monthly(db, "PKR_USD_RATE")

    cpi_changes = _macro_to_changes(cpi_levels)
    rate_changes = _macro_to_changes(rate_levels)
    # FX: convert to % return (PKR depreciation = positive)
    fx_returns: dict[tuple[int, int], float] = {}
    fx_sorted = sorted(fx_levels.keys())
    for i in range(1, len(fx_sorted)):
        prev = fx_levels[fx_sorted[i - 1]]
        curr = fx_levels[fx_sorted[i]]
        if prev > 0:
            fx_returns[fx_sorted[i]] = (curr - prev) / prev

    if not cpi_levels:
        missing_factors.append("inflation")
        notes.append("CPI data not ingested — run app/ingestion/sbp_macro.py (NATIONAL_CPI_YOY).")
    if not rate_levels:
        missing_factors.append("rate")
        notes.append("Policy rate data not ingested — run app/ingestion/sbp_macro.py (SBP_POLICY_RATE).")
    if not fx_levels:
        missing_factors.append("fx")
        notes.append("PKR/USD data not ingested — run app/ingestion/sbp_macro.py (PKR_USD_RATE).")

    # Common months across all available factors
    common = set(co_monthly) & set(mk_monthly)
    if cpi_changes:
        common &= set(cpi_changes)
    if rate_changes:
        common &= set(rate_changes)
    if fx_returns:
        common &= set(fx_returns)
    common_sorted = sorted(common)

    if len(common_sorted) < MIN_MONTHLY_OBS:
        notes.append(
            f"Only {len(common_sorted)} common monthly observations — minimum {MIN_MONTHLY_OBS} required. "
            "Factor model results not computed."
        )
        return FactorModelResult(
            issuer_id=issuer_id, symbol=symbol,
            model_classification="multi_factor_exposure_model",
            apt_expected_return_status="unavailable",
            window_start=common_sorted[0][0].__str__() if common_sorted else "",
            window_end=common_sorted[-1][0].__str__() if common_sorted else "",
            n_monthly_obs=len(common_sorted),
            alpha=None, r_squared=None, residual_vol_monthly=None,
            factors=[], missing_factors=missing_factors, confidence="insufficient_data",
            notes=notes,
        )

    y = [co_monthly[m] for m in common_sorted]
    # X matrix: [intercept, market, inflation, rate, fx]
    active_factors: list[str] = ["market"]
    X_cols: list[list[float]] = [[mk_monthly[m] for m in common_sorted]]
    if cpi_changes:
        active_factors.append("inflation")
        X_cols.append([cpi_changes.get(m, 0.0) for m in common_sorted])
    if rate_changes:
        active_factors.append("rate")
        X_cols.append([rate_changes.get(m, 0.0) for m in common_sorted])
    if fx_returns:
        active_factors.append("fx")
        X_cols.append([fx_returns.get(m, 0.0) for m in common_sorted])

    # Add intercept
    X = [[1.0] + [X_cols[j][i] for j in range(len(X_cols))] for i in range(len(common_sorted))]
    stats = _ols_multivariate(X, y)

    if not stats:
        notes.append("OLS failed to converge — multicollinearity likely.")
        return FactorModelResult(
            issuer_id=issuer_id, symbol=symbol,
            model_classification="multi_factor_exposure_model",
            apt_expected_return_status="unavailable",
            window_start=str(common_sorted[0]), window_end=str(common_sorted[-1]),
            n_monthly_obs=len(common_sorted),
            alpha=None, r_squared=None, residual_vol_monthly=None,
            factors=[], missing_factors=missing_factors, confidence="insufficient_data",
            notes=notes,
        )

    betas = stats["beta"]
    alpha = betas[0]  # intercept
    factor_betas = betas[1:]
    factor_exposures: list[FactorExposure] = []
    for i, fname in enumerate(active_factors):
        b = factor_betas[i] if i < len(factor_betas) else None
        se = stats["se"][i + 1] if i + 1 < len(stats["se"]) else None
        t = stats["t_stats"][i + 1] if i + 1 < len(stats["t_stats"]) else None
        p = stats["p_values"][i + 1] if i + 1 < len(stats["p_values"]) else None
        cl = stats["ci_low"][i + 1] if i + 1 < len(stats["ci_low"]) else None
        ch = stats["ci_high"][i + 1] if i + 1 < len(stats["ci_high"]) else None
        factor_exposures.append(FactorExposure(
            factor_name=fname,
            beta=round(b, 4) if b is not None else None,
            beta_se=round(se, 4) if se is not None else None,
            t_stat=round(t, 3) if t is not None else None,
            p_value=round(p, 4) if p is not None else None,
            ci_low=round(cl, 4) if cl is not None else None,
            ci_high=round(ch, 4) if ch is not None else None,
            interpretation=_interp(fname, b, p),
            data_available=True,
        ))

    # Add stub entries for missing factors
    for mf in missing_factors:
        factor_exposures.append(FactorExposure(
            factor_name=mf, beta=None, beta_se=None, t_stat=None,
            p_value=None, ci_low=None, ci_high=None,
            interpretation="Factor data not ingested.",
            data_available=False,
        ))

    n = len(common_sorted)
    r2 = stats.get("r_squared")
    confidence = "high" if (n >= PREFERRED_OBS and r2 is not None and r2 > 0.25) else (
        "medium" if n >= MIN_MONTHLY_OBS else "insufficient_data"
    )
    notes.append(
        "This is a multi-factor EXPOSURE model. Factor risk premia (λ_k) have not been "
        "estimated via cross-sectional Fama-MacBeth or factor-mimicking portfolios. "
        "APT expected-return decomposition is unavailable for this reason (Blueprint §8.4)."
    )

    return FactorModelResult(
        issuer_id=issuer_id,
        symbol=symbol,
        model_classification="multi_factor_exposure_model",
        apt_expected_return_status="unavailable",
        window_start=f"{common_sorted[0][0]}-{common_sorted[0][1]:02d}",
        window_end=f"{common_sorted[-1][0]}-{common_sorted[-1][1]:02d}",
        n_monthly_obs=n,
        alpha=round(alpha * 100, 3) if alpha is not None else None,
        r_squared=round(r2, 4) if r2 is not None else None,
        residual_vol_monthly=round(stats["resid_vol"] * 100, 3) if "resid_vol" in stats else None,
        factors=factor_exposures,
        missing_factors=missing_factors,
        confidence=confidence,
        notes=notes,
    )
