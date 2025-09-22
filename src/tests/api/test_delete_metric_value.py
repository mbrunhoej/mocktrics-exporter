import pytest
from fastapi.testclient import TestClient

from mocktrics_exporter import api, metricCollection, metrics, valueModels


@pytest.fixture(scope="function", autouse=True)
def client():
    with TestClient(api.api) as client:
        yield client


def test_metric_delete_value(client: TestClient):

    metric = metrics.Metric(
        name="test",
        labels=["type"],
        documentation="documentation for test metric",
        values=[
            valueModels.StaticValue.model_validate(
                {"kind": "static", "value": 0, "labels": ["static"]}
            )
        ],
    )

    metricCollection.metrics.add_metric(metric)

    response = client.delete(
        "/metric/test/value?labels=static",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 200
    assert len(metricCollection.metrics.get_metrics()) == 1
    assert len(metric.values) == 0


def test_mismatching_labels_length(client: TestClient):

    metric = metrics.Metric(
        name="test",
        labels=["type"],
        documentation="documentation for test metric",
        values=[
            valueModels.StaticValue.model_validate(
                {"kind": "static", "value": 0, "labels": ["static"]}
            )
        ],
    )

    metricCollection.metrics.add_metric(metric)

    response = client.delete(
        "/metric/test/value?labels=static&labels=nonexisting",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 419
    assert len(metricCollection.metrics.get_metrics()) == 1
    assert len(metric.values) == 1


def test_delete_mismatching_labels(client: TestClient):

    metric = metrics.Metric(
        name="test",
        labels=["type"],
        documentation="documentation for test metric",
        values=[
            valueModels.StaticValue.model_validate(
                {"kind": "static", "value": 0, "labels": ["static"]}
            )
        ],
    )

    metricCollection.metrics.add_metric(metric)

    response = client.delete(
        "/metric/test/value?labels=wronglabel",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 404
    assert len(metricCollection.metrics.get_metrics()) == 1
    assert len(metric.values) == 1


def test_delete_nonexisting_metric(client: TestClient):

    response = client.delete(
        "/metric/test/value?labels=static",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 404
    assert len(metricCollection.metrics.get_metrics()) == 0
