"""Structural tests for the core read endpoints -- status codes and response shape,
not exact values (this hits the real dev DB like tests/test_health_and_gates.py
does, so data changes over time; asserting "market_cap == 812.2" here would make
this suite flaky for reasons that have nothing to do with a real regression).

Deliberately excludes GET /market/live/all and /market/quote/{symbol}: those hit
psxdata's real scrape (up to 35s, no SLA -- see psx_live.py), which would make this
suite slow and flaky for reasons outside this codebase's control. Covered instead
by manual verification (see the async-live-quotes work) and by
tests/test_price_adjustment.py at the pure-function level.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.requires_seeded_data
def test_list_companies_returns_active_issuers_with_required_fields():
    response = client.get("/companies")
    assert response.status_code == 200
    companies = response.json()
    assert len(companies) > 0
    for c in companies[:5]:
        assert "id" in c and isinstance(c["id"], int)
        assert "name" in c and c["name"]
        # symbol is nullable (parent/holding stubs are excluded, but a company can
        # still lack a Security row in edge cases) -- just check the key exists.
        assert "symbol" in c


@pytest.mark.requires_seeded_data
def test_comparison_returns_one_row_per_active_issuer_with_coverage_status():
    response = client.get("/companies/comparison")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) > 0
    valid_statuses = {"live", "historical", "partial", "unverified"}
    for row in rows:
        assert row["coverage_status"] in valid_statuses
        # price/change_pct/pe_ratio/dividend_yield are deliberately always null here
        # (see comparison.py's docstring) -- the frontend merges live quotes in client-side.
        assert row["price"] is None
        assert row["change_pct"] is None


@pytest.mark.requires_seeded_data
def test_comparison_live_rows_are_a_small_subset_of_the_full_universe():
    # Regression guard for the "465 companies covered" framing bug: coverage_status
    # must actually discriminate, not label everything "live" (or everything anything else).
    rows = client.get("/companies/comparison").json()
    statuses = [r["coverage_status"] for r in rows]
    live_count = statuses.count("live")
    assert 0 < live_count < len(rows)


def test_ratio_benchmarks_returns_mean_and_count_per_ratio_key():
    response = client.get("/companies/ratio-benchmarks")
    assert response.status_code == 200
    benchmarks = response.json()
    for key, stats in benchmarks.items():
        assert "mean" in stats and isinstance(stats["mean"], (int, float))
        assert "count" in stats and stats["count"] > 0


@pytest.mark.requires_seeded_data
def test_company_overview_for_known_pilot_issuer():
    from sqlalchemy import select

    from app.db.models import Security
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        issuer_id = db.execute(select(Security.issuer_id).where(Security.symbol == "FFC")).scalar_one()
    response = client.get(f"/companies/{issuer_id}/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "FFC"
    assert "financials" in data
    assert "ratios" in data
    # live_quote is deliberately not populated by this endpoint anymore -- fetched
    # client-side instead (see companies.py's docstring).
    assert data["live_quote"] is None


def test_company_overview_for_nonexistent_issuer_returns_null():
    response = client.get("/companies/999999999/overview")
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.requires_seeded_data
def test_market_prices_unadjusted_matches_raw_bar_count():
    from sqlalchemy import select

    from app.db.models import Security
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        security_id = db.execute(select(Security.id).where(Security.symbol == "FFC")).scalar_one()
    response = client.get(f"/market/{security_id}/prices")
    assert response.status_code == 200
    data = response.json()
    assert data["adjusted"] is False
    assert len(data["bars"]) > 0
    for bar in data["bars"][:3]:
        assert bar["low"] <= bar["open"] <= bar["high"]
        assert bar["low"] <= bar["close"] <= bar["high"]


@pytest.mark.requires_seeded_data
def test_market_prices_adjusted_reports_corporate_actions_and_verification_status():
    response = client.get("/market/1/prices?adjusted=true")
    assert response.status_code == 200
    data = response.json()
    assert data["adjusted"] is True
    assert "corporate_actions_on_file" in data
    assert "unverified_corporate_actions" in data
    assert data["unverified_corporate_actions"] <= data["corporate_actions_on_file"]
    for bar in data["bars"]:
        assert "adjustment_factor" in bar


@pytest.mark.requires_seeded_data
def test_sector_endpoints_return_only_that_sectors_companies():
    fert = client.get("/sectors/fertilizer").json()
    cement = client.get("/sectors/cement").json()
    fert_symbols = {c["symbol"] for c in fert["companies"]}
    cement_symbols = {c["symbol"] for c in cement["companies"]}
    assert fert_symbols.isdisjoint(cement_symbols)
    assert "FFC" in fert_symbols
    assert "LUCK" in cement_symbols


@pytest.mark.requires_seeded_data
def test_research_workspace_covers_complete_fertilizer_and_cement_universe():
    response = client.get("/research-workspace/universe")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 23
    assert data["sector_counts"] == {"FERTILIZER": 5, "CEMENT": 18}
    assert len(data["entries"]) == 23
    # No unverified fundamentals are loadable since the model-recalled cement seed was deleted.
    assert {entry["coverage_tier"] for entry in data["entries"]} == {"full", "price_only"}
    assert data["tier_counts"] == {"full": 3, "unverified": 0, "price_only": 20}


@pytest.mark.requires_seeded_data
def test_research_workspace_every_ticker_resolves_and_respects_evidence_tier():
    universe = client.get("/research-workspace/universe").json()
    for entry in universe["entries"]:
        response = client.get(f"/research-workspace/{entry['symbol']}")
        assert response.status_code == 200, entry["symbol"]
        data = response.json()
        assert data["ticker"] == entry["symbol"]
        assert data["coverage_tier"] == entry["coverage_tier"]
        assert data["overview"]["issuer"]["sector_name"].upper() == entry["sector"]
        if entry["coverage_tier"] == "full":
            assert data["evidence"]["fundamentals_renderable"] is True
        else:
            assert data["evidence"]["fundamentals_renderable"] is False
            assert data["overview"]["ratios"] == {}


@pytest.mark.requires_seeded_data
def test_research_workspace_rejects_unknown_ticker():
    response = client.get("/research-workspace/NOTREAL")
    assert response.status_code == 404


def test_signals_endpoint_blocked_while_compliance_gate_closed():
    # Duplicate of test_health_and_gates.py's coverage, kept here too since it's the
    # signal-gate invariant this whole suite is meant to guard -- an unvalidated
    # signal must never reach a public-shaped response, even by a future refactor
    # that touches this specific endpoint without touching that other test file.
    response = client.get("/signals/1")
    assert response.status_code == 403
