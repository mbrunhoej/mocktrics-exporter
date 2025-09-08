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
    collect_interval: int = 10
    _collect_interval_read_only: bool = pydantic.PrivateAttr(default=False)

    disable_units: bool = False
    metrics: list[Metric] = pydantic.Field(default_factory=list)

    @pydantic.computed_field(return_type=bool)
    def collect_interval_is_read_only(self) -> bool:
        return self._collect_interval_read_only

    def set_collect_interval(self, interval: int) -> None:
        if self._collect_interval_read_only:
            raise TypeError("collect_interval is read-only")
        logging.debug(f"Setting collect_interval to {self.collect_interval}")
        self._collect_interval = interval

    def lock_collect_interval(self) -> None:
        logging.debug(f"Locking collect_interval to {self.collect_interval}")
        self._collect_interval_read_only = True


if arguments.config_file:
    with open(arguments.config_file, "r") as file:
        config = yaml.safe_load(file)
else:
    config = {}

configuration = Configuration.model_validate(config)
if config.get("collect_interval", None) is not None:
    configuration.lock_collect_interval()
