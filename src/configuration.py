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
    collect_interval: int = 10
    disable_units: bool = False
    metrics: list[Metric]


with open("config.yaml", "r") as file:
    raw_config = yaml.safe_load(file)

config_has_collect_interval = isinstance(raw_config, dict) and (
    "collect_interval" in raw_config
)

configuration = Configuration.model_validate(raw_config)
