from fastapi.testclient import TestClient

from mocktrics_exporter.api import api


def test_health_endpoint_returns_ok_status():
    client = TestClient(api)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
