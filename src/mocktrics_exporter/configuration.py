import logging

import pydantic
import yaml

from mocktrics_exporter import valueModels
from mocktrics_exporter.arguments import arguments


class Metric(pydantic.BaseModel):
    name: str
    documentation: str
    unit: str = ""
    labels: list[str] = []
    values: list[valueModels.MetricValue]


class Configuration(pydantic.BaseModel):

    disable_units: bool = False
    metrics: list[Metric] = pydantic.Field(default_factory=list)


if arguments.config_file:
    with open(arguments.config_file, "r") as file:
        config = yaml.safe_load(file)
        logging.info(f"Config loaded: {config}")
else:
    config = {}

configuration = Configuration.model_validate(config)
