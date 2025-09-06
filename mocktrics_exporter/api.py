from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

from . import configuration, metrics, valueModels

api = FastAPI(redirect_slashes=False)


@api.get("/")
async def get_root() -> JSONResponse:
    return JSONResponse(content=configuration.configuration)


@api.get("/collect-interval")
async def get_collect_interval() -> JSONResponse:
    return JSONResponse(
        content={
            "seconds": metrics.metrics.get_collect_interval(),
            "editable": not configuration.config_has_collect_interval,
        }
    )


@api.post("/collect-interval/{time}")
async def post_collect_interval(time: str | int) -> JSONResponse:
    editable = not configuration.config_has_collect_interval
    if not editable:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": "Configured in config.yaml (read-only)",
            },
        )
    try:
        metrics.metrics.set_collect_interval(valueModels.parse_duration(time))
        return JSONResponse(content={"success": True})
    except Exception as e:
        return JSONResponse(
            status_code=400, content={"success": False, "error": str(e)}
        )


@api.post("/metric")
async def post_metric(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
        metric = configuration.Metric.model_validate(payload)
        values = [v for v in metric.values]
        try:
            metrics.metrics.get_metric(metric.name)
            return JSONResponse(
                status_code=409,
                content={"success": False, "error": "Metric already exists"},
            )
        except KeyError:
            pass
        if len(metric.labels) == 0:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Metric must have atleast one label",
                },
            )
        name = metrics.metrics.add_metric(
            metrics.Metric(
                metric.name,
                values,
                metric.documentation,
                metric.labels,
                metric.unit,
                read_only=False,
            )
        )
        return JSONResponse(
            status_code=201,
            content={"success": True, "name": name, "action": "created"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@api.post("/metric/{id}/value")
async def post_metric_value(id: str, value: valueModels.MetricValue) -> JSONResponse:
    try:
        metric = metrics.metrics.get_metric(id)
        if metric.read_only:
            return JSONResponse(
                status_code=403,
                content={"success": False, "error": "Metric is read-only"},
            )
        metric.add_value(value)
    except AttributeError:
        return JSONResponse(
            status_code=419,
            content={
                "success": False,
                "error": "Value label count does not match metric label count",
            },
        )
    except IndexError:
        return JSONResponse(
            status_code=409,
            content={"success": False, "error": "Labelset already exists"},
        )
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Requested metric does not exist"},
        )

    return JSONResponse(
        status_code=201, content={"success": True, "name": id, "action": "created"}
    )


@api.get("/metric/all")
def get_metric_all() -> JSONResponse:
    return JSONResponse(
        content={
            key: value.to_dict() for key, value in metrics.metrics.get_metrics().items()
        }
    )


@api.get("/metric/{name}")
def get_metric_by_id(name: str) -> JSONResponse:
    try:
        metric = metrics.metrics.get_metric(name)
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "Requested metric does not exist",
            },
        )
    return JSONResponse(content=metric.to_dict())


@api.delete("/metric/{id}")
async def delete_metric(id: str):
    try:
        metrics.metrics.delete_metric(id)
        return JSONResponse(status_code=200, content={"success": True})
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Requested metric does not exist"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@api.delete("/metric/{id}/value")
def delete_metric_value(id: str, labels: list[str] = Query(...)):
    try:
        metric = metrics.metrics.get_metric(id)
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Requested metric does not exist"},
        )
    if len(labels) != len(metric.labels):
        return JSONResponse(
            status_code=419,
            content={
                "success": False,
                "error": "Value label count does not match metric label count",
            },
        )
    for value in metric.values:
        if all([label in value.labels for label in labels]):
            metric.values.remove(value)
            break
    else:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "Label set found not be found for metric",
            },
        )
    return JSONResponse(content={"success": True, "name": id, "action": "deleted"})
