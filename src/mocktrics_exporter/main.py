import asyncio
import logging

import uvicorn
from prometheus_client import start_http_server

from mocktrics_exporter import configuration, dependencies, metrics
from mocktrics_exporter.api import api
from mocktrics_exporter.arguments import arguments

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main() -> None:

    for config_metric in configuration.configuration.metrics:

        dependencies.metrics_collection.add_metric(
            metrics.Metric(
                config_metric.name,
                config_metric.values,
                config_metric.documentation,
                config_metric.labels,
                config_metric.unit,
            ),
            read_only=True,
        )

    if dependencies.database is not None:
        for database_metric in dependencies.database.get_metrics():
            dependencies.metrics_collection.add_metric(database_metric)

    start_http_server(arguments.metrics_port)

    config = uvicorn.Config(api, port=arguments.api_port, host="0.0.0.0")
    server = uvicorn.Server(config)

    asyncio.run(server.serve())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
