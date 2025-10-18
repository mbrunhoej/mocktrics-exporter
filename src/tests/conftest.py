import os
import tempfile
import typing

import pytest
from prometheus_client import CollectorRegistry

import mocktrics_exporter
import mocktrics_exporter.dependencies
from mocktrics_exporter.persistence import Persistence


@pytest.fixture(autouse=True, scope="function")
def registry_mock(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(mocktrics_exporter.metrics.Metric, "_registry", CollectorRegistry())
    monkeypatch.setattr(
        mocktrics_exporter.metaMetrics,
        "metrics",
        mocktrics_exporter.metaMetrics.Metrics(CollectorRegistry()),
    )


@pytest.fixture(autouse=True, scope="function")
def clear_metrics(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(mocktrics_exporter.dependencies.metrics_collection, "_metrics", [])


@pytest.fixture
def database(monkeypatch: pytest.MonkeyPatch) -> typing.Generator[Persistence, None, None]:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        path = tmp.name

    db = Persistence(path)

    monkeypatch.setattr(
        mocktrics_exporter.dependencies,
        "database",
        db,
    )
    yield db
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def base_metric() -> dict:
    return {
        "name": "metric",
        "values": [],
        "documentation": "documentation example",
        "labels": ["test_label"],
        "unit": "meter_per_seconds",
    }
