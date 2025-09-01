import asyncio
import math
import random
import threading
import time
import uuid
from abc import ABC, abstractmethod

from prometheus_client import Counter, Gauge, Histogram, Summary

import configuration


class Value(ABC):

    def get_labels(self) -> list[str]:
        return self._labels

    @abstractmethod
    def get_value(self) -> float:
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, any]:
        pass


class StaticValue(Value):

    kind = "gauge"

    def __init__(self, labels: list[str], value: float):
        self._labels = labels
        self.value = value

    def get_value(self) -> float:
        return self.value

    def to_dict(self) -> dict[str, any]:
        return {"labels": self._labels, "kind": "static"}


class RampValue(Value):

    kind = "gauge"

    def __init__(
        self, labels: list[str], period: int, peak: int, offset: int, invert: bool
    ):
        self._labels = labels
        self.period = period
        self.peak = peak
        self.offset = offset
        self.invert = invert
        self._start_time = time.monotonic()

    def get_value(self) -> float:
        delta = time.monotonic() - self._start_time
        progress = (delta % self.period) / self.period
        value = progress * self.peak
        if self.invert:
            value = self.peak - value

        return value + self.offset

    def to_dict(self) -> dict[str, any]:
        return {
            "labels": self._labels,
            "kind": "ramp",
            "peak": self.peak,
            "offset": self.offset,
            "invert": self.invert,
        }


class SquareValue(Value):

    kind = "gauge"

    def __init__(
        self,
        labels: list[str],
        period: int,
        magnitude: int,
        offset: int,
        duty_cycle: int,
        invert: bool,
    ):
        self._labels = labels
        self.period = period
        self.magnitude = magnitude
        self.offset = offset
        self.invert = invert
        self.duty_cycle = duty_cycle / 100
        self._start_time = time.monotonic()

    def get_value(self) -> float:
        delta = time.monotonic() - self._start_time
        progress = (delta % self.period) / self.period

        if not self.invert:
            value = self.magnitude if progress < self.duty_cycle else 0
        else:
            value = 0 if progress < self.duty_cycle else self.magnitude

        return value + self.offset

    def to_dict(self) -> dict[str, any]:
        return {
            "labels": self._labels,
            "kind": "square",
            "magnitude": self.magnitude,
            "offset": self.offset,
            "duty_cycle": self.duty_cycle,
            "invert": self.invert,
        }


class SineValue(Value):

    kind = "gauge"

    def __init__(self, labels: list[str], period: int, amplitude: int, offset: int):
        self._labels = labels
        self.period = period
        self.amplitude = amplitude
        self.offset = offset
        self._start_time = time.monotonic()

    def get_value(self) -> float:
        delta = time.monotonic() - self._start_time
        progress = (delta % self.period) / self.period

        value = math.sin(progress * math.pi * 2) * self.amplitude

        return value + self.offset

    def to_dict(self) -> dict[str, any]:
        return {
            "labels": self._labels,
            "kind": "sine",
            "amplitude": self.amplitude,
            "offset": self.offset,
        }


class GaussianValue(Value):

    kind = "gauge"

    def __init__(self, labels: list[str], mean: int, sigma: float):
        self._labels = labels
        self.mean = mean
        self.sigma = sigma

    def get_value(self) -> float:
        return random.gauss(self.mean, self.sigma)

    def to_dict(self) -> dict[str, any]:
        return {
            "labels": self._labels,
            "kind": "gaussian",
            "mean": self.mean,
            "sigma": self.sigma,
        }


class Metric:

    def __init__(
        self,
        name: str,
        values: list[Value],
        documentation: str = "",
        labels: list[str] = [],
        unit: str = "",
        read_only: bool = False,
    ) -> None:
        self.name = name
        self.documentation = documentation
        self.labels = labels
        self.unit = unit
        self._read_only = read_only

        self.values = values

        self._metric = Gauge(
            self.name,
            documentation=self.documentation,
            labelnames=labels,
            unit=unit if not configuration.configuration.disable_units else "",
        )

    def set_value(self) -> None:

        for value in self.values:

            self._metric.labels(*value.get_labels()).set(value.get_value())

    @property
    def read_only(self) -> bool:
        return self._read_only

    class MetricCreationException(Exception):
        pass

    @staticmethod
    def create_value(value: configuration.MetricValue) -> Value:

        match value.kind:
            case "static":
                v = StaticValue(value.labels, value.value)
            case "ramp":
                v = RampValue(
                    value.labels,
                    value.period,
                    value.peak,
                    value.offset,
                    value.invert,
                )
            case "square":
                v = SquareValue(
                    value.labels,
                    value.period,
                    value.magnitude,
                    value.offset,
                    value.duty_cycle,
                    value.invert,
                )
            case "sine":
                v = SineValue(value.labels, value.period, value.amplitude, value.offset)
            case "gaussian":
                v = GaussianValue(value.labels, value.mean, value.sigma)

        return v

    def to_dict(self):
        return {
            "name": self.name,
            "documentation": self.documentation,
            "unit": self.unit,
            "labels": self.labels,
            "read_only": self.read_only,
            "values": [value.to_dict() for value in self.values],
        }


class _Metrics:

    def __init__(self):
        self._metrics: dict[str, Metric] = {}
        self._run = False

    def add_metric(self, metric: Metric, read_only: bool = False) -> str:
        id = metric.name
        self._metrics.update({id: metric})
        return id

    def get_metrics(self) -> dict[str, Metric]:
        return self._metrics

    def get_metric(self, name: str) -> Metric:
        return self._metrics[name]

    def delete_metric(self, id: str) -> None:
        metric = self._metrics[id]
        if metric.read_only:
            raise AttributeError
        self._metrics.pop(id)

    def collect(self) -> None:
        for metric in self._metrics.values():
            metric.set_value()

    def start_collecting(
        self,
    ) -> None:

        def _tf() -> None:

            self._run = True
            next_run = time.monotonic()
            while True:

                self.collect()

                next_run += configuration.configuration.collect_interval
                sleep_time = next_run - time.monotonic()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    next_run = time.time()

                if not self._run:
                    break

        thread = threading.Thread(target=_tf, daemon=True)
        thread.start()

    def stop_collecting(self) -> None:
        self._run = False


metrics = _Metrics()

for metric in configuration.configuration.metrics:

    values = [Metric.create_value(value) for value in metric.values]

    metrics.add_metric(
        Metric(
            metric.name,
            values,
            metric.documentation,
            metric.labels,
            metric.unit,
            read_only=True,
        )
    )
