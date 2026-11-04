"""Metric intent and winner rendering over published SQL product rows."""
import re

from . import ranking
from .rendering import _num


def intent(query):
    text = query.lower()
    metric = ('lra' if re.search(r'\b(lra|starting current|inrush|arranque)\b', text) else
              'motor_power' if re.search(r'\b(power|electricity|consumption|potencia)\b', text) else
              'fla' if re.search(r'\b(fla|draws?|current|corriente)\b', text) else
              'duty' if re.search(r'\b(duty|s4)\b', text) else
              'cycles' if re.search(r'\b(cycles?|ciclos?)\b', text) else
              'starts' if re.search(r'\b(starts?|arranques?)\b', text) else
              'operating_time' if re.search(r'\b(faster|fastest|quicker|speed|operating time|tiempo)\b', text) else
              'torque' if re.search(r'\b(stronger|strongest|torque|par)\b', text) else None)
    if metric is None:
        return None
    direction = 'higher' if re.search(r'\b(more|higher|highest|most|stronger|strongest|mas|más|mayor)\b', text) else 'lower'
    hz = re.search(r'\b(50|60)\s*hz\b', text)
    service = ('on_off' if re.search(r'\b(on\s*/?\s*off|open.close)\b', text) else
               'modulating' if re.search(r'\bmodulat', text) else None)
    return metric, direction, int(hz.group(1)) if hz else None, service


def value(product, metric, filters):
    values = product['measurements']
    if metric == 'motor_power':
        return values.get('motor_power_w'), 'W'
    if metric == 'cycles':
        return values.get('cycles_per_hour'), 'cycles/h'
    if metric == 'starts':
        return values.get('starts_per_hour'), 'starts/h'
    if metric == 'duty':
        service = filters.get('service')
        if service is None:
            return None, '%'
        v = values.get(service + '_duty_s4_percent')
        if v is None:
            v = values.get('shared_duty_s4_percent')
        return v, '%'
    if metric == 'operating_time':
        used = ranking.operating_time_used(product, filters)
        return (used[1], 's' + used[0].removeprefix('Operating time')) if used else (None, 's')
    return ranking.measurement(product, metric, filters), 'A' if metric in ('fla', 'lra') else 'Nm'


def verdict(products, query, filters):
    spec = intent(query)
    if not spec or len(products) < 2:
        return None, None
    metric, direction, hz, service = spec
    scope = dict(filters)
    if hz:
        scope['frequency_hz'] = hz
    if service:
        scope['service'] = service
    if metric == 'torque' and scope.get('service') is None:
        scope['service'] = 'on_off'
    if metric == 'duty' and scope.get('service') is None:
        return 'Which service duty matters, On/Off or Modulating?', None
    measured = [(p, *value(p, metric, scope)) for p in products]
    available = [(p, v, unit) for p, v, unit in measured if v is not None]
    label = {'lra': 'LRA', 'fla': 'FLA', 'motor_power': 'motor power', 'duty': 'duty S4',
             'cycles': 'On/Off cycles', 'starts': 'Modulating starts',
             'operating_time': 'operating time', 'torque': 'torque'}[metric]
    if not available:
        return f'The catalogue does not publish comparable {label} values for these models.', None
    best = (max if direction == 'higher' else min)(v for _, v, _ in available)
    winners = [(p, unit) for p, v, unit in available if v == best]
    unit = winners[0][1]
    frequency = f' at {hz} Hz' if hz and metric in ('lra', 'fla', 'operating_time') else ''
    if len(winners) == len(available):
        subject = 'Both' if len(winners) == 2 else 'All ' + str(len(winners))
        return f'{subject} have {_num(best)} {unit.strip()}{frequency} for {label}.', None
    codes = ', '.join(p['base_part_number'] for p, _ in winners)
    if len(products) == 2 and len(available) == 2 and len(winners) == 1:
        order = [(p['base_part_number'], v, u) for p, v, u in available]
        first, second = order
        pair_unit = 's' if hz and metric == 'operating_time' else first[2]
        other_unit = 's' if hz and metric == 'operating_time' else second[2]
        compared = f'{_num(first[1])} {pair_unit} vs {_num(second[1])} {other_unit}'
        phrase = ('is faster' if metric == 'operating_time' and direction == 'lower' else
                  'draws more current' if metric == 'fla' and direction == 'higher' else
                  'has lower LRA' if metric == 'lra' and direction == 'lower' else
                  f'has the {"highest" if direction == "higher" else "lowest"} {label}')
        return f'{codes} {phrase}{frequency}: {compared}.', winners[0][0]['base_part_number']
    if len(winners) > 1:
        return (f'{codes} tie for the {"highest" if direction == "higher" else "lowest"} '
                f'{label}{frequency}: {_num(best)} {unit.strip()}.'), None
    return f'{codes} has the {"highest" if direction == "higher" else "lowest"} {label}{frequency}: {_num(best)} {unit.strip()}.', winners[0][0]['base_part_number'] if len(winners) == 1 else None
