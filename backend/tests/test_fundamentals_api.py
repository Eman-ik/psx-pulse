from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401  registers every table on Base
from app.api.deps import get_db
from app.db.base import Base
from app.db.models import FinancialFact, Issuer, RatioDefinition, RatioValue, Security, SourceDocument
from app.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    session.add_all([Issuer(id=1, name="Test Co"), Security(id=1, issuer_id=1, symbol="TST")])
    session.add(SourceDocument(id=1, issuer_id=1, local_path="workbook.xlsx", content_hash="h", document_type="manual"))
    period = dict(issuer_id=1, period_start=date(2024, 1, 1), period_end=date(2024, 12, 31),
                  period_type="annual", scope="consolidated", source_document_id=1)
    session.add_all([
        FinancialFact(id=1, line_item="revenue", value=100, **period),
        FinancialFact(id=2, line_item="profit_after_tax", value=10, **period),
        FinancialFact(id=3, line_item="profit_after_tax", value=9, superseded_by_id=2, **period),
    ])
    session.add(RatioDefinition(id=1, key="net_profit_margin", formula_version=1, name="Net Profit Margin",
                                category="profitability", formula_description="pat / revenue * 100", unit="percent"))
    common = dict(ratio_definition_id=1, issuer_id=1, period_type="annual", scope="consolidated")
    session.add_all([
        RatioValue(period_end=date(2024, 12, 31), value=10, input_fact_ids=[1, 2], **common),
        RatioValue(period_end=date(2023, 12, 31), value=9, input_fact_ids=[1, 3], **common),
        RatioValue(period_end=date(2022, 12, 31), value=5, input_fact_ids=[], **common),
    ])
    session.commit()

    app.dependency_overrides[get_db] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
    session.close()


def test_only_ratios_traceable_to_current_facts_are_returned(client):
    body = client.get("/fundamentals/tst").json()

    assert {f["id"] for f in body["facts"]} == {1, 2}
    assert [(r["period_end"], r["value"]) for r in body["ratios"]] == [("2024-12-31", 10.0)]
    assert body["sources"][0]["local_path"] == "workbook.xlsx"


def test_unknown_symbol_is_404(client):
    assert client.get("/fundamentals/NOPE").status_code == 404
