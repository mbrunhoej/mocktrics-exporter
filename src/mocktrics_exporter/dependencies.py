from mocktrics_exporter.arguments import arguments
from mocktrics_exporter.metricCollection import MetricsCollection
from mocktrics_exporter.persistence import Persistence

metrics_collection = MetricsCollection()
database: Persistence | None = None
if arguments.persistence_path:
    database = Persistence(arguments.persistence_path)
