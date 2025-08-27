from fastapi import FastAPI
from fastapi.responses import JSONResponse

import configuration
import metrics

api = FastAPI(edirect_slashes=False)


@api.get("/")
async def root() -> JSONResponse:
    return JSONResponse(
        content={"configuration": configuration.configuration.model_dump()}
    )


@api.post("/metric")
async def post_metric(metric: configuration.Metric) -> JSONResponse:

    try:
        match metric.value.kind:
            case "static":
                value = metrics.StaticValue(metric.value.value)

        id = metrics.metrics.add_metric(
            metrics.Metric(
                metric.name,
                value,
                metric.documentation,
                metric.labels,
                metric.unit,
                read_only=True,
            )
        )
        return JSONResponse(status_code=201, content={"success": True, "uuid": id})
    except ValueError as e:
        return JSONResponse(
            status_code=409, content={"success": False, "error": str(e)}
        )
    except Exception as e:
        print(type(e))
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@api.delete("/metric")
async def delete_metric(id: str) -> JSONResponse:

    try:
        metrics.metrics.delete_metric(id)
        return JSONResponse(status_code=200, content={"success": True})
    except Exception as e:
        print(type(e))
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )
