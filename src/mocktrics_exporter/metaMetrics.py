import prometheus_client


class Metrics:

    _metrics_base_name = "mocktrics_exporter"

    _registry = prometheus_client.REGISTRY

    def __init__(self, registry: prometheus_client.CollectorRegistry = _registry):

        self.metric_count = prometheus_client.Gauge(
            name=self._metrics_base_name + "_metrics_count",
            documentation="Total amount of metrics currently managed by the exporter",
            registry=registry,
        )

        self.metric_created = prometheus_client.Counter(
            name=self._metrics_base_name + "_metrics_created",
            documentation="Total amount of metrics created through the API",
            registry=registry,
        )

        self.metric_deleted = prometheus_client.Counter(
            name=self._metrics_base_name + "_metrics_deleted",
            documentation="Total amount of metrics deleted through the API",
            registry=registry,
        )

        self.metric_config = prometheus_client.Gauge(
            name=self._metrics_base_name + "_metrics_config",
            documentation="Total amount of metrics currently sourced from static configuration",
            registry=registry,
        )

    @staticmethod
    def get_value(metric: prometheus_client.Gauge | prometheus_client.Counter) -> float:
        return list(metric.collect())[0].samples[0].value


metrics = Metrics()
