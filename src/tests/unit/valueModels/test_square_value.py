import time

import pydantic
import pytest

from mocktrics_exporter import valueModels
from mocktrics_exporter.valueModels import SquareValue


class MonotonicMock:

    def __init__(self, start: int = 0, step: int = 1):
        self._time = start
        self._step = step

    def monotonic(self) -> float:
        self._time += self._step
        return float(self._time)


@pytest.mark.parametrize(
    "period, magnitude, offset, duty_cycle, invert",
    [
        (10, 10, 0, 50, False),
        (10, -10, 0, 50, False),
        (10, 10, 10, 50, False),
        (10, 10, 0, 0, False),
        (10, 10, 0, 100, False),
    ],
)
def test_square_value(monkeypatch, period, magnitude, offset, duty_cycle, invert):

    monotonic = MonotonicMock()
    monkeypatch.setattr(time, "monotonic", monotonic.monotonic)

    square_value = SquareValue(
        period=period,
        magnitude=magnitude,
        offset=offset,
        duty_cycle=50.0,
        invert=invert,
        labels=[""],
    )

    for i in range(1, period):
        progress = (i / period) % period
        high = progress <= square_value.duty_cycle
        if invert:
            high = not high

        value = square_value.get_value()

        if high:
            assert value == magnitude + offset
        else:
            assert value == offset

    start_value = offset + magnitude if not invert else offset
    assert square_value.get_value() == start_value


@pytest.mark.parametrize(
    "labels",
    [
        ([]),
        ([""]),
        (["test"]),
        (["test1", "test2"]),
    ],
)
def test_square_value_labels(labels):
    square_value = SquareValue(period=10, magnitude=10, duty_cycle=50.0, labels=labels)
    assert labels == square_value.labels


def test_square_value_duration_validator(monkeypatch):
    monkeypatch.setattr(valueModels, "parse_duration", lambda _: 100)
    square_value = SquareValue(period=10, magnitude=10, duty_cycle=50.0, labels=[])
    assert square_value.period == 100


def test_square_value_size_validator(monkeypatch):
    monkeypatch.setattr(valueModels, "parse_size", lambda _: 100.0)
    square_value = SquareValue(period=10, magnitude=10, offset=10, duty_cycle=50.0, labels=[])
    assert square_value.magnitude == 100
    assert square_value.offset == 100


@pytest.mark.parametrize(
    "duty_cycle, should_raise",
    [
        (0.0, None),
        (100.0, None),
        (-1.0, ValueError),
        (101.0, ValueError),
    ],
)
def test_square_value_duty_cycle_validator(duty_cycle, should_raise):
    if should_raise:
        with pytest.raises(ValueError):
            SquareValue(period=10, magnitude=10, offset=10, duty_cycle=duty_cycle, labels=[])
    else:
        square_value = SquareValue(
            period=10, magnitude=10, offset=10, duty_cycle=duty_cycle, labels=[]
        )
        assert square_value.duty_cycle == duty_cycle / 100


def test_static_value_kind():
    SquareValue(period=10, magnitude=10, duty_cycle=50.0, labels=[], kind="square")
    with pytest.raises(pydantic.ValidationError):
        SquareValue(period=10, magnitude=10, duty_cycle=50.0, labels=[], kind="test")  # type: ignore[arg-type]
