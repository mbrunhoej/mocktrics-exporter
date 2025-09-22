from mocktrics_exporter import configuration
from mocktrics_exporter.metrics import Metric


class MetricsCollection:

    def __init__(self):
        self._metrics: dict[str, Metric] = {}

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
