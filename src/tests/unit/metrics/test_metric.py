import pytest

import mocktrics_exporter
from mocktrics_exporter.metrics import Metric
from mocktrics_exporter.valueModels import StaticValue


@pytest.mark.parametrize(
    "name, should_raise",
    [
        ("metric_ok", None),
        ("a", None),
        ("", ValueError),
        ("a" * 200, None),
        ("a" * 201, ValueError),
        ("_test_init_name", ValueError),
        ("test_init_name_", None),
        ("test*init*name", ValueError),
    ],
)
def test_metric_name_validation(base_metric, name, should_raise):
    m = {**base_metric, "name": name}
    if should_raise is not None:
        with pytest.raises(should_raise):
            Metric(**m)
    else:
        obj = Metric(**m)
        assert obj.name == name


@pytest.mark.parametrize(
    "documentation, should_raise",
    [
        ("documentation_ok", None),
        ("", None),
        ("a" * 1000, None),
        ("a" * 1001, ValueError),
        ("test*init*name", None),
        ("test\ninit\nname", ValueError),
    ],
)
def test_metric_documentation_validation(base_metric, documentation, should_raise):
    m = {**base_metric, "documentation": documentation}
    if should_raise is not None:
        with pytest.raises(should_raise):
            Metric(**m)
    else:
        obj = Metric(**m)
        assert obj.documentation == documentation


@pytest.mark.parametrize(
    "labels, should_raise",
    [
        (["label1"], None),
        ([], ValueError),
        ([str(label) for label in range(100)], None),
        ([str(label) for label in range(101)], ValueError),
        (["a"], None),
        ([""], ValueError),
        (["a" * 100], None),
        (["a" * 101], ValueError),
    ],
)
def test_metric_labels_validation(base_metric, labels, should_raise):
    m = {**base_metric, "labels": labels}
    if should_raise is not None:
        with pytest.raises(should_raise):
            Metric(**m)
    else:
        obj = Metric(**m)
        assert obj.labels == labels


@pytest.mark.parametrize(
    "unit, should_raise",
    [
        ("bytes", None),
        ("", None),
        ("a" * 50, None),
        ("a" * 51, ValueError),
        ("_test_init_name_", None),
        ("test*init*name", ValueError),
    ],
)
def test_metric_unit_validation(base_metric, unit, should_raise):
    m = {**base_metric, "unit": unit}
    if should_raise is not None:
        with pytest.raises(should_raise):
            Metric(**m)
    else:
        obj = Metric(**m)
        assert obj.unit == unit


@pytest.mark.parametrize(
    "values, should_raise",
    [
        ([], None),
        ([StaticValue(value=0.0, labels=["a"])], None),
        ([StaticValue(value=0.0, labels=["a"])] * 2, Metric.DuplicateValueLabelsetException),
        ([StaticValue(value=0.0, labels=[])], Metric.ValueLabelsetSizeException),
        ([StaticValue(value=0.0, labels=["a", "b"])], Metric.ValueLabelsetSizeException),
    ],
)
def test_init_values(base_metric, values, should_raise):
    m = {**base_metric, "values": values}
    if should_raise is not None:
        with pytest.raises(should_raise):
            Metric(**m)
    else:
        obj = Metric(**m)
        assert obj.values == values


@pytest.mark.parametrize(
    "values, should_raise",
    [
        ([], None),
        ([StaticValue(value=0.0, labels=["a"])], None),
        ([StaticValue(value=0.0, labels=["a"])] * 2, Metric.DuplicateValueLabelsetException),
        ([StaticValue(value=0.0, labels=[])], Metric.ValueLabelsetSizeException),
        ([StaticValue(value=0.0, labels=["a", "b"])], Metric.ValueLabelsetSizeException),
    ],
)
def test_add_value(base_metric, values, should_raise):
    metric = Metric(**base_metric)
    if should_raise is not None:
        with pytest.raises(should_raise):
            for value in values:
                metric.add_value(value)
    else:
        for value in values:
            metric.add_value(value)
        assert metric.values == values


class MetricFamilyMock:

    def __init__(self, name: str, documentation: str, value: None, labels: list[str], unit: str):
        self.name = name
        self.documentation = documentation
        self.labels = labels
        self.unit = unit

        self.collected_values: list[dict] = []

    def add_metric(self, labels: list[str], value: float) -> None:
        self.collected_values.append({"labels": labels, "value": value})


@pytest.fixture(scope="function")
def metric_family_mock(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        mocktrics_exporter.metrics.Metric.Collector, "_metricFamily", MetricFamilyMock
    )


def test_collector(metric_family_mock, base_metric):
    base_metric.update({"values": [StaticValue(value=100.0, labels=["test"])]})
    metric = Metric(**base_metric)
    collector = metric.Collector(metric)

    metric_family = next(collector.collect())

    assert metric_family.name == base_metric["name"]
    assert metric_family.documentation == base_metric["documentation"]
    assert metric_family.labels == base_metric["labels"]
    assert metric_family.unit == base_metric["unit"]
    assert metric_family.collected_values == [{"labels": ["test"], "value": 100.0}]


def is_registered(metric: Metric):
    return metric._collector in metric._registry._collector_to_names


def test_register(base_metric):
    metric = Metric(**base_metric)
    assert is_registered(metric)


def test_unregister(base_metric):
    metric = Metric(**base_metric)
    metric.unregister()
    assert not is_registered(metric)
