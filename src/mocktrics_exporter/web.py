import os
from importlib.resources import files
from pathlib import Path

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Resolve static and template directories, preferring packaged resources
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
    user_static_dir = os.environ.get(
        "MOCKTRICS_EXPORTER_STATIC_DIR",
        str(Path.home() / ".local" / "mocktrics-exporter" / "static"),
    )
    try:
        os.makedirs(user_static_dir, exist_ok=True)
        static_dir = user_static_dir
    except Exception:
        static_dir = None


templates = Jinja2Templates(directory=templates_dir)


def mount_static(app) -> None:
    if static_dir:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
