import os
from importlib.resources import files
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, FastAPI, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.datastructures import FormData

from . import configuration, metrics, valueModels

api = FastAPI(redirect_slashes=False)
ui = APIRouter(include_in_schema=False)

# Static files and templates for simple UI
# Prefer packaged resources; fall back to local directories if present.
try:
    pkg_root = files(__package__)
    static_res = pkg_root.joinpath("static")
    templates_res = pkg_root.joinpath("templates")
    static_dir = (
        str(static_res) if getattr(static_res, "is_dir", lambda: False)() else None
    )
    templates_dir = (
        str(templates_res)
        if getattr(templates_res, "is_dir", lambda: False)()
        else "templates"
    )
except Exception:
    static_dir = "static" if os.path.isdir("static") else None
    templates_dir = "templates"

# If no packaged/static dir could be resolved, create a user-local one
if not static_dir:
    # Allow override via env; else default under ~/.local/mocktrics-exporter/static
    user_static_dir = os.environ.get(
        "MOCKTRICS_EXPORTER_STATIC_DIR",
        str(Path.home() / ".local" / "mocktrics-exporter" / "static"),
    )
    try:
        os.makedirs(user_static_dir, exist_ok=True)
        static_dir = user_static_dir
    except Exception:
        # If we cannot create it, leave static_dir as None and skip mounting
        static_dir = None

if static_dir:
    api.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# UI routes are added below; include router after definitions


# Small helpers to coerce form values into typed primitives for mypy
def _form_str(form: FormData, key: str, default: str = "") -> str:
    v = form.get(key)
    if isinstance(v, str):
        return v
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, UploadFile):
        # For text inputs we don't expect UploadFile; treat as missing
        return default
    return default


def _form_int(form: FormData, key: str, default: Optional[int] = None) -> int:
    s = _form_str(form, key, "")
    if s == "":
        return 0 if default is None else default
    return int(s)


def _form_float(form: FormData, key: str, default: Optional[float] = None) -> float:
    s = _form_str(form, key, "")
    if s == "":
        return 0.0 if default is None else default
    return float(s)


def _form_bool(form: FormData, key: str) -> bool:
    v = form.get(key)
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        return v.strip().lower() in {"1", "true", "on", "yes"}
    return False


@ui.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": configuration.configuration.model_dump(),
            "config_has_collect_interval": configuration.config_has_collect_interval,
        },
    )


@ui.get("/ui", response_class=HTMLResponse)
async def ui_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": configuration.configuration.model_dump(),
            "config_has_collect_interval": configuration.config_has_collect_interval,
        },
    )


@ui.get("/ui/metrics", response_class=HTMLResponse)
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


@ui.get("/ui/collect-interval", response_class=HTMLResponse)
async def ui_collect_interval(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "partials/collect_interval.html",
        {
            "request": request,
            "seconds": metrics.metrics.get_collect_interval(),
            "editable": not configuration.config_has_collect_interval,
        },
    )


@ui.post("/ui/collect-interval", response_class=HTMLResponse)
async def ui_collect_interval_post(request: Request) -> HTMLResponse:
    form: FormData = await request.form()
    editable = not configuration.config_has_collect_interval
    if editable:
        try:
            seconds = _form_int(form, "seconds", 1)
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


@ui.get("/ui/metric/new", response_class=HTMLResponse)
async def ui_metric_new(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "partials/new_metric_form.html",
        {
            "request": request,
            "disable_units": configuration.configuration.disable_units,
        },
    )


@ui.post("/ui/metric", response_class=HTMLResponse)
async def ui_metric_create(request: Request) -> HTMLResponse:
    form: FormData = await request.form()
    name = _form_str(form, "name").strip()
    documentation = _form_str(form, "documentation").strip()
    unit = _form_str(form, "unit").strip()
    labels_raw = _form_str(form, "labels").strip()
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
    init_kind = (_form_str(form, "init_kind") or _form_str(form, "kind")).strip()
    init_labels_raw = _form_str(form, "init_labels").strip()
    init_labels = [s.strip() for s in init_labels_raw.split(",") if s.strip()]
    if init_kind:
        try:
            if labels and len(init_labels) != len(labels):
                raise AttributeError("Label count mismatch")
            if init_kind == "static":
                init_value_raw = _form_str(form, "init_value").strip()
                if init_value_raw == "":
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
                        period=_form_int(form, "init_period"),
                        peak=_form_int(form, "init_peak"),
                        offset=_form_int(form, "init_offset", 0),
                        invert=_form_bool(form, "init_invert"),
                        labels=init_labels,
                    )
                )
            elif init_kind == "sine":
                values_list.append(
                    valueModels.SineValue(
                        kind="sine",
                        period=_form_int(form, "init_period"),
                        amplitude=_form_int(form, "init_amplitude"),
                        offset=_form_int(form, "init_offset", 0),
                        labels=init_labels,
                    )
                )
            elif init_kind == "square":
                values_list.append(
                    valueModels.SquareValue(
                        kind="square",
                        period=_form_int(form, "init_period"),
                        magnitude=_form_int(form, "init_magnitude"),
                        offset=_form_int(form, "init_offset", 0),
                        duty_cycle=_form_float(form, "init_duty_cycle", 50.0),
                        invert=_form_bool(form, "init_invert"),
                        labels=init_labels,
                    )
                )
            elif init_kind == "gaussian":
                values_list.append(
                    valueModels.GaussianValue(
                        kind="gaussian",
                        mean=_form_int(form, "init_mean"),
                        sigma=_form_float(form, "init_sigma"),
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


@ui.get("/ui/metric/{id}/add-value", response_class=HTMLResponse)
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


@ui.post("/ui/metric/{id}/add-value", response_class=HTMLResponse)
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

    kind = _form_str(form, "kind").strip()
    labels_raw = _form_str(form, "labels").strip()
    labels = [s.strip() for s in labels_raw.split(",") if s.strip()]

    try:
        if metric.labels and len(labels) != len(metric.labels):
            raise AttributeError("Label count mismatch")
        v: valueModels.MetricValue
        if kind == "static":
            value_raw = _form_str(form, "value").strip()
            if value_raw == "":
                raise ValueError("Value required for static kind")
            v = valueModels.StaticValue(
                kind="static", value=float(value_raw), labels=labels
            )
        elif kind == "ramp":
            v = valueModels.RampValue(
                kind="ramp",
                period=_form_int(form, "period"),
                peak=_form_int(form, "peak"),
                offset=_form_int(form, "offset", 0),
                invert=_form_bool(form, "invert"),
                labels=labels,
            )
        elif kind == "sine":
            v = valueModels.SineValue(
                kind="sine",
                period=_form_int(form, "period"),
                amplitude=_form_int(form, "amplitude"),
                offset=_form_int(form, "offset", 0),
                labels=labels,
            )
        elif kind == "square":
            v = valueModels.SquareValue(
                kind="square",
                period=_form_int(form, "period"),
                magnitude=_form_int(form, "magnitude"),
                offset=_form_int(form, "offset", 0),
                duty_cycle=_form_float(form, "duty_cycle", 50.0),
                invert=_form_bool(form, "invert"),
                labels=labels,
            )
        elif kind == "gaussian":
            v = valueModels.GaussianValue(
                kind="gaussian",
                mean=_form_int(form, "mean"),
                sigma=_form_float(form, "sigma"),
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


@ui.get("/ui/metric/{id}/value", response_class=HTMLResponse)
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


@ui.get("/ui/value-fields", response_class=HTMLResponse)
async def ui_value_fields(
    request: Request, kind: str = "", prefix: str = ""
) -> HTMLResponse:
    # Render inputs for the chosen kind; prefix allows reuse for init_ and non-init forms
    return templates.TemplateResponse(
        "partials/value_fields.html",
        {"request": request, "kind": kind, "prefix": prefix},
    )


# Mount the UI router (excluded from OpenAPI/Swagger)
api.include_router(ui)


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
