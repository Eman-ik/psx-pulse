"""Stage 2 industry-intelligence integration tests against the seeded dev dataset."""

import pytest
from fastapi.testclient import TestClient
from datetime import date
from sqlalchemy import select

from app.main import app
from app.db.models import SourceDocument
from app.db.session import SessionLocal
from app.etl.industry_intelligence import build_industry_intelligence
from app.ingestion.industry_data import IndustryObservationInput, create_assessment, upsert_observation


client = TestClient(app)


@pytest.mark.requires_seeded_data
def test_fertilizer_industry_structure_and_economics_are_evidence_controlled():
    response = client.get("/research-workspace/industry/FERTILIZER")
    assert response.status_code == 200
    data = response.json()
    assert data["structure"]["listed_competitor_count"] == 5
    assert data["economics"]["verified_company_count"] == 3
    assert data["economics"]["verified_coverage_pct"] == 60.0
    assert {row["symbol"] for row in data["structure"]["competitors"]} == {
        "AGL", "AHCL", "EFERT", "FATIMA", "FFC"
    }


@pytest.mark.requires_seeded_data
def test_cement_does_not_promote_unverified_financials_into_industry_economics():
    response = client.get("/research-workspace/industry/CEMENT")
    assert response.status_code == 200
    data = response.json()
    assert data["structure"]["listed_competitor_count"] == 18
    assert data["economics"]["verified_company_count"] == 0
    assert data["economics"]["verified_coverage_pct"] == 0.0
    assert all(metric["value"] is None for metric in data["economics"]["sector_medians"])


@pytest.mark.requires_seeded_data
def test_stage_two_gaps_and_structural_conclusion_are_explicit():
    data = client.get("/research-workspace/industry/FERTILIZER").json()
    dimensions = {item["key"]: item for item in data["structure"]["dimensions"]}
    assert set(dimensions) == {
        "market_share", "pricing_power", "capacity", "capacity_utilization",
        "entry_barriers", "imports", "exports", "regulation", "substitutes",
    }
    assert dimensions["imports"]["evidence_status"] == "missing"
    assert dimensions["imports"]["required_source"]
    assert data["cycle"]["state"] == "INSUFFICIENT_EVIDENCE"
    assert data["attractiveness"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert len(data["economy_context"]["transmission_channels"]) >= 5
    assert all(channel["evidence_status"] == "missing" for channel in data["economy_context"]["transmission_channels"])


@pytest.mark.requires_seeded_data
def test_company_workspace_contains_its_industry_context():
    response = client.get("/research-workspace/FFC")
    assert response.status_code == 200
    data = response.json()
    assert data["industry"]["sector"] == "FERTILIZER"
    assert data["industry"]["structure"]["listed_competitor_count"] == 5


def test_unknown_industry_is_rejected():
    response = client.get("/research-workspace/industry/BANKING")
    assert response.status_code == 404


@pytest.mark.requires_seeded_data
def test_sourced_industry_observations_drive_utilization_and_assessments():
    with SessionLocal() as db:
        source = db.execute(select(SourceDocument).order_by(SourceDocument.id)).scalars().first()
        assert source is not None
        common = dict(
            sector="Fertilizer", period_start=date(2025, 1, 1), period_end=date(2025, 12, 31),
            frequency="annual", unit="KT", source_document_id=source.id,
            source_page=12, confidence=0.95, is_verified=True,
        )
        upsert_observation(db, IndustryObservationInput(metric_key="production", value=8_000, **common))
        upsert_observation(db, IndustryObservationInput(metric_key="effective_capacity", value=10_000, **common))
        previous = {**common, "period_start": date(2024, 1, 1), "period_end": date(2024, 12, 31)}
        upsert_observation(db, IndustryObservationInput(metric_key="effective_capacity", value=9_000, **previous))
        upsert_observation(db, IndustryObservationInput(metric_key="domestic_demand", value=7_000, **previous))
        upsert_observation(db, IndustryObservationInput(metric_key="domestic_demand", value=8_000, **common))
        percent_common = {**common, "unit": "%"}
        upsert_observation(db, IndustryObservationInput(metric_key="sector_roic", value=20, **percent_common))
        upsert_observation(db, IndustryObservationInput(metric_key="cost_of_capital", value=15, **percent_common))
        create_assessment(
            db, sector_name="Fertilizer", dimension="entry_barriers", rating="high",
            assessment="Test-only sourced assessment", as_of_date=date(2025, 12, 31),
            source_document_id=source.id, source_page=20, analyst="pytest", confidence=0.9,
        )
        result = build_industry_intelligence(db, "FERTILIZER")
        assert result["economics"]["derived_metrics"]["capacity_utilization"]["value"] == 80.0
        assert result["economics"]["derived_metrics"]["roic_spread"]["value"] == 5.0
        assert result["economics"]["derived_metrics"]["demand_minus_capacity_growth"]["value"] > 0
        assert result["attractiveness"]["status"] == "ATTRACTIVE"
        entry_barriers = next(row for row in result["structure"]["dimensions"] if row["key"] == "entry_barriers")
        assert entry_barriers["evidence_status"] == "available"
        assert entry_barriers["assessment"]["source_page"] == 20
        db.rollback()


def test_industry_ingestion_rejects_unknown_metrics_before_writing():
    with SessionLocal() as db:
        with pytest.raises(ValueError, match="Unsupported industry metric"):
            upsert_observation(db, IndustryObservationInput(
                sector="Fertilizer", metric_key="made_up_metric",
                period_start=date(2025, 1, 1), period_end=date(2025, 12, 31),
                frequency="annual", value=1, unit="x", source_document_id=1,
            ))
