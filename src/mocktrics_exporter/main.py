import asyncio

import uvicorn
from prometheus_client import start_http_server

from mocktrics_exporter.api import api
from mocktrics_exporter.metrics import metrics


def main() -> None:
    start_http_server(8000)
    metrics.start_collecting()

    config = uvicorn.Config(api, port=8080, host="0.0.0.0")
    server = uvicorn.Server(config)

    asyncio.run(server.serve())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
