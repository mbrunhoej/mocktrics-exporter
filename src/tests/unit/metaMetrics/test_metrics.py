import pytest

from mocktrics_exporter import metaMetrics, metricCollection, metrics


def test_metric_count(base_metric):

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_count)) == 0.0

    metricCollection.metrics.add_metric(metrics.Metric(**{**base_metric, "name": "test1"}))

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_count)) == 1.0

    metricCollection.metrics.add_metric(
        metrics.Metric(**{**base_metric, "name": "test2"}), read_only=True
    )

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_count)) == 2.0


def test_metric_created(base_metric):

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_created)) == 0.0

    metricCollection.metrics.add_metric(metrics.Metric(**{**base_metric, "name": "test1"}))

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_created)) == 1.0

    metricCollection.metrics.add_metric(
        metrics.Metric(**{**base_metric, "name": "test2"}), read_only=True
    )

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_created)) == 1.0


def test_metric_config(base_metric):

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_config)) == 0.0

    metricCollection.metrics.add_metric(metrics.Metric(**{**base_metric, "name": "test1"}))

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_config)) == 0.0

    metricCollection.metrics.add_metric(
        metrics.Metric(**{**base_metric, "name": "test2"}), read_only=True
    )

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_config)) == 1.0


def test_metric_deleted(base_metric):

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_deleted)) == 0.0

    m = metrics.Metric(**base_metric)
    metricCollection.metrics.add_metric(m)

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_deleted)) == 0.0

    metricCollection.metrics.delete_metric(m.name)

    assert pytest.approx(metaMetrics.Metrics.get_value(metaMetrics.metrics.metric_deleted)) == 1.0
