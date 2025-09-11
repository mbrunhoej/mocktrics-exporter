import pytest

from mocktrics_exporter.metrics import Metric


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


# def test_init_values(metric_arguments):
#     pass
#


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


#
# def test_init_read_only():
#     pass
