from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

from mocktrics_exporter import configuration, metrics, valueModels

api = FastAPI(redirect_slashes=False)


@api.get("/collect-interval")
async def get_collect_interval() -> JSONResponse:
    return JSONResponse(
        content={
            "seconds": metrics.metrics.get_collect_interval(),
            "editable": not configuration.configuration.collect_interval_is_read_only(),
        }
    )


@api.post("/collect-interval/{interval}")
async def set_collect_interval(interval: str) -> JSONResponse:
    editable = not configuration.configuration.collect_interval_is_read_only()
    if not editable:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": "Configured in config.yaml (read-only)",
            },
        )
    try:
        seconds = valueModels.parse_duration(int(interval) if interval.isdigit() else interval)
        if seconds < 1 or seconds > 60 * 60:
            raise ValueError("Interval must be between 1 and 300 seconds")
        metrics.metrics.set_collect_interval(seconds)
        return JSONResponse(content={"success": True})
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@api.post("/metric")
async def post_metric(metric: configuration.Metric) -> JSONResponse:

    try:

        values = []
        for value in metric.values:
            values.append(value)

        try:
            metrics.metrics.get_metric(metric.name)
            return JSONResponse(
                status_code=409,
                content={"success": False, "error": "Metric already exists"},
            )
        except KeyError:
            pass

        # Create metric
        name = metrics.metrics.add_metric(
            metrics.Metric(
                metric.name,
                values,
                metric.documentation,
                metric.labels,
                metric.unit,
            )
        )
        return JSONResponse(
            status_code=201,
            content={"success": True, "name": name, "action": "created"},
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@api.post("/metric/{id}/value")
def post_metric_value(id: str, value: valueModels.MetricValue) -> JSONResponse:

    try:
        metric = metrics.metrics.get_metric(id)
        metric.add_value(value)
    except metrics.Metric.ValueLabelsetSizeException:
        return JSONResponse(
            status_code=419,
            content={
                "success": False,
                "error": "Value label count does not match metric label count",
            },
        )
    except metrics.Metric.DuplicateValueLabelsetException:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": "Labelset already exists",
            },
        )
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "Requested metric does not exist",
            },
        )

    return JSONResponse(
        status_code=201,
        content={"success": True, "name": id, "action": "created"},
    )


@api.get("/metric/all")
def get_metric_all() -> JSONResponse:
    return JSONResponse(
        content={key: value.to_dict() for key, value in metrics.metrics.get_metrics().items()}
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
async def delete_metric(id: str, request: Request):
    try:
        metrics.metrics.delete_metric(id)
        return JSONResponse(status_code=200, content={"success": True})
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Requested metric does not exist"},
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@api.delete("/metric/{id}/value")
def delete_metric_value(id: str, request: Request, labels: list[str] = Query(...)):
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
