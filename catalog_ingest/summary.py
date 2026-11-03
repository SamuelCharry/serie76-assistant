"""Business-context glossary from series_76_summary.pdf (text layer, no OCR, no network).

The summary supplies definitions only. It is never a source of catalogue magnitudes.
Segmentation uses the PDF's typography, not keyword heuristics:
  bold-italic line  -> section heading, followed by its paragraph
  bold "N. Name:"   -> group (Enclosure Type, Power Supply, Application Type)
  SymbolMT bullet   -> one term, "Label: definition"
  regular text      -> continuation of the open paragraph or term
Definitions keep the source wording; only layout line breaks are unwrapped.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

EXTRACTOR_VERSION = "summary-typography-v1"

# Curated retrieval vocabulary (NOT source text). It maps user wording to a term and a
# term to related catalogue fields. Versioned with the extractor; never shown as a quote.
TERM_METADATA = {
    "Series 76 Electric Actuators": ("series_76_overview", ["Series 76", "what are these actuators"], []),
    "Understanding the Data Tables": ("data_tables", ["table segmentation", "how the tables are organised"], []),
    "Weatherproof": ("weatherproof", ["weather proof", "outdoor enclosure", "CE", "UKCA"], ["enclosure"]),
    "Explosionproof": ("explosionproof", ["explosion proof", "hazardous area", "ATEX", "IECEx", "flammable gas"], ["enclosure"]),
    "24V AC/DC": ("supply_24v_ac_dc", ["24 V", "low voltage"], ["supply_voltage_v", "supply_current"]),
    "110V Single Phase": ("supply_110v_1ph", ["110 V"], ["supply_voltage_v", "phase_count"]),
    "220V Single Phase": ("supply_220v_1ph", ["220 V"], ["supply_voltage_v", "phase_count"]),
    "On/Off": ("on_off", ["on-off", "open/close", "two-position", "isolation"], ["service"]),
    "Modulating": ("modulating", ["modulation", "positioning", "throttling", "control how much it opens"], ["service"]),
    "Base Part Number": ("base_part_number", ["part number", "model code", "BPN"], ["base_part_number"]),
    "Output Torque": ("output_torque", ["torque", "in-lb", "Nm"], ["torque_nm", "torque_in_lb"]),
    "Duty Cycle (S4%)": ("duty_cycle", ["S4", "duty", "duty cycle", "S4%"], ["duty_s4_percent"]),
    "Operating Speed (Sec)": ("operating_speed", ["operating time", "stroke time", "speed", "travel time"], ["operating_time_s"]),
    "Full Load Current (FLA)": ("fla", ["FLA", "full load amps", "running current"], ["fla_a"]),
    "Locked Rotor Current (LRA)": ("lra", ["LRA", "inrush", "starting current"], ["lra_a"]),
    "Motor Power": ("motor_power", ["power", "watts", "wattage", "power draw"], ["motor_power_w"]),
}


def unwrap(lines):
    text = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # A line ending in '-' after an alphanumeric is a real hyphen split by layout
        # ("90-" + "degree", "761A00-" + "11380000/A"): keep the hyphen, add no space.
        if text and re.search(r"[A-Za-z0-9]-$", text):
            text += line
        else:
            text += (" " + line) if text else line
    return re.sub(r"\s+", " ", text).strip()


def _lines(data):
    import pymupdf

    with pymupdf.open(stream=data, filetype="pdf") as document:
        for page_no, page in enumerate(document, 1):
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    spans = line["spans"]
                    if "".join(s["text"] for s in spans).strip():
                        yield page_no, spans


def extract_terms(pdf):
    data = Path(pdf).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    items, current, section, group = [], None, None, None

    def close():
        nonlocal current
        if current:
            current["text"] = unwrap(current.pop("lines"))
            items.append(current)
        current = None

    plain = []
    for page_no, spans in _lines(data):
        raw = "".join(s["text"] for s in spans)
        font = spans[0]["font"]
        if font.startswith("Symbol"):
            body = "".join(s["text"] for s in spans[1:]) if len(spans) > 1 else raw[1:]
            plain.append(body)
        else:
            plain.append(raw)
        if "BoldItalic" in font:
            close()
            section, group = raw.strip(), None
            current = dict(kind="paragraph", label=section, section=section, group=None, page=page_no, lines=[])
        elif font.endswith("-Bold") and re.match(r"^\d+\.\s", raw.strip()):
            close()
            group = re.sub(r"^\d+\.\s*|:\s*$", "", raw.strip())
        elif font.startswith("Symbol"):
            close()
            current = dict(kind="term", section=section, group=group, page=page_no, lines=[body])
        elif current is not None:
            current["lines"].append(raw)
        else:
            raise ValueError(f"Text outside any section on page {page_no}")
    close()

    full_text = unwrap(plain)
    terms, seen = [], set()
    for ordinal, item in enumerate(items, 1):
        if item["kind"] == "term":
            label, sep, definition = item["text"].partition(": ")
            if not sep or not definition:
                raise ValueError(f"Bullet without 'Label: definition' on page {item['page']}")
        else:
            label, definition = item["label"], item["text"]
            if not definition:
                continue  # Pure heading (e.g. "Data Fields in the Tables"): it only groups bullets.
        if label in seen:
            raise ValueError(f"Duplicate term label: {label}")
        if label not in TERM_METADATA:
            raise ValueError(f"Unmapped term label: {label}")
        seen.add(label)
        if not definition:
            raise ValueError(f"Empty definition: {label}")
        if "�" in definition or "•" in definition:
            raise ValueError(f"Bullet or replacement character left in {label}")
        if definition not in full_text:
            raise ValueError(f"Definition is not verbatim source text: {label}")
        key, aliases, fields = TERM_METADATA[label]
        terms.append(dict(term_key=key, label=label, definition=definition, section=item["section"],
                          group=item["group"], page=item["page"], ordinal=ordinal,
                          aliases=aliases, catalog_fields=fields))
    missing = set(TERM_METADATA) - seen
    if missing:
        raise ValueError(f"Expected terms missing: {sorted(missing)}")
    return dict(document="series_76_summary.pdf", document_sha256=sha, kind="business_context",
                extractor=EXTRACTOR_VERSION, terms=terms)
