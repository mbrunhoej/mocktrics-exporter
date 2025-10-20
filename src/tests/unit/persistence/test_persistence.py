import pytest

from mocktrics_exporter import valueModels
from mocktrics_exporter.metrics import Metric


@pytest.mark.parametrize(
    "index",
    [
        "idx_metrics_name",
        "idx_metric_labels_metric_id",
        "idx_value_base_metric_id",
        "idx_value_labels_value_id",
    ],
)
def test_ensure_indicies(index, database):

    indicies = database.get_incidies()
    assert index in indicies


@pytest.mark.parametrize(
    "labels,  values",
    [
        (["response"], []),
        (["response", "port"], []),
        (["response"], [valueModels.StaticValue(value=0.0, labels=["200"])]),
        (
            ["response"],
            [
                valueModels.StaticValue(value=0.0, labels=["200"]),
                valueModels.RampValue(period=1, peak=1, labels=["500"]),
                valueModels.SquareValue(period=1, magnitude=1, duty_cycle=50.0, labels=["404"]),
                valueModels.SineValue(period=1, amplitude=1, labels=["419"]),
                valueModels.GaussianValue(mean=0, sigma=1.0, labels=["201"]),
            ],
        ),
    ],
)
def test_add_and_get_metric(base_metric, labels, values, database):

    base_metric.update({"labels": labels, "values": values})
    metric = Metric(**base_metric)
    database.add_metric(metric)

    metrics = database.get_metrics()
    assert len(metrics) == 1
    assert metric == metrics[0]


def test_get_metric_id(base_metric, database):

    names = ["metric1", "metric2", "metric3", "metric4", "metric5"]

    for name in names:
        base_metric.update({"name": name})
        metric = Metric(**base_metric)

        database.add_metric(metric)

    for index, name in enumerate(names, start=1):

        id = database.get_metric_id(name)
        assert index == id


def test_delete_metric(base_metric, database):

    base_metric.update(
        {"labels": ["response"], "values": [valueModels.StaticValue(value=0.0, labels=["200"])]}
    )
    metric = Metric(**base_metric)
    database.add_metric(metric)

    assert len(database.get_metrics()) == 1

    database.delete_metric(metric)

    assert len(database.get_metrics()) == 0


def test_delete_metric_value(base_metric, database):

    value = valueModels.StaticValue(value=0.0, labels=["200"])

    base_metric.update({"labels": ["response"], "values": [value]})
    metric = Metric(**base_metric)
    database.add_metric(metric)

    db_metric = database.get_metrics()[0]
    assert len(db_metric.values) == 1

    database.delete_metric_value(metric, value)

    db_metric = database.get_metrics()[0]
    assert len(db_metric.values) == 0


@pytest.mark.parametrize(
    "table,  expected_count",
    [
        ("metrics", 1),
        ("metric_labels", 1),
        ("value_base", 5),
        ("value_labels", 5),
        ("static", 1),
        ("ramp", 1),
        ("square", 1),
        ("sine", 1),
        ("gaussian", 1),
    ],
)
def test_cleanup(base_metric, table, expected_count, database):

    values = [
        valueModels.StaticValue(value=0.0, labels=["200"]),
        valueModels.RampValue(period=1, peak=1, labels=["500"]),
        valueModels.SquareValue(period=1, magnitude=1, duty_cycle=50.0, labels=["404"]),
        valueModels.SineValue(period=1, amplitude=1, labels=["419"]),
        valueModels.GaussianValue(mean=0, sigma=1.0, labels=["201"]),
    ]

    base_metric.update({"labels": ["response"], "values": values})
    metric = Metric(**base_metric)
    database.add_metric(metric)

    with database._connection:
        assert (
            database.cursor.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
            == expected_count
        )

    database.delete_metric(metric)

    with database._connection:
        assert database.cursor.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0] == 0
