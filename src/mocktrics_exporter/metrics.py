import threading
import time

from prometheus_client import Gauge

from . import configuration, valueModels


class Metric:

    def __init__(
        self,
        name: str,
        values: list[valueModels.MetricValue],
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
            self._metric.labels(*value.labels).set(value.get_value())

    def add_value(self, value: valueModels.MetricValue) -> None:
        if len(self.labels) != len(value.labels):
            raise AttributeError("Mismatching label count")

        for val in self.values:
            if all(label in value.labels for label in val.labels):
                raise IndexError("Duplicate labels")

        self.values.append(value)

    @property
    def read_only(self) -> bool:
        return self._read_only

    class MetricCreationException(Exception):
        pass

    def to_dict(self):
        return {
            "name": self.name,
            "documentation": self.documentation,
            "unit": self.unit,
            "labels": self.labels,
            "read_only": self.read_only,
            "values": [value.model_dump() for value in self.values],
        }


class _Metrics:

    def __init__(self):
        self._metrics: dict[str, Metric] = {}
        self._run = False
        self._wake_event = threading.Event()
        self._collect_interval: int = configuration.configuration.collect_interval

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

                next_run += self._collect_interval
                sleep_time = next_run - time.monotonic()
                if sleep_time > 0:
                    awakened = self._wake_event.wait(timeout=sleep_time)
                    if awakened:
                        self._wake_event.clear()
                        next_run = time.monotonic()
                        continue
                else:
                    next_run = time.monotonic()

                if not self._run:
                    break

        thread = threading.Thread(target=_tf, daemon=True)
        thread.start()

    def stop_collecting(self) -> None:
        self._run = False

    def wake(self) -> None:
        self._wake_event.set()

    def get_collect_interval(self) -> int:
        return int(self._collect_interval)

    def set_collect_interval(self, seconds: int) -> None:
        self._collect_interval = int(seconds)
        self.wake()


metrics = _Metrics()

for metric in configuration.configuration.metrics:

    metrics.add_metric(
        Metric(
            metric.name,
            metric.values,
            metric.documentation,
            metric.labels,
            metric.unit,
            read_only=True,
        )
    )
