import pytest

from mocktrics_exporter import persistence, valueModels
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
def test_ensure_indicies(index):

    db = persistence.database
    indicies = db.get_incidies()
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
def test_add_and_get_metric(base_metric, labels, values):

    db = persistence.database

    base_metric.update({"labels": labels, "values": values})
    metric = Metric(**base_metric)
    db.add_metric(metric)

    metrics = db.get_metrics()

    print(metric.to_dict())
    print(metrics[0].to_dict())
    assert metric == metrics[0]
