from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.datastructures import FormData

import configuration
import metrics
import valueModels

api = FastAPI(redirect_slashes=False)

# Static files and templates for simple UI
api.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@api.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": configuration.configuration.model_dump(),
            "config_has_collect_interval": configuration.config_has_collect_interval,
        },
    )


@api.get("/ui", response_class=HTMLResponse)
async def ui(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": configuration.configuration.model_dump(),
            "config_has_collect_interval": configuration.config_has_collect_interval,
        },
    )


@api.get("/ui/metrics", response_class=HTMLResponse)
async def ui_metrics(request: Request) -> HTMLResponse:
    # Prepare a simple list for rendering
    metric_items = []
    for name, metric in metrics.metrics.get_metrics().items():
        data = metric.to_dict()
        data.update({"id": name})
        metric_items.append(data)

    return templates.TemplateResponse(
        "partials/metrics.html",
        {"request": request, "metrics": metric_items},
    )


@api.get("/ui/collect-interval", response_class=HTMLResponse)
async def ui_collect_interval(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "partials/collect_interval.html",
        {
            "request": request,
            "seconds": metrics.metrics.get_collect_interval(),
            "editable": not configuration.config_has_collect_interval,
        },
    )


@api.post("/ui/collect-interval", response_class=HTMLResponse)
async def ui_collect_interval_post(request: Request) -> HTMLResponse:
    form: FormData = await request.form()
    editable = not configuration.config_has_collect_interval
    if editable:
        try:
            seconds = int(form.get("seconds") or 1)
            if seconds < 1 or seconds > 300:
                raise ValueError("Interval must be between 1 and 300 seconds")
            metrics.metrics.set_collect_interval(seconds)
        except Exception as e:
            return templates.TemplateResponse(
                "partials/collect_interval.html",
                {
                    "request": request,
                    "seconds": metrics.metrics.get_collect_interval(),
                    "editable": editable,
                    "error": str(e),
                },
            )

    return templates.TemplateResponse(
        "partials/collect_interval.html",
        {
            "request": request,
            "seconds": metrics.metrics.get_collect_interval(),
            "editable": editable,
            "ok": True,
        },
    )


# JSON API for collect interval (runtime override)
@api.get("/collect-interval")
async def get_collect_interval() -> JSONResponse:
    return JSONResponse(
        content={
            "seconds": metrics.metrics.get_collect_interval(),
            "editable": not configuration.config_has_collect_interval,
        }
    )


@api.post("/collect-interval")
async def set_collect_interval(payload: dict) -> JSONResponse:
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
        seconds = int(payload.get("seconds", 1))
        if seconds < 1 or seconds > 300:
            raise ValueError("Interval must be between 1 and 300 seconds")
        metrics.metrics.set_collect_interval(seconds)
        return JSONResponse(content={"success": True, "seconds": seconds})
    except Exception as e:
        return JSONResponse(
            status_code=400, content={"success": False, "error": str(e)}
        )


@api.get("/ui/metric/new", response_class=HTMLResponse)
async def ui_metric_new(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "partials/new_metric_form.html",
        {
            "request": request,
            "disable_units": configuration.configuration.disable_units,
        },
    )


@api.post("/ui/metric", response_class=HTMLResponse)
async def ui_metric_create(request: Request) -> HTMLResponse:
    form: FormData = await request.form()
    name = (form.get("name") or "").strip()
    documentation = (form.get("documentation") or "").strip()
    unit = (form.get("unit") or "").strip()
    labels_raw = (form.get("labels") or "").strip()
    labels = [s.strip() for s in labels_raw.split(",") if s.strip()]

    # Respect disable_units setting
    if configuration.configuration.disable_units:
        unit = ""

    # Validate name
    if not name:
        return templates.TemplateResponse(
            "partials/flash_and_refresh.html",
            {"request": request, "ok": False, "message": "Name is required."},
        )

    # Check duplicate
    if name in metrics.metrics.get_metrics().keys():
        return templates.TemplateResponse(
            "partials/flash_and_refresh.html",
            {
                "request": request,
                "ok": False,
                "message": f"Metric '{name}' already exists.",
            },
        )

    # Optional initial value (supports multiple kinds)
    values_list: list[valueModels.MetricValue] = []
    init_kind = (form.get("init_kind") or form.get("kind") or "").strip()
    init_labels_raw = (form.get("init_labels") or "").strip()
    init_labels = [s.strip() for s in init_labels_raw.split(",") if s.strip()]
    if init_kind:
        try:
            if labels and len(init_labels) != len(labels):
                raise AttributeError("Label count mismatch")
            if init_kind == "static":
                init_value_raw = form.get("init_value")
                if init_value_raw is None or str(init_value_raw).strip() == "":
                    raise ValueError("Initial value required for static kind")
                values_list.append(
                    valueModels.StaticValue(
                        kind="static", value=float(init_value_raw), labels=init_labels
                    )
                )
            elif init_kind == "ramp":
                values_list.append(
                    valueModels.RampValue(
                        kind="ramp",
                        period=form.get("init_period"),
                        peak=form.get("init_peak"),
                        offset=form.get("init_offset") or 0,
                        invert=bool(form.get("init_invert")),
                        labels=init_labels,
                    )
                )
            elif init_kind == "sine":
                values_list.append(
                    valueModels.SineValue(
                        kind="sine",
                        period=form.get("init_period"),
                        amplitude=form.get("init_amplitude"),
                        offset=form.get("init_offset") or 0,
                        labels=init_labels,
                    )
                )
            elif init_kind == "square":
                values_list.append(
                    valueModels.SquareValue(
                        kind="square",
                        period=form.get("init_period"),
                        magnitude=form.get("init_magnitude"),
                        offset=form.get("init_offset") or 0,
                        duty_cycle=float(form.get("init_duty_cycle") or 50),
                        invert=bool(form.get("init_invert")),
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
        except Exception as e:
            return templates.TemplateResponse(
                "partials/flash_and_refresh.html",
                {"request": request, "ok": False, "message": str(e)},
            )

    # Create metric (not read_only)
    try:
        metrics.metrics.add_metric(
            metrics.Metric(
                name,
                values_list,
                documentation,
                labels,
                unit,
                read_only=False,
            )
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/flash_and_refresh.html",
            {"request": request, "ok": False, "message": str(e)},
        )

    return templates.TemplateResponse(
        "partials/flash_and_refresh.html",
        {
            "request": request,
            "ok": True,
            "message": f"Metric '{name}' created.",
        },
    )


@api.get("/ui/metric/{id}/add-value", response_class=HTMLResponse)
async def ui_metric_add_value_form(id: str, request: Request) -> HTMLResponse:
    try:
        metric = metrics.metrics.get_metric(id)
    except KeyError:
        return HTMLResponse("Metric not found", status_code=404)
    if metric.read_only:
        return HTMLResponse("Metric is read-only", status_code=403)
    return templates.TemplateResponse(
        "partials/add_value_form.html",
        {
            "request": request,
            "metric": metric.to_dict() | {"id": id},
        },
    )


@api.post("/ui/metric/{id}/add-value", response_class=HTMLResponse)
async def ui_metric_add_value(id: str, request: Request) -> HTMLResponse:
    form: FormData = await request.form()
    try:
        metric = metrics.metrics.get_metric(id)
    except KeyError:
        return HTMLResponse("Metric not found", status_code=404)
    if metric.read_only:
        return templates.TemplateResponse(
            "partials/flash_and_refresh.html",
            {"request": request, "ok": False, "message": "Metric is read-only"},
        )

    kind = (form.get("kind") or "").strip()
    labels_raw = (form.get("labels") or "").strip()
    labels = [s.strip() for s in labels_raw.split(",") if s.strip()]

    try:
        if metric.labels and len(labels) != len(metric.labels):
            raise AttributeError("Label count mismatch")
        if kind == "static":
            value_raw = form.get("value")
            if value_raw is None or str(value_raw).strip() == "":
                raise ValueError("Value required for static kind")
            v = valueModels.StaticValue(
                kind="static", value=float(value_raw), labels=labels
            )
        elif kind == "ramp":
            v = valueModels.RampValue(
                kind="ramp",
                period=form.get("period"),
                peak=form.get("peak"),
                offset=form.get("offset") or 0,
                invert=bool(form.get("invert")),
                labels=labels,
            )
        elif kind == "sine":
            v = valueModels.SineValue(
                kind="sine",
                period=form.get("period"),
                amplitude=form.get("amplitude"),
                offset=form.get("offset") or 0,
                labels=labels,
            )
        elif kind == "square":
            v = valueModels.SquareValue(
                kind="square",
                period=form.get("period"),
                magnitude=form.get("magnitude"),
                offset=form.get("offset") or 0,
                duty_cycle=float(form.get("duty_cycle") or 50),
                invert=bool(form.get("invert")),
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
    except Exception as e:
        return templates.TemplateResponse(
            "partials/flash_and_refresh.html",
            {"request": request, "ok": False, "message": str(e)},
        )

    return templates.TemplateResponse(
        "partials/flash_and_refresh.html",
        {"request": request, "ok": True, "message": "Labelset added."},
    )


@api.get("/ui/metric/{id}/value", response_class=HTMLResponse)
async def ui_metric_value(
    id: str, request: Request, labels: list[str] = Query(...)
) -> HTMLResponse:
    try:
        metric = metrics.metrics.get_metric(id)
    except KeyError:
        return HTMLResponse("Metric not found", status_code=404)

    # Find value by matching labels (order-insensitive subset match, consistent with add/delete)
    value_obj = None
    for v in metric.values:
        if all(label in v.labels for label in labels):
            value_obj = v
            break
    if value_obj is None:
        return HTMLResponse("Labelset not found", status_code=404)

    return templates.TemplateResponse(
        "partials/value_props.html",
        {
            "request": request,
            "metric": metric.to_dict() | {"id": id},
            "value": value_obj.model_dump(),
        },
    )


@api.get("/ui/value-fields", response_class=HTMLResponse)
async def ui_value_fields(
    request: Request, kind: str = "", prefix: str = ""
) -> HTMLResponse:
    # Render inputs for the chosen kind; prefix allows reuse for init_ and non-init forms
    return templates.TemplateResponse(
        "partials/value_fields.html",
        {"request": request, "kind": kind, "prefix": prefix},
    )


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
def post_metric_value(id: str, value: valueModels.MetricValue) -> JSONResponse:

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
