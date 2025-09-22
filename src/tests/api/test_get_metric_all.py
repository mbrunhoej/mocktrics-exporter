import pytest
from fastapi.testclient import TestClient

from mocktrics_exporter import api, metricCollection, metrics, valueModels


@pytest.fixture(scope="function", autouse=True)
def client():
    with TestClient(api.api) as client:
        yield client


def test_get_value_all(client: TestClient):

    metric = metrics.Metric(
        name="test1",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    metricCollection.metrics.add_metric(metric)

    metric = metrics.Metric(
        name="test2",
        labels=["type"],
        documentation="documentation for test metric",
        values=[
            valueModels.RampValue.model_validate(
                {"kind": "ramp", "labels": ["ramp"], "period": "2m", "peak": 100}
            )
        ],
    )

    metricCollection.metrics.add_metric(metric)

    assert len(metricCollection.metrics.get_metrics()) == 2

    response = client.get(
        "/metric/all",
        headers={
            "accept": "application/json",
        },
    )
    assert response.status_code == 200
