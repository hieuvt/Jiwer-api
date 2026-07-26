"""Phase 0 smoke tests — health + app bootstrap."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert body["version"]


def test_openapi_available() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["title"] == "Jiwer-api"
    assert "/health" in spec["paths"]


def test_wer_routes_not_implemented_yet() -> None:
    """Phase 0 only mounts the router; WER endpoints come in later phases."""
    assert client.post("/api/v1/wer", json={}).status_code == 404
    assert client.post("/api/v1/wer/batch", json={}).status_code == 404
