import asyncio
import threading
import time
import uuid
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

    def __init__(self, increments_per_second, limit: int, offset: int):
        self.increments_per_second = increments_per_second
        self.limit = limit
        self.offset = offset
        self._value = 0.0
        self._time = time.monotonic()

    def get_value(self) -> float:
        last = self._time
        self._start = time.monotonic()
        delta = self._start - last
        self._value += delta * self.increments_per_second

        if self._value > self.limit:
            self._value = self._value - self.limit

        return self._value + self.offset


class Metric:

    base_name = "mock"

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
                metric.value.increments_per_seconds,
                metric.value.limit,
                metric.value.offset,
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
