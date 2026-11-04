"""Strict inputs for deterministic catalogue queries."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NonNegative = Annotated[Decimal, Field(ge=0, le=Decimal("1e12"), allow_inf_nan=False)]


def validate_part_number(value: str) -> str:
    import re

    value = value.strip()
    if not re.fullmatch(r"[A-Z0-9]{6}-[A-Z0-9]{8}/A", value):
        raise ValueError("Use the complete Base Part Number, including /A")
    return value


class NumericBound(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: NonNegative
    op: Literal["gt", "gte", "lt", "lte"]

    @field_validator("value")
    @classmethod
    def representable(cls, value):
        if Decimal(str(float(value))) != value:
            raise ValueError("Bound precision cannot be represented losslessly")
        return value


def bounds(value):
    return value if isinstance(value, list) else [value]


def bound_value(value):
    if isinstance(value, list):
        return bound_value(value[0])
    return value.value if isinstance(value, NumericBound) else value.get("value") if isinstance(value, dict) else value


def bound_operator(value, default):
    if isinstance(value, list):
        return bound_operator(value[0], default)
    return value.op if isinstance(value, NumericBound) else value.get("op", default) if isinstance(value, dict) else default


SortKey = Literal["fastest", "lowest_power", "highest_torque", "lowest_current"]


class SearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enclosure: Literal["weatherproof", "explosionproof"] | None = None
    supply_voltage_v: (
        Annotated[Decimal, Field(gt=0, le=Decimal("1e12"), allow_inf_nan=False)] | None
    ) = None
    supply_current: Literal["AC", "DC", "AC/DC"] | None = None
    phase_count: Literal[1, 3] | None = None
    service: Literal["on_off", "modulating"] | None = Field(default=None, description="On/Off means fully open or closed. Modulating means regulate or throttle flow, hold an intermediate opening, position anywhere between 0 and 90 degrees, or stop at any position; Spanish regule/regular caudal is Modulating.")
    frequency_hz: Literal[50, 60] | None = None
    min_torque_nm: NonNegative | NumericBound | Annotated[list[NumericBound], Field(min_length=2, max_length=2)] | None = None
    # Published in-lb column, compared directly: no unit conversion by model or code.
    min_torque_in_lb: NonNegative | NumericBound | Annotated[list[NumericBound], Field(min_length=2, max_length=2)] | None = None
    min_duty_s4_percent: (
        Annotated[Decimal, Field(ge=0, le=100, allow_inf_nan=False)] | NumericBound | Annotated[list[NumericBound], Field(min_length=2, max_length=2)] | None
    ) = None
    min_cycles_per_hour: Annotated[int, Field(ge=0, le=2147483647)] | NumericBound | Annotated[list[NumericBound], Field(min_length=2, max_length=2)] | None = None
    min_starts_per_hour: Annotated[int, Field(ge=0, le=2147483647)] | NumericBound | Annotated[list[NumericBound], Field(min_length=2, max_length=2)] | None = None
    max_operating_time_s: NonNegative | NumericBound | Annotated[list[NumericBound], Field(min_length=2, max_length=2)] | None = None
    max_fla_a: NonNegative | NumericBound | Annotated[list[NumericBound], Field(min_length=2, max_length=2)] | None = None
    max_lra_a: NonNegative | NumericBound | Annotated[list[NumericBound], Field(min_length=2, max_length=2)] | None = None
    max_motor_power_w: NonNegative | NumericBound | Annotated[list[NumericBound], Field(min_length=2, max_length=2)] | None = None
    sort_by: Annotated[list[SortKey], Field(max_length=4)] = []
    csa_required: bool = False
    limit: Annotated[int, Field(ge=1, le=100)] = 20
    offset: Annotated[int, Field(ge=0, le=1000000)] = 0

    @field_validator(
        "phase_count",
        "frequency_hz",
        "min_cycles_per_hour",
        "min_starts_per_hour",
        "limit",
        "offset",
        mode="before",
    )
    @classmethod
    def no_boolean_dimensions(cls, value):
        if isinstance(value, bool):
            raise ValueError("Boolean is not a phase or frequency")
        return value

    @model_validator(mode="after")
    def compatible(self):
        for value in self.model_dump().values():
            if isinstance(value, Decimal) and Decimal(str(float(value))) != value:
                raise ValueError(
                    "Filter precision cannot be represented losslessly in the response"
                )
        for name, value in self.__dict__.items():
            if isinstance(value, list) and value and isinstance(value[0], NumericBound):
                lower = [v for v in value if v.op in ('gt', 'gte')]
                upper = [v for v in value if v.op in ('lt', 'lte')]
                if len(lower) != 1 or len(upper) != 1 or lower[0].value > upper[0].value:
                    raise ValueError('A range requires one lower and one upper bound')
            if name in ('min_cycles_per_hour', 'min_starts_per_hour', 'min_duty_s4_percent'):
                for item in bounds(value):
                    number = bound_value(item)
                    if number is not None and (number > (100 if name == 'min_duty_s4_percent' else 2147483647)
                                              or (name != 'min_duty_s4_percent' and number != int(number))):
                        raise ValueError('Invalid percentage or integer rate bound')
        if len(set(self.sort_by)) != len(self.sort_by):
            raise ValueError("Duplicate sort key")
        if self.supply_current == "DC" and (self.frequency_hz or self.phase_count):
            raise ValueError("DC cannot be filtered by mains frequency or phase count")
        if self.service == "on_off" and self.min_starts_per_hour is not None:
            raise ValueError("Starts/hour belongs to modulating service")
        if self.service == "modulating" and self.min_cycles_per_hour is not None:
            raise ValueError("Cycles/hour belongs to on/off service")
        if (
            self.min_cycles_per_hour is not None
            and self.min_starts_per_hour is not None
        ):
            raise ValueError("Specify one service, not both rate constraints")
        return self
