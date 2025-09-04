# mocktrics-exporter

Generate realistic, configurable Prometheus metrics with a tiny UI and JSON API.

## What It Does

- Exposes Prometheus metrics on `:8000` (scrape target)
- Serves a minimal UI and API on `:8080` to create/manage metrics
- Supports value generators: `static`, `ramp`, `sine`, `square`, `gaussian`
- Supports labels per metric/value and an adjustable collect interval
- Loads optional `config.yaml` at startup for initial, read‑only metrics

## Install

```bash
pip install mocktrics-exporter
```

## Quick Start

```bash
mocktrics-exporter
```

- UI: http://localhost:8080
- Prometheus metrics: http://localhost:8000

Scrape example:

```yaml
scrape_configs:
  - job_name: mocktrics-exporter
    static_configs:
      - targets: ["localhost:8000"]
```

## Configure

Place a `config.yaml` in the working directory (optional). You can also pass `--config-file PATH` (optional). If neither is provided, the app uses built‑in defaults.

Minimal example:

```yaml
collect_interval: 5   # seconds (UI/API can override at runtime if omitted)
disable_units: false  # true to always omit Prom hints like _total, _bytes
metrics:
  - name: http_requests
    documentation: Example metric
    unit: requests
    labels: [method, code]
    values:
      - kind: static     # one labelset per value entry
        value: 42
        labels: [GET, "200"]
      - kind: ramp
        period: 60s
        peak: 100
        offset: 10
        invert: false
        labels: [POST, "500"]
```

Supported value kinds (fields):

- static: `value`
- ramp: `period`, `peak`, `offset` (optional), `invert` (optional)
- sine: `period`, `amplitude`, `offset` (optional)
- square: `period`, `magnitude`, `offset` (optional), `duty_cycle` (0–100), `invert` (optional)
- gaussian: `mean`, `sigma`

Numeric helpers: durations like `60s`, `5m`; sizes like `10k`, `2.5M`.

## UI How‑To

- Open `http://localhost:8080`
- Create metrics (name, labels, optional unit) and add values by kind
- Adjust collect interval (if not fixed by config)

## API How‑To (JSON)

Interactive docs (Swagger UI): http://localhost:8080/docs (also `/redoc`).

- Create metric:

```http
POST /metric
Content-Type: application/json

{
  "name": "jobs_in_queue",
  "documentation": "Example",
  "unit": "items",
  "labels": ["queue"],
  "values": [{"kind": "static", "labels": ["default"], "value": 5}]
}
```

- Add value to existing metric:

```http
POST /metric/jobs_in_queue/value
Content-Type: application/json

{"kind": "ramp", "labels": ["bulk"], "period": "60s", "peak": 50}
```

- List and read:
  - `GET /metric/all`
  - `GET /metric/{name}`
- Delete:
  - `DELETE /metric/{name}`
  - `DELETE /metric/{name}/value?labels=foo&labels=bar`
- Collect interval:
  - `GET /collect-interval` → `{seconds, editable}`
  - `POST /collect-interval` with `{"seconds": 5}` (if editable)

## CLI

```bash
mocktrics-exporter
```

Arguments:

- `-f, --config-file PATH` (optional): load a specific config file; otherwise `./config.yaml` is used if present, else defaults
- `-a, --api-port PORT` (optional): port for the UI and JSON API (default: 8080)
- `-m, --metrics-port PORT` (optional): port for the Prometheus metrics endpoint (default: 8000)

## Static Files

- The app mounts `/static` for UI assets.
- Wheels include an empty `static/` directory. If missing, the app creates and uses `~/.local/mocktrics-exporter/static` (override with `MOCKTRICS_EXPORTER_STATIC_DIR`).

## Notes

- Metrics are exported via `prometheus_client` Gauge and updated every `collect_interval` seconds.
- If `disable_units` is `true`, unit hints are omitted.
