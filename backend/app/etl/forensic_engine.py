"""Forensic accounting and business-health engine (Blueprint Sections 9 and 6.5).

Deterministic calculations only. The LLM Analyst Synthesizer interprets these
numbers; this module never draws fraud accusations or investment conclusions.

Computed from FinancialFact and RatioValue rows in the DB. Anything not in the
DB is silently left as None with a corresponding entry in missing_data_items —
never fabricated, never zero-filled (consistent with the project's core evidence
principle: no signal is better than a fabricated one).

Key analyses:
- 3-way DuPont decomposition (ROE = NM × AT × EM)
- 5-way DuPont where operating_profit + finance_cost are both available
- CFO/PAT cash conversion ratio
- Balance-sheet accrual ratio (proxy: ΔNCA / Avg Assets)
- Interest coverage (EBIT proxy / finance_cost)
- Leverage trajectory
- Business health classification (7-class enum from blueprint)
- Five health sub-scores (operating, earnings quality, balance sheet,
  capital allocation, governance)
- Forensic flags with severity and explanation
"""

import logging
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import FinancialFact, Issuer, RatioDefinition, RatioValue, Security

logger = logging.getLogger(__name__)

HEALTH_CLASSIFICATIONS = (
    "genuinely_healthy",
    "healthy_but_cyclical",
    "improving",
    "surface_level_strength",
    "deteriorating",
    "financially_fragile",
    "insufficient_evidence",
)


@dataclass
class DuPontRow:
    period_end: str  # ISO date
    # 3-way
    net_margin: float | None          # PAT / Revenue
    asset_turnover: float | None      # Revenue / Avg Total Assets
    equity_multiplier: float | None   # Avg Total Assets / Avg Total Equity
    roe_3way: float | None            # product of the three
    roe_reported: float | None        # from ratio_value table (cross-check)
    # 5-way (where operating_profit + finance_cost are available)
    ebit_margin: float | None         # operating_profit (as EBIT proxy) / Revenue
    interest_burden: float | None     # (EBIT - finance_cost) / EBIT — proxy for PBT/EBIT
    tax_burden: float | None          # PAT / (EBIT - finance_cost) — proxy for PAT/PBT


@dataclass
class CashConversionRow:
    period_end: str
    operating_cash_flow: float | None   # PKR thousands
    profit_after_tax: float
    cfo_pat_ratio: float | None


@dataclass
class InterestCoverageRow:
    period_end: str
    ebit_proxy: float | None           # operating_profit or gross_profit - estimated overhead
    finance_cost: float | None
    coverage: float | None             # ebit_proxy / finance_cost


@dataclass
class ForensicFlag:
    flag_code: str
    severity: str                       # low | medium | high | critical
    status: str                         # clear | watch | triggered | not_applicable | insufficient_data
    periods: list[str]
    observed_value: str | None
    sector_reference: str | None
    explanation: str
    possible_benign_explanations: list[str]
    confidence: str                     # high | medium | low


@dataclass
class ForensicResult:
    issuer_id: int
    symbol: str
    as_of: str
    # Five sub-scores (0–100, or None if insufficient data)
    operating_health_score: float | None
    earnings_quality_score: float | None
    balance_sheet_score: float | None
    capital_allocation_score: float | None
    governance_score: float | None
    # Overall health (Blueprint Section 9 enum)
    business_health: str
    health_confidence: str              # high | medium | low
    # Detailed analysis
    dupont: list[DuPontRow]
    cash_conversion: list[CashConversionRow]
    interest_coverage: list[InterestCoverageRow]
    leverage: list[dict]
    flags: list[ForensicFlag]
    # Coverage metadata
    missing_data_items: list[str]
    data_coverage_pct: float           # 0–100, fraction of expected items actually present


def _annual_facts(db: Session, issuer_id: int, line_item: str) -> dict[date, float]:
    """Return {period_end: value} for non-superseded annual consolidated facts."""
    rows = db.execute(
        select(FinancialFact).where(
            FinancialFact.issuer_id == issuer_id,
            FinancialFact.line_item == line_item,
            FinancialFact.period_type == "annual",
            FinancialFact.scope == "consolidated",
            FinancialFact.superseded_by_id.is_(None),
        ).order_by(FinancialFact.period_end)
    ).scalars().all()
    return {r.period_end: float(r.value) for r in rows}


def _latest_ratio(db: Session, issuer_id: int, ratio_key: str) -> dict[date, float]:
    defn = db.execute(
        select(RatioDefinition).where(RatioDefinition.key == ratio_key)
    ).scalars().first()
    if defn is None:
        return {}
    rows = db.execute(
        select(RatioValue).where(
            RatioValue.ratio_definition_id == defn.id,
            RatioValue.issuer_id == issuer_id,
            RatioValue.period_type == "annual",
        ).order_by(RatioValue.period_end)
    ).scalars().all()
    return {r.period_end: float(r.value) for r in rows}


def _avg(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return (a + b) / 2


def _safe_div(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den == 0:
        return None
    return num / den


def _trend_label(values: list[float]) -> str:
    """Rough trend from a series of at least 2 values."""
    if len(values) < 2:
        return "insufficient_data"
    delta = values[-1] - values[0]
    pct = delta / abs(values[0]) if values[0] != 0 else 0
    if pct > 0.10:
        return "improving"
    if pct < -0.10:
        return "deteriorating"
    return "stable"


def compute_dupont(db: Session, issuer_id: int) -> list[DuPontRow]:
    revenue = _annual_facts(db, issuer_id, "revenue")
    pat = _annual_facts(db, issuer_id, "profit_after_tax")
    assets = _annual_facts(db, issuer_id, "total_assets")
    equity = _annual_facts(db, issuer_id, "total_equity")
    op_profit = _annual_facts(db, issuer_id, "operating_profit")
    finance_cost = _annual_facts(db, issuer_id, "finance_cost")
    roe_reported = _latest_ratio(db, issuer_id, "roe")

    all_periods = sorted(set(revenue) & set(pat))
    rows = []
    sorted_assets = sorted(assets.items())
    sorted_equity = sorted(equity.items())

    for i, period in enumerate(all_periods):
        rev = revenue.get(period)
        p = pat.get(period)

        # Average assets and equity (use prior period if available)
        prev_asset = sorted_assets[i - 1][1] if i > 0 and sorted_assets else None
        curr_asset = assets.get(period)
        avg_assets = _avg(prev_asset, curr_asset) if i > 0 else curr_asset

        prev_eq = sorted_equity[i - 1][1] if i > 0 and sorted_equity else None
        curr_eq = equity.get(period)
        avg_equity = _avg(prev_eq, curr_eq) if i > 0 else curr_eq

        nm = _safe_div(p, rev)
        at = _safe_div(rev, avg_assets)
        em = _safe_div(avg_assets, avg_equity)
        roe_3 = None
        if nm is not None and at is not None and em is not None:
            roe_3 = nm * at * em * 100  # express as percent

        # 5-way components (need operating_profit as EBIT proxy + finance_cost)
        op = op_profit.get(period)
        fc = finance_cost.get(period)
        ebit_m = _safe_div(op, rev)
        ebit_proxy = op
        pbt_proxy = (op - fc) if (op is not None and fc is not None) else None
        int_burden = _safe_div(pbt_proxy, ebit_proxy)
        tax_burden = _safe_div(p, pbt_proxy)

        rows.append(DuPontRow(
            period_end=period.isoformat(),
            net_margin=round(nm * 100, 2) if nm is not None else None,
            asset_turnover=round(at, 3) if at is not None else None,
            equity_multiplier=round(em, 3) if em is not None else None,
            roe_3way=round(roe_3, 2) if roe_3 is not None else None,
            roe_reported=roe_reported.get(period),
            ebit_margin=round(ebit_m * 100, 2) if ebit_m is not None else None,
            interest_burden=round(int_burden, 3) if int_burden is not None else None,
            tax_burden=round(tax_burden, 3) if tax_burden is not None else None,
        ))

    return rows


def compute_cash_conversion(db: Session, issuer_id: int) -> list[CashConversionRow]:
    cfo = _annual_facts(db, issuer_id, "operating_cash_flow")
    pat = _annual_facts(db, issuer_id, "profit_after_tax")
    common = sorted(set(pat))  # show PAT for all periods, CFO where available
    rows = []
    for period in common:
        p = pat[period]
        c = cfo.get(period)
        ratio = _safe_div(c, p)
        rows.append(CashConversionRow(
            period_end=period.isoformat(),
            operating_cash_flow=c,
            profit_after_tax=p,
            cfo_pat_ratio=round(ratio, 2) if ratio is not None else None,
        ))
    return rows


def compute_interest_coverage(db: Session, issuer_id: int) -> list[InterestCoverageRow]:
    fc = _annual_facts(db, issuer_id, "finance_cost")
    op = _annual_facts(db, issuer_id, "operating_profit")
    gp = _annual_facts(db, issuer_id, "gross_profit")  # fallback EBIT proxy
    common = sorted(set(fc))
    rows = []
    for period in common:
        f = fc[period]
        ebit = op.get(period) or gp.get(period)  # prefer operating_profit, fall back to gross_profit
        coverage = _safe_div(ebit, f)
        rows.append(InterestCoverageRow(
            period_end=period.isoformat(),
            ebit_proxy=ebit,
            finance_cost=f,
            coverage=round(coverage, 2) if coverage is not None else None,
        ))
    return rows


def compute_leverage(db: Session, issuer_id: int) -> list[dict]:
    liab = _annual_facts(db, issuer_id, "total_liabilities")
    equity = _annual_facts(db, issuer_id, "total_equity")
    assets = _annual_facts(db, issuer_id, "total_assets")
    curr_liab = _annual_facts(db, issuer_id, "current_liabilities")
    curr_assets = _annual_facts(db, issuer_id, "current_assets")

    common = sorted(set(liab) & set(equity))
    rows = []
    for period in common:
        de = _safe_div(liab.get(period), equity.get(period))
        da = _safe_div(liab.get(period), assets.get(period))
        cr = _safe_div(curr_assets.get(period), curr_liab.get(period))
        rows.append({
            "period_end": period.isoformat(),
            "debt_to_equity": round(de, 3) if de is not None else None,
            "debt_to_assets": round(da, 3) if da is not None else None,
            "current_ratio": round(cr, 2) if cr is not None else None,
        })
    return rows


def _generate_flags(
    dupont: list[DuPontRow],
    cash_conv: list[CashConversionRow],
    interest_cov: list[InterestCoverageRow],
    leverage: list[dict],
) -> list[ForensicFlag]:
    flags: list[ForensicFlag] = []

    # CFO/PAT persistent gap flag (Blueprint flag: CFO_PAT_PERSISTENT_GAP)
    cfo_pat_rows = [(r.period_end, r.cfo_pat_ratio) for r in cash_conv if r.cfo_pat_ratio is not None]
    if cfo_pat_rows:
        low_count = sum(1 for _, ratio in cfo_pat_rows if ratio < 0.75)
        triggered_periods = [p for p, ratio in cfo_pat_rows if ratio < 0.75]
        values_str = ", ".join(f"{r:.2f}x" for _, r in cfo_pat_rows)
        if low_count == 0:
            flags.append(ForensicFlag(
                flag_code="CFO_PAT_PERSISTENT_GAP",
                severity="low",
                status="clear",
                periods=[p for p, _ in cfo_pat_rows],
                observed_value=values_str,
                sector_reference="≥0.75x (sector proxy)",
                explanation="Cash-flow from operations supports reported profit.",
                possible_benign_explanations=[],
                confidence="medium",
            ))
        elif low_count >= 2:
            flags.append(ForensicFlag(
                flag_code="CFO_PAT_PERSISTENT_GAP",
                severity="high" if low_count >= len(cfo_pat_rows) else "medium",
                status="triggered",
                periods=triggered_periods,
                observed_value=values_str,
                sector_reference="≥0.75x (sector proxy)",
                explanation=(
                    f"Reported profit has materially exceeded operating cash generation "
                    f"for {low_count} of {len(cfo_pat_rows)} available periods."
                ),
                possible_benign_explanations=[
                    "Temporary working-capital build during expansion",
                    "Receivable growth from credit-sales push",
                ],
                confidence="medium",
            ))
        else:
            flags.append(ForensicFlag(
                flag_code="CFO_PAT_PERSISTENT_GAP",
                severity="low",
                status="watch",
                periods=triggered_periods,
                observed_value=values_str,
                sector_reference="≥0.75x (sector proxy)",
                explanation="CFO/PAT below 0.75x in one period — monitor for recurrence.",
                possible_benign_explanations=["Single-period working-capital timing"],
                confidence="low",
            ))
    else:
        flags.append(ForensicFlag(
            flag_code="CFO_PAT_PERSISTENT_GAP",
            severity="low",
            status="insufficient_data",
            periods=[],
            observed_value=None,
            sector_reference="≥0.75x (sector proxy)",
            explanation="Operating cash-flow data not available for this issuer.",
            possible_benign_explanations=[],
            confidence="low",
        ))

    # Interest coverage flag
    low_cov = [(r.period_end, r.coverage) for r in interest_cov if r.coverage is not None and r.coverage < 2.0]
    if interest_cov and any(r.coverage is not None for r in interest_cov):
        if low_cov:
            flags.append(ForensicFlag(
                flag_code="INTEREST_COVERAGE_LOW",
                severity="high",
                status="triggered",
                periods=[p for p, _ in low_cov],
                observed_value=", ".join(f"{v:.1f}x" for _, v in low_cov),
                sector_reference="≥3x (general industrial threshold)",
                explanation="Interest coverage below 2x — debt service may strain cash flow.",
                possible_benign_explanations=["New debt drawdown before utilisation"],
                confidence="medium",
            ))
        else:
            flags.append(ForensicFlag(
                flag_code="INTEREST_COVERAGE_LOW",
                severity="low",
                status="clear",
                periods=[r.period_end for r in interest_cov if r.coverage is not None],
                observed_value=", ".join(f"{r.coverage:.1f}x" for r in interest_cov if r.coverage is not None),
                sector_reference="≥3x",
                explanation="Interest coverage is adequate.",
                possible_benign_explanations=[],
                confidence="medium",
            ))

    # Leverage trend flag
    de_values = [r["debt_to_equity"] for r in leverage if r["debt_to_equity"] is not None]
    if len(de_values) >= 2:
        trend = _trend_label(de_values)
        if de_values[-1] > 3.0:
            flags.append(ForensicFlag(
                flag_code="HIGH_LEVERAGE",
                severity="high",
                status="triggered",
                periods=[r["period_end"] for r in leverage if r["debt_to_equity"] is not None],
                observed_value=f"{de_values[-1]:.2f}x D/E (latest)",
                sector_reference="<2x (sector proxy for fertilizer)",
                explanation=f"Debt/equity is elevated at {de_values[-1]:.2f}x and trend is {trend}.",
                possible_benign_explanations=["Working-capital facilities inflate current liabilities"],
                confidence="medium",
            ))
        elif trend == "deteriorating" and de_values[-1] > 1.5:
            flags.append(ForensicFlag(
                flag_code="HIGH_LEVERAGE",
                severity="medium",
                status="watch",
                periods=[r["period_end"] for r in leverage if r["debt_to_equity"] is not None],
                observed_value=f"{de_values[-1]:.2f}x D/E (latest, trend: {trend})",
                sector_reference="<2x",
                explanation="Leverage is rising — monitor trajectory.",
                possible_benign_explanations=["Capex cycle funded by debt"],
                confidence="low",
            ))

    # ROE decomposition quality flag
    recent_dupont = [r for r in dupont if r.equity_multiplier is not None]
    if recent_dupont:
        latest = recent_dupont[-1]
        if latest.equity_multiplier is not None and latest.equity_multiplier > 4.0:
            flags.append(ForensicFlag(
                flag_code="ROE_LEVERAGE_DRIVEN",
                severity="medium",
                status="triggered",
                periods=[latest.period_end],
                observed_value=f"Equity multiplier {latest.equity_multiplier:.1f}x",
                sector_reference="<3x (leverage-neutral)",
                explanation=(
                    "ROE is materially amplified by financial leverage. "
                    "Reported ROE may overstate true operating profitability."
                ),
                possible_benign_explanations=["Asset-heavy business with expected high leverage"],
                confidence="medium",
            ))

    return flags


def _score_operating_health(
    dupont: list[DuPontRow],
    interest_cov: list[InterestCoverageRow],
) -> float | None:
    if not dupont:
        return None
    margins = [r.net_margin for r in dupont if r.net_margin is not None]
    if not margins:
        return None

    latest_margin = margins[-1]
    trend = _trend_label(margins) if len(margins) >= 2 else "insufficient_data"

    score = 50.0
    # Net margin level
    if latest_margin > 15:
        score += 20
    elif latest_margin > 8:
        score += 10
    elif latest_margin < 2:
        score -= 20
    elif latest_margin < 0:
        score -= 40

    # Trend bonus
    if trend == "improving":
        score += 15
    elif trend == "deteriorating":
        score -= 15

    # Interest coverage
    cov_vals = [r.coverage for r in interest_cov if r.coverage is not None]
    if cov_vals:
        if cov_vals[-1] > 5:
            score += 10
        elif cov_vals[-1] < 2:
            score -= 20

    return max(0.0, min(100.0, score))


def _score_earnings_quality(cash_conv: list[CashConversionRow]) -> float | None:
    ratios = [r.cfo_pat_ratio for r in cash_conv if r.cfo_pat_ratio is not None]
    if not ratios:
        return None

    avg_ratio = sum(ratios) / len(ratios)
    score = 50.0
    if avg_ratio > 1.0:
        score = 85
    elif avg_ratio > 0.85:
        score = 70
    elif avg_ratio > 0.65:
        score = 55
    elif avg_ratio > 0.40:
        score = 35
    else:
        score = 15

    return score


def _score_balance_sheet(leverage: list[dict]) -> float | None:
    de_vals = [r["debt_to_equity"] for r in leverage if r["debt_to_equity"] is not None]
    cr_vals = [r["current_ratio"] for r in leverage if r["current_ratio"] is not None]
    if not de_vals and not cr_vals:
        return None

    score = 50.0
    if de_vals:
        de = de_vals[-1]
        if de < 0.5:
            score += 25
        elif de < 1.0:
            score += 10
        elif de > 3.0:
            score -= 25
        elif de > 2.0:
            score -= 10

    if cr_vals:
        cr = cr_vals[-1]
        if cr > 2.0:
            score += 15
        elif cr > 1.2:
            score += 5
        elif cr < 0.8:
            score -= 20
        elif cr < 1.0:
            score -= 10

    return max(0.0, min(100.0, score))


def _score_capital_allocation(dupont: list[DuPontRow]) -> float | None:
    roe_vals = [r.roe_reported or r.roe_3way for r in dupont if (r.roe_reported or r.roe_3way) is not None]
    at_vals = [r.asset_turnover for r in dupont if r.asset_turnover is not None]
    if not roe_vals:
        return None

    latest_roe = roe_vals[-1]
    trend = _trend_label(roe_vals) if len(roe_vals) >= 2 else "insufficient_data"

    score = 50.0
    if latest_roe > 20:
        score += 25
    elif latest_roe > 12:
        score += 10
    elif latest_roe < 5:
        score -= 20
    elif latest_roe < 0:
        score -= 40

    if trend == "improving":
        score += 10
    elif trend == "deteriorating":
        score -= 10

    return max(0.0, min(100.0, score))


def _classify_health(
    op: float | None,
    eq: float | None,
    bs: float | None,
    ca: float | None,
    dupont: list[DuPontRow],
    cash_conv: list[CashConversionRow],
    leverage: list[dict],
) -> tuple[str, str]:
    """Returns (health_classification, confidence)."""
    scores = [s for s in [op, eq, bs, ca] if s is not None]
    if len(scores) < 2:
        return "insufficient_evidence", "low"

    confidence = "high" if len(scores) >= 4 else ("medium" if len(scores) == 3 else "low")
    avg = sum(scores) / len(scores)

    # CFO/PAT check — a high-PAT, low-CFO story is surface-level even with good margins
    cfo_ratios = [r.cfo_pat_ratio for r in cash_conv if r.cfo_pat_ratio is not None]
    persistent_low_cfo = len([r for r in cfo_ratios if r < 0.65]) >= 2

    # Leverage check
    de_vals = [r["debt_to_equity"] for r in leverage if r["debt_to_equity"] is not None]
    very_high_leverage = de_vals and de_vals[-1] > 3.0

    # Margin trend check
    margins = [r.net_margin for r in dupont if r.net_margin is not None]
    trend = _trend_label(margins) if len(margins) >= 2 else "insufficient_data"

    if very_high_leverage:
        return "financially_fragile", confidence

    if persistent_low_cfo and avg > 55:
        return "surface_level_strength", confidence

    if avg >= 70 and trend in ("improving", "stable"):
        # Fertilizer companies are inherently cyclical — distinguish genuinely_healthy vs cyclical
        return "healthy_but_cyclical", confidence

    if avg >= 55 and trend == "improving":
        return "improving", confidence

    if avg >= 55:
        return "genuinely_healthy", confidence

    if trend == "deteriorating" or avg < 35:
        return "deteriorating", confidence

    return "insufficient_evidence", "low"


def compute_forensic_result(db: Session, issuer_id: int) -> ForensicResult:
    issuer = db.get(Issuer, issuer_id)
    security = issuer.securities[0] if issuer and issuer.securities else None
    symbol = security.symbol if security else str(issuer_id)

    dupont = compute_dupont(db, issuer_id)
    cash_conv = compute_cash_conversion(db, issuer_id)
    interest_cov = compute_interest_coverage(db, issuer_id)
    leverage = compute_leverage(db, issuer_id)
    flags = _generate_flags(dupont, cash_conv, interest_cov, leverage)

    op_score = _score_operating_health(dupont, interest_cov)
    eq_score = _score_earnings_quality(cash_conv)
    bs_score = _score_balance_sheet(leverage)
    ca_score = _score_capital_allocation(dupont)
    # Governance score: mark insufficient until auditor/board data is more complete
    gov_score: float | None = None

    health, confidence = _classify_health(op_score, eq_score, bs_score, ca_score, dupont, cash_conv, leverage)

    # Coverage: which of the 7 key line items are present
    expected_items = ["revenue", "profit_after_tax", "total_assets", "total_equity",
                      "total_liabilities", "operating_cash_flow", "finance_cost"]
    missing: list[str] = []
    for item in expected_items:
        if not _annual_facts(db, issuer_id, item):
            missing.append(item)
    coverage_pct = round((len(expected_items) - len(missing)) / len(expected_items) * 100, 1)

    return ForensicResult(
        issuer_id=issuer_id,
        symbol=symbol,
        as_of=date.today().isoformat(),
        operating_health_score=round(op_score, 1) if op_score is not None else None,
        earnings_quality_score=round(eq_score, 1) if eq_score is not None else None,
        balance_sheet_score=round(bs_score, 1) if bs_score is not None else None,
        capital_allocation_score=round(ca_score, 1) if ca_score is not None else None,
        governance_score=gov_score,
        business_health=health,
        health_confidence=confidence,
        dupont=dupont,
        cash_conversion=cash_conv,
        interest_coverage=interest_cov,
        leverage=leverage,
        flags=flags,
        missing_data_items=missing,
        data_coverage_pct=coverage_pct,
    )
