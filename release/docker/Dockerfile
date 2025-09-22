FROM python:3.13-slim

ARG VERSION=0.0.0
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION}

WORKDIR /app

COPY pyproject.toml LICENSE ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

EXPOSE 8000 8080

CMD ["mocktrics-exporter"]
