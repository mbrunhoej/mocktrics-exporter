import asyncio
import logging

import uvicorn
from prometheus_client import start_http_server

from mocktrics_exporter.api import api
from mocktrics_exporter.arguments import arguments

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main() -> None:

    start_http_server(arguments.metrics_port)

    config = uvicorn.Config(api, port=arguments.api_port, host="0.0.0.0")
    server = uvicorn.Server(config)

    asyncio.run(server.serve())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
