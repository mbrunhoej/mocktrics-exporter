import re
from copy import copy
from typing import cast

from prometheus_client import REGISTRY, registry
from prometheus_client.core import GaugeMetricFamily

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

        self._collector = self.Collector(self)

        self.register()

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

    def add_value(self, value: valueModels.MetricValue) -> None:
        v = copy(self.values)
        v.append(value)
        self.validate_values(v)
        self.values.append(value)

    def register(self):
        self._registry.register(cast(registry.Collector, self._collector))

    def unregister(self):
        self._registry.unregister(cast(registry.Collector, self._collector))

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

    class Collector:

        _metricFamily = GaugeMetricFamily

        def __init__(self, metric: "Metric"):
            self._metric = metric

        def collect(self):

            c = self._metricFamily(
                self._metric.name,
                self._metric.documentation,
                None,
                self._metric.labels,
                self._metric.unit if not configuration.configuration.disable_units else "",
            )

            for value in self._metric.values:

                c.add_metric(value.labels, value.get_value())

            yield c
