import re
import threading
import time
from copy import copy

from prometheus_client import REGISTRY, Gauge

from mocktrics_exporter import configuration, valueModels


class Metric:

    _registry = REGISTRY

    def __init__(
        self,
        name: str,
        values: list[valueModels.MetricValue],
        documentation: str = "",
        labels: list[str] = [],
        unit: str = "",
    ) -> None:

        self.validate_name(name)
        self.name = name
        self.validate_documentation(documentation)
        self.documentation = documentation
        self.validate_labels(labels)
        self.labels = labels
        self.validate_unit(unit)
        self.unit = unit

        self.validate_values(values)
        self.values = values

        self._metric = Gauge(
            self.name,
            documentation=self.documentation,
            labelnames=labels,
            unit=unit if not configuration.configuration.disable_units else "",
            registry=self._registry,
        )

    @staticmethod
    def validate_name(name: str):
        if len(name) < 1 or len(name) > 200:
            raise ValueError("Metric name must be between 1 and 200 characters long")
        pattern = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")
        if pattern.match(name) is None:
            raise ValueError("Metric name must only contain _, a-z or A-Z")

    @staticmethod
    def validate_documentation(documentation: str):

        if len(documentation) > 1000:
            raise ValueError("Metric documentation must be atmost 1000 characters long")
        pattern = re.compile(r"^[^\n]*$")
        if pattern.match(documentation) is None:
            raise ValueError(
                "Metric documentation most not contain newline and contain ony UTF-8 formatting"
            )

    @staticmethod
    def validate_labels(labels: list[str]):
        if len(labels) < 1 or len(labels) > 100:
            raise ValueError("Metric labels must be between 1 and 100")
        for label in labels:
            if len(label) < 1 or len(label) > 100:
                raise ValueError("Label names must be between 1 and 100")

    @staticmethod
    def validate_unit(unit: str):
        if len(unit) > 50:
            raise ValueError("Metric unit must be atmost 50 characters long")
        if unit != "":
            pattern = re.compile(r"^[a-zA-Z0-9_]*$")
            if pattern.match(unit) is None:
                raise ValueError("Metric unit must only contain _, a-z or A-Z")

    def validate_values(self, values: list[valueModels.MetricValue]):
        v = []
        for value in values:
            s = set(value.labels)
            if s in v:
                raise self.DuplicateValueLabelsetException(
                    "Matric values can not have duplicate labels"
                )
            v.append(s)
        for value in values:
            if len(self.labels) != len(value.labels):
                raise self.ValueLabelsetSizeException(
                    "Value label count must match metric label count"
                )

    def set_value(self) -> None:
        for value in self.values:
            self._metric.labels(*value.labels).set(value.get_value())

    def add_value(self, value: valueModels.MetricValue) -> None:
        v = copy(self.values)
        v.append(value)
        self.validate_values(v)
        self.values.append(value)

    class DuplicateValueLabelsetException(Exception):
        pass

    class ValueLabelsetSizeException(Exception):
        pass

    class MetricCreationException(Exception):
        pass

    def to_dict(self):
        return {
            "name": self.name,
            "documentation": self.documentation,
            "unit": self.unit,
            "labels": self.labels,
            "values": [value.model_dump() for value in self.values],
        }


class _Metrics:

    def __init__(self):
        self._metrics: dict[str, Metric] = {}
        self._run = False
        self._wake_event = threading.Event()
        self._collect_interval: int = configuration.configuration.collect_interval

    def add_metric(self, metric: Metric) -> str:
        id = metric.name
        self._metrics.update({id: metric})
        return id

    def get_metrics(self) -> dict[str, Metric]:
        return self._metrics

    def get_metric(self, name: str) -> Metric:
        return self._metrics[name]

    def delete_metric(self, id: str) -> None:
        self._metrics[id]
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
        )
    )
