"""Offline evaluation ONLY. The production pipeline never imports this script."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path


def number_equal(actual: str, expected: str) -> bool:
    try:
        return Decimal(actual.replace(",", "")) == Decimal(expected.replace(",", ""))
    except (InvalidOperation, AttributeError):
        return False


def evaluate(catalog: Path, reference: Path) -> dict:
    with catalog.open(encoding="utf-8-sig", newline="") as f:
        actual = list(csv.DictReader(f))
    with reference.open(encoding="utf-8-sig", newline="") as f:
        expected = list(csv.DictReader(f))
    indexed = {}
    for row in actual:
        indexed.setdefault(row["base_part_number"], []).append(row)
    errors = []
    numeric_total = 0
    numeric_exact = 0
    codes_exact = 0
    na_exact = 0
    na_total = 0
    star_exact = 0
    star_total = 0
    context_exact = 0
    context_total = 0
    for row in expected:
        code = row["base_part_number"]
        candidates = indexed.get(code, [])
        observed = candidates[0] if len(candidates) == 1 else {}
        if observed:
            codes_exact += 1
        else:
            errors.append(
                dict(
                    code=code,
                    field="base_part_number",
                    expected=code,
                    actual=[r.get("source_part_number") for r in candidates],
                )
            )
        if row["data_status"] == "source_NA":
            na_total += 1
            na_exact += observed.get("data_status") == "source_NA"
            if observed.get("data_status") != "source_NA":
                errors.append(
                    dict(
                        code=code,
                        field="data_status",
                        expected="source_NA",
                        actual=observed.get("data_status"),
                    )
                )
        for field, value in row.items():
            numeric = field.startswith(
                ("on_off_", "modulating_", "shared_", "operating_time_", "fla_", "lra_")
            ) or field in {"motor_power_w", "cycles_per_hour", "starts_per_hour"}
            if not numeric:
                continue
            prediction = observed.get(field, "")
            if value:
                numeric_total += 1
                if number_equal(prediction, value):
                    numeric_exact += 1
                else:
                    errors.append(
                        dict(code=code, field=field, expected=value, actual=prediction)
                    )
            elif prediction:
                errors.append(
                    dict(code=code, field=field, expected=None, actual=prediction)
                )
        if row["source_part_number"].endswith("*"):
            star_total += 1
            star_exact += (
                observed.get("source_part_number") == row["source_part_number"]
            )
            if observed.get("source_part_number") != row["source_part_number"]:
                errors.append(
                    dict(
                        code=code,
                        field="footnote_marker",
                        expected=row["source_part_number"],
                        actual=observed.get("source_part_number"),
                    )
                )
        for field in ("enclosure", "supply_voltage_v", "supply_current", "phase_count"):
            context_total += 1
            a = observed.get(field, "")
            b = row[field]
            equal = (
                number_equal(a, b)
                if field in {"supply_voltage_v", "phase_count"} and b
                else a == b
            )
            if equal:
                context_exact += 1
            else:
                errors.append(dict(code=code, field=field, expected=b, actual=a))
    expected_ids = {r["base_part_number"] for r in expected}
    for row in actual:
        if row["base_part_number"] not in expected_ids:
            errors.append(
                dict(
                    code=row["base_part_number"],
                    field="unexpected_identity",
                    actual=row["source_part_number"],
                )
            )
    return dict(
        status="passed" if not errors and len(actual) == len(expected) else "failed",
        actual_rows=len(actual),
        expected_rows=len(expected),
        codes_exact=codes_exact,
        codes_total=len(expected),
        numeric_exact=numeric_exact,
        numeric_total=numeric_total,
        source_na_exact=na_exact,
        source_na_total=na_total,
        footnote_markers_exact=star_exact,
        footnote_markers_total=star_total,
        context_exact=context_exact,
        context_total=context_total,
        primary_exact=codes_exact + numeric_exact + na_exact,
        primary_total=len(expected) + numeric_total + na_total,
        discrepancies=errors,
        reference_scope="visual reference, not independent proof of arbitrary future PDFs",
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = evaluate(a.catalog, a.reference)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps({k: v for k, v in result.items() if k != "discrepancies"}, indent=2)
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
