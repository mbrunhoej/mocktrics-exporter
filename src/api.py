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

        value = metrics.Metric.create_value(metric.value)

        try:
            m = metrics.metrics.get_metric(metric.name)
        except KeyError:
            # Create metric
            name = metrics.metrics.add_metric(
                metrics.Metric(
                    metric.name,
                    value,
                    metric.documentation,
                    metric.labels,
                    metric.unit,
                    read_only=True,
                )
            )
            return JSONResponse(
                status_code=201,
                content={"success": True, "name": name, "action": "created"},
            )

        # check labels match
        if not all(
            [keys in m.labels.keys() for keys in metric.labels.keys()]
        ) or not len(metric.labels.keys()) == len(m.labels.keys()):
            return JSONResponse(
                status_code=409,
                content={
                    "success": False,
                    "error": f"Mismatching labels: {metric.labels.keys()}, {m.labels.keys()}",
                },
            )

        m.value = value
        return JSONResponse(
            status_code=200,
            content={"success": True, "name": metric.name, "action": "updated"},
        )

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@api.delete("/metric")
async def delete_metric(id: str) -> JSONResponse:
    try:
        metrics.metrics.delete_metric(id)
        return JSONResponse(status_code=200, content={"success": True})
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )
