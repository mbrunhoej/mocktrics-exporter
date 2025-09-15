import pytest

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
def test_metric_documentation_validation(base_metric, registry, documentation, should_raise):
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
