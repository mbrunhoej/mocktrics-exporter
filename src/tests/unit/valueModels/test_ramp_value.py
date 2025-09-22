import time

import pydantic
import pytest

from mocktrics_exporter import valueModels
from mocktrics_exporter.valueModels import RampValue


class MonotonicMock:

    def __init__(self, start: int = 0, step: int = 1):
        self._time = start
        self._step = step

    def monotonic(self) -> float:
        self._time += self._step
        return float(self._time)


@pytest.mark.parametrize(
    "period, peak, offset, invert",
    [
        (10, 10, 0, False),
        (10, -10, 0, False),
        (10, 10, 10, False),
        (10, 10, 0, True),
    ],
)
def test_ramp_value(monkeypatch, period, peak, offset, invert):

    monotonic = MonotonicMock()
    monkeypatch.setattr(time, "monotonic", monotonic.monotonic)

    ramp_value = RampValue(period=period, peak=peak, offset=offset, invert=invert, labels=[""])

    for i in range(1, period):
        progress = (i / period) % period
        if invert:
            progress = 1 - progress

        value = ramp_value.get_value()

        assert pytest.approx(value) == (progress * peak) + offset

    start_value = offset if not invert else offset + peak
    assert pytest.approx(ramp_value.get_value()) == start_value


@pytest.mark.parametrize(
    "labels",
    [
        ([]),
        ([""]),
        (["test"]),
        (["test1", "test2"]),
    ],
)
def test_ramp_value_labels(labels):
    ramp_value = RampValue(period=10, peak=10, labels=labels)
    assert labels == ramp_value.labels


def test_ramp_value_duration_validator(monkeypatch):
    monkeypatch.setattr(valueModels, "parse_duration", lambda _: 100)
    ramp_value = RampValue(period=10, peak=10, labels=[])
    assert ramp_value.period == 100


def test_ramp_value_size_validator(monkeypatch):
    monkeypatch.setattr(valueModels, "parse_size", lambda _: 100.0)
    ramp_value = RampValue(period=10, peak=10, offset=10, labels=[])
    assert ramp_value.peak == 100
    assert ramp_value.offset == 100


def test_static_value_kind():
    RampValue(period=10, peak=10, labels=[], kind="ramp")
    with pytest.raises(pydantic.ValidationError):
        RampValue(period=10, peak=10, labels=[], kind="test")  # type: ignore[arg-type]
