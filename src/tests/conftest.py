import pytest
from prometheus_client import CollectorRegistry

import mocktrics_exporter


@pytest.fixture(autouse=True, scope="function")
def registry(monkeypatch):
    monkeypatch.setattr(mocktrics_exporter.metrics.Metric, "_registry", CollectorRegistry())


@pytest.fixture
def base_metric():
    return {
        "name": "metric",
        "values": [],
        "documentation": "documentation example",
        "labels": "test_label",
        "unit": "meter_per_seconds",
    }
