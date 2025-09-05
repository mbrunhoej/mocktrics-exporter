from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import TypeAdapter

from . import configuration, metrics, valueModels
from .web import templates

api = FastAPI(redirect_slashes=False)


# JSON API for collect interval (runtime override)
@api.get("/collect-interval")
async def get_collect_interval(request: Request):
    seconds = metrics.metrics.get_collect_interval()
    editable = not configuration.config_has_collect_interval
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            "partials/collect_interval.html",
            {"request": request, "seconds": seconds, "editable": editable},
        )
    return JSONResponse(content={"seconds": seconds, "editable": editable})


@api.post("/collect-interval")
async def set_collect_interval(request: Request):
    editable = not configuration.config_has_collect_interval
    # Support form submissions from HTMX UI
    if request.headers.get("HX-Request") == "true":
        context = {"request": request, "editable": editable}
        if not editable:
            context.update(
                {
                    "seconds": metrics.metrics.get_collect_interval(),
                    "error": "Configured in config.yaml (read-only)",
                }
            )
            return templates.TemplateResponse(
                "partials/collect_interval.html", context, status_code=403
            )
        form = await request.form()
        try:
            seconds = int(str(form.get("seconds", "1")))
            if seconds < 1 or seconds > 300:
                raise ValueError("Interval must be between 1 and 300 seconds")
            metrics.metrics.set_collect_interval(seconds)
            context.update({"seconds": seconds, "ok": True})
            return templates.TemplateResponse("partials/collect_interval.html", context)
        except Exception as e:
            context.update(
                {"seconds": metrics.metrics.get_collect_interval(), "error": str(e)}
            )
            return templates.TemplateResponse(
                "partials/collect_interval.html", context, status_code=400
            )

    # JSON API path
    if not editable:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": "Configured in config.yaml (read-only)",
            },
        )
    try:
        payload = await request.json()
        seconds = int(payload.get("seconds", 1))
        if seconds < 1 or seconds > 300:
            raise ValueError("Interval must be between 1 and 300 seconds")
        metrics.metrics.set_collect_interval(seconds)
        return JSONResponse(content={"success": True, "seconds": seconds})
    except Exception as e:
        return JSONResponse(
            status_code=400, content={"success": False, "error": str(e)}
        )


@api.post("/metric")
async def post_metric(request: Request):
    # If HTMX form submission, build a Metric from form fields
    if request.headers.get("HX-Request") == "true":
        form = await request.form()
        try:
            name = str(form.get("name", "")).strip()
            documentation = str(form.get("documentation", "")).strip()
            unit = str(form.get("unit", "")).strip()
            labels_raw = str(form.get("labels", "")).strip()
            labels = [s.strip() for s in labels_raw.split(",") if s.strip()]
            if configuration.configuration.disable_units:
                unit = ""
            # Optional initial value
            values_list: list[valueModels.MetricValue] = []
            init_kind = str(form.get("init_kind", form.get("kind", ""))).strip()
            init_labels_raw = str(form.get("init_labels", "")).strip()
            init_labels = [s.strip() for s in init_labels_raw.split(",") if s.strip()]
            if init_kind:
                if labels and len(init_labels) != len(labels):
                    raise AttributeError("Label count mismatch")
                if init_kind == "static":
                    init_value_raw = str(form.get("init_value", "")).strip()
                    if init_value_raw == "":
                        raise ValueError("Initial value required for static kind")
                    values_list.append(
                        valueModels.StaticValue(
                            kind="static",
                            value=float(init_value_raw),
                            labels=init_labels,
                        )
                    )
                elif init_kind == "ramp":
                    values_list.append(
                        valueModels.RampValue(
                            kind="ramp",
                            period=form.get("init_period"),
                            peak=form.get("init_peak"),
                            offset=form.get("init_offset", 0),
                            invert=str(form.get("init_invert", "")).lower()
                            in {"1", "true", "on", "yes"},
                            labels=init_labels,
                        )
                    )
                elif init_kind == "sine":
                    values_list.append(
                        valueModels.SineValue(
                            kind="sine",
                            period=form.get("init_period"),
                            amplitude=form.get("init_amplitude"),
                            offset=form.get("init_offset", 0),
                            labels=init_labels,
                        )
                    )
                elif init_kind == "square":
                    values_list.append(
                        valueModels.SquareValue(
                            kind="square",
                            period=form.get("init_period"),
                            magnitude=form.get("init_magnitude"),
                            offset=form.get("init_offset", 0),
                            duty_cycle=form.get("init_duty_cycle", 50.0),
                            invert=str(form.get("init_invert", "")).lower()
                            in {"1", "true", "on", "yes"},
                            labels=init_labels,
                        )
                    )
                elif init_kind == "gaussian":
                    values_list.append(
                        valueModels.GaussianValue(
                            kind="gaussian",
                            mean=form.get("init_mean"),
                            sigma=form.get("init_sigma"),
                            labels=init_labels,
                        )
                    )
                else:
                    raise ValueError("Unsupported initial kind")

            # Now perform creation via same rules as JSON path
            try:
                metrics.metrics.get_metric(name)
                return templates.TemplateResponse(
                    "partials/flash_and_refresh.html",
                    {
                        "request": request,
                        "ok": False,
                        "message": f"Metric '{name}' already exists.",
                    },
                    status_code=409,
                )
            except KeyError:
                pass
            if len(labels) == 0:
                return templates.TemplateResponse(
                    "partials/flash_and_refresh.html",
                    {
                        "request": request,
                        "ok": False,
                        "message": "Metric must have atleast one label",
                    },
                    status_code=401,
                )
            metrics.metrics.add_metric(
                metrics.Metric(
                    name=name,
                    values=values_list,
                    documentation=documentation,
                    labels=labels,
                    unit=unit,
                    read_only=False,
                )
            )
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {
                    "request": request,
                    "ok": True,
                    "message": f"Metric '{name}' created.",
                },
                status_code=201,
            )
        except Exception as e:
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {"request": request, "ok": False, "message": str(e)},
                status_code=400,
            )

    # JSON API path (Swagger)
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
async def post_metric_value(request: Request, id: str):

    # HTMX form path
    if request.headers.get("HX-Request") == "true":
        form = await request.form()
        try:
            metric = metrics.metrics.get_metric(id)
        except KeyError:
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {
                    "request": request,
                    "ok": False,
                    "message": "Requested metric does not exist",
                },
                status_code=404,
            )
        if metric.read_only:
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {"request": request, "ok": False, "message": "Metric is read-only"},
                status_code=403,
            )

        kind = str(form.get("kind", "")).strip()
        labels_raw = str(form.get("labels", "")).strip()
        labels = [s.strip() for s in labels_raw.split(",") if s.strip()]
        try:
            if metric.labels and len(labels) != len(metric.labels):
                raise AttributeError
            if kind == "static":
                value_raw = str(form.get("value", "")).strip()
                if value_raw == "":
                    raise ValueError("Value required for static kind")
                v = valueModels.StaticValue(
                    kind="static", value=float(value_raw), labels=labels
                )
            elif kind == "ramp":
                v = valueModels.RampValue(
                    kind="ramp",
                    period=form.get("period"),
                    peak=form.get("peak"),
                    offset=form.get("offset", 0),
                    invert=str(form.get("invert", "")).lower()
                    in {"1", "true", "on", "yes"},
                    labels=labels,
                )
            elif kind == "sine":
                v = valueModels.SineValue(
                    kind="sine",
                    period=form.get("period"),
                    amplitude=form.get("amplitude"),
                    offset=form.get("offset", 0),
                    labels=labels,
                )
            elif kind == "square":
                v = valueModels.SquareValue(
                    kind="square",
                    period=form.get("period"),
                    magnitude=form.get("magnitude"),
                    offset=form.get("offset", 0),
                    duty_cycle=form.get("duty_cycle", 50.0),
                    invert=str(form.get("invert", "")).lower()
                    in {"1", "true", "on", "yes"},
                    labels=labels,
                )
            elif kind == "gaussian":
                v = valueModels.GaussianValue(
                    kind="gaussian",
                    mean=form.get("mean"),
                    sigma=form.get("sigma"),
                    labels=labels,
                )
            else:
                raise ValueError("Unsupported kind")
            metric.add_value(v)
        except AttributeError:
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {
                    "request": request,
                    "ok": False,
                    "message": "Value label count does not match metric label count",
                },
                status_code=419,
            )
        except IndexError:
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {"request": request, "ok": False, "message": "Labelset already exists"},
                status_code=409,
            )
        except Exception as e:
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {"request": request, "ok": False, "message": str(e)},
                status_code=400,
            )

        return templates.TemplateResponse(
            "partials/flash_and_refresh.html",
            {"request": request, "ok": True, "message": "Labelset added."},
            status_code=201,
        )

    # JSON API path
    try:
        payload = await request.json()
        value = TypeAdapter(valueModels.MetricValue).validate_python(payload)
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
async def delete_metric(id: str, request: Request):
    try:
        metrics.metrics.delete_metric(id)
        if request.headers.get("HX-Request") == "true":
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {"request": request, "ok": True, "message": ""},
            )
        return JSONResponse(status_code=200, content={"success": True})
    except KeyError:
        if request.headers.get("HX-Request") == "true":
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {
                    "request": request,
                    "ok": False,
                    "message": "Requested metric does not exist",
                },
            )
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Requested metric does not exist"},
        )
    except Exception as e:
        if request.headers.get("HX-Request") == "true":
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {"request": request, "ok": False, "message": str(e)},
            )
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@api.delete("/metric/{id}/value")
def delete_metric_value(id: str, request: Request, labels: list[str] = Query(...)):
    try:
        metric = metrics.metrics.get_metric(id)
    except KeyError:
        if request.headers.get("HX-Request") == "true":
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {
                    "request": request,
                    "ok": False,
                    "message": "Requested metric does not exist",
                },
            )
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Requested metric does not exist"},
        )
    if len(labels) != len(metric.labels):
        if request.headers.get("HX-Request") == "true":
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {
                    "request": request,
                    "ok": False,
                    "message": "Value label count does not match metric label count",
                },
            )
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
        if request.headers.get("HX-Request") == "true":
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {
                    "request": request,
                    "ok": False,
                    "message": "Label set could not be found for metric",
                },
            )
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "Label set found not be found for metric",
            },
        )
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            "partials/flash_and_refresh.html",
            {"request": request, "ok": True, "message": ""},
        )
    return JSONResponse(content={"success": True, "name": id, "action": "deleted"})
