"""Enhanced CAPM engine with full OLS diagnostics (Blueprint Section 7).

Extends the existing beta.py (which computes Cov/Var beta) to produce:
- OLS beta and intercept (Jensen's alpha)
- R², residual volatility, annualised alpha
- t-statistic, p-value (normal approximation, accurate for n > 30)
- 95% confidence interval
- Up-market and down-market beta (asymmetric sensitivity)
- Rolling 52-week beta (weekly data)
- Required return: R_f + beta × ERP (base, low-ERP, high-ERP scenarios)

Returns a CAPMDiagnostics dataclass. No side effects on the DB —
the existing compute_and_store_beta (beta.py) is the persistence path;
this module is evidence-assembly for the analyst packet.

Interpretation rules (Blueprint Section 7.5):
- The LLM may interpret beta magnitude, reliability, and asymmetry.
- It must NOT claim that beta predicts price direction.
- CAPM required return is the default WACC cost-of-equity input;
  APT remains a risk cross-check until PSX factor premia are stable.
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CapmAssumption, IndexOHLCV, Issuer, MarketIndex, PriceOHLCV, Security

logger = logging.getLogger(__name__)

MIN_WEEKLY_OBS = 52    # ~1 year minimum; 2 years preferred
BENCHMARK_CODE = "KSE100"
WEEKS_PER_YEAR = 52


@dataclass
class RollingBetaPoint:
    window_end: str     # ISO date
    beta: float
    n_obs: int


@dataclass
class CAPMDiagnostics:
    issuer_id: int
    symbol: str
    benchmark: str
    window_label: str           # e.g. "2yr weekly"
    start_date: str
    end_date: str
    n_obs: int
    # OLS estimates
    beta: float | None
    alpha_weekly: float | None      # weekly Jensen's alpha
    alpha_annualised: float | None  # alpha × 52
    r_squared: float | None
    residual_vol_weekly: float | None
    residual_vol_annualised: float | None
    # Statistical tests
    beta_se: float | None
    beta_t_stat: float | None
    beta_p_value: float | None
    beta_ci_low: float | None       # 95% CI lower bound
    beta_ci_high: float | None      # 95% CI upper bound
    # Asymmetric beta
    up_market_beta: float | None
    down_market_beta: float | None
    asymmetry_note: str | None
    # Liquidity / data quality
    zero_return_pct: float | None   # fraction of obs with exactly zero return
    stale_price_warning: bool
    # CAPM required return (annualised, percent)
    risk_free_rate_pct: float | None
    erp_pct: float | None           # equity risk premium used
    required_return_pct: float | None
    required_return_low_pct: float | None   # ERP - 1pp
    required_return_high_pct: float | None  # ERP + 1pp
    # Rolling beta time series
    rolling_beta: list[RollingBetaPoint]
    # Diagnostics
    confidence: str     # high | medium | low
    confidence_notes: list[str]


def _to_weekly_series(daily_bars: list[tuple[date, float]]) -> list[tuple[date, float]]:
    """Resample daily close bars to weekly (last close of each ISO week)."""
    from collections import defaultdict
    buckets: dict[tuple[int, int], list[tuple[date, float]]] = defaultdict(list)
    for d, close in daily_bars:
        iso = d.isocalendar()
        buckets[(iso.year, iso.week)].append((d, close))
    weekly = []
    for key in sorted(buckets):
        week_bars = sorted(buckets[key], key=lambda x: x[0])
        weekly.append(week_bars[-1])  # last close of week
    return weekly


def _returns(bars: list[tuple[date, float]]) -> list[tuple[date, float]]:
    """Close-to-close returns [(date, return), ...]."""
    result = []
    for i in range(1, len(bars)):
        prev_close = bars[i - 1][1]
        curr_date, curr_close = bars[i]
        if prev_close > 0:
            result.append((curr_date, (curr_close - prev_close) / prev_close))
    return result


def _ols_stats(x: list[float], y: list[float]) -> dict:
    """OLS regression y = alpha + beta * x. Returns dict of stats."""
    n = len(x)
    if n < 10:
        return {}
    x_bar = sum(x) / n
    y_bar = sum(y) / n
    ss_xx = sum((xi - x_bar) ** 2 for xi in x)
    ss_xy = sum((xi - x_bar) * (yi - y_bar) for xi, yi in zip(x, y))
    ss_yy = sum((yi - y_bar) ** 2 for yi in y)
    if ss_xx == 0:
        return {}
    beta = ss_xy / ss_xx
    alpha = y_bar - beta * x_bar
    y_hat = [alpha + beta * xi for xi in x]
    residuals = [yi - yhi for yi, yhi in zip(y, y_hat)]
    ss_res = sum(r ** 2 for r in residuals)
    r_squared = 1 - ss_res / ss_yy if ss_yy > 0 else 0.0
    df = n - 2
    mse = ss_res / df if df > 0 else 0.0
    se_beta = math.sqrt(mse / ss_xx) if ss_xx > 0 else None
    t_stat = beta / se_beta if se_beta and se_beta > 0 else None
    # p-value: two-tailed using normal approximation (accurate for n > 30)
    p_value = math.erfc(abs(t_stat) / math.sqrt(2)) if t_stat is not None else None
    # 95% CI using t_critical (normal approx for large df)
    t_crit = _t_critical(df)
    ci_low = beta - t_crit * se_beta if se_beta is not None else None
    ci_high = beta + t_crit * se_beta if se_beta is not None else None
    resid_vol = math.sqrt(sum(r ** 2 for r in residuals) / max(n - 1, 1))

    return {
        "beta": beta, "alpha": alpha, "r_squared": r_squared,
        "se_beta": se_beta, "t_stat": t_stat, "p_value": p_value,
        "ci_low": ci_low, "ci_high": ci_high, "resid_vol": resid_vol,
        "n": n,
    }


def _t_critical(df: int, alpha: float = 0.05) -> float:
    """Two-tailed t-critical at alpha significance. Normal approx for large df."""
    table = {1: 12.706, 2: 4.303, 3: 3.182, 5: 2.571, 10: 2.228,
             20: 2.086, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980}
    for df_key in sorted(table.keys(), reverse=True):
        if df >= df_key:
            return table[df_key]
    return 12.706


def compute_capm_diagnostics(db: Session, issuer_id: int) -> CAPMDiagnostics | None:
    issuer = db.get(Issuer, issuer_id)
    if issuer is None:
        return None
    security = next((s for s in issuer.securities if s.is_active), None) or (issuer.securities[0] if issuer.securities else None)
    if security is None:
        return None
    symbol = security.symbol or str(issuer_id)

    index = db.execute(select(MarketIndex).where(MarketIndex.code == BENCHMARK_CODE)).scalar_one_or_none()
    if index is None:
        return None

    company_bars = sorted(
        [(b.trade_date, float(b.close)) for b in db.execute(select(PriceOHLCV).where(PriceOHLCV.security_id == security.id)).scalars()],
        key=lambda x: x[0],
    )
    market_bars = sorted(
        [(b.trade_date, float(b.close)) for b in db.execute(select(IndexOHLCV).where(IndexOHLCV.market_index_id == index.id)).scalars()],
        key=lambda x: x[0],
    )

    company_weekly = _to_weekly_series(company_bars)
    market_weekly = _to_weekly_series(market_bars)

    company_ret = {d: r for d, r in _returns(company_weekly)}
    market_ret = {d: r for d, r in _returns(market_weekly)}
    common_dates = sorted(set(company_ret) & set(market_ret))

    confidence_notes: list[str] = []

    if len(common_dates) < MIN_WEEKLY_OBS:
        confidence_notes.append(f"Only {len(common_dates)} overlapping weekly obs (minimum {MIN_WEEKLY_OBS}).")
        return CAPMDiagnostics(
            issuer_id=issuer_id, symbol=symbol, benchmark=BENCHMARK_CODE,
            window_label="weekly", start_date="", end_date="",
            n_obs=len(common_dates), beta=None, alpha_weekly=None,
            alpha_annualised=None, r_squared=None, residual_vol_weekly=None,
            residual_vol_annualised=None, beta_se=None, beta_t_stat=None,
            beta_p_value=None, beta_ci_low=None, beta_ci_high=None,
            up_market_beta=None, down_market_beta=None, asymmetry_note=None,
            zero_return_pct=None, stale_price_warning=False,
            risk_free_rate_pct=None, erp_pct=None,
            required_return_pct=None, required_return_low_pct=None, required_return_high_pct=None,
            rolling_beta=[], confidence="low",
            confidence_notes=confidence_notes,
        )

    co_ret = [company_ret[d] for d in common_dates]
    mk_ret = [market_ret[d] for d in common_dates]

    # Risk-free rate: use most recent CapmAssumption
    capm_assump = db.execute(
        select(CapmAssumption)
        .where(CapmAssumption.issuer_id == issuer_id)
        .order_by(CapmAssumption.as_of_date.desc())
    ).scalars().first()
    if capm_assump is None:
        capm_assump = db.execute(
            select(CapmAssumption).where(CapmAssumption.issuer_id.is_(None)).order_by(CapmAssumption.as_of_date.desc())
        ).scalars().first()

    rf_annual = float(capm_assump.risk_free_rate_pct) if capm_assump else 10.0  # fallback 10%
    erp_annual = float(capm_assump.base_equity_risk_premium_pct + capm_assump.country_risk_premium_pct) if capm_assump else 6.0
    rf_weekly = (1 + rf_annual / 100) ** (1 / WEEKS_PER_YEAR) - 1

    # Excess returns
    co_excess = [r - rf_weekly for r in co_ret]
    mk_excess = [r - rf_weekly for r in mk_ret]

    stats = _ols_stats(mk_excess, co_excess)

    # Up/down-market beta
    up_x = [m for m in mk_excess if m > 0]
    up_y = [co_excess[i] for i, m in enumerate(mk_excess) if m > 0]
    dn_x = [m for m in mk_excess if m <= 0]
    dn_y = [co_excess[i] for i, m in enumerate(mk_excess) if m <= 0]
    up_stats = _ols_stats(up_x, up_y) if len(up_x) > 10 else {}
    dn_stats = _ols_stats(dn_x, dn_y) if len(dn_x) > 10 else {}
    up_beta = up_stats.get("beta")
    dn_beta = dn_stats.get("beta")

    asym_note = None
    if up_beta is not None and dn_beta is not None:
        if dn_beta > up_beta * 1.2:
            asym_note = "Stock falls more than it rises relative to the market — downside asymmetry."
        elif up_beta > dn_beta * 1.2:
            asym_note = "Stock rises more than it falls relative to the market — upside asymmetry."
        else:
            asym_note = "Beta is broadly symmetric across up and down market periods."

    # Zero-return fraction (stale-price proxy)
    zero_count = sum(1 for r in co_ret if r == 0.0)
    zero_pct = zero_count / len(co_ret) if co_ret else 0.0
    stale_warning = zero_pct > 0.30

    if stale_warning:
        confidence_notes.append(f"{zero_pct*100:.0f}% zero-return days detected — stale pricing may bias beta.")

    # Rolling 52-week beta
    rolling: list[RollingBetaPoint] = []
    window = 52
    for i in range(window, len(common_dates)):
        window_dates = common_dates[i - window: i]
        wx = [market_ret[d] - rf_weekly for d in window_dates]
        wy = [company_ret[d] - rf_weekly for d in window_dates]
        ws = _ols_stats(wx, wy)
        if ws and "beta" in ws:
            rolling.append(RollingBetaPoint(
                window_end=common_dates[i - 1].isoformat(),
                beta=round(ws["beta"], 3),
                n_obs=window,
            ))

    # Confidence assessment
    n = len(common_dates)
    beta_val = stats.get("beta")
    r2 = stats.get("r_squared")
    p_val = stats.get("p_value")
    if n >= 104 and p_val is not None and p_val < 0.05 and r2 is not None and r2 > 0.10:
        confidence = "high"
    elif n >= 52 and p_val is not None and p_val < 0.10:
        confidence = "medium"
    else:
        confidence = "low"
        confidence_notes.append("Beta not statistically significant at 10% level — treat with caution.")

    if zero_pct > 0.15:
        if confidence == "high":
            confidence = "medium"
        confidence_notes.append(f"Elevated zero-return fraction ({zero_pct*100:.0f}%) — illiquidity may distort beta.")

    # Required return
    req_return = rf_annual + (beta_val or 1.0) * erp_annual if beta_val is not None else None

    return CAPMDiagnostics(
        issuer_id=issuer_id,
        symbol=symbol,
        benchmark=BENCHMARK_CODE,
        window_label=f"{n // WEEKS_PER_YEAR}yr weekly ({n} obs)",
        start_date=common_dates[0].isoformat(),
        end_date=common_dates[-1].isoformat(),
        n_obs=n,
        beta=round(beta_val, 4) if beta_val is not None else None,
        alpha_weekly=round(stats["alpha"], 5) if "alpha" in stats else None,
        alpha_annualised=round(stats["alpha"] * WEEKS_PER_YEAR * 100, 2) if "alpha" in stats else None,
        r_squared=round(r2, 4) if r2 is not None else None,
        residual_vol_weekly=round(stats["resid_vol"], 5) if "resid_vol" in stats else None,
        residual_vol_annualised=round(stats["resid_vol"] * math.sqrt(WEEKS_PER_YEAR) * 100, 2) if "resid_vol" in stats else None,
        beta_se=round(stats["se_beta"], 4) if stats.get("se_beta") is not None else None,
        beta_t_stat=round(stats["t_stat"], 3) if stats.get("t_stat") is not None else None,
        beta_p_value=round(p_val, 4) if p_val is not None else None,
        beta_ci_low=round(stats["ci_low"], 4) if stats.get("ci_low") is not None else None,
        beta_ci_high=round(stats["ci_high"], 4) if stats.get("ci_high") is not None else None,
        up_market_beta=round(up_beta, 3) if up_beta is not None else None,
        down_market_beta=round(dn_beta, 3) if dn_beta is not None else None,
        asymmetry_note=asym_note,
        zero_return_pct=round(zero_pct * 100, 1),
        stale_price_warning=stale_warning,
        risk_free_rate_pct=rf_annual,
        erp_pct=erp_annual,
        required_return_pct=round(req_return, 2) if req_return is not None else None,
        required_return_low_pct=round(rf_annual + (beta_val or 1.0) * (erp_annual - 1.0), 2) if beta_val is not None else None,
        required_return_high_pct=round(rf_annual + (beta_val or 1.0) * (erp_annual + 1.0), 2) if beta_val is not None else None,
        rolling_beta=rolling[-24:] if rolling else [],  # last 24 points for display
        confidence=confidence,
        confidence_notes=confidence_notes,
    )
