import logging

from mocktrics_exporter import configuration
from mocktrics_exporter.metrics import Metric


class MetricsCollection:

    def __init__(self):
        self._metrics: dict[str, Metric] = {}

    def add_metric(self, metric: Metric) -> str:
        if metric.name in self._metrics.keys():
            raise KeyError("Metric id already exists")
        id = metric.name
        self._metrics.update({id: metric})
        logging.info(f"Adding metric: {id}: {metric}")
        return id

    def get_metrics(self) -> dict[str, Metric]:
        return self._metrics

    def get_metric(self, id: str) -> Metric:
        return self._metrics[id]

    def delete_metric(self, id: str) -> None:
        metric = self.get_metric(id)
        metric.unregister()
        logging.debug(f"Unregistering metric: {id}")
        self._metrics.pop(id)
        logging.info(f"Removing metric: {id}: {metric}")


metrics = MetricsCollection()

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
