"""Extract measurable user requirements before SQL; disclose anything unrepresentable."""
from __future__ import annotations

from decimal import Decimal
import re

NUMBER = r'(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:[.,]\d+)?)'
UNIT = r'k\s*n\s*-?\s*m|n\s*-?\s*m|m\s*n|in\s*-?\s*lbs?|volts?|v(?:ac|dc)?|hz|seconds?|sec|s|amps?|a|watts?|w|%'
RANGE = re.compile(rf'(?<![\w-])(?:between\s+)?({NUMBER})\s*(?:to|and|–|-)\s*({NUMBER})\s*({UNIT})(?![a-z])', re.I)
SINGLE = re.compile(rf'(?<![\w-])({NUMBER})\s*({UNIT})(?![a-z])', re.I)
POSSIBLE_UNIT = re.compile(rf'(?<![\w-])({NUMBER})\s*([a-z]{{1,8}})(?![\w/-])', re.I)


def _distance_one(left, right):
    if left == right:
        return True
    if abs(len(left) - len(right)) > 1:
        return False
    for index in range(max(len(left), len(right))):
        if index >= min(len(left), len(right)) or left[index] != right[index]:
            return (left[index + 1:] == right[index:] or left[index:] == right[index + 1:]
                    or left[index + 1:] == right[index + 1:])
    return True


def _number(raw):
    value = Decimal(raw.replace(',', '') if re.fullmatch(r'\d{1,3}(?:,\d{3})+(?:\.\d+)?', raw)
                    else raw.replace(',', '.'))
    return int(value) if value == int(value) else float(value)


def _unit(raw):
    normalized = re.sub(r'[\s-]', '', raw.lower())
    return {'nm': 'nm', 'mn': 'nm', 'knm': 'knm', 'inlb': 'in_lb', 'inlbs': 'in_lb',
            'v': 'v', 'vac': 'v', 'vdc': 'v', 'volt': 'v', 'volts': 'v', 'hz': 'hz',
            's': 's', 'sec': 's', 'second': 's', 'seconds': 's',
            'a': 'a', 'amp': 'a', 'amps': 'a',
            'w': 'w', 'watt': 'w', 'watts': 'w', '%': '%'}.get(normalized)


def _field(unit, nearby, context=None):
    if unit in ('nm', 'knm'):
        return 'min_torque_nm'
    if unit == 'in_lb':
        return 'min_torque_in_lb'
    if unit == 'v':
        return 'supply_voltage_v'
    if unit == 'hz':
        return 'frequency_hz'
    if unit == 'w':
        return 'max_motor_power_w'
    if unit == '%':
        return 'min_duty_s4_percent' if re.search(r'\bduty\b|\bs4\b', nearby) else None
    if unit == 'a':
        if re.search(r'\b(?:lra|locked rotor|starting current|inrush)\b', nearby):
            return 'max_lra_a'
        if re.search(r'\b(?:fla|full.load|current|draw|amps?)\b', nearby):
            return 'max_fla_a'
        relevant = [field for field in ('max_fla_a', 'max_lra_a') if (context or {}).get(field) is not None]
        if len(relevant) == 1:
            return relevant[0]
        return None
    if unit == 's':
        return ('max_operating_time_s' if re.search(r'\b(?:operating time|time|speed|faster|seconds?)\b', nearby)
                or (context or {}).get('max_operating_time_s') is not None else None)
    return None


def _operator(prefix, field, suffix=''):
    # The nearest operator belongs to this quantity. A trailing "maximum" is
    # common in additions; inspecting only the prefix reversed that constraint.
    operators = (
        ('lte', r'no more than|not more than|at most|up to|max(?:imum)?|upper(?:\s+\w+){0,2}\s+limit|hasta|m[aá?]xim[oa]|no m[aá?]s de|<=|≤'),
        ('gte', r'at least|no less than|not less than|min(?:imum)?|lower(?:\s+\w+){0,2}\s+limit|al menos|m[ií?]nim[oa]|como poco|>=|≥'),
        ('lt', r'below|under|less than|menor\s+(?:a|que)|menos de|por debajo de|<'),
        ('gt', r'more than|above|over|mayor\s+(?:a|que)|m[aá?]s de|por encima de|>'),
    )
    pattern = '|'.join(rf'(?P<{op}>(?<!\w)(?:{words})(?!\w))' for op, words in operators)
    # Consume each phrase once: "no more than" must not also match "more than".
    matches = list(re.finditer(pattern, prefix, re.I))
    trailing = re.match(r'^\s*(?:as\s+(?:a\s+)?)?(maximum|minimum|max|min|m[aá?]xim[oa]|m[ií?]nim[oa])\b', suffix, re.I)
    if trailing:
        return 'lte' if re.match(r'max|m[aá?]x', trailing.group(1), re.I) else 'gte'
    if matches:
        return matches[-1].lastgroup
    return 'gte' if field.startswith('min_') else 'lte'


def apply(query, filters, context=None):
    """Return an updated filter delta and plain-language disclosures.

    The parser prefers the user's written quantity over any model argument. Ambiguous
    units are reported instead of turning into a guess or silently vanishing.
    """
    updated, issues = dict(filters), []
    text = query.lower()
    occupied = []
    found = {}
    named_rates = re.compile(rf'\b(cycles?|ciclos?|starts?|arranques?)\s*(>=|<=|>|<|at least|at most|minimum|maximum)?\s*({NUMBER})\s*(?:/\s*h(?:our)?|per\s+hour|por\s+hora)\b', re.I)
    for match in named_rates.finditer(text):
        field = 'min_cycles_per_hour' if match.group(1).startswith(('cycl', 'cicl')) else 'min_starts_per_hour'
        op = _operator(match.group(2) or '', field)
        found[field] = {'value': _number(match.group(3)), 'op': op}
        occupied.append(match.span())
    rates = re.compile(rf'(?<![\w-])(?:between\s+|entre\s+)?({NUMBER})(?:\s*(?:to|and|a|y|–|-)\s*({NUMBER}))?\s*(cycles?|ciclos?|starts?|arranques?)\s*(?:/\s*h(?:our)?|per\s+hour|an?\s+hour|por\s+hora)\b', re.I)
    for match in rates.finditer(text):
        field = 'min_cycles_per_hour' if match.group(3).startswith(('cycl', 'cicl')) else 'min_starts_per_hour'
        value = _number(match.group(1))
        op = _operator(text[max(0, match.start()-60):match.start()], field, text[match.end():])
        limits = ([{'value': value, 'op': 'gte'}, {'value': _number(match.group(2)), 'op': 'lte'}]
                  if match.group(2) else [value if op == 'gte' else {'value': value, 'op': op}])
        previous = found.get(field, [])
        previous = previous if isinstance(previous, list) else [previous]
        limits = previous + limits
        found[field] = limits[0] if len(limits) == 1 else limits
        occupied.append(match.span())
    for match in RANGE.finditer(text):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        unit = _unit(match.group(3))
        field = _field(unit, text[max(0, match.start()-32):match.end()+18], context)
        occupied.append(match.span())
        if field not in ('min_torque_nm', 'min_torque_in_lb', 'min_duty_s4_percent',
                         'max_operating_time_s', 'max_fla_a', 'max_lra_a', 'max_motor_power_w'):
            issues.append(f'I couldn\'t apply "{query[match.start():match.end()]}" as one filter; specify one value.')
            continue
        factor = 1000 if unit == 'knm' else 1
        lower, upper = _number(match.group(1)) * factor, _number(match.group(2)) * factor
        found[field] = [{'value': lower, 'op': 'gte'}, {'value': upper, 'op': 'lte'}]
    for match in SINGLE.finditer(text):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        occupied.append(match.span())
        unit = _unit(match.group(2))
        nearby = text[max(0, match.start()-32):match.end()+18]
        field = _field(unit, nearby, context)
        phrase = query[max(0, match.start()-8):match.end()].strip()
        if field is None:
            if unit == '%' and re.search(r'\b(?:open|position|valve)\b', nearby):
                issues.append(f'Modulating service can hold intermediate positions, but I could not filter by {match.group(0)} position.')
                continue
            issues.append(f'I couldn\'t apply "{phrase}" — specify the catalogue field and limit.')
            continue
        value = _number(match.group(1)) * (1000 if unit == 'knm' else 1)
        if field in ('supply_voltage_v', 'frequency_hz'):
            previous = found.get(field)
            if previous is not None and previous != value:
                found.pop(field, None)
                issues.append(f'I couldn\'t apply both stated {"voltages" if unit == "v" else "frequencies"}; choose one.')
            elif not any('both stated' in issue for issue in issues):
                found[field] = value
        else:
            prefix_start = max((end for start, end in occupied if end <= match.start()), default=0)
            op = _operator(text[max(prefix_start, match.start()-60):match.start()], field, text[match.end():])
            limit = value if op == 'gte' and field.startswith('min_') else {'value': value, 'op': op}
            previous = found.get(field)
            found[field] = (previous if isinstance(previous, list) else [previous]) + [limit] if previous is not None else limit
    for match in POSSIBLE_UNIT.finditer(text):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        token = match.group(2)
        if token in ('wp', 'xp', 'phase', 'phases', 'fase', 'fases', 'models', 'model', 'times'):
            continue
        candidates = [canonical for canonical in ('nm', 'knm', 'v', 'volts', 'hz', 's', 'seconds', 'a', 'amps', 'w', 'watts')
                      if _distance_one(token, canonical)]
        if not candidates and match.start(2) > match.end(1):
            continue
        normalized = {_unit(candidate) for candidate in candidates}
        # Only attached unit typos are recoverable; a separate word is not a unit.
        if len(normalized) == 1 and match.start(2) == match.end(1):
            unit = normalized.pop()
            field = _field(unit, text[max(0, match.start()-32):match.end()+18], context)
            if field:
                amount = _number(match.group(1)) * (1000 if unit == 'knm' else 1)
                if field in ('supply_voltage_v', 'frequency_hz'):
                    found[field] = amount
                else:
                    op = _operator(text[max(0, match.start()-60):match.start()], field, text[match.end():])
                    found[field] = amount if op == 'gte' and field.startswith('min_') else {'value': amount, 'op': op}
                continue
        if match.start(2) == match.end(1):
            issues.append(f'I could not apply "{match.group(0)}"; please state the unit and limit clearly.')
    # Bare supply shorthand is restricted to the catalogue's published voltages.
    bare = [int(m.group()) for m in re.finditer(r'(?<![\w./-])(?:24|110|220)(?![\w./-])', text)
            if not any(start <= m.start() < end for start, end in occupied)]
    if len(set(bare)) == 1 and 'supply_voltage_v' not in found:
        found['supply_voltage_v'] = bare[0]
    updated.update(found)
    return updated, list(dict.fromkeys(issues))


def unsupported(query, filters):
    """Reverse coverage: each numeric argument needs compatible quantity evidence.

    Operators are handled by apply/merge; a repeated number in another physical
    dimension never licenses a filter. Structured UI values are validated separately.
    """
    from backend.catalog.models import bound_value, bounds
    from .policy import NUMERIC_FIELDS
    evidence, _ = apply(query, {}, filters)
    for kind in ('cycles', 'starts'):
        values = re.findall(rf'({NUMBER})\s*{kind}\s*(?:/\s*h(?:our)?|per\s+hour|an?\s+hour)', query, re.I)
        if values and f'min_{kind}_per_hour' not in evidence:
            evidence[f'min_{kind}_per_hour'] = [_number(v) for v in values]
    rejected = []
    for field, value in filters.items():
        if field not in NUMERIC_FIELDS or value is None:
            continue
        published = {Decimal(str(bound_value(v))) for v in bounds(evidence[field])} if field in evidence else set()
        if any(Decimal(str(bound_value(v))) not in published for v in bounds(value)):
            rejected.append(field)
    return rejected


def missing(claims, filters):
    """Independent check that a carried user quantity survived filter merging."""
    from backend.catalog.models import bound_operator, bound_value, bounds
    omitted = []
    for field, expected in claims.items():
        actual = filters.get(field)
        if actual is None:
            omitted.append(field)
            continue
        if field in ('supply_voltage_v', 'frequency_hz'):
            if Decimal(str(actual)) != Decimal(str(expected)):
                omitted.append(field)
            continue
        wanted = [(Decimal(str(bound_value(item))), bound_operator(item, 'gte' if field.startswith('min_') else 'lte'))
                  for item in bounds(expected)]
        present = [(Decimal(str(bound_value(item))), bound_operator(item, 'gte' if field.startswith('min_') else 'lte'))
                   for item in bounds(actual)]
        if not all(item in present for item in wanted):
            omitted.append(field)
    return omitted
