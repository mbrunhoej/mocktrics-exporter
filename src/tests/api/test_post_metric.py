import pytest
from fastapi.testclient import TestClient

from mocktrics_exporter import api, metricCollection


@pytest.fixture(scope="function", autouse=True)
def client():
    with TestClient(api.api) as client:
        yield client


def test_metric_single_value(client: TestClient):

    response = client.post(
        "/metric",
        headers={
            "accept": "application/json",
        },
        json={
            "name": "test",
            "documentation": "documentation for test metric",
            "unit": "",
            "labels": ["type"],
            "values": [{"kind": "static", "labels": ["static"], "value": 0}],
        },
    )
    assert response.status_code == 201
    assert len(metricCollection.metrics.get_metrics()) == 1
    metric = metricCollection.metrics.get_metric("test")
    assert len(metric.values) == 1


def test_metric_multiple_value(client: TestClient):

    response = client.post(
        "/metric",
        headers={
            "accept": "application/json",
        },
        json={
            "name": "test",
            "documentation": "documentation for test metric",
            "unit": "",
            "labels": ["type"],
            "values": [
                {"kind": "static", "labels": ["static"], "value": 0},
                {
                    "kind": "ramp",
                    "labels": ["ramp"],
                    "period": "2m",
                    "peak": 100,
                    "invert": False,
                },
            ],
        },
    )
    assert response.status_code == 201
    assert len(metricCollection.metrics.get_metrics()) == 1
    metric = metricCollection.metrics.get_metric("test")
    assert len(metric.values) == 2


def test_metric_no_value(client: TestClient):

    response = client.post(
        "/metric",
        headers={
            "accept": "application/json",
        },
        json={
            "name": "test",
            "documentation": "documentation for test metric",
            "unit": "",
            "labels": ["type"],
            "values": [],
        },
    )
    assert response.status_code == 201
    assert len(metricCollection.metrics.get_metrics()) == 1
    metric = metricCollection.metrics.get_metric("test")
    assert len(metric.values) == 0


def test_metric_duplicate_value(client: TestClient):

    client.post(
        "/metric",
        headers={
            "accept": "application/json",
        },
        json={
            "name": "test",
            "documentation": "documentation for test metric",
            "unit": "",
            "labels": ["type"],
            "values": [],
        },
    )

    response = client.post(
        "/metric",
        headers={
            "accept": "application/json",
        },
        json={
            "name": "test",
            "documentation": "documentation for test metric",
            "unit": "",
            "labels": ["type"],
            "values": [],
        },
    )
    assert response.status_code == 409
    assert len(metricCollection.metrics.get_metrics()) == 1
