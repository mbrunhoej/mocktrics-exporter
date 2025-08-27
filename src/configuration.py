from typing import Literal

import pydantic
import yaml


class StaticValue(pydantic.BaseModel):
    kind: Literal["static"]
    value: float


class RampValue(pydantic.BaseModel):
    kind: Literal["ramp"]
    increments_per_seconds: int
    limit: int
    offset: int


class Metric(pydantic.BaseModel):
    name: str
    documentation: str
    unit: str
    labels: dict[str, str] = {}
    value: StaticValue | RampValue


class Configuration(pydantic.BaseModel):
    collect_interval: int = 60
    disable_units: bool = False
    metrics: list[Metric]


with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

configuration = Configuration.model_validate(config)
