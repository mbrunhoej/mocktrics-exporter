import math
import random
import re
import time
from typing import Annotated, Literal, Union

import pydantic


def parse_duration(duration: str | int):
    if isinstance(duration, int):
        if duration < 1:
            raise ValueError("Duration must be atlest 1")
        return duration
    match = re.fullmatch(r"(\d+)([smhd])", duration.strip().lower())
    if not match:
        raise ValueError(f"Invalid duration: {duration}")
    num, unit = match.groups()
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return int(num) * multipliers[unit]


def parse_size(size: str | int | float):
    if isinstance(size, (int, float)):
        return float(size)
    s = str(size).strip()
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([umkMG])", s)
    if not match:
        raise ValueError(f"Invalid size: {size}")
    num, unit = match.groups()
    multipliers = {
        "u": 1e-6,
        "m": 1e-3,
        "k": 1e3,
        "M": 1e6,
        "G": 1e9,
    }
    return float(num) * multipliers[unit]


class StaticValue(pydantic.BaseModel):
    value: float
    labels: list[str]
    kind: Literal["static"] = "static"

    @pydantic.field_validator("value", mode="before")
    def convert_value(cls, v):
        return parse_size(v)

    def get_value(self) -> float:
        return self.value


class RampValue(pydantic.BaseModel):
    kind: Literal["ramp"] = "ramp"
    period: int
    peak: int
    offset: int = 0
    invert: bool = False
    labels: list[str]
    _start_time: float = pydantic.PrivateAttr(default_factory=lambda: time.monotonic())

    @pydantic.field_validator("period", mode="before")
    def convert_period(cls, v):
        return parse_duration(v)

    @pydantic.field_validator("peak", mode="before")
    def convert_peak(cls, v):
        return int(parse_size(v))

    @pydantic.field_validator("offset", mode="before")
    def convert_offset(cls, v):
        return int(parse_size(v))

    def get_value(self) -> float:
        delta = time.monotonic() - self._start_time
        progress = (delta % self.period) / self.period
        value = progress * self.peak
        if self.invert:
            value = self.peak - value

        return value + self.offset


class SquareValue(pydantic.BaseModel):
    kind: Literal["square"] = "square"
    period: int
    magnitude: int
    offset: int = 0
    duty_cycle: float
    invert: bool = False
    labels: list[str]
    _start_time: float = pydantic.PrivateAttr(default_factory=lambda: time.monotonic())

    @pydantic.field_validator("period", mode="before")
    def convert_period(cls, v):
        return int(parse_duration(v))

    @pydantic.field_validator("magnitude", mode="before")
    def convert_magnitude(cls, v):
        return int(parse_size(v))

    @pydantic.field_validator("offset", mode="before")
    def convert_offset(cls, v):
        return int(parse_size(v))

    @pydantic.field_validator("duty_cycle", mode="before")
    def validate_duty_cycle(cls, v):
        if v < 0.0 or v > 100.0:
            raise ValueError("Duty cycle must be between 0 and 100")
        return float(v) / 100

    def get_value(self) -> float:
        delta = time.monotonic() - self._start_time
        progress = (delta % self.period) / self.period
        if not self.invert:
            value = self.magnitude if progress <= self.duty_cycle else 0
        else:
            value = 0 if progress < self.duty_cycle else self.magnitude

        return value + self.offset


class SineValue(pydantic.BaseModel):
    kind: Literal["sine"] = "sine"
    period: int
    amplitude: int
    offset: int = 0
    labels: list[str]
    __start_time: float = pydantic.PrivateAttr(default_factory=lambda: time.monotonic())

    @pydantic.field_validator("period", mode="before")
    def convert_period(cls, v):
        return parse_duration(v)

    @pydantic.field_validator("amplitude", mode="before")
    def convert_amplitude(cls, v):
        return parse_size(v)

    @pydantic.field_validator("offset", mode="before")
    def convert_offset(cls, v):
        return parse_size(v)

    def get_value(self) -> float:
        delta = time.monotonic() - self.__start_time
        progress = (delta % self.period) / self.period

        value = math.sin(progress * math.pi * 2) * self.amplitude

        return value + self.offset


class GaussianValue(pydantic.BaseModel):
    kind: Literal["gaussian"] = "gaussian"
    mean: int
    sigma: float
    labels: list[str]

    def get_value(self) -> float:
        return random.gauss(self.mean, self.sigma)


MetricValue = Annotated[
    Union[RampValue, SineValue, SquareValue, StaticValue, GaussianValue],
    pydantic.Field(discriminator="kind"),
]
