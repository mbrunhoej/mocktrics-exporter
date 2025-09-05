import pydantic
import yaml

from . import valueModels
from .arguments import arguments


class Metric(pydantic.BaseModel):
    name: str
    documentation: str = ""
    unit: str = ""
    labels: list[str]
    values: list[valueModels.MetricValue] = []


class Configuration(pydantic.BaseModel):
    collect_interval: int = 10
    disable_units: bool = False
    metrics: list[Metric] = []


if arguments.config_file:
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
else:
    config = {}

config_has_collect_interval = isinstance(config, dict) and (
    "collect_interval" in config
)

configuration = Configuration.model_validate(config)
