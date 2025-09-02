import asyncio

import uvicorn
from prometheus_client import start_http_server

import api
from metrics import metrics


async def main() -> None:
    start_http_server(8000)
    metrics.start_collecting()

    config = uvicorn.Config(api.api, port=8080, host="0.0.0.0")
    server = uvicorn.Server(config)

    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
