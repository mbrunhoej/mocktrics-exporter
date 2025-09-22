import pytest
from fastapi.testclient import TestClient

from mocktrics_exporter import api, metricCollection, metrics


@pytest.fixture(scope="function", autouse=True)
def client():
    with TestClient(api.api) as client:
        yield client


def test_metric_add_value(client: TestClient):

    metric = metrics.Metric(
        name="test",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metricCollection.metrics.add_metric(metric)

    response = client.post(
        "/metric/test/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["type"], "value": 0},
    )

    assert response.status_code == 201
    assert len(metricCollection.metrics.get_metrics()) == 1
    assert len(metric.values) == 1


def test_metric_add_multiple_values(client: TestClient):

    metric = metrics.Metric(
        name="test",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metricCollection.metrics.add_metric(metric)

    response = client.post(
        "/metric/test/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["static"], "value": 0},
    )
    response = client.post(
        "/metric/test/value",
        headers={
            "accept": "application/json",
        },
        json={
            "kind": "ramp",
            "labels": ["ramp"],
            "period": "2m",
            "peak": 100,
            "invert": False,
        },
    )
    assert response.status_code == 201
    assert len(metricCollection.metrics.get_metrics()) == 1
    assert len(metric.values) == 2


def test_mismatching_labels(client: TestClient):

    metric = metrics.Metric(
        name="test",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metricCollection.metrics.add_metric(metric)

    response = client.post(
        "/metric/test/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["static", "mismatch"], "value": 0},
    )

    assert response.status_code == 419
    assert len(metricCollection.metrics.get_metrics()) == 1
    assert len(metric.values) == 0


def test_duplicate_labels(client: TestClient):

    metric = metrics.Metric(
        name="test",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metricCollection.metrics.add_metric(metric)

    client.post(
        "/metric/test/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["static"], "value": 0},
    )
    response = client.post(
        "/metric/test/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["static"], "value": 0},
    )

    assert response.status_code == 409
    assert len(metricCollection.metrics.get_metrics()) == 1
    assert len(metric.values) == 1


def test_nonexisting_metric(client: TestClient):

    response = client.post(
        "/metric/test/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["type"], "value": 0},
    )

    assert response.status_code == 404
    assert len(metricCollection.metrics.get_metrics()) == 0
