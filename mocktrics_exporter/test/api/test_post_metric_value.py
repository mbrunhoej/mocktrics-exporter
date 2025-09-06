import pytest
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry, core

from mocktrics_exporter import api, metrics


@pytest.fixture(scope="function", autouse=True)
def client():
    with TestClient(api.api) as client:
        yield client


@pytest.fixture(scope="function", autouse=True)
def cleanup():
    yield
    delete = []
    for name, metric in metrics.metrics.get_metrics().items():
        if not metric.read_only:
            delete.append(name)

    for name in delete:
        metrics.metrics.delete_metric(name)

    core.REGISTRY = CollectorRegistry()


def test_metric_add_value(client: TestClient):

    metric = metrics.Metric(
        name="test_metric_add_single_value",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metrics.metrics.add_metric(metric)

    metric_count = len(metrics.metrics.get_metrics())

    response = client.post(
        "/metric/test_metric_add_single_value/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["type"], "value": 0},
    )

    assert response.status_code == 201
    assert len(metrics.metrics.get_metrics()) == metric_count
    assert len(metric.values) == 1


def test_metric_add_multiple_values(client: TestClient):

    metric = metrics.Metric(
        name="test_metric_add_multiple_values",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metrics.metrics.add_metric(metric)

    metric_count = len(metrics.metrics.get_metrics())

    response = client.post(
        "/metric/test_metric_add_multiple_values/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["static"], "value": 0},
    )
    response = client.post(
        "/metric/test_metric_add_multiple_values/value",
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
    assert len(metrics.metrics.get_metrics()) == metric_count
    assert len(metric.values) == 2


def test_mismatching_labels(client: TestClient):

    metric = metrics.Metric(
        name="test_mismatching_labels",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metrics.metrics.add_metric(metric)

    metric_count = len(metrics.metrics.get_metrics())

    response = client.post(
        "/metric/test_mismatching_labels/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["static", "mismatch"], "value": 0},
    )

    assert response.status_code == 419
    assert len(metrics.metrics.get_metrics()) == metric_count
    assert len(metric.values) == 0


def test_duplicate_labels(client: TestClient):

    metric = metrics.Metric(
        name="test_duplicate_labels",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metrics.metrics.add_metric(metric)

    metric_count = len(metrics.metrics.get_metrics())

    client.post(
        "/metric/test_duplicate_labels/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["static"], "value": 0},
    )
    response = client.post(
        "/metric/test_duplicate_labels/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["static"], "value": 0},
    )

    assert response.status_code == 409
    assert len(metrics.metrics.get_metrics()) == metric_count
    assert len(metric.values) == 1


def test_nonexisting_metric(client: TestClient):

    metric_count = len(metrics.metrics.get_metrics())

    response = client.post(
        "/metric/test_nonexisting_metric/value",
        headers={
            "accept": "application/json",
        },
        json={"kind": "static", "labels": ["type"], "value": 0},
    )

    assert response.status_code == 404
    assert len(metrics.metrics.get_metrics()) == metric_count
