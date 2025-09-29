import logging
from dataclasses import dataclass

from mocktrics_exporter import configuration, metaMetrics
from mocktrics_exporter.metrics import Metric


class MetricsCollection:

    @dataclass(slots=True)
    class Metrics:
        name: str
        metric: Metric
        read_only: bool

    def __init__(self):
        self._metrics: list[MetricsCollection.Metrics] = []
        self.update_metrics()

    def add_metric(self, metric: Metric, read_only: bool = False) -> str:
        if metric.name in [metric.name for metric in self._metrics]:
            raise KeyError("Metric id already exists")
        id = metric.name
        self._metrics.append(self.Metrics(id, metric, read_only))
        if read_only:
            metaMetrics.metrics.metric_config.inc()
        else:
            metaMetrics.metrics.metric_created.inc()
        self.update_metrics()
        logging.info(f"Adding metric: {id}: {metric}")
        return id

    def get_metrics(self) -> list[Metric]:
        return [metric.metric for metric in self._metrics]

    def get_metric(self, id: str) -> Metric:
        return [metric.metric for metric in self._metrics if metric.name == id][0]

    def delete_metric(self, id: str) -> None:
        metric = [metric for metric in self._metrics if metric.name == id][0]
        if metric.read_only:
            raise AttributeError("Metric is read only and cant be altered or removed")
        metric.metric.unregister()
        logging.debug(f"Unregistering metric: {metric.name}")
        self._metrics.remove(metric)
        metaMetrics.metrics.metric_deleted.inc()
        self.update_metrics()
        logging.info(f"Removing metric: {id}: {metric.name}")

    def update_metrics(self) -> None:
        metaMetrics.metrics.metric_count.set(len(self._metrics))


metrics = MetricsCollection()

for metric in configuration.configuration.metrics:

    metrics.add_metric(
        Metric(
            metric.name,
            metric.values,
            metric.documentation,
            metric.labels,
            metric.unit,
        ),
        read_only=True,
    )
