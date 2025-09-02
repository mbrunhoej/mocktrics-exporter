import pytest
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry, core

import api
import metrics


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


def test_metric_delete_value(client: TestClient):

    metric = metrics.Metric(
        name="test_metric_delete_value",
        labels=["type"],
        documentation="documentation for test metric",
        values=[metrics.StaticValue(["static"], 0.0)],
    )

    metrics.metrics.add_metric(metric)

    metric_count = len(metrics.metrics.get_metrics())

    response = client.delete(
        "/metric/test_metric_delete_value/value?labels=static",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 200
    assert len(metrics.metrics.get_metrics()) == metric_count
    assert len(metric.values) == 0


def test_mismatching_labels_length(client: TestClient):

    metric = metrics.Metric(
        name="test_mismatching_labels_length",
        labels=["type"],
        documentation="documentation for test metric",
        values=[metrics.StaticValue(["static"], 0.0)],
    )

    metrics.metrics.add_metric(metric)

    metric_count = len(metrics.metrics.get_metrics())

    response = client.delete(
        "/metric/test_mismatching_labels_length/value?labels=static&labels=nonexisting",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 419
    assert len(metrics.metrics.get_metrics()) == metric_count
    assert len(metric.values) == 1


def test_delete_mismatching_labels(client: TestClient):

    metric = metrics.Metric(
        name="test_delete_mismatching_labels",
        labels=["type"],
        documentation="documentation for test metric",
        values=[metrics.StaticValue(["static"], 0.0)],
    )

    metrics.metrics.add_metric(metric)

    metric_count = len(metrics.metrics.get_metrics())

    response = client.delete(
        "/metric/test_delete_mismatching_labels/value?labels=wronglabel",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 404
    assert len(metrics.metrics.get_metrics()) == metric_count
    assert len(metric.values) == 1


def test_delete_nonexisting_metric(client: TestClient):

    metric_count = len(metrics.metrics.get_metrics())

    response = client.delete(
        "/metric/test_delete_nonexisting_metric/value?labels=static",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 404
    assert len(metrics.metrics.get_metrics()) == metric_count
