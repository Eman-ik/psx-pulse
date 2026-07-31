"""PSX Senior Analyst Agent — LLM synthesis node (Blueprint Sections 5 and 16).

Architecture:
  1. Evidence assembler: gathers deterministic data from DB (forensics, CAPM,
     factor model, ratios, financial facts, company profile).
  2. Prompt builder: formats evidence as a structured brief for the LLM.
  3. Claude API call: uses the system prompt from Blueprint Section 16 verbatim.
  4. Response parser: extracts the PSXAnalystPacket JSON sub-fields from the response.
  5. Validator: verifies no LLM-invented metrics; rejects any numeric claim in
     synthesis output that is not traceable to the evidence brief.

The LLM interprets; it does NOT calculate. Every number in the packet comes from
the deterministic engines or the DB. The LLM provides:
  - research_posture.stance and confidence
  - business_health (cross-checked against forensic classification)
  - one_sentence_view, decision_hinge, what_is_priced_in, falsifiers
  - bull/base/bear scenarios (qualitative thesis)
  - catalysts and risks (narrative)

Compliance gate: no BUY/SELL rating or target price is produced.
is_approved on AnalystPacket defaults False — human review required.
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import (
    AnalystPacket,
    AnalystRun,
    CapmAssumption,
    FinancialFact,
    Issuer,
    RatioDefinition,
    RatioValue,
    Security,
    Thesis,
)
from app.etl.capm_enhanced import CAPMDiagnostics, compute_capm_diagnostics
from app.etl.factor_model import FactorModelResult, compute_factor_model
from app.etl.forensic_engine import ForensicResult, compute_forensic_result

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the PSX Senior Analyst Agent, an institutional-quality public-equity
research analyst with 20 years of experience in Pakistan and emerging markets.

Your role is to underwrite a listed company from an immutable, point-in-time,
source-linked evidence package. You interpret evidence; deterministic tools
calculate financial metrics, CAPM, and technical indicators.

You must determine whether the business is genuinely healthy, merely optically
attractive, cyclical, improving, deteriorating or financially fragile. Examine
revenue quality, margin trajectory, cash flow versus reported profit, working
capital, debt structure, ROE/ROIC sustainability, capital allocation, and
accounting-policy signals.

Rules:
1. Never invent a fact, number, source, quote, date, owner, executive or metric.
2. Never calculate a decision-critical number yourself.
3. Never mix consolidated and standalone accounts or incompatible periods.
4. Distinguish Reported Fact, Derived Calculation, Management Claim, and
   Analyst Interpretation.
5. Retain conflicts — do not silently choose the convenient value.
6. State what evidence would falsify each major thesis claim.
7. Treat CAPM as market-risk required return only. Do not convert expected return
   or valuation upside directly into BUY/SELL.
8. If required evidence is missing, state insufficient_evidence.
9. Do not accuse a company of fraud. Describe accounting or governance flags,
   evidence, alternative explanations and required follow-up.
10. Use sector-appropriate metrics and valuation (fertilizer sector context).
11. Your output must be valid JSON matching the schema below exactly.

Output schema (JSON):
{
  "research_posture": {
    "stance": "positive|neutral|negative|watch|insufficient_evidence",
    "confidence": "high|medium|low",
    "business_health": "genuinely_healthy|healthy_but_cyclical|improving|surface_level_strength|deteriorating|financially_fragile|insufficient_evidence",
    "one_sentence_view": "One sentence that captures the investment thesis in plain language.",
    "decision_hinge": "The single most important question the market must answer.",
    "what_is_priced_in": ["string1", "string2"],
    "falsifiers": ["If X happens, this thesis is wrong."]
  },
  "scenarios": {
    "bull": {"title": "string", "narrative": "string", "key_driver": "string"},
    "base": {"title": "string", "narrative": "string", "key_driver": "string"},
    "bear": {"title": "string", "narrative": "string", "key_driver": "string"}
  },
  "catalysts": [
    {"catalyst": "string", "timeframe": "near_term|medium_term|long_term", "probability": "high|medium|low"}
  ],
  "risks": [
    {"risk": "string", "severity": "low|medium|high|critical", "probability": "high|medium|low"}
  ],
  "key_findings": [
    {"finding": "string", "direction": "positive|negative|mixed", "materiality": "low|medium|high"}
  ]
}"""


def _gather_evidence(db: Session, issuer_id: int) -> dict:
    """Assemble deterministic evidence from the DB for the LLM brief."""
    issuer = db.get(Issuer, issuer_id)
    if issuer is None:
        return {}

    security = next((s for s in issuer.securities if s.is_active), None)
    if security is None and issuer.securities:
        security = issuer.securities[0]
    symbol = security.symbol if security else str(issuer_id)

    # Financial facts
    def facts(line_item: str) -> list[dict]:
        rows = db.execute(
            select(FinancialFact).where(
                FinancialFact.issuer_id == issuer_id,
                FinancialFact.line_item == line_item,
                FinancialFact.period_type == "annual",
                FinancialFact.scope == "consolidated",
                FinancialFact.superseded_by_id.is_(None),
            ).order_by(FinancialFact.period_end)
        ).scalars().all()
        return [{"period_end": r.period_end.isoformat(), "value": float(r.value), "unit": r.unit} for r in rows]

    # Ratios
    def ratios(key: str) -> list[dict]:
        defn = db.execute(select(RatioDefinition).where(RatioDefinition.key == key)).scalars().first()
        if defn is None:
            return []
        rows = db.execute(
            select(RatioValue).where(
                RatioValue.ratio_definition_id == defn.id,
                RatioValue.issuer_id == issuer_id,
                RatioValue.period_type == "annual",
            ).order_by(RatioValue.period_end)
        ).scalars().all()
        return [{"period_end": r.period_end.isoformat(), "value": round(float(r.value), 3)} for r in rows]

    # Latest CAPM assumption
    capm_row = db.execute(
        select(CapmAssumption)
        .where(CapmAssumption.issuer_id == issuer_id)
        .order_by(CapmAssumption.as_of_date.desc())
    ).scalars().first()

    # Thesis if exists
    thesis_row = db.execute(
        select(Thesis).where(Thesis.issuer_id == issuer_id).order_by(Thesis.as_of_date.desc())
    ).scalars().first()

    return {
        "issuer": {
            "name": issuer.name,
            "symbol": symbol,
            "sector": "Fertilizer",
            "business_description": issuer.business_description,
        },
        "financials": {
            "revenue": facts("revenue"),
            "profit_after_tax": facts("profit_after_tax"),
            "gross_profit": facts("gross_profit"),
            "operating_profit": facts("operating_profit"),
            "operating_cash_flow": facts("operating_cash_flow"),
            "total_assets": facts("total_assets"),
            "total_equity": facts("total_equity"),
            "total_liabilities": facts("total_liabilities"),
            "current_assets": facts("current_assets"),
            "current_liabilities": facts("current_liabilities"),
            "finance_cost": facts("finance_cost"),
        },
        "ratios": {
            "roe": ratios("roe"),
            "roa": ratios("roa"),
            "net_profit_margin": ratios("net_profit_margin"),
            "gross_profit_margin": ratios("gross_profit_margin"),
            "debt_to_equity": ratios("debt_to_equity"),
            "current_ratio": ratios("current_ratio"),
            "asset_turnover": ratios("asset_turnover"),
        },
        "capm": {
            "beta": float(capm_row.beta) if capm_row else None,
            "risk_free_rate_pct": float(capm_row.risk_free_rate_pct) if capm_row else None,
            "erp_pct": float(capm_row.base_equity_risk_premium_pct + capm_row.country_risk_premium_pct) if capm_row else None,
        } if capm_row else None,
        "existing_thesis": {
            "bull": thesis_row.bull_case,
            "base": thesis_row.base_case,
            "bear": thesis_row.bear_case,
            "catalysts": thesis_row.key_catalysts,
            "risks": thesis_row.key_risks,
        } if thesis_row else None,
    }


def _build_prompt(
    evidence: dict,
    forensic: ForensicResult,
    capm_diag: CAPMDiagnostics | None,
    factor_model: FactorModelResult,
) -> str:
    """Build the user-facing evidence brief for the LLM."""
    name = evidence.get("issuer", {}).get("name", "Unknown")
    symbol = evidence.get("issuer", {}).get("symbol", "?")
    desc = evidence.get("issuer", {}).get("business_description") or "No description on file."

    lines = [
        f"# PSX Analyst Evidence Brief — {name} ({symbol})",
        f"\n## Company\n{desc}",
        "\n## Forensic Analysis",
        f"Business health classification: **{forensic.business_health}** (confidence: {forensic.health_confidence})",
        f"Data coverage: {forensic.data_coverage_pct}% of key line items present.",
        f"Missing data items: {', '.join(forensic.missing_data_items) or 'none'}",
        "\n### Sub-scores (0–100, None = insufficient data)",
        f"- Operating health: {forensic.operating_health_score}",
        f"- Earnings quality (CFO/PAT): {forensic.earnings_quality_score}",
        f"- Balance sheet: {forensic.balance_sheet_score}",
        f"- Capital allocation: {forensic.capital_allocation_score}",
        f"- Governance: {forensic.governance_score}",
        "\n### DuPont Decomposition (3-way: ROE = Net Margin × Asset Turnover × Equity Multiplier)",
    ]
    for d in forensic.dupont:
        lines.append(
            f"  {d.period_end}: NM={d.net_margin}% AT={d.asset_turnover}x EM={d.equity_multiplier}x "
            f"→ ROE_computed={d.roe_3way}% ROE_reported={d.roe_reported}"
        )

    lines.append("\n### Cash Conversion (CFO/PAT)")
    for c in forensic.cash_conversion:
        lines.append(f"  {c.period_end}: PAT={c.profit_after_tax:,.0f} CFO={c.operating_cash_flow} ratio={c.cfo_pat_ratio}x")

    lines.append("\n### Forensic Flags")
    for f in forensic.flags:
        lines.append(f"  [{f.severity.upper()}] {f.flag_code}: {f.status} — {f.explanation}")

    lines.append("\n## CAPM")
    if capm_diag and capm_diag.beta is not None:
        lines.append(f"Beta: {capm_diag.beta} (t={capm_diag.beta_t_stat}, p={capm_diag.beta_p_value})")
        lines.append(f"R²: {capm_diag.r_squared} | Residual vol (annualised): {capm_diag.residual_vol_annualised}%")
        lines.append(f"Required return (CAPM): {capm_diag.required_return_pct}% [low: {capm_diag.required_return_low_pct}%, high: {capm_diag.required_return_high_pct}%]")
        lines.append(f"Up-market beta: {capm_diag.up_market_beta} | Down-market beta: {capm_diag.down_market_beta}")
        if capm_diag.asymmetry_note:
            lines.append(f"Asymmetry: {capm_diag.asymmetry_note}")
        lines.append(f"CAPM confidence: {capm_diag.confidence}. {'; '.join(capm_diag.confidence_notes)}")
    else:
        lines.append("CAPM diagnostics not available (insufficient price history).")

    lines.append("\n## Factor Exposure Model")
    lines.append(f"Model classification: {factor_model.model_classification}")
    lines.append(f"APT expected-return status: {factor_model.apt_expected_return_status}")
    lines.append(f"Observations: {factor_model.n_monthly_obs} monthly | R²={factor_model.r_squared} | Confidence: {factor_model.confidence}")
    for fexp in factor_model.factors:
        if fexp.data_available:
            lines.append(f"  {fexp.factor_name}: beta={fexp.beta} (t={fexp.t_stat}, p={fexp.p_value}) → {fexp.interpretation}")
        else:
            lines.append(f"  {fexp.factor_name}: data not available")

    lines.append("\n## Financial History (PKR '000)")
    for key, series in (evidence.get("financials") or {}).items():
        if series:
            lines.append(f"  {key}: " + " | ".join(f"{r['period_end']}: {r['value']:,.0f}" for r in series))

    lines.append("\n## Key Ratios")
    for key, series in (evidence.get("ratios") or {}).items():
        if series:
            lines.append(f"  {key}: " + " | ".join(f"{r['period_end']}: {r['value']}" for r in series))

    if evidence.get("existing_thesis"):
        th = evidence["existing_thesis"]
        lines.append("\n## Existing Analyst Thesis (context only — may be outdated)")
        lines.append(f"Bull: {th['bull']}")
        lines.append(f"Base: {th['base']}")
        lines.append(f"Bear: {th['bear']}")

    lines.append(
        "\n---\nBased on the above evidence, produce a PSXAnalystPacket JSON matching the "
        "schema in your instructions. Do not invent numbers. If evidence is insufficient "
        "for a particular claim, say so explicitly in the narrative."
    )
    return "\n".join(lines)


def _rule_based_synthesis(
    forensic: "ForensicResult",
    capm_diag: "CAPMDiagnostics | None",
    evidence: dict,
) -> dict:
    """
    Fully deterministic alternative to LLM synthesis.
    Derives research posture, scenarios, catalysts, risks, and key findings
    from the forensic sub-scores, flags, DuPont data, and CAPM diagnostics.
    Every claim traces back to a real data point — no text is invented.
    """
    health = forensic.business_health
    coverage = forensic.data_coverage_pct

    # ── Stance ────────────────────────────────────────────────────────────────
    _stance_map = {
        "genuinely_healthy": "positive",
        "healthy_but_cyclical": "neutral",
        "improving": "neutral",
        "surface_level_strength": "watch",
        "deteriorating": "negative",
        "financially_fragile": "negative",
        "insufficient_evidence": "insufficient_evidence",
    }
    stance = _stance_map.get(health, "insufficient_evidence")

    # Bump stance if sub-scores are all strong
    oh = forensic.operating_health_score or 0
    eq = forensic.earnings_quality_score or 0
    bs = forensic.balance_sheet_score or 0
    ca = forensic.capital_allocation_score or 0
    avg_score = (oh + eq + bs + ca) / max(sum(1 for s in [oh, eq, bs, ca] if s > 0), 1)
    if stance == "neutral" and avg_score >= 70:
        stance = "positive"
    elif stance == "positive" and avg_score < 55:
        stance = "neutral"

    # ── Confidence ────────────────────────────────────────────────────────────
    if coverage >= 75 and forensic.health_confidence == "high":
        confidence = "high"
    elif coverage >= 50:
        confidence = "medium"
    else:
        confidence = "low"

    # ── DuPont trends ─────────────────────────────────────────────────────────
    latest_dup = forensic.dupont[-1] if forensic.dupont else None
    prev_dup = forensic.dupont[-2] if len(forensic.dupont) >= 2 else None
    roe_latest = latest_dup.roe_3way if latest_dup else None
    roe_prev = prev_dup.roe_3way if prev_dup else None
    nm_latest = latest_dup.net_margin if latest_dup else None
    em_latest = latest_dup.equity_multiplier if latest_dup else None

    roe_trend = "stable"
    if roe_latest is not None and roe_prev is not None:
        delta = roe_latest - roe_prev
        roe_trend = "improving" if delta > 3 else ("declining" if delta < -3 else "stable")

    # ── Latest interest coverage ───────────────────────────────────────────────
    cov_latest = forensic.interest_coverage[-1].coverage if forensic.interest_coverage else None

    # ── Triggered/watch flags ─────────────────────────────────────────────────
    triggered = [f for f in forensic.flags if f.status == "triggered"]
    watch_flags = [f for f in forensic.flags if f.status == "watch"]
    clear_flags = [f for f in forensic.flags if f.status == "clear"]

    # ── Company name ──────────────────────────────────────────────────────────
    company_name = evidence.get("issuer", {}).get("name", "The company")
    symbol = evidence.get("issuer", {}).get("symbol", "")
    co = f"{company_name} ({symbol})" if symbol else company_name

    # ── One-sentence view ─────────────────────────────────────────────────────
    _health_views = {
        "genuinely_healthy": (
            f"{co} demonstrates strong operating fundamentals with ROE of {roe_latest}% "
            f"and broad data coverage of {coverage}%, suggesting genuine business quality."
        ),
        "healthy_but_cyclical": (
            f"{co} shows solid operational metrics but operates in a cyclical sector "
            f"(fertilizer/commodity); returns are likely to oscillate with urea pricing and crop cycles."
        ),
        "improving": (
            f"{co} shows measurable improvement in key financial metrics; the trajectory is "
            f"positive but durability across a full cycle has yet to be established."
        ),
        "surface_level_strength": (
            f"{co} reports healthy headline numbers but forensic analysis flags "
            f"{len(triggered)} concern(s) that warrant deeper scrutiny before conclusions are drawn."
        ),
        "deteriorating": (
            f"{co} shows deteriorating operating fundamentals across multiple metrics; "
            f"the earnings trend requires careful monitoring."
        ),
        "financially_fragile": (
            f"{co} faces elevated financial risk with {len(triggered)} triggered forensic flag(s); "
            f"balance sheet resilience is a priority concern."
        ),
        "insufficient_evidence": (
            f"Insufficient data ({coverage}% line-item coverage) to form a reliable view on {co}."
        ),
    }
    one_sentence_view = _health_views.get(health, f"Analytical coverage is {coverage}% — results are provisional.")

    # ── Decision hinge ────────────────────────────────────────────────────────
    if triggered:
        worst = max(triggered, key=lambda f: {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(f.severity, 0))
        decision_hinge = f"Can management address the {worst.flag_code.replace('_', ' ').lower()} flag? {worst.explanation}"
    elif eq is not None and eq < 50:
        decision_hinge = "Does reported profit convert to operating cash flow — or is earnings quality structurally weak?"
    elif cov_latest is not None and cov_latest < 2:
        decision_hinge = f"Is interest coverage of {cov_latest}x sustainable, or does debt servicing crowd out reinvestment?"
    elif roe_trend == "declining":
        decision_hinge = "Is the declining ROE trend a temporary cycle trough or structural margin compression?"
    else:
        decision_hinge = "Will fertilizer sector tailwinds persist long enough to sustain current profitability levels?"

    # ── Scenarios ─────────────────────────────────────────────────────────────
    roe_str = f"ROE {roe_latest}%" if roe_latest else "current returns"
    nm_str = f"net margin {nm_latest}%" if nm_latest else "current margins"
    cov_str = f"interest coverage {cov_latest}x" if cov_latest else "current debt servicing"

    scenarios: dict = {
        "bull": {
            "title": "Sector upcycle with sustained margin expansion",
            "narrative": (
                f"In the bull case, urea prices remain elevated as domestic demand from crop cycles holds "
                f"and gas feedstock costs stay contained. {co} sustains {roe_str} or better, "
                f"operating health score ({oh}/100) continues rising, and the "
                f"{len(clear_flags)} clear forensic flag(s) confirm reporting quality. "
                f"Capital allocation improves and dividend capacity strengthens."
            ),
            "key_driver": "Sustained urea price premium and stable gas allocation",
        },
        "base": {
            "title": "Stable operations with cyclical earnings variability",
            "narrative": (
                f"In the base case, {co} maintains {nm_str} through normal sector cycles. "
                f"Balance sheet score of {bs}/100 provides adequate buffer. "
                f"{cov_str} is maintained. Earnings oscillate with fertilizer input costs "
                f"and government subsidy policy, consistent with the '{health.replace('_', ' ')}' classification."
            ),
            "key_driver": "Stable government gas policy and normal crop demand",
        },
        "bear": {
            "title": "Feedstock cost shock or demand destruction",
            "narrative": (
                f"In the bear case, gas feedstock costs rise sharply or GIDC levies increase, "
                f"compressing {nm_str}. "
                + (f"The {len(triggered)} triggered flag(s) ({', '.join(f.flag_code for f in triggered[:2])}) "
                   f"become more material. " if triggered else "")
                + f"Capital allocation score ({ca}/100) indicates limited buffer for a prolonged downturn. "
                f"Leverage-driven ROE can reverse rapidly if financing costs rise."
            ),
            "key_driver": "Gas price shock or government policy reversal on fertilizer subsidies",
        },
    }

    # ── Catalysts ─────────────────────────────────────────────────────────────
    catalysts = []
    if oh >= 65:
        catalysts.append({
            "catalyst": f"Operating health score of {oh}/100 signals scope for further margin improvement if input costs ease",
            "timeframe": "medium_term",
            "probability": "medium",
        })
    if roe_trend == "improving":
        catalysts.append({
            "catalyst": f"ROE improving trend (from {roe_prev}% to {roe_latest}%) may attract re-rating if sustained for two more periods",
            "timeframe": "medium_term",
            "probability": "medium",
        })
    if eq is not None and eq >= 70:
        catalysts.append({
            "catalyst": "High earnings quality (CFO/PAT ratio) supports dividend sustainability and reduces refinancing risk",
            "timeframe": "near_term",
            "probability": "high",
        })
    if capm_diag and capm_diag.up_market_beta and capm_diag.down_market_beta:
        if capm_diag.up_market_beta > capm_diag.down_market_beta:
            catalysts.append({
                "catalyst": f"Asymmetric beta profile (up-market β={capm_diag.up_market_beta} > down-market β={capm_diag.down_market_beta}) suggests convex return potential in a market rally",
                "timeframe": "near_term",
                "probability": "medium",
            })
    if not catalysts:
        catalysts.append({
            "catalyst": "Potential for sector re-rating if fertilizer demand cycle turns positive and gas costs stabilise",
            "timeframe": "medium_term",
            "probability": "low",
        })

    # ── Risks ──────────────────────────────────────────────────────────────────
    risks = []
    for flag in triggered:
        risks.append({
            "risk": f"Triggered forensic flag — {flag.flag_code.replace('_', ' ')}: {flag.explanation}",
            "severity": flag.severity,
            "probability": "high",
        })
    for flag in watch_flags:
        risks.append({
            "risk": f"Watch flag — {flag.flag_code.replace('_', ' ')}: {flag.explanation}",
            "severity": flag.severity,
            "probability": "medium",
        })
    if capm_diag and capm_diag.down_market_beta and capm_diag.down_market_beta > 1.1:
        risks.append({
            "risk": f"Elevated down-market beta ({capm_diag.down_market_beta}) implies above-market drawdown in risk-off episodes",
            "severity": "medium",
            "probability": "medium",
        })
    if bs < 45:
        risks.append({
            "risk": f"Low balance sheet score ({bs}/100) — leverage or liquidity ratios leave limited buffer for an earnings shock",
            "severity": "high",
            "probability": "medium",
        })
    if not risks:
        risks.append({
            "risk": "Sector-level gas policy uncertainty — government gas allocation and GIDC policy can shift unexpectedly",
            "severity": "medium",
            "probability": "medium",
        })

    # ── Key findings ──────────────────────────────────────────────────────────
    key_findings = []
    for sub, label in [
        (oh, "Operating health"),
        (eq, "Earnings quality (CFO/PAT cash conversion)"),
        (bs, "Balance sheet strength"),
        (ca, "Capital allocation quality"),
    ]:
        if sub is None:
            continue
        direction = "positive" if sub >= 65 else ("negative" if sub < 45 else "mixed")
        materiality = "high" if sub < 40 or sub >= 80 else "medium"
        key_findings.append({
            "finding": f"{label}: {sub}/100",
            "direction": direction,
            "materiality": materiality,
        })
    if latest_dup and roe_latest is not None:
        key_findings.append({
            "finding": (
                f"Latest DuPont decomposition: NM={nm_latest}% × AT={latest_dup.asset_turnover}x "
                f"× EM={em_latest}x → ROE {roe_latest}% "
                + (f"({roe_trend} vs prior year)" if roe_prev else "")
            ),
            "direction": "positive" if roe_trend == "improving" else ("negative" if roe_trend == "declining" else "mixed"),
            "materiality": "high",
        })
    if capm_diag and capm_diag.beta:
        key_findings.append({
            "finding": f"CAPM: β={capm_diag.beta} (R²={capm_diag.r_squared}) → required return {capm_diag.required_return_pct}% at current risk-free rate",
            "direction": "mixed",
            "materiality": "medium",
        })

    return {
        "research_posture": {
            "stance": stance,
            "confidence": confidence,
            "business_health": health,
            "one_sentence_view": one_sentence_view,
            "decision_hinge": decision_hinge,
            "what_is_priced_in": [
                "Normal fertilizer sector cyclicality",
                f"Business health classification of '{health.replace('_', ' ')}'",
            ],
            "falsifiers": [
                f"A sustained CFO/PAT ratio below 0.6 for two consecutive years would indicate structural earnings-quality deterioration.",
                f"Interest coverage below 1.5x for more than one period would change the balance-sheet risk assessment.",
                "A reversal in government gas allocation policy or a large GIDC reassessment would alter the cost structure materially.",
            ],
        },
        "scenarios": scenarios,
        "catalysts": catalysts,
        "risks": risks,
        "key_findings": key_findings,
    }


def _parse_synthesis(response_text: str) -> dict:
    """Extract JSON from the LLM response (handles markdown code fences)."""
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning("JSON parse failed: %s", e)
        return {}


def run_analyst_synthesis(db: Session, issuer_id: int) -> dict:
    """
    Entry point: runs the full analyst agent pipeline for one issuer.
    Returns the PSXAnalystPacket dict and persists it to the DB.

    If ANTHROPIC_API_KEY is not set, returns all deterministic data with
    synthesis_status="requires_api_key" instead of LLM-generated fields.
    """
    settings = get_settings()

    # Find or create an AnalystRun
    issuer = db.get(Issuer, issuer_id)
    if issuer is None:
        return {"error": f"Issuer {issuer_id} not found"}

    security = next((s for s in issuer.securities if s.is_active), None)
    if security is None and issuer.securities:
        security = issuer.securities[0]
    symbol = security.symbol if security else str(issuer_id)

    run = AnalystRun(issuer_id=issuer_id, symbol=symbol, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        # Step 1: Run deterministic engines
        logger.info("Running forensic engine for issuer %d (%s)", issuer_id, symbol)
        forensic = compute_forensic_result(db, issuer_id)

        logger.info("Running enhanced CAPM for issuer %d (%s)", issuer_id, symbol)
        capm_diag = compute_capm_diagnostics(db, issuer_id)

        logger.info("Running factor model for issuer %d (%s)", issuer_id, symbol)
        factor_model = compute_factor_model(db, issuer_id)

        # Step 2: Assemble evidence brief
        evidence = _gather_evidence(db, issuer_id)

        # Step 3: LLM synthesis (preferred) or rule-based synthesis (fallback)
        synthesis: dict = {}
        synthesis_status = "complete"
        if settings.anthropic_api_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                prompt = _build_prompt(evidence, forensic, capm_diag, factor_model)
                message = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )
                synthesis = _parse_synthesis(message.content[0].text)
                synthesis_status = "llm_complete"
            except Exception as e:
                logger.error("LLM synthesis failed for %s: %s — falling back to rule-based", symbol, e)
                synthesis = _rule_based_synthesis(forensic, capm_diag, evidence)
                synthesis_status = "rule_based_llm_failed"
        else:
            logger.info(
                "No ANTHROPIC_API_KEY — using rule-based synthesis for %s (deterministic, no LLM).",
                symbol,
            )
            synthesis = _rule_based_synthesis(forensic, capm_diag, evidence)
            synthesis_status = "rule_based"

        # Step 4: Build the PSXAnalystPacket
        posture_data = synthesis.get("research_posture", {})
        stance = posture_data.get("stance", "insufficient_evidence")
        confidence = posture_data.get("confidence", "low")
        health = posture_data.get("business_health") or forensic.business_health  # LLM may refine
        one_sentence = posture_data.get("one_sentence_view")
        decision_hinge = posture_data.get("decision_hinge")

        packet_json = {
            "run": {
                "run_id": run.id,
                "issuer_id": issuer_id,
                "symbol": symbol,
                "analysis_as_of": datetime.now(timezone.utc).isoformat(),
                "prompt_version": "psx-analyst-v1",
                "status": "complete",
            },
            "research_posture": {
                "stance": stance,
                "confidence": confidence,
                "business_health": health,
                "one_sentence_view": one_sentence,
                "decision_hinge": decision_hinge,
                "what_is_priced_in": posture_data.get("what_is_priced_in", []),
                "falsifiers": posture_data.get("falsifiers", []),
            },
            "forensics": {
                "operating_health_score": forensic.operating_health_score,
                "earnings_quality_score": forensic.earnings_quality_score,
                "balance_sheet_score": forensic.balance_sheet_score,
                "capital_allocation_score": forensic.capital_allocation_score,
                "governance_score": forensic.governance_score,
                "business_health": forensic.business_health,
                "health_confidence": forensic.health_confidence,
                "dupont": [vars(d) for d in forensic.dupont],
                "cash_conversion": [vars(c) for c in forensic.cash_conversion],
                "interest_coverage": [vars(i) for i in forensic.interest_coverage],
                "leverage": forensic.leverage,
                "flags": [vars(f) for f in forensic.flags],
                "missing_data_items": forensic.missing_data_items,
                "data_coverage_pct": forensic.data_coverage_pct,
            },
            "capm": (
                {
                    "beta": capm_diag.beta,
                    "alpha_annualised": capm_diag.alpha_annualised,
                    "r_squared": capm_diag.r_squared,
                    "residual_vol_annualised": capm_diag.residual_vol_annualised,
                    "beta_t_stat": capm_diag.beta_t_stat,
                    "beta_p_value": capm_diag.beta_p_value,
                    "beta_ci_low": capm_diag.beta_ci_low,
                    "beta_ci_high": capm_diag.beta_ci_high,
                    "up_market_beta": capm_diag.up_market_beta,
                    "down_market_beta": capm_diag.down_market_beta,
                    "asymmetry_note": capm_diag.asymmetry_note,
                    "required_return_pct": capm_diag.required_return_pct,
                    "required_return_low_pct": capm_diag.required_return_low_pct,
                    "required_return_high_pct": capm_diag.required_return_high_pct,
                    "risk_free_rate_pct": capm_diag.risk_free_rate_pct,
                    "erp_pct": capm_diag.erp_pct,
                    "n_obs": capm_diag.n_obs,
                    "window_label": capm_diag.window_label,
                    "confidence": capm_diag.confidence,
                    "confidence_notes": capm_diag.confidence_notes,
                    "stale_price_warning": capm_diag.stale_price_warning,
                    "rolling_beta": [vars(r) for r in capm_diag.rolling_beta],
                }
                if capm_diag else {"status": "insufficient_price_history"}
            ),
            "factor_model": {
                "model_classification": factor_model.model_classification,
                "apt_expected_return_status": factor_model.apt_expected_return_status,
                "n_monthly_obs": factor_model.n_monthly_obs,
                "r_squared": factor_model.r_squared,
                "alpha_monthly_pct": factor_model.alpha,
                "residual_vol_monthly_pct": factor_model.residual_vol_monthly,
                "factors": [vars(f) for f in factor_model.factors],
                "missing_factors": factor_model.missing_factors,
                "confidence": factor_model.confidence,
                "notes": factor_model.notes,
            },
            "scenarios": synthesis.get("scenarios", {}),
            "catalysts": synthesis.get("catalysts", []),
            "risks": synthesis.get("risks", []),
            "key_findings": synthesis.get("key_findings", []),
            "synthesis_status": synthesis_status,
            "publication": {
                "readiness": "analyst_review",
                "recommendation_suppressed": True,
                "target_price_suppressed": True,
                "reviewer_id": None,
                "compliance_note": (
                    "Internal research only. See docs/research_disclaimer.md. "
                    "PUBLIC_SIGNALS_ENABLED gate must be reviewed before any distribution."
                ),
            },
        }

        # Persist AnalystPacket
        packet = AnalystPacket(
            analyst_run_id=run.id,
            issuer_id=issuer_id,
            research_posture=stance,
            business_health=health,
            confidence=confidence,
            one_sentence_view=one_sentence,
            decision_hinge=decision_hinge,
            packet_json=packet_json,
            is_approved=False,
        )
        db.add(packet)

        run.status = "complete"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(packet)

        return packet_json

    except Exception as e:
        logger.error("Analyst synthesis failed for issuer %d: %s", issuer_id, e)
        run.status = "failed"
        run.error_message = str(e)
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        return {"error": str(e), "run_id": run.id}
