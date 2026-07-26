from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_compliance_flags_default_false():
    response = client.get("/admin/flags")
    assert response.status_code == 200
    flags = response.json()
    assert flags["public_launch_enabled"] is False
    assert flags["public_signals_enabled"] is False
    assert flags["commercial_data_enabled"] is False


def test_signals_endpoint_blocked_while_gate_closed():
    response = client.get("/signals/1")
    assert response.status_code == 403
    assert "compliance" in response.json()["detail"].lower() or "review" in response.json()["detail"].lower()
