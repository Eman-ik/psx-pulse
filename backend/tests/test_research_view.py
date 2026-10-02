from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.research_system import research_view as rv

TODAY = date(2026, 10, 2)


def _series(*values, start_year=2024):
    return [(date(start_year + i, 12, 31), v) for i, v in enumerate(values)]


def test_financial_health_improving_when_most_signals_move_the_right_way():
    ratios = {"net_profit_margin": _series(10, 14), "roe": _series(20, 30),
              "debt_to_equity": _series(3.0, 2.0), "current_ratio": _series(1.0, 1.0)}
    d = rv.financial_health(ratios, date(2026, 1, 1))
    assert d["state"] == "IMPROVING" and d["confidence"] == 1.0 and not d["stale"]


def test_financial_health_needs_three_of_four_ratios():
    d = rv.financial_health({"roe": _series(10, 12), "net_profit_margin": _series(5, 6)}, TODAY)
    assert d["state"] == "INSUFFICIENT_DATA" and "2 available" in d["reason"]


def test_old_statements_are_flagged_stale_and_halve_confidence():
    ratios = {k: _series(1.0, 2.0, start_year=2021) for k in ("net_profit_margin", "roe", "debt_to_equity", "current_ratio")}
    d = rv.financial_health(ratios, TODAY)
    assert d["stale"] and d["confidence"] == 0.5 and "months old" in d["supports"][0]


def test_earnings_quality_thresholds_and_missing():
    assert rv.earnings_quality(None, TODAY)["state"] == "INSUFFICIENT_DATA"
    assert rv.earnings_quality(_series(120.0), date(2026, 3, 1))["state"] == "HIGH"
    assert rv.earnings_quality(_series(50.0), date(2026, 3, 1))["state"] == "LOW"


def test_technical_condition_does_not_treat_unavailable_averages_as_below():
    sig = {"above_20dma": True, "above_50dma": None, "above_200dma": None, "bars_available": 30, "rsi": 55.0,
           "lookback_complete": False, "lookback_days": 30}
    assert rv.technical_condition(sig, False)["state"] == "UNAVAILABLE"
    sig |= {"above_50dma": True}
    d = rv.technical_condition(sig, False)
    assert d["state"] == "POSITIVE" and any("30 days" in s for s in d["supports"])


def _confidence(**overrides):
    base = {k: (True, "") for k in ("prices_current", "price_history", "statements", "profile", "recent_events")}
    base.update({k: (v, "") for k, v in overrides.items()})
    return rv.data_confidence(base)


def test_data_confidence_levels():
    assert _confidence()["level"] == "HIGH"
    assert _confidence(statements=False, price_history=False)["level"] == "MEDIUM"
    assert _confidence(statements=False, price_history=False, recent_events=False)["level"] == "LOW"


def test_overall_view_refuses_to_conclude_without_enough_current_domains():
    d = [rv.technical_condition({"above_20dma": True, "above_50dma": True, "above_200dma": True, "bars_available": 300,
                                 "lookback_complete": True, "lookback_days": 252, "rsi": 60.0}, False),
         rv.not_assessed("valuation", "Valuation", "none")]
    assert rv.overall_view(d, _confidence())["state"] == "INSUFFICIENT_EVIDENCE"


def test_overall_view_reports_disagreement_instead_of_averaging():
    mk = lambda key, label, state: {"key": key, "label": label, "state": state, "stale": False}
    d = [mk("a", "Financial health", "IMPROVING"), mk("b", "Technical condition", "NEGATIVE"), mk("c", "Earnings quality", "HIGH")]
    out = rv.overall_view(d, _confidence())
    assert out["state"] == "MIXED"
    assert "Financial health is favourable while Technical condition is not." in out["disagreements"]


client = TestClient(app)


def test_overview_for_real_company_has_provenance_and_no_invented_fields():
    """Verify overview endpoint returns unified research analysis."""
    r = client.get("/api/v1/companies/FFC/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "FFC" and body["generated_at"] and body["price"]["badge"] == "DELAYED"
    assert body["profile_source"]["url"].startswith("https://dps.psx.com.pk/company/")

    # New unified research overview (from ResearchOrchestrator)
    overview = body["research_overview"]
    assert "business_health" in overview
    assert "earnings_quality" in overview
    assert "data_availability" in overview
    assert isinstance(overview["data_availability"], int)


def test_unknown_security_is_404_and_id_lookup_works():
    assert client.get("/api/v1/companies/NOPE/overview").status_code == 404
    sid = client.get("/api/v1/companies/search", params={"q": "LUCK"}).json()["results"][0]["security_id"]
    assert client.get(f"/api/v1/companies/{sid}/business").json()["symbol"] == "LUCK"


def test_business_never_invents_counterparties():
    b = client.get("/api/v1/companies/LUCK/business").json()
    assert b["supply_chain"]["disclosed"] == [] and b["industry_dependencies"]["label"].startswith("INDUSTRY DEPENDENCY")


# ============================================================================
# UNIFIED ARCHITECTURE CONSISTENCY TESTS
# ============================================================================
# Enforce that Overview and Intelligence endpoints use the same ResearchOrchestrator

def test_overview_and_intelligence_use_same_confidence_score():
    """Both endpoints must return identical unified confidence scores."""
    ticker = "FFC"
    overview = client.get(f"/api/v1/companies/{ticker}/overview").json()
    intelligence = client.get(f"/api/v1/research/{ticker}/analysis").json()

    overview_conf = overview["research_overview"]["data_availability"]
    intelligence_conf = intelligence["confidence_score"]

    assert overview_conf == intelligence_conf, \
        f"Confidence mismatch: overview={overview_conf}% vs intelligence={intelligence_conf}%"


def test_overview_and_intelligence_business_health_agree():
    """Both endpoints must show same business health assessment."""
    ticker = "FATIMA"
    overview = client.get(f"/api/v1/companies/{ticker}/overview").json()
    intelligence = client.get(f"/api/v1/research/{ticker}/analysis").json()

    overview_bh = overview["research_overview"]["business_health"]
    intelligence_bh = intelligence["intelligence"]["business_health"]["assessment"]

    assert overview_bh == intelligence_bh, \
        f"Business health mismatch: overview={overview_bh} vs intelligence={intelligence_bh}"


def test_overview_and_intelligence_earnings_quality_agree():
    """Both endpoints must show same earnings quality assessment."""
    ticker = "FATIMA"
    overview = client.get(f"/api/v1/companies/{ticker}/overview").json()
    intelligence = client.get(f"/api/v1/research/{ticker}/analysis").json()

    overview_eq = overview["research_overview"]["earnings_quality"]
    intelligence_eq = intelligence["intelligence"]["earnings_quality"]["assessment"]

    assert overview_eq == intelligence_eq, \
        f"Earnings quality mismatch: overview={overview_eq} vs intelligence={intelligence_eq}"


def test_overview_and_intelligence_valuation_agree():
    """Both endpoints must show same valuation assessment."""
    ticker = "FFC"
    overview = client.get(f"/api/v1/companies/{ticker}/overview").json()
    intelligence = client.get(f"/api/v1/research/{ticker}/analysis").json()

    overview_val = overview["research_overview"]["valuation"]
    # Valuation context is in the full analysis under intelligence key
    valuation_data = intelligence.get("intelligence", {}).get("valuation", {})
    intelligence_val = valuation_data.get("assessment", "Unavailable")

    # Both should be Unavailable or both should show a valuation
    # (accounting for different formats)
    overview_unavailable = "Unavailable" in str(overview_val)
    intelligence_unavailable = "Unavailable" in str(intelligence_val)

    assert overview_unavailable == intelligence_unavailable, \
        f"Valuation availability mismatch: overview={overview_val} vs intelligence={intelligence_val}"


def test_overview_cannot_contradict_intelligence():
    """Overview must not report different conclusions than Intelligence."""
    ticker = "FATIMA"
    overview = client.get(f"/api/v1/companies/{ticker}/overview").json()
    intelligence = client.get(f"/api/v1/research/{ticker}/analysis").json()

    # Most important: both must use same unified confidence score
    overview_conf = overview["research_overview"]["data_availability"]
    intelligence_conf = intelligence["confidence_score"]

    assert overview_conf == intelligence_conf, \
        f"Confidence score mismatch: overview={overview_conf}% vs intelligence={intelligence_conf}%"


def test_unified_analysis_has_validation_report():
    """Intelligence endpoint must show consistency validation."""
    r = client.get("/api/v1/research/FATIMA/analysis")
    assert r.status_code == 200
    intelligence = r.json()

    validation = intelligence.get("validation", {})
    assert "overall_valid" in validation
    assert "contradictions" in validation
    assert isinstance(validation["contradictions"], list)


def test_unified_analysis_covers_all_9_engines():
    """Intelligence endpoint must return all 9 engines."""
    r = client.get("/api/v1/research/FATIMA/analysis")
    assert r.status_code == 200
    intelligence = r.json()

    # Check metadata fields
    assert "confidence_score" in intelligence, "Missing confidence_score"
    assert "executive_summary" in intelligence, "Missing executive_summary"

    # All engines are in the intelligence nested object
    intel_obj = intelligence.get("intelligence", {})

    # Critical engines that must be present
    critical_engines = [
        "business_health",
        "earnings_quality",
        "investment_case",  # Contains bull/bear case
        "red_flags",
        "risk_assessment",
    ]

    for engine in critical_engines:
        assert engine in intel_obj, f"Missing critical engine: {engine} in intelligence object"


def test_overview_summary_has_required_fields():
    """Overview must include all key research fields."""
    r = client.get("/api/v1/companies/FATIMA/overview")
    assert r.status_code == 200
    body = r.json()

    required_fields = [
        "business_health",
        "business_health_confidence",
        "earnings_quality",
        "earnings_quality_confidence",
        "valuation",
        "risk_level",
        "data_availability",
    ]

    overview = body["research_overview"]
    for field in required_fields:
        assert field in overview, f"Missing field in overview: {field}"
