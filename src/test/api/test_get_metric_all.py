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


def test_get_value_all(client: TestClient):

    metric_count = len(metrics.metrics.get_metrics())

    metric = metrics.Metric(
        name="test_get_value_all1",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metrics.metrics.add_metric(metric)

    metric = metrics.Metric(
        name="test_get_value_all2",
        labels=["type"],
        documentation="documentation for test metric",
        values=[
            metrics.RampValue(
                labels=["ramp"], period=120, peak=100, offset=0, invert=False
            )
        ],
    )

    metrics.metrics.add_metric(metric)

    assert len(metrics.metrics.get_metrics()) == metric_count + 2

    response = client.get(
        "/metric/all",
        headers={
            "accept": "application/json",
        },
    )
    assert response.status_code == 200
