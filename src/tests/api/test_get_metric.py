import pytest
from fastapi.testclient import TestClient

from mocktrics_exporter import api, metricCollection, metrics


@pytest.fixture(scope="function", autouse=True)
def client():
    with TestClient(api.api) as client:
        yield client


def test_get_metric(client: TestClient):

    metric = metrics.Metric(
        name="test",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metricCollection.metrics.add_metric(metric)

    response = client.get(
        "/metric/test",
        headers={
            "accept": "application/json",
        },
    )
    assert response.status_code == 200


def test_metric_nonexisting(client: TestClient):

    response = client.get(
        "/metric/test",
        headers={
            "accept": "application/json",
        },
    )
    assert response.status_code == 404
