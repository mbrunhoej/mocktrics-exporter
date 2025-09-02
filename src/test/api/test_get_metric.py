import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY, CollectorRegistry, core

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


def test_get_metric(client: TestClient):

    metric = metrics.Metric(
        name="test_get_metric",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metrics.metrics.add_metric(metric)

    response = client.get(
        "/metric/test_get_metric",
        headers={
            "accept": "application/json",
        },
    )
    assert response.status_code == 200


def test_metric_nonexisting(client: TestClient):

    response = client.get(
        "/metric/test_metric_nonexisting",
        headers={
            "accept": "application/json",
        },
    )
    assert response.status_code == 404
