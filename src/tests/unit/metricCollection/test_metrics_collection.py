import pytest

from mocktrics_exporter.metricCollection import MetricsCollection
from mocktrics_exporter.metrics import Metric


def test_add_metric(base_metric):

    metric = Metric(**base_metric)

    collection = MetricsCollection()
    collection.add_metric(metric)

    assert metric.name in collection._metrics
    assert metric in collection._metrics.values()


def test_add_metric_duplicate(base_metric):

    metric1 = Metric(**base_metric)
    metric2 = Metric(**base_metric)

    collection = MetricsCollection()
    collection.add_metric(metric1)

    with pytest.raises(KeyError):
        collection.add_metric(metric2)

    assert len(collection._metrics) == 1


def test_get_metrics(base_metric):

    collection = MetricsCollection()
    metric = Metric(**base_metric)
    collection.add_metric(metric)

    assert metric == collection.get_metrics()[metric.name]


def test_get_metric(base_metric):

    collection = MetricsCollection()
    metric = Metric(**base_metric)
    collection.add_metric(metric)

    assert metric == collection.get_metric(metric.name)


def test_delete_metric(base_metric):

    metric = Metric(**base_metric)

    collection = MetricsCollection()
    collection.add_metric(metric)

    collection.delete_metric(metric.name)

    assert len(collection._metrics) == 0


def test_delete_unregister(monkeypatch, base_metric):

    metric = Metric(**base_metric)

    collection = MetricsCollection()
    collection.add_metric(metric)

    monkeypatch.setattr(metric, "unregister", lambda: (_ for _ in ()).throw(Exception()))

    with pytest.raises(Exception):
        collection.delete_metric(metric.name)
