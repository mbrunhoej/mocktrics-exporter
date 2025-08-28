from typing import Literal

import pydantic
import yaml
import re


def parse_duration(duration: str | int):
    if isinstance(duration, int):
        return duration
    match = re.fullmatch(r"(\d+)([smhd])", duration.strip().lower())
    if not match:
        raise ValueError(f"Invalid duration: {duration}")
    num, unit = match.groups()
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return int(num) * multipliers[unit]


def parse_size(size: str | int):
    if isinstance(size, int):
        return size
    match = re.fullmatch(r"(\d+)([umMkG])", size.strip().lower())
    if not match:
        raise ValueError(f"Invalid duration: {size}")
    num, unit = match.groups()
    multipliers = {"u": 1e-6, "m": 1e-3, "k": 1e3, "M": 1e6, "G": 1e9}
    return int(num) * multipliers[unit]


class StaticValue(pydantic.BaseModel):
    kind: Literal["static"]
    value: float

    @pydantic.field_validator("value", mode="before")
    def convert_value(cls, v):
        return parse_size(v)


class RampValue(pydantic.BaseModel):
    kind: Literal["ramp"]
    period: int
    peak: int
    offset: int = 0
    invert: bool = False

    @pydantic.field_validator("period", mode="before")
    def convert_period(cls, v):
        return parse_duration(v)

    @pydantic.field_validator("peak", mode="before")
    def convert_peak(cls, v):
        return parse_size(v)

    @pydantic.field_validator("offset", mode="before")
    def convert_offset(cls, v):
        return parse_size(v)


class SquareValue(pydantic.BaseModel):
    kind: Literal["square"]
    period: int
    magnitude: int
    offset: int = 0
    duty_cycle: int
    invert: bool = False

    @pydantic.field_validator("period", mode="before")
    def convert_period(cls, v):
        return parse_duration(v)

    @pydantic.field_validator("magnitude", mode="before")
    def convert_magnitude(cls, v):
        return parse_size(v)

    @pydantic.field_validator("offset", mode="before")
    def convert_offset(cls, v):
        return parse_size(v)

    @pydantic.field_validator("duty_cycle", mode="before")
    def validate_duty_cycle(cls, v):
        if v < 0 or v > 100:
            raise Exception("Duty cycle must be between 0 and 100")
        return v


class SineValue(pydantic.BaseModel):
    kind: Literal["sine"]
    period: int
    amplitude: int
    offset: int = 0

    @pydantic.field_validator("period", mode="before")
    def convert_period(cls, v):
        return parse_duration(v)

    @pydantic.field_validator("amplitude", mode="before")
    def convert_amplitude(cls, v):
        return parse_size(v)

    @pydantic.field_validator("offset", mode="before")
    def convert_offset(cls, v):
        return parse_size(v)


class GaussianValue(pydantic.BaseModel):
    kind: Literal["gaussian"]
    mean: int
    sigma: float


class Metric(pydantic.BaseModel):
    name: str
    documentation: str
    unit: str = ""
    labels: dict[str, str] = {}
    value: StaticValue | RampValue | SquareValue | SineValue | GaussianValue


class Configuration(pydantic.BaseModel):
    collect_interval: int = 1
    disable_units: bool = False
    metrics: list[Metric]


with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

configuration = Configuration.model_validate(config)
