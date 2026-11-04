"""Extract measurable user requirements before SQL; disclose anything unrepresentable."""
from __future__ import annotations

from decimal import Decimal
import re

NUMBER = r'\d+(?:[.,]\d+)?'
UNIT = r'k\s*n\s*-?\s*m|n\s*-?\s*m|m\s*n|in\s*-?\s*lb|volts?|v|hz|seconds?|sec|s|amps?|a|watts?|w|%'
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
    value = Decimal(raw.replace(',', '.'))
    return int(value) if value == int(value) else float(value)


def _unit(raw):
    normalized = re.sub(r'[\s-]', '', raw.lower())
    return {'nm': 'nm', 'mn': 'nm', 'knm': 'knm', 'inlb': 'in_lb',
            'v': 'v', 'volt': 'v', 'volts': 'v', 'hz': 'hz',
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


def _operator(prefix, field):
    if re.search(r'\b(?:no more than|at most|up to|max(?:imum)?|below|under|less than|menor\s+a|menor\s+que)\b|≤', prefix):
        return 'lt' if re.search(r'\b(?:below|under|less than|menor\s+a|menor\s+que)\b', prefix) else 'lte'
    if re.search(r'\b(?:more than|above|over)\b', prefix):
        return 'gt'
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
    for match in RANGE.finditer(text):
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
            op = _operator(text[max(0, match.start()-30):match.start()], field)
            found[field] = value if op == 'gte' and field.startswith('min_') else {'value': value, 'op': op}
    for match in POSSIBLE_UNIT.finditer(text):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        token = match.group(2)
        if token in ('phase', 'phases', 'fase', 'fases', 'models', 'model', 'times'):
            continue
        candidates = [canonical for canonical in ('nm', 'knm', 'v', 'volts', 'hz', 's', 'seconds', 'a', 'amps', 'w', 'watts')
                      if _distance_one(token, canonical)]
        if not candidates and match.start(2) > match.end(1):
            continue
        normalized = {_unit(candidate) for candidate in candidates}
        if len(normalized) == 1:
            unit = normalized.pop()
            field = _field(unit, text[max(0, match.start()-32):match.end()+18], context)
            if field:
                amount = _number(match.group(1)) * (1000 if unit == 'knm' else 1)
                if field in ('supply_voltage_v', 'frequency_hz'):
                    found[field] = amount
                else:
                    op = _operator(text[max(0, match.start()-30):match.start()], field)
                    found[field] = amount if op == 'gte' and field.startswith('min_') else {'value': amount, 'op': op}
                continue
        issues.append(f'I could not apply "{match.group(0)}"; please state the unit and limit clearly.')
    updated.update(found)
    return updated, list(dict.fromkeys(issues))


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
