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


def test_delete_metric(client: TestClient):

    metric = metrics.Metric(
        name="test_delete_metric",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metrics.metrics.add_metric(metric)

    metric_count = len(metrics.metrics.get_metrics())

    response = client.delete(
        "/metric/test_delete_metric",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 200
    assert len(metrics.metrics.get_metrics()) == metric_count - 1


def test_delete_metric_nonexisting(client: TestClient):

    metric_count = len(metrics.metrics.get_metrics())

    response = client.delete(
        "/metric/test_delete_metric_nonexisting",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 404
    assert len(metrics.metrics.get_metrics()) == metric_count
