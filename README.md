# mocktrics-exporter

Small, configurable Prometheus exporter for generating test metrics. It exposes:
- a Prometheus metrics endpoint for scraping
- a small FastAPI HTTP API for defining/updating metrics at runtime

Works great for demos, integration tests, and performance scenarios where you need predictable metrics behavior (static, ramp, square, sine, gaussian) with labels.

Note: The Python package is named `mocktrics_exporter` (underscore in the import path).

## Install

- From PyPI:
  - `pip install mocktrics-exporter`
- From source (editable):
  - `pip install -e .`

## Quick Start

- Run the exporter:
  - `mocktrics-exporter -f config.yaml`
- Alternatively from source:
  - `python -m mocktrics_exporter.main -f config.yaml`
- Defaults:
  - Metrics served on `:8000`
  - HTTP API served on `:8080`

Example Prometheus scrape config:
-
  - job_name: `mocktrics`
  - static_configs: `['localhost:8000']`

## CLI Options

- `-f, --config-file` path to YAML configuration file
- `-a, --api-port` API port (default `8080`)
- `-m, --metrics-port` Prometheus metrics port (default `8000`)

Options can also be provided via environment or process managers as needed.

## Configuration

- File: `config.yaml` (optional). If provided, metrics are preloaded at startup.
- Schema overview: each metric defines a `name`, `documentation`, optional `unit`, a list of `labels`, and a list of `values`. Values use a `kind` discriminator and fields specific to the chosen kind (see Supported Value Models below).

Example:

```
disable_units: true

metrics:
  - name: combined
    documentation: Mock metric for all types
    labels: [type]
    values:
      - kind: static
        value: 100
        labels: [static]
      - kind: ramp
        period: 2m
        peak: 100
        invert: false
        labels: [ramp]
      - kind: square
        period: 2m
        magnitude: 100
        duty_cycle: 50
        labels: [square]
      - kind: sine
        period: 2m
        amplitude: 50
        offset: 50
        labels: [sine]
```

### Supported Value Models

- `static`: constant numeric value
- `ramp`: linear ramp up to `peak` over `period`, optional `invert`, `offset`
- `square`: square wave with `period`, `magnitude`, `duty_cycle` (0–100), optional `invert`, `offset`
- `sine`: sine wave with `period`, `amplitude`, optional `offset`
- `gaussian`: random gaussian with `mean`, `sigma`

Helpers:
- Duration strings: `1s`, `2m`, `3h`, `1d`
- Size strings: `2u`, `2m`, `2k`, `2M`, `2G`

## HTTP API

Base URL is the API port (default `http://localhost:8080`).
Interactive API docs are available at `http://localhost:8080/docs` (Swagger UI).

Example requests:

```
# Create a metric
curl -X POST localhost:8080/metric \
  -H 'content-type: application/json' \
  -d '{
    "name": "http_requests",
    "documentation": "Demo metric",
    "unit": "",
    "labels": ["method"],
    "values": [{"kind": "static", "labels": ["GET"], "value": 42}]
  }'

# Add a value
curl -X POST localhost:8080/metric/http_requests/value \
  -H 'content-type: application/json' \
  -d '{"kind": "ramp", "labels": ["POST"], "period": "2m", "peak": 100}'

# List metrics
curl localhost:8080/metric/all

# Delete a value
curl -X DELETE 'localhost:8080/metric/http_requests/value?labels=GET'

# Delete metric
curl -X DELETE localhost:8080/metric/http_requests
```

## Prometheus Metrics

- Metrics endpoint runs on the metrics port (default `8000`).
- Each metric is exported as a Gauge with labels as defined.
- Units in the metric name suffix can be disabled with `disable_units: true` in config.

## Development

- Run tests: `pytest -q` (includes fast API and unit tests)
- Run API with autoreload for local dev: `uvicorn mocktrics_exporter.api:api --reload --port 8080`
- Code style: Black, isort, autoflake via pre-commit hooks
- Python: `>=3.9`

## License

Apache 2.0. See `LICENSE`.
