"""Infer table rows/columns from OCR headers and positions, not PDF-specific coordinates."""

from __future__ import annotations

from dataclasses import dataclass
import re
from statistics import median

import numpy as np


class GeometryError(ValueError):
    """The document does not provide enough evidence for a safe table mapping."""


@dataclass(frozen=True)
class Token:
    text: str
    bbox: tuple[float, float, float, float]
    score: float

    @property
    def x(self):
        return (self.bbox[0] + self.bbox[2]) / 2

    @property
    def y(self):
        return (self.bbox[1] + self.bbox[3]) / 2

    @property
    def height(self):
        return self.bbox[3] - self.bbox[1]


@dataclass
class Column:
    field: str
    center: float
    raw_unit: str
    unit: str
    service: str | None = None
    frequency_hz: int | None = None


@dataclass
class Table:
    title: str
    title_bbox: tuple
    header_bbox: tuple
    columns: list[Column]
    rows: list[Token]
    x_bounds: list[float]
    y_bounds: list[float]
    family: str
    supply: dict


PART = re.compile(r"[A-Z0-9]{6}-[A-Z0-9]{8}/A\*?\Z")


def compact(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def part_number(text: str) -> str | None:
    value = re.sub(r"\s+", "", text).upper()
    return value if PART.fullmatch(value) else None


def unit_kind(text: str) -> str | None:
    c = compact(text)
    return {
        "INLBS": "in_lb",
        "INLB": "in_lb",
        "NM": "nm",
        "S4": "duty",
        "54": "duty",
        "CYCLES": "cycles",
        "STARTS": "starts",
        "WATTS": "power",
        "WATT": "power",
        "SEC": "time",
        "AMPS": "amps",
    }.get(c) or ("frequency" if re.fullmatch(r"\d{2,4}(?:HZ)?", c) else None)


def nearest_anchor(tokens: list[Token], x: float, predicates: dict) -> str:
    choices = [
        (abs(t.x - x), name)
        for t in tokens
        for name, predicate in predicates.items()
        if predicate(compact(t.text))
    ]
    if not choices:
        raise GeometryError("Required service or measurement header was not recognized")
    return min(choices)[1]


def infer_columns(
    tokens: list[Token], unit_y: float, font_height: float
) -> list[Column]:
    units = [
        t
        for t in tokens
        if abs(t.y - unit_y) <= font_height * 1.2 and unit_kind(t.text)
    ]
    units.sort(key=lambda t: t.x)
    # 60 + Hz may be separate OCR words. Hz is intentionally not its own column.
    if len(units) < 5:
        raise GeometryError("Not enough recognized units to map the table")
    headers = [t for t in tokens if t.y < unit_y - font_height * 0.8]
    services = [
        t for t in headers if "ONOFF" in compact(t.text) or "MODULAT" in compact(t.text)
    ]
    columns = []
    for token in units:
        kind = unit_kind(token.text)
        service, frequency = None, None
        if kind in {"in_lb", "nm", "duty"}:
            service = (
                nearest_anchor(
                    services,
                    token.x,
                    {
                        "on_off": lambda s: "ONOFF" in s,
                        "modulating": lambda s: "MODULAT" in s,
                    },
                )
                if services
                else "shared"
            )
            field = f"{service}_" + (
                "duty_s4_percent" if kind == "duty" else f"torque_{kind}"
            )
            unit = "% S4" if kind == "duty" else "Nm" if kind == "nm" else "in-lb"
        elif kind in {"cycles", "starts"}:
            rate = nearest_anchor(
                headers,
                token.x,
                {"hour": lambda s: "HOUR" in s, "minute": lambda s: "MINUTE" in s},
            )
            nearest = min(
                (
                    abs(t.x - token.x)
                    for t in headers
                    if rate.upper() in compact(t.text)
                ),
                default=float("inf"),
            )
            spacing = median(b.x - a.x for a, b in zip(units, units[1:]))
            if nearest > spacing * 0.8:
                raise GeometryError("Rate time unit is not aligned with its column")
            field = f"{kind}_per_{rate}"
            unit = f"{kind}/" + ("h" if rate == "hour" else "min")
        elif kind == "power":
            if not any(
                "MOTOR" in compact(t.text) and abs(t.x - token.x) < font_height * 2
                for t in headers
            ):
                raise GeometryError("A power unit has no aligned Motor Power header")
            field, unit = "motor_power_w", "W"
        else:
            parent = nearest_anchor(
                headers,
                token.x,
                {
                    "operating_time": lambda s: "OPERATING" in s,
                    "fla": lambda s: "FULLLOAD" in s,
                    "lra": lambda s: "LOCKED" in s,
                },
            )
            suffix = "s" if parent == "operating_time" else "a"
            unit = "s" if parent == "operating_time" else "A"
            if kind == "frequency":
                frequency = int(re.sub(r"HZ$", "", compact(token.text)))
                field = f"{parent}_{frequency}hz_{suffix}"
            else:
                field = f"{parent}_unqualified_{suffix}"
        columns.append(Column(field, token.x, token.text, unit, service, frequency))
    if len({c.field for c in columns}) != len(columns):
        raise GeometryError(
            "Duplicate/ambiguous column headers; refusing positional guesses"
        )
    return columns


def horizontal_rules(
    gray: np.ndarray, x0: float, x1: float, y0: float, y1: float
) -> list[float]:
    left, right = max(0, int(x0)), min(gray.shape[1], int(x1))
    top, bottom = max(0, int(y0)), min(gray.shape[0], int(y1))
    if right <= left or bottom <= top:
        return []
    # Long grey ruling lines survive; alternating light-grey row fills do not.
    hits = np.flatnonzero((gray[top:bottom, left:right] < 205).mean(axis=1) >= 0.68)
    if not len(hits):
        return []
    groups = np.split(hits, np.flatnonzero(np.diff(hits) > 2) + 1)
    return [float(g.mean() + top) for g in groups]


def supply_from_title(title: str) -> dict:
    voltage = re.search(
        r"(?<![\d.,])((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*V\b", title, re.I
    )
    if not voltage:
        raise GeometryError("Supply voltage is absent from the recognized table title")
    upper = title.upper()
    if "SINGLE" in upper:
        phase = 1
    elif "THREE" in upper:
        phase = 3
    elif match := re.search(r"(\d+)[\s-]*PHASE", upper):
        phase = int(match.group(1))
    else:
        phase = None
    if "PHASE" in upper and phase is None:
        raise GeometryError("Supply phase heading is unreadable")
    current = (
        "AC/DC"
        if re.search(r"AC\s*/\s*DC", upper)
        else "DC"
        if re.search(r"\bDC\b", upper)
        else "AC"
        if phase or re.search(r"\bAC\b", upper)
        else None
    )
    from .schema import parse_number

    try:
        voltage_value = parse_number(voltage.group(1))
    except ValueError as error:
        raise GeometryError(f"Ambiguous supply voltage: {error}") from error
    return dict(
        supply_voltage_v=voltage_value,
        supply_current=current,
        phase_count=phase,
        supply_title_raw=title,
        current_interpretation="explicit"
        if re.search(r"\b(?:AC|DC)\b", upper)
        else "phase/frequency header",
    )


def infer_tables(tokens: list[Token], width: int, height: int) -> list[Table]:
    anchors = sorted(
        (t for t in tokens if compact(t.text) == "BASEPARTNUMBER"), key=lambda t: t.y
    )
    parts = [t for t in tokens if part_number(t.text)]
    if parts and not anchors:
        raise GeometryError("Part-number rows exist but no table header was recognized")
    titles = [
        t
        for t in tokens
        if re.search(r"\d+\s*V\b", t.text, re.I) and "POWER" in t.text.upper()
    ]
    if not anchors and titles and any(compact(t.text) == "NM" for t in tokens):
        raise GeometryError(
            "A potential technical table has no readable part-number header"
        )
    notes = [t.y for t in tokens if compact(t.text) == "NOTES"]
    tables = []
    assigned = set()
    for anchor in anchors:
        previous = [t for t in titles if t.y < anchor.y]
        if not previous:
            raise GeometryError("A table has no recognized supply title")
        title = max(previous, key=lambda t: t.y)
        end = min(
            [t.y for t in titles if t.y > anchor.y]
            + [y for y in notes if y > anchor.y]
            + [height]
        )
        body_rows = sorted(
            (t for t in parts if anchor.y < t.y < end and t.x < width * 0.5),
            key=lambda t: t.y,
        )
        if not body_rows:
            raise GeometryError(
                "Table header recognized but its product rows are missing"
            )
        for token in tokens:
            if (
                anchor.y < token.y < end
                and token.x < width * 0.4
                and re.match(r"^[A-Z0-9?]{4,}-", re.sub(r"\s+", "", token.text.upper()))
                and not part_number(token.text)
            ):
                raise GeometryError(
                    "An unreadable product identifier cannot be silently dropped"
                )
        row_height = median(t.height for t in body_rows)
        unit_tokens = [
            t
            for t in tokens
            if compact(t.text) == "NM"
            and anchor.y < t.y < body_rows[0].y - row_height / 2
        ]
        if not unit_tokens:
            raise GeometryError(
                "Nm unit header is missing; cannot establish column alignment"
            )
        unit_y = median(t.y for t in unit_tokens)
        unit_font = median(t.height for t in unit_tokens)
        header_tokens = [
            t for t in tokens if title.bbox[3] < t.y < body_rows[0].y - row_height / 2
        ]
        columns = infer_columns(header_tokens, unit_y, unit_font)
        fields = {c.field for c in columns}
        torque_services = {c.service for c in columns if "torque_nm" in c.field}
        family = (
            "mixed"
            if torque_services == {"on_off", "modulating"}
            else next(iter(torque_services), "unknown")
        )
        expected = {"mixed": 15, "shared": 12, "on_off": 8, "modulating": 8}
        if family not in expected or len(columns) != expected[family]:
            raise GeometryError(
                f"Unsupported or incomplete header schema: {family}, {len(columns)} columns"
            )
        if "motor_power_w" not in fields or not all(
            c.center < columns[i + 1].center for i, c in enumerate(columns[:-1])
        ):
            raise GeometryError("Cannot establish ordered numeric columns")
        centers = [t.y for t in body_rows]
        step = (
            median(b - a for a, b in zip(centers, centers[1:]))
            if len(centers) > 1
            else row_height * 1.8
        )
        if any(
            b - a > step * 1.6 or b - a < row_height * 0.55
            for a, b in zip(centers, centers[1:])
        ):
            raise GeometryError(
                "Product row gap/overlap suggests a missing or duplicated part number"
            )
        x = [c.center for c in columns]
        bounds = [
            min(t.bbox[0] for t in body_rows) - row_height * 0.5,
            x[0] - (x[1] - x[0]) / 2,
        ]
        bounds += [(a + b) / 2 for a, b in zip(x, x[1:])]
        bounds += [x[-1] + (x[-1] - x[-2]) / 2]
        ys = (
            [centers[0] - step / 2]
            + [(a + b) / 2 for a, b in zip(centers, centers[1:])]
            + [centers[-1] + step / 2]
        )
        for token in tokens:
            numeric_like = re.fullmatch(r"[0-9][0-9,.: ]*", token.text.strip())
            if (
                numeric_like
                and bounds[1] < token.x < bounds[-2]
                and unit_y + unit_font < token.y < end
            ):
                if min(abs(token.y - y) for y in centers) > max(
                    row_height * 0.7, step * 0.35
                ):
                    raise GeometryError("Numeric row has no aligned product identifier")
        # No unrecognized text row can disappear just because its identifier OCR failed.
        for token in tokens:
            if bounds[0] <= token.x < bounds[1] and ys[0] <= token.y <= ys[-1]:
                if min(abs(token.y - y) for y in centers) > row_height * 0.65:
                    raise GeometryError("Unassigned text in the part-number column")
        tables.append(
            Table(
                title.text,
                title.bbox,
                (bounds[0], title.bbox[1], bounds[-1], ys[0]),
                columns,
                body_rows,
                bounds,
                ys,
                family,
                supply_from_title(title.text),
            )
        )
        assigned |= {id(t) for t in body_rows}
    if any(id(p) not in assigned for p in parts):
        raise GeometryError(
            "Some product identifiers could not be assigned to any recognized table"
        )
    return tables
