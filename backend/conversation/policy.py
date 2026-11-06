"""Deterministic conversation policy: the code, not the LLM, owns every constraint.

- Part numbers are canonicalised (case, spaces, a missing hyphen) but never completed.
- Every numeric value the model sets must be traceable to the conversation text, or to
  an explicit, user-visible assumption whose phrase the user actually wrote.
- Follow-ups send a delta; the code merges it with the persisted filters.
- Contradictions become specific clarification questions, not validation errors.
"""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from backend.catalog.models import bound_value, bound_operator, bounds

CODE_RE = re.compile(r"^[A-Z0-9]{6}-[A-Z0-9]{8}/A$")
CODE_IN_TEXT = re.compile(r"\b[A-Za-z0-9]{6}-?[A-Za-z0-9]{8}/?[Aa]\b")
PARTIAL_RE = re.compile(r"^[A-Z0-9][A-Z0-9\-/]{2,16}$")

NUMERIC_FIELDS = ("supply_voltage_v", "frequency_hz", "min_torque_nm", "min_torque_in_lb",
                  "min_duty_s4_percent", "min_cycles_per_hour", "min_starts_per_hour",
                  "max_operating_time_s", "max_fla_a", "max_lra_a", "max_motor_power_w")
CATEGORICAL_FIELDS = ("enclosure", "supply_current", "phase_count", "service", "csa_required", "dc_only")
FILTER_FIELDS = CATEGORICAL_FIELDS + NUMERIC_FIELDS


def sort_grounded(sort_key, query):
    """Ignore a model-supplied ranking preference the user never requested."""
    text = query.lower()
    patterns = {
        'fastest': r'\b(?:fast(?:est)?|quick(?:est)?|speed|r[aá]pid[oa])\b',
        'lowest_power': r'\b(?:low(?:est)?|least|less|minimum|menos)\b.*\b(?:power|wattage|watts?|energy|electricity|consumption|potencia|energ[ií]a)\b|\b(?:consum\w*|gasta)\b',
        'highest_torque': r'\bstrongest\b|\b(?:highest|biggest|most|maximi[sz]e|maximum|m[aá]ximo|mayor)\b.*\b(?:torque|par|strength)\b',
        'lowest_current': r'\b(?:low(?:est)?|least|less|minimum|menos)\b.*\b(?:current|fla|amps?|corriente)\b|\b(?:corriente|current|fla)\b.*\b(?:low(?:est)?|least|less|minimum|menos)\b',
    }
    return bool(re.search(patterns.get(sort_key, r'(?!)'), text))

# Deterministic evidence that a categorical value was expressed by the user. Anything
# else needs an explicit assumption (shown to the user) quoting the user's own words.
LEXICON = {
    ("service", "on_off"): ("on/off", "on_off", "on-off", "on off"),
    ("service", "modulating"): ("modulating", "modulation", "modulante"),
    ("enclosure", "explosionproof"): ("explosionproof", "explosion proof", "explosion-proof", "antiexplos",
                                        "a prueba de explosión", "a prueba de explosion"),
    ("enclosure", "weatherproof"): ("weatherproof", "weather proof", "weather-proof"),
    ("supply_current", "DC"): ("dc", "vdc", "direct current", "corriente continua", "battery"),
    # Phases exist only for AC supplies (DC has none), so stated phases ground AC.
    ("supply_current", "AC"): ("ac", "vac", "alternating", "alterna", "mains", "hz", "single phase", "single-phase",
                               "three phase", "three-phase", "1-phase", "3-phase", "monofas", "trifas"),
    ("supply_current", "AC/DC"): ("ac/dc", "ac or dc", "ac-dc", "ac and dc", "ac y dc", "ac o dc",
                                    "dc and ac", "dc y ac", "alterna y continua", "alternating and direct current"),
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
    phase_text = _evidence_text(text)
    for stem, count in (('monofas', 1), ('trifas', 3)):
        if stem in phase_text:
            result['phase_count'] = count
    if not nonhazard_signal(text) and re.search(r'\b(?:classified as hazardous|hazardous (?:area|room|zone)|(?:area|room|zone) is hazardous)\b', text):
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
    if enclosure_withdrawal(text):
        result.pop('enclosure', None)
        notes = [n for n in notes if 'Explosionproof' not in n and 'nonhazardous' not in n]
    if re.search(r'\bopening and closing\b|\bopen close\b', text):
        result['service'] = 'on_off'
    supply = current_requirement(text)
    if supply:
        result.update(supply)
    return result, notes


def enclosure_withdrawal(text):
    text = canonical_enclosures(text)
    withdrawal = bool(re.search(r'\b(?:remove|drop|withdraw|retract|clear|forget|elimina|quita|retira|olvida)\b[^.;!?]*\b(?:enclosure|explosionproof|weatherproof|envolvente|carcasa|antiexplos\w*)\b', text, re.I))
    explicit_constraint = re.search(r'\b(?:restriction|requirement|constraint|filter|restricci[óo]n|requisito|filtro)\b', text, re.I)
    # Removing one enclosure and affirming its replacement is a replacement,
    # not a request to discard the whole categorical field.
    clauses = re.split(r'[.;]|\b(?:and|y|instead|replace|busca)\b', text, flags=re.I)
    if withdrawal and any(re.search(r'\b(?:weatherproof|explosionproof|intemperie)\b', c, re.I)
                          and not re.search(r'\b(?:remove|drop|withdraw|retract|clear|forget|elimina|quita|retira|olvida)\b', c, re.I)
                          for c in clauses[1:]):
        return False
    # Explicitly withdrawing a filter means no enclosure preference even when
    # site context is supplied. A generic site correction retains T10 clearance.
    return withdrawal and (bool(explicit_constraint) or not nonhazard_signal(text))


def current_requirement(text):
    """Ground a stated supply type and distinguish exclusive DC from compatibility."""
    text = text.lower()
    exclusive = re.search(r'\b(?:dc[ -]*only|only\s+(?:dc|direct current)|solo\s+dc|solamente\s+dc|[úu?]nicamente\s+continua)\b', text)
    excluded_dual = re.search(r'\b(?:exclude|excluded|excluding)\b[^.!?;]*\bac/dc\b|\bac/dc\b[^.!?;]*\bexcluded\b', text)
    if excluded_dual:
        return {'supply_current': 'DC', 'dc_only': True}
    exclusive = exclusive or re.search(r'\b(?:exclusivamente|solamente)\s+(?:de\s+)?(?:corriente\s+)?continua\b|\bcorriente continua solamente\b', text)
    if exclusive and not re.search(r'\b(?:or|o)\b', text):
        return {'supply_current': 'DC', 'dc_only': True}
    # Compatibility includes dual-rated units; mentioning AC/DC does not require
    # every result to be dual-rated. Strip that label before reading the supply.
    dual = r'\bac\s*[/\-]\s*dc\b'
    without_dual = re.sub(dual, '', text)
    dual_only = re.search(r'\bonly\s+' + dual + '|' + dual + r'\s+(?:(?:units|models|entries)\s+)?only\b', text)
    inclusive_dual = re.search(
        r'\b(?:including|include|also|as well as|incluye|incluyendo|tambi[eé]n)\b[^.!?;]*' + dual +
        r'|\bdc(?:[ -]only)?\s+(?:or|and|o|y)\s+(?:dual\s+)?' + dual +
        '|' + dual + r'\s+(?:or|and|o|y)\s+dc\b|\bboth\b[^.!?;]*' + dual, text)
    if (inclusive_dual and not dual_only
            and re.search(r'\b(?:v?dc|direct current|corriente continua)\b', without_dual)
            and not re.search(r'\b(?:ac|vac)\b', without_dual)):
        return {'supply_current': 'DC', 'dc_only': False}
    if re.search(r'\bvac\s*/\s*vdc\b', text) or _dual_current(text):
        return {'supply_current': 'AC/DC', 'dc_only': False}
    if re.search(r'(?<![a-z])v?dc\b|\bdirect current\b', text) and not re.search(r'\b(?:ac|vac)\b', text):
        return {'supply_current': 'DC', **({'dc_only': True} if exclusive else {})}
    if re.search(r'(?<![a-z])vac\b', text) and not re.search(r'\bvdc\b', text):
        return {'supply_current': 'AC', 'dc_only': False}
    return {}


NONHAZARD_RE = re.compile(
    r'\b(?:away from (?:all|anything) flammable|nonflammable|not hazardous|non[ -]?hazardous|not a (?:classified|hazardous) (?:area|zone)|'
    r'outside (?:the )?(?:classified|hazardous) (?:area|zone)|'
    r'(?:safe|normal|ordinary|regular) (?:area|room|zone)|area is safe|'
    r'(?:zona|area|sala) (?:segura|normal|ordinaria|no peligrosa)|'
    r'(?:no|not|nothing|without|sin)\s+(?:(?:any|longer|stored|materials?|materiales|sustancias|hay)\s+){0,2}'
    r'(?:gas|fuel|solvents?|flammable|explosive|hazardous|combustibles?|inflamables?|explosiv[oa]s?)'
    r'(?:\s+(?:materials?|gases|gas|vapou?rs?|liquids?))?)\b', re.I)


def nonhazard_signal(text):
    from .context_fallback import HAZARD_RE
    # A negated hazard does not cancel a different affirmative hazard nearby.
    return bool(NONHAZARD_RE.search(text)) and not HAZARD_RE.search(NONHAZARD_RE.sub(' ', text))


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
                if not re.search(r'\b(?:no|not|sin|forget|drop|remove|withdraw|retract|olvida|quita|elimina|retira|any)\s+(?:\w+\s+){0,2}$', prefix, re.I):
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
    'enclosure': r'enclosure|explosionproof|weatherproof|hazardous|classified|envolvente|carcasa',
    'supply_voltage_v': r'voltage|volts?|voltaje|tensi[oó]n|\d+\s*v\b',
    'supply_current': r'(?:supply )?current|corriente|ac|dc',
    'service': r'service|servicio|on\s*/?\s*off|modulating|modulante',
    'phase_count': r'phases?|fases?|trif[aá?]sic[oa]|monof[aá?]sic[oa]',
    'frequency_hz': r'frequency|frecuencia|hz',
    'min_torque_nm': r'torque|\bnm\b',
    'min_torque_in_lb': r'torque|in\s*-?\s*lb',
    'max_fla_a': r'fla|full.load current',
    'max_lra_a': r'lra|locked.rotor current',
    'max_motor_power_w': r'motor power|wattage',
    'min_duty_s4_percent': r'duty|s4',
    'min_cycles_per_hour': r'cycles?|ciclos?',
    'min_starts_per_hour': r'starts?|arranques?',
    'max_operating_time_s': r'operating time|tiempo',
    'csa_required': r'csa|certification|certificaci[oó]n',
}


REMOVAL_PREFIX = re.compile(
    r'\b(?:forget|drop|remove|withdraw|retract|clear|without|sin|ya no|elimina|quita|olvida|no|not|'
    r'rather than|instead of|en vez de)\b', re.I)


def _affirmed_fields(text):
    """Distinguish an affirmed value from a negated alternative or a field name.

    In "DC, not AC" the negative clause must not erase the affirmative one.
    "Any DC actuator" also affirms DC; "any current" supplies no value.
    """
    from .context_fallback import CONTEXT_LEXICON
    from .requirement_coverage import apply
    fields = set()
    clauses = re.split(r'[,;!?]|(?<!\d)\.(?!\d)|\b(?:but|pero|sino|only|solo|solamente)\b|'
                       r'\b(?:and|y)\s+(?=use\b|need\b|want\b|usa\b|necesito\b|quiero\b)', text, flags=re.I)
    for clause in clauses:
        if NO_PREFERENCE.search(clause):
            continue
        for key in set(LEXICON) | set(CONTEXT_LEXICON):
            field, _ = key
            for word in LEXICON.get(key, ()) + CONTEXT_LEXICON.get(key, ()):
                # Short electrical labels need whole tokens; long stems follow
                # the same bounded vocabulary as grounding_errors.
                pattern = (r'(?<![a-z])' + re.escape(word) + r'(?![a-z])'
                           if len(word) <= 3 else re.escape(word))
                for match in re.finditer(pattern, clause, re.I):
                    denied_after = re.search(r'\b(?:no longer (?:needed|required)|ya no|no (?:es necesario|importa))\b',
                                             clause[match.end():match.end() + 45])
                    if not REMOVAL_PREFIX.search(clause[:match.start()]) and not denied_after:
                        fields.add(field)
        if not REMOVAL_PREFIX.search(clause):
            quantities, _ = apply(clause, {})
            fields.update(quantities)
    return fields


def removed_fields(query, pending_questions=()):
    """Map an explicit negation to filter keys, independent of model output."""
    text = query.lower()
    text = re.sub(r'\bno\s*[, ]\s*sorry\b', 'correction', text)
    text = re.sub(r'\b(?:no more than|not more than|no less than|no m[aá?]s de)\b', 'bound', text)
    affirmed = _affirmed_fields(text)
    if re.search(r'\b(?:clear|remove|drop|forget)\s+(?:all|every)(?:\s+\w+)?\s+(?:filters?|requirements?|constraints?)\b|'
                 r'\b(?:quita|elimina|borra|olvida)\s+tod[oa]s?\s+(?:(?:los|las)\s+)?(?:filtros|requisitos|restricciones)\b', text):
        return set(FILTER_FIELDS) - affirmed
    removed = set()
    for clause in context_clauses(text):
        for field, words in REMOVE_WORDS.items():
            if re.search(r'\b(?:forget|drop|remove|withdraw|retract|clear|without|sin|ya no|elimina|quita|olvida|no|not)\b(?:\W+\w+){0,3}?\W+(?:' + words + r')\b', clause) or \
                    re.search(r'\b(?:any|cualquier)\s+(?:' + words + r')\b', clause) or \
                    (NO_PREFERENCE.search(clause) and re.search(r'\b(?:' + words + r')\b', clause)) or \
                    re.search(r'\b(?:' + words + r')\b.{0,35}\b(?:no longer (?:needed|required)|ya no|no (?:es necesario|importa))\b', clause) or \
                    re.search(r'\b(?:' + words + r')\b.{0,20}\bany(?:thing)?\b', clause):
                removed.add(field)
    if NO_PREFERENCE.search(text) and not removed and pending_questions:
        removed.add(pending_questions[0]['id'])
    if nonhazard_signal(text):
        removed.add('enclosure')
    return removed - affirmed


CATALOGUE_ATTRIBUTE_WORDS = frozenset({
    'spec', 'specs', 'specification', 'specifications', 'data', 'detail', 'details',
    'torque', 'duty', 'cycle', 'cycles', 'starts', 'hour', 'time', 'speed', 'fast',
    'fla', 'lra', 'current', 'power', 'voltage', 'supply', 'phase', 'frequency',
    'enclosure', 'weatherproof', 'explosionproof', 'csa', 'certification',
})

UNPUBLISHED_TOPICS = (
    (r'\b(?:position feedback(?: output)?|feedback output)\b', 'position feedback output'),
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


def recommendation_request(query):
    """Selection intent, including buying advice; no catalogue-wide expansion."""
    text = query.lower()
    if re.search(r'\b(?:compare|compara|comparar)\b', text):
        return False
    return bool(re.search(
        r'\b(?:recommend\w*|recomiend\w*|recomend\w*|better|best|mejor|mejores)\b|'
        r'\bwhich\b.{0,45}\b(?:buy|purchase|for me|for low|should i choose)\b|'
        r'\b(?:cu[aá]l|qu[eé])\b.{0,35}\b(?:comprar|compro|conviene|para m[ií])\b', text))


def purchase_request(query):
    # A selection question does not ask us to place an order. Explicit commerce
    # clauses still keep their limitation, even when combined with a recommendation.
    if recommendation_request(query) and not re.search(
            r'\b(?:orders?|ordering|delivery|shipping|price|prices|pedido|entrega|precio)\b', query, re.I):
        return False
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
    corpus = _evidence_text(" ".join(texts))
    numbers = numbers_in(texts)
    assumed = {a["field"] for a in assumptions if _evidence_text(a["user_phrase"]) in corpus}
    errors = []
    for field, value in delta.items():
        if value is None or field in assumed:
            continue
        if field in NUMERIC_FIELDS:
            if any(Decimal(str(bound_value(item))) not in numbers for item in bounds(value)):
                errors.append(field)
        elif field in CATEGORICAL_FIELDS:
            if field == 'dc_only':
                if value and not current_requirement(corpus).get('dc_only'):
                    errors.append(field)
                continue
            if field == "csa_required" and value is False:
                continue
            if field == 'supply_current' and value == 'AC/DC' and _dual_current(corpus):
                continue
            words = LEXICON.get((field, value), ())
            if field in ('service', 'enclosure'):
                from .context_fallback import CONTEXT_LEXICON
                words = words + CONTEXT_LEXICON.get((field, value), ())
            evidence = corpus
            # Long, unambiguous domain labels may have a small spelling error;
            # short electrical tokens (AC/DC) must always match exactly.
            if field in ('service', 'enclosure'):
                labels = ('weatherproof', 'explosionproof', 'modulating', 'modulante', 'exterior', 'intemperie')
                for token in re.findall(r'\b[a-z]{6,}\b', corpus):
                    candidates = [label for label in labels if _edit_distance(token, label) <= (2 if len(label) >= 10 else 1)]
                    if len(candidates) == 1:
                        evidence = re.sub(r'\b' + re.escape(token) + r'\b', candidates[0], evidence)
            if not any(_has_word(evidence, _evidence_text(w)) for w in words):
                errors.append(field)
    return errors


def _has_word(corpus, word):
    if len(word) <= 3:  # "ac", "dc", "hz", "csa": whole word only
        return (re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", corpus) is not None
                or re.search(rf"\dv{re.escape(word)}(?![a-z])", corpus) is not None)
    return word in corpus


def _evidence_text(text):
    text = ''.join(c for c in unicodedata.normalize('NFKD', text).lower() if not unicodedata.combining(c))
    text = re.sub(r'\b(monof|trif)\?sic', r'\1asic', text)
    return ' '.join(text.split())


def removed_bound_sides(query, fields):
    """A named floor/ceiling withdrawal removes one direction of a range."""
    result = {}
    bounded = [field for field in fields if field.startswith(('min_', 'max_'))]
    for clause in re.split(r'[.;]|\b(?:but|keep|retain|retaining)\b', query, flags=re.I):
        if not re.search(r'\b(?:remove|drop|withdraw|clear|forget|quita|elimina)\b', clause, re.I):
            continue
        lower = bool(re.search(r'\b(?:minimum|lower|floor)\b', clause, re.I))
        upper = bool(re.search(r'\b(?:maximum|upper|ceiling)\b', clause, re.I))
        if lower == upper:
            continue
        for field in bounded:
            if (re.search(REMOVE_WORDS.get(field, r'(?!)'), clause, re.I)
                    or len(bounded) == 1 and re.search(r'\b(?:bound|limit|floor|ceiling)\b', clause, re.I)):
                result[field] = 'g' if lower else 'l'
    return result


def _dual_current(text):
    ac = r'(?:ac|alternating(?: current)?|(?:corriente )?alterna)'
    dc = r'(?:dc|direct(?: current)?|(?:corriente )?continua)'
    join = r'\s*(?:[/&+]|and|or|y|o|as well as)\s*'
    return bool(re.search(r'\b(?:' + ac + join + dc + '|' + dc + join + ac + r')\b', text))


def invalid_assumptions(assumptions, texts):
    corpus = _evidence_text(" ".join(texts))
    return [a for a in assumptions if _evidence_text(a["user_phrase"]) not in corpus]


def replaced_fields(query, delta):
    """Corrections replace only quantities in their clause; additions retain a range.

    This signal comes from user text, never an ungrounded model flag. Keep it shared
    by filter state and the independent quantity ledger so their deltas agree.
    """
    from .requirement_coverage import apply
    correction = r'\b(?:make (?:that|it)|change (?:that|it) to|i meant|actually|instead|rather|no\s*[, ]\s*sorry|sorry|correction|correct(?:ion)?|revers(?:e|ed)|replace|quise decir|queria decir|rectifico|corrijo|en vez de|mejor dicho)\b'
    fields = set()
    for clause in re.split(r';|(?<!\d)\.(?!\d)|\b(?:but|pero)\b|\b(?:and|y)\s+(?=add\b|keep\b|also\b|conserva\b|agrega\b)', query, flags=re.I):
        if re.search(correction, clause, re.I):
            evidence, _ = apply(clause, {}, delta)
            fields.update(field for field in evidence if field in delta)
    return fields


def merge_filters(previous, delta, *, refine, remove, more, query=''):
    """Return (merged, notes). Only the delta is the model's; carried values are the code's."""
    notes = []
    replacements = replaced_fields(query, delta)
    refine = refine or bool(remove)  # removing a requirement only makes sense on the previous search
    base = {k: v for k, v in (previous or {}).items() if k in FILTER_FIELDS and v is not None} if (refine or more) else {}
    merged = dict(base)
    merged.update({k: v for k, v in delta.items() if v is not None})
    for field in NUMERIC_FIELDS:
        if field in ('supply_voltage_v', 'frequency_hz') or field not in base or delta.get(field) is None:
            continue
        merged[field] = merge_bounds(field, base[field], delta[field], replace=field in replacements)
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


def merge_bounds(field, previous, incoming, *, replace=False):
    """Replace only the incoming direction; preserve the opposite end of a range."""
    if replace:
        return incoming
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
    "dc_only": "DC-only models",
}


def _label(field):
    return LABELS.get(field, field)


def describe(filters):
    parts = []
    for field in FILTER_FIELDS:
        value = filters.get(field)
        if value is None or (field in ("csa_required", "dc_only") and not value):
            continue
        if isinstance(value, list):
            parts.append(' and '.join(describe({field: item}) for item in value))
            continue
        text = {
            "service": lambda v: "On/Off service" if v == "on_off" else "Modulating service",
            "enclosure": lambda v: str(v).capitalize(),
            "supply_voltage_v": lambda v: f"{v} V",
            "supply_current": lambda v: v,
            "dc_only": lambda v: "DC-only models",
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
