# mocktrics-exporter

Small Prometheus exporter for generating configurable test metrics with a simple web UI.

## Install

- From PyPI (once released):
  - `pip install mocktrics-exporter`

## Usage

- Run the exporter:
  - `mocktrics-exporter`
- By default it:
  - Serves Prometheus metrics on `:8000`
  - Serves the API and UI on `:8080`

Place a `config.yaml` in your working directory to define initial metrics and settings (see `src/mocktrics_exporter/configuration.py` for schema). The UI lets you add and edit metrics at runtime when not marked as read-only by the config.

## Development

- Run locally with reload:
  - `uvicorn mocktrics_exporter.api:api --reload --port 8080`
- Prometheus client is started by the app on port `8000`.

## Release

To publish to PyPI:
- Build: `python -m build` (or `pipx run build`)
- Check: `twine check dist/*`
- Upload: `twine upload dist/*`
