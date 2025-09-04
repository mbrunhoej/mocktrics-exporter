"""Compatibility shim for tests importing `metrics` as a top-level module.

Re-exports symbols from `mocktricks_exporter.metrics`.
"""

from mocktricks_exporter.metrics import *  # noqa: F401,F403
