"""Compatibility shim for tests importing `ui` as a top-level module.

Re-exports symbols from `mocktrics_exporter.api` so that
`import api` works during local testing without installation.
"""

from mocktrics_exporter.ui import *  # noqa: F401,F403
