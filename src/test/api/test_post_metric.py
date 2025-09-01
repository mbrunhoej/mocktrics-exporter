import pytest
from main import main
import multiprocessing
import time
import requests
import asyncio
from fastapi.testclient import TestClient
import api
import metrics
from prometheus_client import REGISTRY, CollectorRegistry


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
    from prometheus_client import core

    core.REGISTRY = CollectorRegistry()


def test_metric_single_value(client: TestClient):
    metric_count = len(metrics.metrics.get_metrics())

    response = client.post(
        "/metric",
        headers={
            "accept": "application/json",
        },
        json={
            "name": "test_metric_single_value",
            "documentation": "documentation for test metric",
            "unit": "",
            "labels": ["type"],
            "values": [{"kind": "static", "labels": ["static"], "value": 0}],
        },
    )
    assert response.status_code == 201
    assert len(metrics.metrics.get_metrics()) == metric_count + 1
    metric = metrics.metrics.get_metric("test_metric_single_value")
    assert len(metric.values) == 1


def test_metric_multiple_value(client: TestClient):
    metric_count = len(metrics.metrics.get_metrics())

    response = client.post(
        "/metric",
        headers={
            "accept": "application/json",
        },
        json={
            "name": "test_metric_multiple_value",
            "documentation": "documentation for test metric",
            "unit": "",
            "labels": ["type"],
            "values": [
                {"kind": "static", "labels": ["static"], "value": 0},
                {
                    "kind": "ramp",
                    "labels": ["ramp"],
                    "period": "2m",
                    "peak": 100,
                    "invert": False,
                },
            ],
        },
    )
    assert response.status_code == 201
    assert len(metrics.metrics.get_metrics()) == metric_count + 1
    metric = metrics.metrics.get_metric("test_metric_multiple_value")
    assert len(metric.values) == 2


def test_metric_no_value(client: TestClient):
    metric_count = len(metrics.metrics.get_metrics())

    response = client.post(
        "/metric",
        headers={
            "accept": "application/json",
        },
        json={
            "name": "test_metric_no_value",
            "documentation": "documentation for test metric",
            "unit": "",
            "labels": ["type"],
            "values": [],
        },
    )
    assert response.status_code == 201
    assert len(metrics.metrics.get_metrics()) == metric_count + 1
    metric = metrics.metrics.get_metric("test_metric_no_value")
    assert len(metric.values) == 0


def test_metric_duplicate_value(client: TestClient):
    metric_count = len(metrics.metrics.get_metrics())

    client.post(
        "/metric",
        headers={
            "accept": "application/json",
        },
        json={
            "name": "test_metric_duplicate_value",
            "documentation": "documentation for test metric",
            "unit": "",
            "labels": ["type"],
            "values": [],
        },
    )

    response = client.post(
        "/metric",
        headers={
            "accept": "application/json",
        },
        json={
            "name": "test_metric_duplicate_value",
            "documentation": "documentation for test metric",
            "unit": "",
            "labels": ["type"],
            "values": [],
        },
    )
    assert response.status_code == 409
    assert len(metrics.metrics.get_metrics()) == metric_count + 1


def test_metric_unprocessable_value(client: TestClient):

    metric_count = len(metrics.metrics.get_metrics())

    response = client.post(
        "/metric",
        headers={
            "accept": "application/json",
        },
        json={
            "name": "test_metric_duplicate_value",
            "documentation": "documentation for test metric",
            "unit": "",
            "labels": ["type"],
            "values": [],
        },
    )

    assert response.status_code == 500
    assert len(metrics.metrics.get_metrics()) == metric_count
