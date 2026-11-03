"""Preserve page headers and notes directly from OCR, with source boxes and retries."""

from __future__ import annotations

import re
import cv2

from .geometry import Token, Table, compact


def normalized_text(text: str) -> str:
    # Compare formatting only. Never replace letters with numeric answers.
    return re.sub(r"\s+", "", text).casefold().strip("•")


def clean_technical_notation(text: str) -> tuple[str, list[dict]]:
    """Restricted lexical grammars, never a global O/0 or decimal replacement."""
    changes = []

    def standard(match):
        before = match.group(0)
        identifier = match.group(1).translate(
            str.maketrans({"o": "0", "O": "0", "I": "1", "l": "1"})
        )
        after = "IEC " + identifier
        if before != after:
            changes.append(
                dict(rule="numeric_IEC_identifier", before=before, after=after)
            )
        return after

    cleaned = re.sub(r"\bIEC\s+([0-9OoIl]+(?:-[0-9OoIl]+)+)\b", standard, text)

    def group(match):
        before = match.group(0)
        after = match.group(1) + "II" + match.group(2)[-1].upper()
        if before != after:
            changes.append(dict(rule="roman_gas_group", before=before, after=after))
        return after

    cleaned = re.sub(r"((?:AEx|Ex)\s+d\s+)([Il1]{2}[ABC])\b", group, cleaned)
    return cleaned, changes


def page_metadata(tokens: list[Token], tables: list[Table], image, ocr) -> dict:
    heading_markers = [t for t in tokens if "PROOF" in compact(t.text)]
    contexts = []
    header_tokens = []
    for table in tables:
        preceding = [t for t in heading_markers if t.y < table.title_bbox[1]]
        heading = max(preceding, key=lambda t: t.y, default=None)
        line = sorted(
            [
                t
                for t in tokens
                if heading and abs(t.y - heading.y) < heading.height * 0.6
            ],
            key=lambda t: t.x,
        )
        raw = " ".join(t.text for t in line)
        label = compact(raw)
        weather = "WEATHERPROOF" in label
        explosion = "EXPLOSIONPROOF" in label
        enclosure = (
            ("weatherproof" if weather else "explosionproof")
            if weather != explosion
            else None
        )
        contexts.append(
            dict(
                enclosure=enclosure,
                certification_header_raw=raw,
                header_evidence=[
                    dict(text=t.text, bbox=list(t.bbox), confidence=t.score)
                    for t in line
                ],
            )
        )
        header_tokens.extend(line)
    first = (
        contexts[0] if contexts else dict(enclosure=None, certification_header_raw="")
    )
    notes_markers = [t.y for t in tokens if compact(t.text) == "NOTES"]
    notes_start = min(notes_markers, default=image.shape[0])
    note_tokens = [
        t for t in tokens if t.y > notes_start and compact(t.text) != "NOTES"
    ]
    footnotes = [
        t
        for t in tokens
        if t.text.strip().startswith("*")
        and t.y < notes_start
        and not any(tab.y_bounds[0] < t.y < tab.y_bounds[-1] for tab in tables)
    ]
    chosen = sorted(note_tokens + footnotes, key=lambda t: (round(t.y / 8), t.x))
    if len(chosen) > 1000:
        from .geometry import GeometryError

        raise GeometryError("Page note budget exceeded")
    readings = []
    for start in range(0, len(chosen), 16):
        images = []
        for token in chosen[start : start + 16]:
            x0, y0, x1, y1 = map(int, token.bbox)
            crop = image[
                max(0, y0) : min(image.shape[0], y1),
                max(0, x0) : min(image.shape[1], x1),
            ]
            images += [
                crop,
                cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC),
            ]
        readings.extend(ocr.recognize(images))
    notes = []
    for i, token in enumerate(chosen):
        candidates = [dict(text=token.text, confidence=token.score, method="page_ocr")]
        candidates += [
            dict(text=text, confidence=score, method=method)
            for method, (text, score) in zip(
                ("detected_box", "detected_box_scale"), readings[2 * i : 2 * i + 2]
            )
        ]
        groups = {}
        for c in candidates:
            if c["confidence"] >= 0.90:
                groups.setdefault(normalized_text(c["text"]), []).append(c)
        winner = max(
            groups.values(),
            key=lambda g: (len(g), sum(c["confidence"] for c in g) / len(g)),
            default=[],
        )
        accepted = len(winner) >= 2
        best = max(winner, key=lambda c: c["confidence"]) if winner else candidates[0]
        cleaned, changes = clean_technical_notation(best["text"])
        notes.append(
            dict(
                raw_text=token.text,
                text=cleaned,
                cleaning=changes,
                bbox=list(token.bbox),
                confidence=best["confidence"],
                status="ocr_consensus" if accepted else "raw_ocr_unconfirmed",
                candidates=candidates,
                kind="footnote" if token in footnotes else "note",
            )
        )
    return dict(
        enclosure=first["enclosure"],
        certification_header_raw=first["certification_header_raw"],
        table_contexts=contexts,
        notes=notes,
        header_evidence=[
            dict(text=t.text, bbox=list(t.bbox), confidence=t.score)
            for t in header_tokens
        ],
    )


def table_footnotes(notes: list[dict], table: Table, tables: list[Table]) -> list[dict]:
    next_title = min(
        (t.title_bbox[1] for t in tables if t.title_bbox[1] > table.title_bbox[1]),
        default=float("inf"),
    )
    return [
        n
        for n in notes
        if n["kind"] == "footnote"
        and table.y_bounds[-1] < (n["bbox"][1] + n["bbox"][3]) / 2 < next_title
    ]
