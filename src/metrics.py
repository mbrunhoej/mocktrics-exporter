"""Compatibility shim for tests importing `metrics` as a top-level module.

Re-exports symbols from `mocktrics_exporter.metrics`.
"""

from mocktrics_exporter.metrics import *  # noqa: F401,F403
