"""Deterministic conversation policy: the code, not the LLM, owns every constraint.

- Part numbers are canonicalised (case, spaces, a missing hyphen) but never completed.
- Every numeric value the model sets must be traceable to the conversation text, or to
  an explicit, user-visible assumption whose phrase the user actually wrote.
- Follow-ups send a delta; the code merges it with the persisted filters.
- Contradictions become specific clarification questions, not validation errors.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from backend.catalog.models import bound_value, bound_operator, bounds

CODE_RE = re.compile(r"^[A-Z0-9]{6}-[A-Z0-9]{8}/A$")
CODE_IN_TEXT = re.compile(r"\b[A-Za-z0-9]{6}-?[A-Za-z0-9]{8}/?[Aa]\b")
PARTIAL_RE = re.compile(r"^[A-Z0-9][A-Z0-9\-/]{2,16}$")

NUMERIC_FIELDS = ("supply_voltage_v", "frequency_hz", "min_torque_nm", "min_torque_in_lb",
                  "min_duty_s4_percent", "min_cycles_per_hour", "min_starts_per_hour",
                  "max_operating_time_s", "max_fla_a", "max_lra_a", "max_motor_power_w")
CATEGORICAL_FIELDS = ("enclosure", "supply_current", "phase_count", "service", "csa_required")
FILTER_FIELDS = CATEGORICAL_FIELDS + NUMERIC_FIELDS

# Deterministic evidence that a categorical value was expressed by the user. Anything
# else needs an explicit assumption (shown to the user) quoting the user's own words.
LEXICON = {
    ("service", "on_off"): ("on/off", "on_off", "on-off", "on off", "open/close", "open-close", "open or close",
                            "fully open", "fully closed", "two-position", "two position", "isolation", "todo/nada", "todo o nada",
                            "abrir completo o cerrar completo", "abrir completamente o cerrar completamente"),
    ("service", "modulating"): ("modulat", "positioning", "throttl", "proportional", "intermediate position", "modulante"),
    ("enclosure", "explosionproof"): ("explosion", "hazardous", "atex", "iecex", "flammable", "class i", "zone 1", "antiexplos"),
    ("enclosure", "weatherproof"): ("weatherproof", "weather proof", "weather-proof", "outdoor", "rain", "intemperie", "exteriores"),
    ("supply_current", "DC"): ("dc", "direct current", "corriente continua", "battery"),
    # Phases exist only for AC supplies (DC has none), so stated phases ground AC.
    ("supply_current", "AC"): ("ac", "alternating", "alterna", "mains", "hz", "single phase", "single-phase",
                               "three phase", "three-phase", "1-phase", "3-phase", "monofas", "trifas"),
    ("supply_current", "AC/DC"): ("ac/dc", "ac or dc", "ac-dc"),
    ("phase_count", 1): ("single phase", "single-phase", "1 phase", "1-phase", "one phase", "monofas", "1ph"),
    ("phase_count", 3): ("three phase", "three-phase", "3 phase", "3-phase", "trifas", "3ph"),
    ("csa_required", True): ("csa",),
}

CONFLICT_MESSAGES = {
    "dc_frequency": "DC supply has no mains frequency. Do you need a DC actuator, or an AC actuator at {frequency_hz} Hz?",
    "dc_phase": "DC supply has no phase count. Do you need a DC actuator, or an AC {phase_count}-phase actuator?",
    "starts_on_off": "Starts per hour are published for Modulating service, cycles per hour for On/Off. Which service do you need?",
    "cycles_modulating": "Cycles per hour are published for On/Off service, starts per hour for Modulating. Which service do you need?",
    "both_rates": "Cycles per hour (On/Off) and starts per hour (Modulating) belong to different services. Which service do you need?",
}


def canonical_code(raw):
    """Return (code, note) for a complete code, or (None, prefix) when it is partial/malformed."""
    text = re.sub(r"\s+", "", str(raw)).upper()
    if CODE_RE.fullmatch(text):
        return text, None if text == str(raw).strip() else f"Interpreted '{raw}' as {text}."
    compact = re.fullmatch(r"([A-Z0-9]{6})-?([A-Z0-9]{8})/?A", text)
    if compact:
        code = f"{compact.group(1)}-{compact.group(2)}/A"
        return code, f"Interpreted '{raw}' as {code}."
    return None, text if PARTIAL_RE.fullmatch(text) else ""


def codes_in_text(text):
    found = []
    for match in CODE_IN_TEXT.findall(text or ""):
        code, _ = canonical_code(match)
        if code and code not in found:
            found.append(code)
    return found


def grounded_lookup_codes(raw_codes, query):
    """Repair a model-only truncation from a unique full code in this query, never SQL.

    A prefix actually written by the user stays incomplete, even if another full code
    shares it. Unmatched/ambiguous model prefixes also keep the clarification path.
    """
    explicit = codes_in_text(query)
    def characters(value):
        return re.sub(r'[-/\s]', '', value).upper()
    written_tokens = {characters(token) for token in re.findall(r'\b[A-Za-z0-9][A-Za-z0-9/-]*', query)}
    chosen, repaired = [], []
    for raw in raw_codes:
        code, prefix = canonical_code(raw)
        value = raw
        if code is None and prefix:
            # Compare identity characters, not presentation punctuation. The complete
            # user code must still contain its explicit A suffix; no DB completion.
            written = characters(prefix) in written_tokens
            matches = [c for c in explicit if characters(c).startswith(characters(prefix))]
            if not written and len(matches) == 1:
                value = matches[0]
                repaired.append(raw)
        if value not in chosen:
            chosen.append(value)
    return chosen, repaired


def purchase_request(query):
    return bool(re.search(r'\b(buy|purchase|order|delivery|comprar|compra)\b', query, re.I))


def numbers_in(texts):
    values = set()
    for text in texts:
        for token in re.findall(r"\d+(?:[.,]\d+)*", text or ""):
            for candidate in [token.replace(",", "") if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", token) else token.replace(",", ".")]:
                try:
                    values.add(Decimal(candidate))
                except InvalidOperation:
                    pass
    return values


def grounding_errors(delta, assumptions, texts):
    """Fields whose value is not traceable to the conversation or to a quoted assumption."""
    corpus = " ".join(texts).lower()
    numbers = numbers_in(texts)
    assumed = {a["field"] for a in assumptions if a["user_phrase"].strip().lower() in corpus}
    errors = []
    for field, value in delta.items():
        if value is None or field in assumed:
            continue
        if field in NUMERIC_FIELDS:
            if any(Decimal(str(bound_value(item))) not in numbers for item in bounds(value)):
                errors.append(field)
        elif field in CATEGORICAL_FIELDS:
            if field == "csa_required" and value is False:
                continue
            words = LEXICON.get((field, value), ())
            if not any(_has_word(corpus, w) for w in words):
                errors.append(field)
    return errors


def _has_word(corpus, word):
    if len(word) <= 3:  # "ac", "dc", "hz", "csa": whole word only
        return (re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", corpus) is not None
                or re.search(rf"\dv{re.escape(word)}(?![a-z])", corpus) is not None)
    return word in corpus


def invalid_assumptions(assumptions, texts):
    corpus = " ".join(texts).lower()
    return [a for a in assumptions if a["user_phrase"].strip().lower() not in corpus]


def merge_filters(previous, delta, *, refine, remove, more):
    """Return (merged, notes). Only the delta is the model's; carried values are the code's."""
    notes = []
    refine = refine or bool(remove)  # removing a requirement only makes sense on the previous search
    base = {k: v for k, v in (previous or {}).items() if k in FILTER_FIELDS and v is not None} if (refine or more) else {}
    merged = dict(base)
    merged.update({k: v for k, v in delta.items() if v is not None})
    for field in remove:
        merged.pop(field, None)
    old_service, new_service = base.get("service"), merged.get("service")
    if old_service and new_service and old_service != new_service:
        incompatible = "min_cycles_per_hour" if new_service == "modulating" else "min_starts_per_hour"
        if incompatible in base and incompatible not in delta:
            notes.append(f"Removed the previous {_label(incompatible)} requirement because it does not apply to "
                         f"{'Modulating' if new_service == 'modulating' else 'On/Off'} service.")
            merged.pop(incompatible)
    limit = delta.get("limit") or (previous or {}).get("limit") or 5
    offset = ((previous or {}).get("offset", 0) + (previous or {}).get("limit", limit)) if more else 0
    if (refine or more) and previous and previous.get("sort_by"):
        merged["sort_by"] = previous["sort_by"]
    merged.update(limit=limit, offset=offset)
    return merged, notes


def conflicts(filters):
    found = []
    if filters.get("supply_current") == "DC" and filters.get("frequency_hz"):
        found.append(("dc_frequency", ["supply_current", "frequency_hz"]))
    if filters.get("supply_current") == "DC" and filters.get("phase_count"):
        found.append(("dc_phase", ["supply_current", "phase_count"]))
    if filters.get("min_cycles_per_hour") is not None and filters.get("min_starts_per_hour") is not None:
        found.append(("both_rates", ["min_cycles_per_hour", "min_starts_per_hour"]))
    elif filters.get("service") == "on_off" and filters.get("min_starts_per_hour") is not None:
        found.append(("starts_on_off", ["service", "min_starts_per_hour"]))
    elif filters.get("service") == "modulating" and filters.get("min_cycles_per_hour") is not None:
        found.append(("cycles_modulating", ["service", "min_cycles_per_hour"]))
    return found


LABELS = {
    "enclosure": "enclosure", "supply_voltage_v": "supply voltage", "supply_current": "supply current",
    "phase_count": "phase count", "service": "service", "frequency_hz": "frequency",
    "min_torque_nm": "minimum torque", "min_torque_in_lb": "minimum torque", "min_duty_s4_percent": "minimum duty S4",
    "min_cycles_per_hour": "minimum cycles/hour", "min_starts_per_hour": "minimum starts/hour",
    "max_operating_time_s": "maximum operating time", "max_fla_a": "maximum FLA", "max_lra_a": "maximum LRA",
    "max_motor_power_w": "maximum motor power", "csa_required": "CSA",
}


def _label(field):
    return LABELS.get(field, field)


def describe(filters):
    parts = []
    for field in FILTER_FIELDS:
        value = filters.get(field)
        if value is None or (field == "csa_required" and not value):
            continue
        if isinstance(value, list):
            parts.append(' and '.join(describe({field: item}) for item in value))
            continue
        text = {
            "service": lambda v: "On/Off service" if v == "on_off" else "Modulating service",
            "enclosure": lambda v: str(v).capitalize(),
            "supply_voltage_v": lambda v: f"{v} V",
            "supply_current": lambda v: v,
            "phase_count": lambda v: f"{v}-phase",
            "frequency_hz": lambda v: f"{v} Hz",
            "min_torque_nm": lambda v: f"torque ≥ {v} Nm",
            "min_torque_in_lb": lambda v: f"torque ≥ {v} in-lb",
            "min_duty_s4_percent": lambda v: f"duty S4 ≥ {v}%",
            "min_cycles_per_hour": lambda v: f"≥ {v} cycles/h",
            "min_starts_per_hour": lambda v: f"≥ {v} starts/h",
            "max_operating_time_s": lambda v: f"operating time ≤ {v} s",
            "max_fla_a": lambda v: f"FLA ≤ {v} A",
            "max_lra_a": lambda v: f"LRA ≤ {v} A",
            "max_motor_power_w": lambda v: f"motor power ≤ {v} W",
            "csa_required": lambda v: "CSA listed in the table header",
        }[field](value)
        if isinstance(value, dict):
            number = bound_value(value)
            text = text.replace(str(value), str(number))
            op = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}[bound_operator(value, "gte" if field.startswith("min_") else "lte")]
            text = text.replace("≥", op).replace("≤", op)
        parts.append(text)
    return ", ".join(parts)


UNKNOWN_TOKEN = re.compile(r"\b(?:NEMA\s?\d{1,2}X?|[A-Z]{1,5}\s?\d{1,5}[A-Z]{0,2})\b")


STOPWORDS = set("""the and what does mean means meaning for with this that these those your you have are how which about tell
explain define defined definition difference between is in of on to a an it its do me please can could would should there
their they them from into any some show give print list all one ones need want data value values table tables column columns
actuator actuators series""".split())


def _vocabulary(text):
    words = set()
    for raw in re.findall(r"[A-Za-z0-9/%-]+", text or ""):
        word = raw.lower().strip("-/%")
        # Short words count only as acronyms (AC, DC, Nm) or when they contain a digit (S4).
        if (len(word) >= 3 or any(c.isdigit() for c in word) or (len(raw) >= 2 and raw.isupper())) and word not in STOPWORDS:
            words.add(word)
            for part in re.split(r"[/-]", word):
                if len(part) >= 2 and part not in STOPWORDS:
                    words.add(part)
    return words


def term_is_relevant(query, term):
    """The question must share vocabulary with the term (label, aliases, key or definition)."""
    vocabulary = _vocabulary(" ".join([term["label"], term["term_key"].replace("_", " "), " ".join(term["aliases"]), term["definition"]]))
    return bool(_vocabulary(query) & vocabulary)


def term_is_named(query, term):
    """Direct glossary identity, not overlap with generic words in a definition."""
    names = [term['term_key'], term['term_key'].replace('_', ' '), term['label'], *term['aliases']]
    return any(re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', query, re.I) for name in names)


def normalized_term_keys(keys, query, terms):
    """Resolve supplied glossary aliases and deduplicate; unknown ratings stay explicit.

    If an absent rating is asked, do not substitute a related term unless the user
    also named that term. Other unrecognised keys are retained for schema rejection.
    """
    aliases = {name.casefold(): t['term_key'] for t in terms
               for name in [t['term_key'], t['label'], *t['aliases']]}
    index = {t['term_key']: t for t in terms}
    unknown = {t.casefold() for t in terms_not_in_glossary(query, terms)}
    chosen = []
    for raw in keys:
        if not isinstance(raw, str):
            raise ValueError('Invalid term key')
        key = aliases.get(raw.casefold(), raw)
        if raw.casefold() in unknown:
            continue
        if unknown and key in index and not term_is_named(query, index[key]):
            continue
        if key not in chosen:
            chosen.append(key)
    return chosen


def terms_not_in_glossary(query, terms):
    """Rating/standard-like tokens in the question (IP67, NEMA 4X, IEC 60034) the glossary lacks."""
    corpus = " ".join(f"{t['label']} {t['definition']} {' '.join(t['aliases'])}" for t in terms).lower()
    found = []
    for token in UNKNOWN_TOKEN.findall(query or ""):
        if token.lower() not in corpus and not codes_in_text(token) and token not in found:
            found.append(token)
    return found
