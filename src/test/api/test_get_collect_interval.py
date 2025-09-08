import pytest
from fastapi.testclient import TestClient

from mocktrics_exporter import api, configuration, metrics


@pytest.fixture(scope="function", autouse=True)
def client():
    with TestClient(api.api) as client:
        yield client


def test_get_collect_interval(client: TestClient):

    metrics.metrics.set_collect_interval(1)

    response = client.get(
        "/collect-interval",
    )

    assert response.status_code == 200
    assert response.json()["seconds"] == 1
    assert response.json()["editable"] is True


def test_get_collect_interval_read_only(client: TestClient, monkeypatch):

    monkeypatch.setattr(configuration.configuration, "_collect_interval_read_only", True)

    response = client.get(
        "/collect-interval",
    )

    assert response.status_code == 200
    assert response.json()["editable"] is False
