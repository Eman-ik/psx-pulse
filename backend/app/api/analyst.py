"""PSX Analyst Agent API — Blueprint Section 14.

Endpoints:
  POST /companies/{issuer_id}/analyst-run      → trigger a new analysis run (synchronous for pilot)
  GET  /companies/{issuer_id}/analyst-run/latest → get latest run + packet
  GET  /companies/{issuer_id}/forensics          → deterministic forensic results only
  GET  /companies/{issuer_id}/capm-diagnostics   → enhanced CAPM results only
  GET  /companies/{issuer_id}/factor-model       → factor exposure model only

All endpoints are internal-research-only and carry a disclaimer.
No endpoint produces a public BUY/SELL rating or target price.

The blueprint specifies async 202-accepted runs. For the pilot, synthesis
runs synchronously (typically 10-30s) since we don't yet have a Celery
worker queue. The frontend polls /latest for status.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import AnalystPacket, AnalystRun, Issuer
from app.etl.analyst_synthesizer import run_analyst_synthesis
from app.etl.capm_enhanced import compute_capm_diagnostics
from app.etl.factor_model import compute_factor_model
from app.etl.forensic_engine import compute_forensic_result

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/companies", tags=["analyst"])

_INTERNAL_DISCLAIMER = (
    "Internal research only. Not a regulated investment recommendation. "
    "See docs/research_disclaimer.md."
)


def _run_row_to_dict(run: AnalystRun, packet: AnalystPacket | None) -> dict:
    return {
        "run_id": run.id,
        "symbol": run.symbol,
        "status": run.status,
        "prompt_version": run.prompt_version,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "error_message": run.error_message,
        "packet": (
            {
                "research_posture": packet.research_posture,
                "business_health": packet.business_health,
                "confidence": packet.confidence,
                "one_sentence_view": packet.one_sentence_view,
                "decision_hinge": packet.decision_hinge,
                "is_approved": packet.is_approved,
                "packet_json": packet.packet_json,
            }
            if packet else None
        ),
        "is_research_only": True,
        "disclaimer": _INTERNAL_DISCLAIMER,
    }


def _forensic_to_dict(result) -> dict:
    return {
        "issuer_id": result.issuer_id,
        "symbol": result.symbol,
        "as_of": result.as_of,
        "sub_scores": {
            "operating_health": result.operating_health_score,
            "earnings_quality": result.earnings_quality_score,
            "balance_sheet": result.balance_sheet_score,
            "capital_allocation": result.capital_allocation_score,
            "governance": result.governance_score,
        },
        "business_health": result.business_health,
        "health_confidence": result.health_confidence,
        "dupont": [vars(d) for d in result.dupont],
        "cash_conversion": [vars(c) for c in result.cash_conversion],
        "interest_coverage": [vars(i) for i in result.interest_coverage],
        "leverage": result.leverage,
        "flags": [vars(f) for f in result.flags],
        "missing_data_items": result.missing_data_items,
        "data_coverage_pct": result.data_coverage_pct,
        "is_research_only": True,
        "disclaimer": _INTERNAL_DISCLAIMER,
    }


def _capm_to_dict(result) -> dict:
    if result is None:
        return {"status": "insufficient_data", "is_research_only": True}
    return {
        "issuer_id": result.issuer_id,
        "symbol": result.symbol,
        "benchmark": result.benchmark,
        "window_label": result.window_label,
        "start_date": result.start_date,
        "end_date": result.end_date,
        "n_obs": result.n_obs,
        "beta": result.beta,
        "alpha_annualised": result.alpha_annualised,
        "r_squared": result.r_squared,
        "residual_vol_annualised": result.residual_vol_annualised,
        "beta_se": result.beta_se,
        "beta_t_stat": result.beta_t_stat,
        "beta_p_value": result.beta_p_value,
        "beta_ci_low": result.beta_ci_low,
        "beta_ci_high": result.beta_ci_high,
        "up_market_beta": result.up_market_beta,
        "down_market_beta": result.down_market_beta,
        "asymmetry_note": result.asymmetry_note,
        "zero_return_pct": result.zero_return_pct,
        "stale_price_warning": result.stale_price_warning,
        "required_return_pct": result.required_return_pct,
        "required_return_low_pct": result.required_return_low_pct,
        "required_return_high_pct": result.required_return_high_pct,
        "risk_free_rate_pct": result.risk_free_rate_pct,
        "erp_pct": result.erp_pct,
        "rolling_beta": [vars(r) for r in result.rolling_beta],
        "confidence": result.confidence,
        "confidence_notes": result.confidence_notes,
        "is_research_only": True,
        "disclaimer": _INTERNAL_DISCLAIMER,
    }


def _factor_to_dict(result) -> dict:
    return {
        "issuer_id": result.issuer_id,
        "symbol": result.symbol,
        "model_classification": result.model_classification,
        "apt_expected_return_status": result.apt_expected_return_status,
        "window_start": result.window_start,
        "window_end": result.window_end,
        "n_monthly_obs": result.n_monthly_obs,
        "alpha_monthly_pct": result.alpha,
        "r_squared": result.r_squared,
        "residual_vol_monthly_pct": result.residual_vol_monthly,
        "factors": [vars(f) for f in result.factors],
        "missing_factors": result.missing_factors,
        "confidence": result.confidence,
        "notes": result.notes,
        "is_research_only": True,
        "disclaimer": _INTERNAL_DISCLAIMER,
    }


@router.post("/{issuer_id}/analyst-run")
def trigger_analyst_run(issuer_id: int, db: Session = Depends(get_db)) -> dict:
    """Trigger a new analyst run for an issuer.

    Runs synchronously for the pilot (no Celery queue yet). Expected duration 10-60s
    depending on whether ANTHROPIC_API_KEY is set and the LLM response time.
    Returns the completed packet or an error status.
    """
    issuer = db.get(Issuer, issuer_id)
    if issuer is None:
        raise HTTPException(status_code=404, detail=f"Issuer {issuer_id} not found")

    # Check for in-progress run to avoid duplicates
    in_progress = db.execute(
        select(AnalystRun).where(
            AnalystRun.issuer_id == issuer_id,
            AnalystRun.status == "running",
        )
    ).scalars().first()
    if in_progress:
        return {
            "status": "already_running",
            "run_id": in_progress.id,
            "message": "An analyst run is already in progress for this issuer.",
        }

    packet_json = run_analyst_synthesis(db, issuer_id)
    return {
        "status": "complete" if "error" not in packet_json else "failed",
        "packet": packet_json,
        "is_research_only": True,
        "disclaimer": _INTERNAL_DISCLAIMER,
    }


@router.get("/{issuer_id}/analyst-run/latest")
def get_latest_analyst_run(issuer_id: int, db: Session = Depends(get_db)) -> dict:
    """Return the latest completed analyst run and packet for an issuer."""
    run = db.execute(
        select(AnalystRun)
        .where(AnalystRun.issuer_id == issuer_id)
        .order_by(AnalystRun.created_at.desc())
    ).scalars().first()

    if run is None:
        return {
            "status": "no_run",
            "message": "No analyst run found for this issuer. POST to /analyst-run to start one.",
            "is_research_only": True,
        }

    packet = db.execute(
        select(AnalystPacket).where(AnalystPacket.analyst_run_id == run.id)
    ).scalars().first()

    return _run_row_to_dict(run, packet)


@router.get("/{issuer_id}/forensics")
def get_forensics(issuer_id: int, db: Session = Depends(get_db)) -> dict:
    """Compute and return live forensic results (no LLM, fully deterministic)."""
    issuer = db.get(Issuer, issuer_id)
    if issuer is None:
        raise HTTPException(status_code=404, detail=f"Issuer {issuer_id} not found")
    result = compute_forensic_result(db, issuer_id)
    return _forensic_to_dict(result)


@router.get("/{issuer_id}/capm-diagnostics")
def get_capm_diagnostics(issuer_id: int, db: Session = Depends(get_db)) -> dict:
    """Compute and return full CAPM diagnostics (OLS beta, R², CI, rolling beta)."""
    issuer = db.get(Issuer, issuer_id)
    if issuer is None:
        raise HTTPException(status_code=404, detail=f"Issuer {issuer_id} not found")
    result = compute_capm_diagnostics(db, issuer_id)
    return _capm_to_dict(result)


@router.get("/{issuer_id}/factor-model")
def get_factor_model(issuer_id: int, db: Session = Depends(get_db)) -> dict:
    """Compute and return the multi-factor exposure model (explicitly NOT an APT model)."""
    issuer = db.get(Issuer, issuer_id)
    if issuer is None:
        raise HTTPException(status_code=404, detail=f"Issuer {issuer_id} not found")
    result = compute_factor_model(db, issuer_id)
    return _factor_to_dict(result)
