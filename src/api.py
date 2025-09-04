"""Compatibility shim for tests importing `api` as a top-level module.

Re-exports symbols from `mocktricks_exporter.api` so that
`import api` works during local testing without installation.
"""

from mocktricks_exporter.api import *  # noqa: F401,F403
