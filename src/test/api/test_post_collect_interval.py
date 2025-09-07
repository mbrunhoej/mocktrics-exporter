import pytest
from fastapi.testclient import TestClient

from mocktrics_exporter import api, configuration, metrics


@pytest.fixture(scope="function", autouse=True)
def client():
    with TestClient(api.api) as client:
        yield client


def test_post_collect_interval(client: TestClient):

    response = client.post(
        "/collect-interval/100",
    )

    assert response.status_code == 200
    assert metrics.metrics.get_collect_interval() == 100


def test_post_collect_interval_str(client: TestClient):

    response = client.post(
        "/collect-interval/50s",
    )

    assert response.status_code == 200
    assert metrics.metrics.get_collect_interval() == 50

    response = client.post(
        "/collect-interval/2m",
    )

    assert response.status_code == 200
    assert metrics.metrics.get_collect_interval() == 120


def test_post_collect_interval_under_min(client: TestClient):

    metrics.metrics.set_collect_interval(10)

    response = client.post(
        "/collect-interval/-1",
    )

    assert response.status_code == 400
    assert metrics.metrics.get_collect_interval() == 10


def test_post_collect_interval_over_max(client: TestClient):

    metrics.metrics.set_collect_interval(10)

    response = client.post(
        "/collect-interval/3601",
    )

    assert response.status_code == 400
    assert metrics.metrics.get_collect_interval() == 10


def test_post_collect_interval_read_only(client: TestClient, monkeypatch):

    metrics.metrics.set_collect_interval(10)

    monkeypatch.setattr(configuration, "config_has_collect_interval", True)

    response = client.post(
        "/collect-interval/100",
    )

    assert response.status_code == 403
    assert metrics.metrics.get_collect_interval() == 10
