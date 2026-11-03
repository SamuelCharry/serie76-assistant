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


class SearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enclosure: Literal["weatherproof", "explosionproof"] | None = None
    supply_voltage_v: (
        Annotated[Decimal, Field(gt=0, le=Decimal("1e12"), allow_inf_nan=False)] | None
    ) = None
    supply_current: Literal["AC", "DC", "AC/DC"] | None = None
    phase_count: Literal[1, 3] | None = None
    service: Literal["on_off", "modulating"] | None = None
    frequency_hz: Literal[50, 60] | None = None
    min_torque_nm: NonNegative | None = None
    # Published in-lb column, compared directly: no unit conversion by model or code.
    min_torque_in_lb: NonNegative | None = None
    min_duty_s4_percent: (
        Annotated[Decimal, Field(ge=0, le=100, allow_inf_nan=False)] | None
    ) = None
    min_cycles_per_hour: Annotated[int, Field(ge=0, le=2147483647)] | None = None
    min_starts_per_hour: Annotated[int, Field(ge=0, le=2147483647)] | None = None
    max_operating_time_s: NonNegative | None = None
    max_fla_a: NonNegative | None = None
    max_lra_a: NonNegative | None = None
    max_motor_power_w: NonNegative | None = None
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
