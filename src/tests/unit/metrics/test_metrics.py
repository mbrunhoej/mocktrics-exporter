import pytest

from mocktrics_exporter.metrics import Metric


@pytest.mark.parametrize(
    "name, should_raise",
    [
        ("metric_ok", None),
    ],
)
def test_metric(base_metric, name, should_raise):
    m = {**base_metric, "name": name}
    if should_raise is not None:
        with pytest.raises(should_raise):
            Metric(**m)
    else:
        obj = Metric(**m)
        assert obj.name == name
