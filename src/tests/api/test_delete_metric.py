import pytest
from fastapi.testclient import TestClient

from mocktrics_exporter import api, metricCollection, metrics


@pytest.fixture(scope="function", autouse=True)
def client():
    with TestClient(api.api) as client:
        yield client


def test_delete_metric(client: TestClient):

    metric = metrics.Metric(
        name="test",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metricCollection.metrics.add_metric(metric)

    response = client.delete(
        "/metric/test",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 200
    assert len(metricCollection.metrics.get_metrics()) == 0


def test_delete_metric_nonexisting(client: TestClient):

    response = client.delete(
        "/metric/test",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 404
    assert len(metricCollection.metrics.get_metrics()) == 0
