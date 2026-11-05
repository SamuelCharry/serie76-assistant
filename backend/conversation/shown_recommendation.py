"""Recommendations over a frozen visible set; requirements and verdicts are code-owned."""
from decimal import Decimal
import re

from backend.catalog.models import SearchFilters, bounds, bound_operator, bound_value
from . import integrity, policy, quality, ranking, requirement_coverage
from .rendering import _num


PRIORITIES = (
    ('lowest_fla', r'\b(?:low(?:est)? current|less current|low(?:est)? fla|menor corriente|menos corriente|bajo consumo de corriente)\b'),
    ('fastest', r'\b(?:fast(?:est)?|quick(?:est)?|r[aá]pid[oa]|velocidad)\b'),
    ('most_torque', r'\b(?:strong(?:est|er)?|most torque|highest torque|m[aá]s torque|mayor torque|fuerte)\b'),
    ('lowest_power', r'\b(?:low(?:est)? power|low(?:est)? motor power|less power|menor potencia|menos potencia|cheap(?:est)?)\b'),
    ('most_duty', r'\b(?:high(?:est)? duty|most duty|best duty|better duty|(?:for|prefer|prioriti[sz]e) duty|mayor duty|mayor ciclo de trabajo)\b'),
    ('most_cycles', r'\b(?:most cycles|high(?:est)? cycles|(?:for|prefer|prioriti[sz]e) cycles|m[aá]s ciclos|mayor cantidad de ciclos)\b'),
)
HINTS = {'lowest_current': 'lowest_fla', 'fastest': 'fastest',
         'highest_torque': 'most_torque', 'lowest_power': 'lowest_power'}
LABELS = dict(ranking.LABELS, most_duty='highest duty S4', most_cycles='most On/Off cycles')
UNITS = {'torque_nm': 'Nm', 'torque_in_lb': 'in-lb', 'duty_s4_percent': '%',
         'cycles_per_hour': 'cycles/h', 'starts_per_hour': 'starts/h',
         'operating_time_s': 's', 'fla_a': 'A', 'lra_a': 'A'}
METRIC_LABELS = {'torque_nm': 'torque', 'torque_in_lb': 'torque', 'duty_s4_percent': 'duty S4',
                 'cycles_per_hour': 'cycles', 'starts_per_hour': 'starts',
                 'operating_time_s': 'Operating time', 'fla_a': 'FLA', 'lra_a': 'LRA'}
SERVICE_LABELS = {'on_off': 'On/Off', 'modulating': 'Modulating', 'shared': 'Shared'}


def requirements(query, previous):
    inferred, notes = policy.colloquial_requirements(query)
    written, issues = requirement_coverage.apply(query, {}, dict(previous, **inferred))
    inferred.update(written)
    merged, merge_notes = policy.merge_filters(previous, inferred, refine=True,
                                              remove=policy.removed_fields(query), more=False)
    # Every quantity must be represented before any candidate can be recommended.
    if requirement_coverage.missing(written, merged):
        issues.append('Please restate the limits; I could not preserve every stated quantity.')
    return merged, notes + merge_notes, issues


def priority(query, previous='closest_torque', hint=()):
    choices = [(m.start(), name) for name, pattern in PRIORITIES
               if (m := re.search(pattern, query, re.I))]
    if choices:
        return min(choices)[1]
    return next((HINTS[h] for h in hint if h in HINTS),
                previous if previous in LABELS else 'closest_torque')


def measured(product, by, filters):
    """Value and labelled scope used by the stable ranking (no invented frequency)."""
    if by == 'lowest_power':
        return product['measurements'].get('motor_power_w'), 'Motor power', 'W'
    if by in ('closest_torque', 'most_torque'):
        found = ranking.qualifying_torques(product, filters)
        if found:
            value = ranking.measurement(product, 'torque', filters)
            label = next(label for label, amount in found if amount == value)
            return value, label, ranking.torque_unit(filters)
        return None, 'Torque', ranking.torque_unit(filters)
    if by in ('most_duty', 'most_cycles'):
        column = 'duty_s4_percent' if by == 'most_duty' else 'cycles_per_hour'
        service = filters.get('service') or ('on_off' if by == 'most_cycles' else None)
        found = [(row[column], SERVICE_LABELS[row['service']] + ' ' + METRIC_LABELS[column])
                 for row in product.get('services', [])
                 if (service is None or row['service'] in (service, 'shared')) and row.get(column) is not None]
        value, label = min(found) if found else (None, METRIC_LABELS[column])
        return value, label, UNITS[column]
    stem = {'lowest_fla': 'fla', 'lowest_lra': 'lra', 'fastest': 'operating_time'}[by]
    unit = 'A' if stem in ('fla', 'lra') else 's'
    field = stem + '_' + unit.lower()
    found = [(row[field], row.get('frequency_hz')) for row in product.get('frequencies', [])
             if row.get(field) is not None and
             (not filters.get('frequency_hz') or row.get('frequency_hz') == filters['frequency_hz'])]
    value, hz = min(found, key=lambda item: (item[0], item[1] or 0)) if found else (None, None)
    label = METRIC_LABELS[field] + (f' at {hz} Hz' if hz else ' (frequency not specified)')
    return value, label, unit


def criterion(filters, by):
    if by in ('most_duty', 'most_cycles'):
        return LABELS[by] + ', then lowest FLA, then shortest operating time, then part number'
    text = ranking.ranked_by(filters, by)
    if by == 'closest_torque' and any(filters.get(f) is not None for f in ('min_torque_nm', 'min_torque_in_lb')):
        text += ', then shortest operating time'
    return text + ', then part number'


def ordered(products, filters, by):
    return ranking.rank(products, filters, by)


def failures(product, filters):
    """Explain exclusions independently of sorting; return distance for nearest-only prose."""
    reasons, distance = [], Decimal(0)
    if product.get('data_status') != 'reported':
        return ['The required measurements are not published'], Decimal('Infinity')
    for field in policy.FILTER_FIELDS:
        wanted = filters.get(field)
        if wanted is None or wanted is False:
            continue
        scope = ({'service': filters.get('service')} if field in integrity.SERVICE_FIELDS else
                 {'frequency_hz': filters.get('frequency_hz')} if field in integrity.FREQUENCY_FIELDS else {})
        scoped = SearchFilters.model_validate(dict(scope, **{field: wanted}))
        if integrity.satisfies(product, scoped):
            continue
        if field in integrity.SERVICE_FIELDS or field in integrity.FREQUENCY_FIELDS or field == 'max_motor_power_w':
            if field == 'max_motor_power_w':
                values = [(product['measurements'].get('motor_power_w'), 'Motor power', 'W')]
            else:
                service = field in integrity.SERVICE_FIELDS
                column = (integrity.SERVICE_FIELDS if service else integrity.FREQUENCY_FIELDS)[field]
                rows = product.get('services' if service else 'frequencies', [])
                rows = [r for r in rows if (not scope.get('service') or r['service'] in (scope['service'], 'shared'))
                        and (not scope.get('frequency_hz') or r.get('frequency_hz') == scope['frequency_hz'])]
                values = [(r.get(column),
                           SERVICE_LABELS[r['service']] + ' ' + METRIC_LABELS[column] if service else
                           METRIC_LABELS[column] + (f" at {r['frequency_hz']} Hz" if r.get('frequency_hz') else ' (frequency not specified)'),
                           UNITS[column]) for r in rows]
            values = [v for v in values if v[0] is not None]
            if not values:
                reasons.append(policy.LABELS[field].capitalize() + ' is not published for the required scope')
                distance += 1
                continue
            for bound in bounds(wanted):
                op = bound_operator(bound, 'gte' if field.startswith('min_') else 'lte')
                target = Decimal(str(bound_value(bound)))
                if any(integrity._passes(v, bound, 'gte' if field.startswith('min_') else 'lte') for v, _, _ in values):
                    continue
                value, label, unit = min(values, key=lambda v: abs(Decimal(str(v[0])) - target))
                sign = {'gte': '<', 'gt': '<=', 'lte': '>', 'lt': '>='}[op]
                reasons.append(f'{label} {_num(value)} {unit} {sign} {_num(target)} {unit}')
                distance += abs(Decimal(str(value)) - target) / max(abs(target), 1)
        else:
            label = policy.LABELS[field].capitalize()
            actual = product.get(field)
            if field == 'service':
                actual = ', '.join(SERVICE_LABELS[r['service']] for r in product.get('services', [])) or 'not published'
                wanted = SERVICE_LABELS.get(wanted, wanted)
            elif field == 'frequency_hz':
                actual = ', '.join(str(r['frequency_hz']) for r in product.get('frequencies', []) if r.get('frequency_hz')) or 'not published'
                label += ' (Hz)'
            elif field == 'supply_voltage_v':
                actual, wanted = f'{_num(actual)} V', f'{_num(wanted)} V'
            elif field == 'csa_required':
                actual, wanted = product.get('certification', {}).get('csa_status', 'not published').replace('_', ' '), 'CSA certification'
            elif field == 'enclosure':
                actual, wanted = str(actual).capitalize(), str(wanted).capitalize()
            reasons.append(f'{label} {actual} does not meet {wanted}'.replace('on_off', 'On/Off'))
            distance += 1
    if not reasons and not integrity.satisfies(product, SearchFilters.model_validate(filters)):
        reasons.append('No single published service or frequency meets all the limits together')
        distance += 1
    return reasons, distance


def pair_rows(winner, runner, filters, by):
    compared = quality.comparison([winner, runner], filters=filters)
    rows = compared['rows']
    if filters.get('service'):
        opposite = 'modulating' if filters['service'] == 'on_off' else 'on_off'
        rows = [r for r in rows if not r['field'].startswith(opposite) and
                r['field'] != ('starts_per_hour' if opposite == 'modulating' else 'cycles_per_hour')]
    if filters.get('frequency_hz'):
        other = '60hz' if filters['frequency_hz'] == 50 else '50hz'
        rows = [r for r in rows if other not in r['field'] and 'unqualified' not in r['field']]
    prefix = {'lowest_fla': 'fla', 'lowest_lra': 'lra', 'fastest': 'operating_time',
              'lowest_power': 'motor_power', 'most_torque': 'torque', 'closest_torque': 'torque',
              'most_duty': 'duty', 'most_cycles': 'cycles'}[by]
    rows.sort(key=lambda r: (prefix not in r['field'], 'fla' not in r['field'], 'operating_time' not in r['field']))
    return rows


def verdict(products, filters, by):
    valid, excluded = [], []
    for product in products:
        reasons, distance = failures(product, filters)
        if reasons:
            excluded.append((product, reasons, distance))
        else:
            valid.append(product)
    exclusions = '\n'.join(p['base_part_number'] + ' is out: ' + '; '.join(reasons) + '.'
                           for p, reasons, _ in excluded)
    if not valid:
        nearest = min(excluded, key=lambda row: (len(row[1]), row[2], row[0]['base_part_number'])) if excluded else None
        answer = 'None of the shown models meets every requirement.'
        if nearest:
            answer += f" Nearest shown model: {nearest[0]['base_part_number']}; it still fails: " + '; '.join(nearest[1]) + '.'
        return answer + ('\n' + exclusions if exclusions else ''), dict(ranked_by=criterion(filters, by), total=0, shown=0, items=[]), []
    primary = 'lowest_fla' if by == 'closest_torque' and not any(filters.get(f) is not None for f in ('min_torque_nm', 'min_torque_in_lb')) else by
    ranked = ordered(valid, filters, by)
    winner = ranked[0]
    value, label, unit = measured(winner, primary, filters)
    if value is None:
        return 'The shown models do not publish the priority measurement in the required scope; I cannot choose a winner.', dict(ranked_by=criterion(filters, by), total=0, shown=0, items=[]), []
    code = winner['base_part_number']
    why = f'{label} {_num(value)} {unit}'
    if policy.describe(filters):
        why += '; meets ' + policy.describe(filters)
    answer = f'I recommend {code}: {why}. Ranked by {criterion(filters, by)}.'
    if len(ranked) > 1:
        runner = ranked[1]
        other = runner['base_part_number']
        other_value = measured(runner, primary, filters)[0]
        if value == other_value:
            tie_break = next((name for name in ('lowest_fla', 'fastest')
                              if measured(winner, name, filters)[0] != measured(runner, name, filters)[0]), 'part number')
            answer += f' The priority ties at {_num(value)} {unit}; ' + (LABELS[tie_break] if tie_break in LABELS else tie_break) + ' breaks the tie.'
        rows = pair_rows(winner, runner, filters, by)
        advantages = [r for r in rows if r['better'] == 0][:3]
        tradeoff = next((r for r in rows if r['better'] == 1), None)
        answer += f' Versus {other}: ' + ('; '.join(r['label'] + ': ' + r['values'][0] + ' vs ' + r['values'][1] for r in advantages)
                                          if advantages else 'no additional published field advantage under the stated scopes') + '.'
        if tradeoff:
            answer += f" Choose {other} only if its {tradeoff['label']} advantage ({tradeoff['values'][1]} vs {tradeoff['values'][0]}) matters more than the stated priority."
        else:
            answer += f' {other} has no published advantage in the compared fields under these scopes.'
    else:
        answer += ' It is the only shown model meeting every requirement.'
    if by == 'most_duty' and not filters.get('service'):
        answer += ' Duty ranking uses the lowest published service duty for each model.'
        for service in ('on_off', 'modulating', 'shared'):
            values = [(p['base_part_number'], r['duty_s4_percent']) for p in ranked
                      for r in p.get('services', []) if r['service'] == service and r.get('duty_s4_percent') is not None]
            if values:
                answer += '\n' + SERVICE_LABELS[service] + ': ' + '; '.join(code + ' ' + _num(value) + ' %' for code, value in values) + '.'
    if not any(filters.get(f) is not None for f in ('min_torque_nm', 'min_torque_in_lb')):
        answer += ' Assumes no torque requirement; tell me the torque you need.'
    if exclusions:
        answer += '\n' + exclusions
    items = [ranking.item(p, filters, reason=why if p is winner else None) for p in ranked[:3]]
    return answer, dict(ranked_by=criterion(filters, by), total=len(ranked), shown=len(items), items=items), ranked
