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


def sort_grounded(sort_key, query):
    """Ignore a model-supplied ranking preference the user never requested."""
    text = query.lower()
    patterns = {
        'fastest': r'\b(?:fast(?:est)?|quick(?:est)?|speed|r[aá]pid[oa])\b',
        'lowest_power': r'\b(?:low(?:est)?|least|less|minimum|menos)\b.*\b(?:power|energy|electricity|consumption|potencia|energ[ií]a)\b|\b(?:consum\w*|gasta)\b',
        'highest_torque': r'\bstrongest\b|\b(?:highest|biggest|most|maximum|m[aá]ximo|mayor)\b.*\b(?:torque|par|strength)\b',
        'lowest_current': r'\b(?:low(?:est)?|least|less|minimum|menos)\b.*\b(?:current|fla|amps?|corriente)\b|\b(?:corriente|current|fla)\b.*\b(?:low(?:est)?|least|less|minimum|menos)\b',
    }
    return bool(re.search(patterns.get(sort_key, r'(?!)'), text))

# Deterministic evidence that a categorical value was expressed by the user. Anything
# else needs an explicit assumption (shown to the user) quoting the user's own words.
LEXICON = {
    ("service", "on_off"): ("on/off", "on_off", "on-off", "on off"),
    ("service", "modulating"): ("modulating", "modulation", "modulante"),
    ("enclosure", "explosionproof"): ("explosionproof", "explosion proof", "explosion-proof", "antiexplos"),
    ("enclosure", "weatherproof"): ("weatherproof", "weather proof", "weather-proof"),
    ("supply_current", "DC"): ("dc", "direct current", "corriente continua", "battery"),
    # Phases exist only for AC supplies (DC has none), so stated phases ground AC.
    ("supply_current", "AC"): ("ac", "alternating", "alterna", "mains", "hz", "single phase", "single-phase",
                               "three phase", "three-phase", "1-phase", "3-phase", "monofas", "trifas"),
    ("supply_current", "AC/DC"): ("ac/dc", "ac or dc", "ac-dc"),
    ("phase_count", 1): ("single phase", "single-phase", "1 phase", "1-phase", "one phase", "monofas", "1ph"),
    ("phase_count", 3): ("three phase", "three-phase", "3 phase", "3-phase", "trifas", "3ph"),
    ("csa_required", True): ("csa",),
}


def colloquial_requirements(query, semantic=None):
    """Explicit constraints plus optional semantic suggestions; None preserves fallback."""
    text = canonical_enclosures(query.lower())
    result, notes = {}, []
    for phrase, name in (('indoors', 'indoor'), ('indoor', 'indoor'),
                         ('quiet', 'quiet'), ('compact', 'compact')):
        if re.search(r'\b' + phrase + r'\b', text):
            note = ("The catalogue doesn't classify models as indoor; showing all enclosures."
                    if name == 'indoor' else
                    f"The catalogue doesn't classify models as {name}; showing models by published fields.")
            if note not in notes:
                notes.append(note)
    from .context_fallback import colloquial
    result.update(colloquial(text))
    if nonhazard_signal(text):
        result['enclosure'] = 'weatherproof'
    if re.search(r'\bxp\b', text):
        result['enclosure'] = 'explosionproof'
    if re.search(r'\bwp\b', text):
        result['enclosure'] = 'weatherproof'
    if re.search(r'\b(?:[13])[-\s]*(?:phase|phases|fases)\b', text):
        result['phase_count'] = int(re.search(r'\b([13])[-\s]*(?:phase|phases|fases)\b', text).group(1))
    if re.search(r'\b(?:classified as hazardous|hazardous area|area is hazardous)\b', text):
        result['enclosure'] = 'explosionproof'
        notes.append('Interpreted the explicit hazardous-area requirement as Explosionproof.')
    if re.search(r'\b(battery|low voltage|bater[ií]a|bajo voltaje)\b', text):
        result['supply_voltage_v'] = 24
    if re.search(r'\b(solar|battery|bater[ií]a)\b', text):
        result['supply_current'] = 'DC'
        notes.append('Solar or battery supply is DC; compatible AC/DC models remain eligible.')
    if re.search(r'\bbattery (?:room|storage)\b', text):
        result.pop('supply_voltage_v', None)
        result.pop('supply_current', None)
        notes = [note for note in notes if not note.startswith('Solar or battery supply')]
    match = re.search(r'\b(\d+(?:[.,]\d+)?)\s*knm\b', text)
    if match:
        number = Decimal(match.group(1).replace(',', '.'))
        value = number * 1000
        result['min_torque_nm'] = int(value) if value == int(value) else value
        notes.append(f'{match.group(1)} kNm = {value:f} Nm.'.replace('.0 Nm.', ' Nm.'))
    match = re.search(r'\b(?:at least|minimum|min(?:imum)?\s+torque)\s*(\d+(?:[.,]\d+)?)\s*nm\b', text)
    if match:
        number = Decimal(match.group(1).replace(',', '.'))
        result['min_torque_nm'] = int(number) if number == int(number) else float(number)
    upper = re.search(r'(?:\b|(?<=\s))(no more than|at most|up to|max(?:imum)?|below|under|less than|hasta|m[aá]ximo|como m[aá]ximo|≤)\s*(?:(?:torque|par)\s+)?(\d+(?:[.,]\d+)?)\s*nm\b|\b(?:torque|par)\s+(no more than|at most|up to|max(?:imum)?|below|under|less than|hasta|m[aá]ximo|como m[aá]ximo|≤)\s*(\d+(?:[.,]\d+)?)\s*nm\b', text)
    if upper:
        operator = upper.group(1) or upper.group(3)
        number = Decimal((upper.group(2) or upper.group(4)).replace(',', '.'))
        result['min_torque_nm'] = {'value': int(number) if number == int(number) else float(number),
                                   'op': 'lt' if operator in ('below', 'under', 'less than') else 'lte'}
    if re.search(r'\b(?:a prueba de explosi[oó]n)\b', text):
        result['enclosure'] = 'explosionproof'
    match = re.search(r'\b(?:toque|torque|par)\s*m[ií]nimo\s*(?:de\s*)?(\d+(?:[.,]\d+)?)\s*nm\b', text)
    if match:
        result['min_torque_nm'] = Decimal(match.group(1).replace(',', '.'))
    labels = {'explosionproof': ('enclosure', 'explosionproof', 'Explosionproof'),
              'weatherproof': ('enclosure', 'weatherproof', 'Weatherproof'),
              'modulating': ('service', 'modulating', 'Modulating')}
    for token in re.findall(r'\b[a-z]{6,}\b', text):
        ranked = sorted(((_edit_distance(token, label), label) for label in labels))
        if ranked[0][0] <= 2 and (len(ranked) == 1 or ranked[0][0] < ranked[1][0]):
            field, value, display = labels[ranked[0][1]]
            result[field] = value
            if token != ranked[0][1]:
                notes.append(f"Interpreted '{token}' as {display}.")
    if nonhazard_signal(text):
        result['enclosure'] = 'weatherproof'
    # Retrieval is additive: deterministic normalization and negations run first.
    result.update(explicit_context_values(text))
    if semantic is not None:
        removed = removed_fields(text)
        for concept in ('on_off', 'modulating'):
            if concept in semantic and 'service' not in result and 'service' not in removed:
                result['service'] = concept
                notes.append('Interpreted the requested operation as ' + ('On/Off' if concept == 'on_off' else 'Modulating') + '.')
        if 'safe_area' in semantic and 'enclosure' not in result and 'enclosure' not in removed:
            result['enclosure'] = 'weatherproof'
            notes.append('Interpreted the site as a nonhazardous area; please confirm if that is incorrect.')
    return result, notes


NONHAZARD_RE = re.compile(r'\b(?:not hazardous|not a (?:classified|hazardous) (?:area|zone)|outside (?:the )?(?:classified|hazardous) (?:area|zone)|(?:safe|normal) area|area is safe|no gas)\b', re.I)


def nonhazard_signal(text):
    return bool(NONHAZARD_RE.search(text) or re.search(
        r'\b(?:no|not|nothing|without|sin)\s+(?:\w+\s+){0,2}(?:flammable|explosive|hazardous|inflamables?|explosiv[oa]s?)\b', text, re.I))


def canonical_enclosures(text):
    """Use the same published enclosure spellings before all context decisions."""
    return re.sub(r'\b(explosion|weather)[\s-]*proof\b',
                  lambda match: match.group(1).lower() + 'proof', text, flags=re.I)


NO_PREFERENCE = re.compile(
    r"\b(?:does\s+not\s+matter|doesn['’]t\s+matter|do\s+not\s+care|don['’]t\s+care|"
    r"no\s+preference|not\s+(?:required|needed|necessary))\b", re.I)


def context_clauses(text):
    return re.split(r'[,;.!?]|\bbut\b', canonical_enclosures(text), flags=re.I)


def explicit_context_values(text):
    values = {}
    patterns = [('service', 'on_off', r'\bon[ /_-]*off\b'),
                ('service', 'modulating', r'\b(?:modulating|modulation|modulante)\b'),
                ('enclosure', 'weatherproof', r'\bweatherproof\b'),
                ('enclosure', 'explosionproof', r'\bexplosionproof\b')]
    for clause in context_clauses(text):
        if NO_PREFERENCE.search(clause):
            continue
        for field, value, pattern in patterns:
            for match in re.finditer(pattern, clause, re.I):
                prefix = clause[:match.start()]
                if not re.search(r'\b(?:no|not|sin|forget|drop|remove|any)\s+(?:\w+\s+){0,2}$', prefix, re.I):
                    values[field] = value
    return values


def hazard_signal(text, semantic=None):
    if nonhazard_signal(text):
        return False
    from .context_fallback import HAZARD_RE
    if HAZARD_RE.search(text):
        return True
    if semantic is not None and 'hazard' in semantic:
        stated, _ = colloquial_requirements(text)
        return 'enclosure' not in stated and 'enclosure' not in removed_fields(text)
    return False


def weather_exposure(text, semantic=None):
    from .context_fallback import weather_exposure as fallback
    return fallback(text) or semantic is not None and 'safe_area' in semantic


REMOVE_WORDS = {
    'enclosure': r'enclosure|explosionproof|weatherproof|hazardous|classified',
    'supply_voltage_v': r'voltage|volts?|\d+\s*v\b',
    'service': r'service|on\s*/?\s*off|modulating',
    'phase_count': r'phases?|fases?',
    'frequency_hz': r'frequency|hz',
    'min_torque_nm': r'torque|\bnm\b',
    'min_torque_in_lb': r'torque|in\s*-?\s*lb',
    'max_fla_a': r'fla|full.load current',
    'max_lra_a': r'lra|locked.rotor current',
    'max_motor_power_w': r'motor power|wattage',
}


def removed_fields(query, pending_questions=()):
    """Map an explicit negation to filter keys, independent of model output."""
    text = query.lower()
    text = re.sub(r'\b(?:no more than|not more than|no less than)\b', 'bound', text)
    removed = set()
    for clause in context_clauses(text):
        for field, words in REMOVE_WORDS.items():
            if re.search(r'\b(?:forget|drop|remove|no|not|any)\b(?:\W+\w+){0,3}?\W+(?:' + words + r')\b', clause) or \
                    (NO_PREFERENCE.search(clause) and re.search(r'\b(?:' + words + r')\b', clause)) or \
                    re.search(r'\b(?:' + words + r')\b.{0,20}\bany(?:thing)?\b', clause):
                removed.add(field)
    if NO_PREFERENCE.search(text) and not removed and pending_questions:
        removed.add(pending_questions[0]['id'])
    if nonhazard_signal(text):
        removed.add('enclosure')
    return removed


CATALOGUE_ATTRIBUTE_WORDS = frozenset({
    'spec', 'specs', 'specification', 'specifications', 'data', 'detail', 'details',
    'torque', 'duty', 'cycle', 'cycles', 'starts', 'hour', 'time', 'speed', 'fast',
    'fla', 'lra', 'current', 'power', 'voltage', 'supply', 'phase', 'frequency',
    'enclosure', 'weatherproof', 'explosionproof', 'csa', 'certification',
})

UNPUBLISHED_TOPICS = (
    (r'\b(?:operating temperature|temperature range|ambient temperature)\b', 'operating temperature range'),
    (r'\b(?:install|installation|mount(?:ing)?)\b', 'installation instructions'),
    (r'\b(?:noise|quietest|sound level|decibels?)\b', 'noise levels'),
    (r'\b(?:maintenance|service interval|before servicing)\b', 'maintenance interval'),
    (r'\b(?:service life|lifespan|how long .* last|lasts? longest)\b', 'service life'),
    (r'\b(?:efficien(?:cy|t)|efficient)\b', 'efficiency'),
    (r'\bip\s*rating\b', 'IP rating'),
    (r'\bweight\b', 'weight'),
    (r'\b(?:cad|drawing|blueprint)\b', 'CAD drawing'),
    (r'\b(?:wiring|wire diagram)\b', 'wiring diagram'),
    (r'\b(?:4\s*[-–]\s*20\s*ma|control.signal|signal compatibility)\b', 'signal compatibility'),
    (r'\b(?:generator|genset)\b', 'generator operation'),
)


def unpublished_topic(query, *, asked_only=False):
    for pattern, noun in UNPUBLISHED_TOPICS:
        match = re.search(pattern, query, re.I)
        if match:
            if asked_only:
                prefix = query[:match.start()]
                # Site context is not a request for an unsupported capability.
                if not re.search(r'\b(?:what|how|does|do|can|could|is|are|which|tell|show|give|send)\b', prefix, re.I):
                    continue
                if re.search(r'\b(?:beside|near|next to|inside|located at)\b', prefix, re.I):
                    continue
            return noun
    return None


def unsupported_lookup_attribute(query, code, terms):
    """Extract a named attribute of one code; unknown attributes cannot trigger a spec dump."""
    text = re.sub(re.escape(code), '#', query, flags=re.I).strip().rstrip('?! .')
    patterns = (
        r"(?:what(?:'s| is)|tell me)\s+(?:the\s+)?(.+?)\s+(?:of|for|about)\s+#",
        r"(?:send|show|give)\s+me\s+(?:the\s+)?(.+?)\s+(?:for|of)\s+#",
        r"is\s+#\s+compatible\s+with\s+(?:a\s+|the\s+)?(.+)",
        r"can\s+#\s+(.+)",
        r"does\s+#\s+(.+)",
    )
    match = next((found for pattern in patterns if (found := re.search(pattern, text, re.I))), None)
    if not match:
        return None
    attribute = match.group(1).strip().lower()
    if re.search(r'\b(?:full|all|complete|overview)\s+(?:specs?|data|details?)\b', attribute):
        return None
    words = set(re.findall(r'[a-z]+', attribute))
    glossary_names = {word for term in terms for name in [term['label'], *term['aliases']]
                      for word in re.findall(r'[a-z]+', name.lower())}
    if words & (CATALOGUE_ATTRIBUTE_WORDS | glossary_names):
        return None
    return unpublished_topic(attribute) or '__unknown__'


def _edit_distance(left, right):
    if abs(len(left) - len(right)) > 2:
        return 3
    row = list(range(len(right) + 1))
    for i, char in enumerate(left, 1):
        next_row = [i]
        for j, other in enumerate(right, 1):
            next_row.append(min(next_row[-1] + 1, row[j] + 1, row[j - 1] + (char != other)))
        row = next_row
    return row[-1]

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


def grounding_errors(delta, assumptions, texts, semantic=None):
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
            if field in ('service', 'enclosure'):
                from .context_fallback import CONTEXT_LEXICON
                words = CONTEXT_LEXICON.get((field, value), words)
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
    for field in NUMERIC_FIELDS:
        if field in ('supply_voltage_v', 'frequency_hz') or field not in base or delta.get(field) is None:
            continue
        merged[field] = merge_bounds(field, base[field], delta[field])
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


def merge_bounds(field, previous, incoming):
    """Replace only the incoming direction; preserve the opposite end of a range."""
    default = 'gte' if field.startswith('min_') else 'lte'
    direction = lambda item: bound_operator(item, default).startswith('g')
    replaced = {direction(item) for item in bounds(incoming)}
    combined = [item for item in bounds(previous) if direction(item) not in replaced] + bounds(incoming)
    return combined[0] if len(combined) == 1 else [
        {'value': bound_value(item), 'op': bound_operator(item, default)} for item in combined]


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
