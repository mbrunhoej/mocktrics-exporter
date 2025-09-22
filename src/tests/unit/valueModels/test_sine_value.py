import math
import time

import pydantic
import pytest

from mocktrics_exporter import valueModels
from mocktrics_exporter.valueModels import SineValue


class MonotonicMock:

    def __init__(self, start: int = 0, step: int = 1):
        self._time = start
        self._step = step

    def monotonic(self) -> float:
        self._time += self._step
        return float(self._time)


@pytest.mark.parametrize(
    "period, amplitude, offset",
    [
        (10, 10, 0),
        (10, 0, 0),
        (10, 10, 10),
    ],
)
def test_sine_value(monkeypatch, period, amplitude, offset):

    monotonic = MonotonicMock()
    monkeypatch.setattr(time, "monotonic", monotonic.monotonic)

    sine_value = SineValue(period=period, amplitude=amplitude, offset=offset, labels=[""])

    for i in range(1, period):
        progress = (i / period) % period

        value = sine_value.get_value()

        assert pytest.approx(value) == math.sin(progress * math.pi * 2) * amplitude + offset

    start_value = offset
    assert pytest.approx(sine_value.get_value()) == start_value


@pytest.mark.parametrize(
    "labels",
    [
        ([]),
        ([""]),
        (["test"]),
        (["test1", "test2"]),
    ],
)
def test_sine_value_labels(labels):
    sine_value = SineValue(period=10, amplitude=10, labels=labels)
    assert labels == sine_value.labels


def test_sine_value_duration_validator(monkeypatch):
    monkeypatch.setattr(valueModels, "parse_duration", lambda _: 100)
    sine_value = SineValue(period=10, amplitude=10, labels=[])
    assert sine_value.period == 100


def test_sine_value_size_validator(monkeypatch):
    monkeypatch.setattr(valueModels, "parse_size", lambda _: 100.0)
    sine_value = SineValue(period=10, amplitude=10, offset=10, labels=[])
    assert sine_value.amplitude == 100
    assert sine_value.offset == 100


def test_static_value_kind():
    SineValue(period=10, amplitude=10, labels=[], kind="sine")
    with pytest.raises(pydantic.ValidationError):
        SineValue(period=10, amplitude=10, labels=[], kind="test")  # type: ignore[arg-type]
