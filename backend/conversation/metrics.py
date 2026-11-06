"""Metric intent and winner rendering over published SQL product rows."""
from . import ranking, answer_planner
from .rendering import _num


def intent(query):
    planned = answer_planner.plan(query)
    if not planned.metrics:
        return None
    return planned.metrics[0], planned.direction, planned.frequency_hz, planned.service


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
    if metric in ('fla', 'lra') and not filters.get('frequency_hz'):
        options = [(values.get(f'{metric}_{hz}hz_a'), hz) for hz in (50, 60)]
        published = [(amount, hz) for amount, hz in options if amount is not None]
        if published:
            amount, hz = min(published)
            return amount, f'A at {hz} Hz'
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
        answers = []
        for service_name, display in (('on_off', 'On/Off'), ('modulating', 'Modulating')):
            scoped = dict(scope, service=service_name)
            measured_duty = [(p, *value(p, 'duty', scoped)) for p in products]
            available_duty = [(p, amount) for p, amount, _ in measured_duty if amount is not None]
            if available_duty:
                highest = (max if direction == 'higher' else min)(amount for _, amount in available_duty)
                winners_duty = [p['base_part_number'] for p, amount in available_duty if amount == highest]
                answers.append(f'{display}: {", ".join(winners_duty)} at {_num(highest)}% duty S4')
        if answers:
            return '; '.join(answers) + '.', None
        service_values = [(p['measurements'].get('on_off_duty_s4_percent'),
                           p['measurements'].get('modulating_duty_s4_percent'),
                           p['measurements'].get('shared_duty_s4_percent')) for p in products]
        if len(set(service_values)) == 1 and all(value is not None for value in service_values[0][:2]):
            on_off, modulating, _ = service_values[0]
            subject = 'Both' if len(products) == 2 else 'All compared models'
            return f'{subject} have the same duty: On/Off {_num(on_off)}% and Modulating {_num(modulating)}%.', None
        if all((p['measurements'].get('on_off_duty_s4_percent') ==
                p['measurements'].get('modulating_duty_s4_percent') and
                p['measurements'].get('on_off_duty_s4_percent') is not None) or
               p['measurements'].get('shared_duty_s4_percent') is not None for p in products):
            scope['service'] = 'on_off'
        else:
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
        codes = ', '.join(p['base_part_number'] for p, _ in winners)
        return f'{codes} tie at {_num(best)} {unit.strip()}{frequency} for {label}.', None
    codes = ', '.join(p['base_part_number'] for p, _ in winners)
    if len(products) == 2 and len(available) == 2 and len(winners) == 1:
        order = [(p['base_part_number'], v, u) for p, v, u in available]
        first, second = order
        pair_unit = 's' if hz and metric == 'operating_time' else first[2]
        other_unit = 's' if hz and metric == 'operating_time' else second[2]
        compared = (f'{first[0]} {_num(first[1])} {pair_unit} vs '
                    f'{second[0]} {_num(second[1])} {other_unit}')
        phrase = ('is faster' if metric == 'operating_time' and direction == 'lower' else
                  'draws more current' if metric == 'fla' and direction == 'higher' else
                  'has lower LRA' if metric == 'lra' and direction == 'lower' else
                  f'has the {"highest" if direction == "higher" else "lowest"} {label}')
        return f'{codes} {phrase}{frequency}: {compared}.', winners[0][0]['base_part_number']
    if len(winners) > 1:
        return (f'{codes} tie for the {"highest" if direction == "higher" else "lowest"} '
                f'{label}{frequency}: {_num(best)} {unit.strip()}.'), None
    return f'{codes} has the {"highest" if direction == "higher" else "lowest"} {label}{frequency}: {_num(best)} {unit.strip()}.', winners[0][0]['base_part_number'] if len(winners) == 1 else None
