"""Strict numeric parsing and domain diagnostics; never invent source values."""

from __future__ import annotations

from decimal import Decimal
import re

NUMBER = re.compile(r"(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?\Z")


def parse_number(text: str) -> int | float:
    value = text.strip().replace("\u00a0", " ")
    if re.fullmatch(r"\d{1,3}(?: \d{3})+(?:\.\d+)?", value):
        value = value.replace(" ", "")
    if not NUMBER.fullmatch(value):
        raise ValueError(f"Not an unambiguous English numeric cell: {text!r}")
    number = Decimal(value.replace(",", ""))
    if number > Decimal("1e12"):
        raise ValueError("Numeric cell exceeds the supported magnitude")
    if number == number.to_integral_value():
        return int(number)
    value = float(number)
    if Decimal(str(value)) != number:
        raise ValueError("Cell exceeds the supported lossless JSON numeric precision")
    return value


def validate_measurements(values: dict[str, int | float | None]) -> list[dict]:
    issues = []
    for field, value in values.items():
        if value is None:
            continue
        if "duty" in field and not 0 <= value <= 100:
            issues.append(dict(code="duty_out_of_range", field=field, value=value))
        if field.startswith(("cycles_per_", "starts_per_")) and value != int(value):
            issues.append(dict(code="non_integer_count", field=field, value=value))
    for service in ("on_off", "modulating", "shared"):
        lb, nm = (
            values.get(f"{service}_torque_in_lb"),
            values.get(f"{service}_torque_nm"),
        )
        # A deliberately broad diagnostic, not a conversion or numeric correction.
        if lb and nm and not 6 <= lb / nm <= 12:
            issues.append(
                dict(code="torque_unit_inconsistency", service=service, in_lb=lb, nm=nm)
            )
    return issues


def valid_field_value(field: str, text: str) -> bool:
    try:
        value = parse_number(text)
    except ValueError:
        return False
    return not validate_measurements({field: value})
