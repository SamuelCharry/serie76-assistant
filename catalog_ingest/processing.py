"""Source cell reconstruction, merged-cell evidence and image-based numeric retries."""

from __future__ import annotations

from statistics import median
import re

import cv2
import numpy as np

from .geometry import (
    Table,
    Token,
    GeometryError,
    horizontal_rules,
    part_number,
    compact,
)
from .schema import parse_number, valid_field_value, validate_measurements


def inside(tokens: list[Token], bbox: tuple) -> list[Token]:
    x0, y0, x1, y1 = bbox
    return sorted(
        [t for t in tokens if x0 <= t.x < x1 and y0 <= t.y < y1],
        key=lambda t: (t.y, t.x),
    )


def primary_read(tokens: list[Token], bbox: tuple) -> dict:
    selected = inside(tokens, bbox)
    return dict(
        method="page_ocr",
        text=" ".join(t.text.strip() for t in selected),
        confidence=min((t.score for t in selected), default=0.0),
        detected_bbox=list(selected[0].bbox) if len(selected) == 1 else None,
    )


def cell_variants(
    image: np.ndarray, bbox: tuple, trim: bool = True
) -> list[np.ndarray]:
    x0, y0, x1, y1 = bbox
    crop = image[
        max(0, int(y0) + 2) : min(image.shape[0], int(y1) - 2),
        max(0, int(x0) + 2) : min(image.shape[1], int(x1) - 2),
    ].copy()
    if crop.size == 0:
        raise GeometryError("Empty cell crop")
    if crop.shape[0] * crop.shape[1] > 2_000_000:
        raise GeometryError("Cell crop exceeds the pixel budget")
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    # Remove ruling lines and excessive merged-cell whitespace for both variants.
    ink = (gray < 155).astype(np.uint8)
    ink[:2] = 0
    ink[-2:] = 0
    ink[:, :2] = 0
    ink[:, -2:] = 0
    if trim and ink.any():
        ys, xs = np.nonzero(ink)
        # Keep small breathing room and decimal points. No dot-removal morphology.
        l, r = max(0, int(xs.min()) - 3), min(crop.shape[1], int(xs.max()) + 4)
        t, b = max(0, int(ys.min()) - 3), min(crop.shape[0], int(ys.max()) + 4)
        crop = crop[t:b, l:r]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    contrast = cv2.cvtColor(
        cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX), cv2.COLOR_GRAY2BGR
    )
    variants = []
    for im in (crop, contrast):
        padded = cv2.copyMakeBorder(
            im, 10, 10, 12, 12, cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )
        variants.append(
            cv2.resize(padded, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        )
    return variants


def candidate_value(field: str, text: str):
    if field == "base_part_number":
        return part_number(text)
    try:
        return parse_number(text) if valid_field_value(field, text) else None
    except ValueError:
        return None


def choose_reading(field: str, candidates: list[dict]) -> tuple[object, dict | None]:
    groups = {}
    for candidate in candidates:
        value = candidate_value(field, candidate["text"])
        if value is not None:
            groups.setdefault(value, []).append(candidate)
    # Correlated readings of an over-wide cell can agree on the wrong glyph.
    # Favor agreement between the detected text region and its direct reread,
    # provided both have strong scores. No O/0 substitution is performed.
    trusted = []
    for value, votes in groups.items():
        direct = [
            v
            for v in votes
            if v["method"] in {"page_ocr", "detected_box", "detected_box_scale"}
            and v["confidence"] >= 0.97
        ]
        if len(direct) >= 2:
            trusted.append(value)
    if len(trusted) == 1:
        return trusted[0], None
    if len(trusted) > 1:
        return None, dict(
            code="conflicting_detected_region_readings", candidates=candidates
        )
    supported = []
    for value, votes in groups.items():
        credible = [v for v in votes if v["confidence"] >= 0.90]
        average = (
            sum(v["confidence"] for v in credible) / len(credible) if credible else 0
        )
        qualifies = (
            len(credible) >= 2
            and average >= 0.955
            and max(v["confidence"] for v in credible) >= 0.985
        ) or (len(credible) >= 3 and average >= 0.92)
        supported.append((len(credible) if qualifies else 0, average, value))
    supported.sort(key=lambda item: (item[0], item[1]), reverse=True)
    if supported and supported[0][0] >= 2:
        if len(supported) > 1 and supported[1][0] >= 2:
            return None, dict(code="conflicting_strong_readings", candidates=candidates)
        return supported[0][2], None
    primary = candidates[0]
    value = candidate_value(field, primary["text"])
    credible_alternative = any(
        v != value and any(c["confidence"] >= 0.97 for c in votes)
        for v, votes in groups.items()
    )
    if (
        value is not None
        and primary["confidence"] >= 0.995
        and not credible_alternative
    ):
        return value, None
    return None, dict(code="uncertain_cell", candidates=candidates)


def table_cells(
    table: Table, tokens: list[Token], image: np.ndarray
) -> tuple[list[dict], dict]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    top, bottom = table.y_bounds[0], table.y_bounds[-1]
    row_height = median(t.height for t in table.rows)
    margin = row_height * 0.4
    power_index = next(
        i for i, c in enumerate(table.columns) if c.field == "motor_power_w"
    )
    px0, px1 = table.x_bounds[power_index + 1 : power_index + 3]
    width = px1 - px0
    rules = horizontal_rules(
        gray, px0 + width * 0.15, px1 - width * 0.15, top - margin, bottom + margin
    )
    if len(rules) < 2:
        raise GeometryError("Power column has no detectable merged-cell boundaries")
    power_spans = {}
    for i, row in enumerate(table.rows):
        before = [y for y in rules if y < row.y]
        after = [y for y in rules if y > row.y]
        if not before or not after:
            raise GeometryError("Power span is not bounded by visible ruling lines")
        power_spans[i] = (max(before), min(after))
    na_rows = {}
    for token in tokens:
        if compact(token.text) != "NA" or not (
            table.x_bounds[1] < token.x < table.x_bounds[-1] and top < token.y < bottom
        ):
            continue
        rules_na = horizontal_rules(
            gray, table.x_bounds[1], table.x_bounds[-1], top - margin, bottom + margin
        )
        before = [y for y in rules_na if y < token.y]
        after = [y for y in rules_na if y > token.y]
        if not before or not after:
            raise GeometryError("N/A block boundaries are ambiguous")
        lo, hi = max(before), min(after)
        for i, row in enumerate(table.rows):
            if lo < row.y < hi:
                na_rows[i] = (lo, hi)
        other = [
            t
            for t in tokens
            if table.x_bounds[1] < t.x < table.x_bounds[-1]
            and lo < t.y < hi
            and t is not token
        ]
        if any(re.search(r"\d", t.text) for t in other):
            raise GeometryError(
                "Numeric text conflicts with an explicit merged N/A block"
            )
    cells = []
    for i, row in enumerate(table.rows):
        cells.append(
            dict(
                source_row=i + 1,
                field="base_part_number",
                unit=None,
                bbox=[
                    table.x_bounds[0],
                    table.y_bounds[i],
                    table.x_bounds[1],
                    table.y_bounds[i + 1],
                ],
                status="reported",
                source_span_rows=[i + 1, i + 1],
            )
        )
        for j, column in enumerate(table.columns):
            y0, y1 = table.y_bounds[i : i + 2]
            span = [i + 1, i + 1]
            if column.field == "motor_power_w":
                y0, y1 = power_spans[i]
                members = [n + 1 for n, r in enumerate(table.rows) if y0 < r.y < y1]
                span = [min(members), max(members)]
            if i in na_rows:
                lo, hi = na_rows[i]
                members = [n + 1 for n, r in enumerate(table.rows) if lo < r.y < hi]
                span = [min(members), max(members)]
            cells.append(
                dict(
                    source_row=i + 1,
                    field=column.field,
                    unit=column.unit,
                    frequency_hz=column.frequency_hz,
                    service=column.service,
                    header_unit_raw=column.raw_unit,
                    bbox=[table.x_bounds[j + 1], y0, table.x_bounds[j + 2], y1],
                    source_merged_bbox=[
                        table.x_bounds[1],
                        na_rows[i][0],
                        table.x_bounds[-1],
                        na_rows[i][1],
                    ]
                    if i in na_rows
                    else None,
                    status="source_NA" if i in na_rows else "reported",
                    source_span_rows=span,
                )
            )
    return cells, dict(na_rows=sorted(i + 1 for i in na_rows), power_rules=rules)


def read_table(
    table: Table, tokens: list[Token], image: np.ndarray, ocr, strict: bool = True
) -> tuple[list[dict], list[dict], dict]:
    cells, geometry = table_cells(table, tokens, image)
    unique = {}
    for cell in cells:
        if cell["status"] == "source_NA":
            cell.update(
                value=None, raw_text="N/A", readings=[], method="explicit_merged_NA"
            )
            continue
        key = (cell["field"], tuple(cell["bbox"]))
        if key not in unique:
            primary = primary_read(tokens, cell["bbox"])
            # A product identifier was already discovered geometrically. Use its full OCR token.
            if cell["field"] == "base_part_number":
                row = table.rows[cell["source_row"] - 1]
                primary = dict(method="page_ocr", text=row.text, confidence=row.score)
                primary["detected_bbox"] = list(row.bbox)
            unique[key] = dict(
                field=cell["field"], bbox=cell["bbox"], readings=[primary]
            )
    pending = []
    images = []
    recognitions = 0

    def flush():
        for (key, name), (text, score) in zip(pending, ocr.recognize(images)):
            unique[key]["readings"].append(
                dict(method=name, text=text, confidence=score)
            )
        pending.clear()
        images.clear()

    for key, item in unique.items():
        primary = item["readings"][0]
        needs_retry = (
            strict
            or primary["confidence"] < 0.985
            or candidate_value(item["field"], primary["text"]) is None
        )
        if needs_retry:
            recognitions += 2
            if recognitions > 12000:
                raise GeometryError("Per-table recognition budget exceeded")
            variants = cell_variants(image, item["bbox"])
            for name, im in zip(("cell_original", "cell_contrast"), variants):
                pending.append((key, name))
                images.append(im)
                if len(images) >= 32:
                    flush()
    if images:
        flush()
    # A tightly trimmed glyph can lose useful character context. Retry the whole
    # cell if the first readings disagree; never repair punctuation in the text.
    for key, item in unique.items():
        if choose_reading(item["field"], item["readings"])[1] is not None:
            for name, im in zip(
                ("cell_full", "cell_full_contrast"),
                cell_variants(image, item["bbox"], trim=False),
            ):
                pending.append((key, name))
                images.append(im)
                if len(images) >= 32:
                    flush()
    if images:
        flush()
    for key, item in unique.items():
        value, problem = choose_reading(item["field"], item["readings"])
        primary = item["readings"][0]
        detected = primary.get("detected_bbox")
        if detected and (
            problem or value != candidate_value(item["field"], primary["text"])
        ):
            x0, y0, x1, y1 = map(int, detected)
            crop = image[
                max(0, y0) : min(image.shape[0], y1),
                max(0, x0) : min(image.shape[1], x1),
            ]
            if not crop.size:
                continue
            for name, scale in (("detected_box", 1), ("detected_box_scale", 2)):
                pending.append((key, name))
                images.append(
                    cv2.resize(
                        crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
                    )
                )
                if len(images) >= 32:
                    flush()
    if images:
        flush()
    issues = []
    for cell in cells:
        if cell["status"] == "source_NA":
            continue
        item = unique[cell["field"], tuple(cell["bbox"])]
        readings = item["readings"]
        if len(readings) == 1:
            value = candidate_value(cell["field"], readings[0]["text"])
            problem = None
        else:
            value, problem = choose_reading(cell["field"], readings)
        confirmations = [
            reading
            for reading in readings
            if value is not None
            and candidate_value(cell["field"], reading["text"]) == value
            and reading["confidence"] >= 0.90
        ]
        method = (
            "unresolved"
            if value is None
            else "image_consensus"
            if len(confirmations) >= 2
            else "page_high_confidence_unconfirmed"
        )
        cell.update(
            value=value,
            raw_text=readings[0]["text"],
            readings=readings,
            method=method,
            confirmation_count=len(confirmations),
            selection_source_methods=sorted(
                {reading["method"] for reading in confirmations}
            ),
        )
        if problem or value is None:
            issues.append(
                dict(
                    **(problem or {"code": "unread_cell"}),
                    field=cell["field"],
                    source_row=cell["source_row"],
                    bbox=cell["bbox"],
                )
            )
    rows = []
    for i, part in enumerate(table.rows, 1):
        rowcells = [c for c in cells if c["source_row"] == i]
        values = {
            c["field"]: c["value"] for c in rowcells if c["field"] != "base_part_number"
        }
        issues.extend(dict(**p, source_row=i) for p in validate_measurements(values))
        code = next(c["value"] for c in rowcells if c["field"] == "base_part_number")
        rows.append(
            dict(
                base_part_number=code.rstrip("*") if code else None,
                source_part_number=code,
                data_status="source_NA" if i in geometry["na_rows"] else "reported",
                source_row=i,
                service_layout=table.family,
                **table.supply,
                **values,
                field_status={
                    c["field"]: c["status"]
                    for c in rowcells
                    if c["field"] != "base_part_number"
                },
            )
        )
    return rows, issues, dict(cells=cells, **geometry)
