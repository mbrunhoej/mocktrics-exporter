import os
import tempfile

import pytest
from prometheus_client import CollectorRegistry

import mocktrics_exporter
import mocktrics_exporter.dependencies


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


@pytest.fixture(autouse=True, scope="function")
def database_temp(monkeypatch: pytest.MonkeyPatch):

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_path = tmp.name
    monkeypatch.setattr(
        mocktrics_exporter.persistence,
        "database",
        mocktrics_exporter.persistence.Persistence(db_path),
    )
    yield
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def base_metric():
    return {
        "name": "metric",
        "values": [],
        "documentation": "documentation example",
        "labels": ["test_label"],
        "unit": "meter_per_seconds",
    }
