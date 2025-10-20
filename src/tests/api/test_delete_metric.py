from fastapi.testclient import TestClient

from mocktrics_exporter import api, dependencies, metrics


def test_delete_metric():

    metric = metrics.Metric(
        name="test",
        labels=["type"],
        documentation="documentation for test metric",
        values=[],
    )

    dependencies.metrics_collection.add_metric(metric)

    client = TestClient(api.api)
    response = client.delete(
        "/metric/test",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 200
    assert len(dependencies.metrics_collection.get_metrics()) == 0


def test_delete_metric_nonexisting():

    client = TestClient(api.api)
    response = client.delete(
        "/metric/test",
        headers={
            "accept": "application/json",
        },
    )

    assert response.status_code == 404
    assert len(dependencies.metrics_collection.get_metrics()) == 0
