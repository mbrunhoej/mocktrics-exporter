import pydantic
import pytest

from mocktrics_exporter import valueModels
from mocktrics_exporter.valueModels import StaticValue


@pytest.mark.parametrize(
    "labels, value",
    [
        ([""], 10.0),
        ([""], -10.0),
        (["test"], 0.0),
        (["test1", "test2"], 0.0),
        ([], 0.0),
    ],
)
def test_static_value(labels, value):
    static_value = StaticValue(labels=labels, value=value)
    assert pytest.approx(static_value.value) == static_value.get_value()


def test_static_value_validator(monkeypatch):
    monkeypatch.setattr(valueModels, "parse_size", lambda _: 100.0)
    static_value = StaticValue(labels=[], value=0.0)
    assert pytest.approx(static_value.get_value()) == 100.0


def test_static_value_kind():
    StaticValue(labels=[], value=0.0, kind="static")
    with pytest.raises(pydantic.ValidationError):
        StaticValue(labels=[], value=0.0, kind="test")  # type: ignore[arg-type]
