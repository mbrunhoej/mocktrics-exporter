import pydantic
import yaml

import valueModels


class Metric(pydantic.BaseModel):
    name: str
    documentation: str
    unit: str = ""
    labels: list[str] = []
    values: list[valueModels.MetricValue]


class Configuration(pydantic.BaseModel):
    collect_interval: int = 1
    disable_units: bool = False
    metrics: list[Metric]


with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

configuration = Configuration.model_validate(config)
