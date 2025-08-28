import asyncio
import threading
import time
import uuid
import math
import random
from abc import ABC, abstractmethod

from prometheus_client import Counter, Gauge, Histogram, Summary

import configuration


class Value(ABC):

    kind: str = ""

    @abstractmethod
    def get_value(self) -> float:
        pass


class StaticValue(Value):

    kind = "gauge"

    def __init__(self, value: float):
        self.value = value

    def get_value(self) -> float:
        return self.value


class RampValue(Value):

    kind = "gauge"

    def __init__(self, period: int, peak: int, offset: int, invert: bool):
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


class SquareValue(Value):

    kind = "gauge"

    def __init__(
        self, period: int, magnitude: int, offset: int, duty_cycle: int, invert: bool
    ):
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


class SineValue(Value):

    kind = "gauge"

    def __init__(self, period: int, amplitude: int, offset: int):
        self.period = period
        self.amplitude = amplitude
        self.offset = offset
        self._start_time = time.monotonic()

    def get_value(self) -> float:
        delta = time.monotonic() - self._start_time
        progress = (delta % self.period) / self.period

        value = math.sin(progress * math.pi * 2) * self.amplitude

        return value + self.offset


class GaussianValue(Value):

    kind = "gauge"

    def __init__(self, mean: int, sigma: float):
        self.mean = mean
        self.sigma = sigma

    def get_value(self) -> float:
        return random.gauss(self.mean, self.sigma)
    
class Metric:

    base_name = "mocktrick"

    def __init__(
        self,
        name: str,
        value: Value,
        documentation: str = "",
        labels: dict[str, str] = {},
        unit: str = "",
        read_only: bool = False,
    ) -> None:
        self.name = f"{self.base_name}_{name}"
        self.documentation = documentation
        self.labels = labels
        self.unit = unit
        self._read_only = read_only

        self.value = value

        self._metric: Counter | Gauge | Histogram | Summary | None = None

        metric_type: (
            type[Counter] | type[Gauge] | type[Histogram] | type[Summary] | None
        ) = None
        match self.value.kind:
            case "counter":
                metric_type = Counter
            case "gauge":
                metric_type = Gauge
            case "histogram":
                metric_type = Histogram
            case "summary":
                metric_type = Summary

        if metric_type is None:
            raise self.MetricCreationException

        self._metric = metric_type(
            self.name,
            documentation=self.documentation,
            labelnames=labels.keys(),
            unit=unit if not configuration.configuration.disable_units else "",
        )

    def set_value(self) -> None:

        self._metric.labels(*[value for value in self.labels.values()]).set(
            self.value.get_value()
        )

    class MetricCreationException(Exception):
        pass


class _Metrics:

    def __init__(self):
        self._metrics: dict[str, Metric] = {}
        self._run = False

    def add_metric(self, metric: Metric, read_only: bool = False) -> str:
        id = str(uuid.uuid4())
        self._metrics.update({id: metric})
        return id

    def delete_metric(self, id: str) -> None:
        metric = self._metrics[id]
        metric._metric.remove(metric.labels.keys())
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

    match metric.value.kind:
        case "static":
            value = StaticValue(metric.value.value)
        case "ramp":
            value = RampValue(
                metric.value.period,
                metric.value.peak,
                metric.value.offset,
                metric.value.invert,
            )
        case "square":
            value = SquareValue(
                metric.value.period,
                metric.value.magnitude,
                metric.value.offset,
                metric.value.duty_cycle,
                metric.value.invert,
            )
        case "sine":
            value = SineValue(
                metric.value.period, metric.value.amplitude, metric.value.offset
            )
        case "gaussian":
            value = GaussianValue(
                metric.value.mean,
                metric.value.sigma
            )

    metrics.add_metric(
        Metric(
            metric.name,
            value,
            metric.documentation,
            metric.labels,
            metric.unit,
            read_only=True,
        )
    )
