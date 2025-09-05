import asyncio

import uvicorn
from prometheus_client import start_http_server

from . import api
from .arguments import arguments
from .metrics import metrics
from .ui import register as register_ui


async def main() -> None:
    start_http_server(arguments.metrics_port)
    metrics.start_collecting()

    # Register UI (templates + routes) with the FastAPI app
    register_ui(api.api)

    config = uvicorn.Config(api.api, port=arguments.api_port, host="0.0.0.0")
    server = uvicorn.Server(config)

    await server.serve()


def cli() -> None:
    """Console script entry point."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    cli()
