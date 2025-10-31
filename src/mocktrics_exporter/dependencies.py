from mocktrics_exporter import metrics, prometheusApi, valueModels
from mocktrics_exporter.arguments import arguments
from mocktrics_exporter.metricCollection import MetricsCollection
from mocktrics_exporter.persistence import Persistence

metrics_collection = MetricsCollection()
database: Persistence | None = None
if arguments.persistence_path:
    database = Persistence(arguments.persistence_path)


base_address = "http://mimir.priv/prometheus"
tenant = 1
prom = prometheusApi.PrometheisApi(base_address, tenant)

res = prom.query_metric("up", "2025-10-28T09:50:00Z", "2025-10-28T10:00:00Z", step="60s")

val = valueModels.TimeSeriesValue(labels=res[0]["labels"].values(), series=res[0]["series"])
metric = metrics.Metric(
    res[0]["labels"]["__name__"], [val], documentation="", labels=res[0]["labels"].items()
)

metrics_collection.add_metric(metric)
