"""Stable ranking of hydrated catalogue rows; missing measurements always sort last."""
from decimal import Decimal
from backend.catalog.models import bound_value, bound_operator, bounds
from .rendering import _num


LABELS = {
    'closest_torque': 'closest torque', 'lowest_fla': 'lowest FLA',
    'fastest': 'fastest operating time', 'most_torque': 'most torque',
    'lowest_power': 'lowest motor power', 'lowest_lra': 'lowest LRA',
    'most_duty': 'highest duty S4', 'most_cycles': 'most On/Off cycles',
}


def torque_unit(filters):
    return 'in-lb' if filters.get('min_torque_in_lb') is not None and filters.get('min_torque_nm') is None else 'Nm'


def upper_torque_only(filters):
    constraint = filters.get('min_torque_nm') if filters.get('min_torque_nm') is not None else filters.get('min_torque_in_lb')
    return constraint is not None and all(bound_operator(item, 'gte') in ('lt', 'lte') for item in bounds(constraint))


def measurement(product, stem, filters):
    values = product['measurements']
    if stem in ('duty', 'cycles'):
        column = 'duty_s4_percent' if stem == 'duty' else 'cycles_per_hour'
        service = filters.get('service') or ('on_off' if stem == 'cycles' else None)
        found = [r[column] for r in product.get('services', []) if r.get(column) is not None
                 and (service is None or r['service'] in (service, 'shared'))]
        return min(found) if found else None
    if stem == 'torque':
        service = filters.get('service')
        unit = 'in_lb' if torque_unit(filters) == 'in-lb' else 'nm'
        keys = ([f'{service}_torque_{unit}', f'shared_torque_{unit}'] if service else
                [f'on_off_torque_{unit}', f'modulating_torque_{unit}', f'shared_torque_{unit}'])
    else:
        frequency = filters.get('frequency_hz')
        unit = 'a' if stem in ('fla', 'lra') else 's'
        keys = ([f'{stem}_{frequency}hz_{unit}'] if frequency else
                [f'{stem}_{hz}hz_{unit}' for hz in (50, 60)] +
                [f'{stem}_unqualified_{unit}'])
    found = [values[k] for k in keys if values.get(k) is not None]
    if stem == 'torque':
        threshold = filters.get('min_torque_nm') if unit == 'nm' else filters.get('min_torque_in_lb')
        if threshold is not None:
            found = [value for value in found if _inside_bounds(value, threshold)]
    return (max(found) if upper_torque_only(filters) else min(found)) if found else None


def _inside_bounds(value, constraint):
    checks = {'gt': lambda x, y: x > y, 'gte': lambda x, y: x >= y,
              'lt': lambda x, y: x < y, 'lte': lambda x, y: x <= y}
    return all(checks[bound_operator(item, 'gte')](value, Decimal(str(bound_value(item))))
               for item in bounds(constraint))


def qualifying_torques(product, filters):
    """Published service values that satisfy the active torque requirement."""
    unit = 'in_lb' if torque_unit(filters) == 'in-lb' else 'nm'
    values = product['measurements']
    service = filters.get('service')
    keys = ([f'{service}_torque_{unit}', f'shared_torque_{unit}'] if service else
            [f'on_off_torque_{unit}', f'modulating_torque_{unit}', f'shared_torque_{unit}'])
    threshold = filters.get('min_torque_nm') if unit == 'nm' else filters.get('min_torque_in_lb')
    labels = {'on_off': 'On/Off torque', 'modulating': 'Modulating torque', 'shared': 'Shared torque'}
    result = []
    for key in keys:
        value = values.get(key)
        if value is None or threshold is not None and not _inside_bounds(value, threshold):
            continue
        result.append((labels[key.split('_torque_')[0]], value))
    return result


def operating_time_used(product, filters):
    values = product['measurements']
    hz = filters.get('frequency_hz')
    keys = ([f'operating_time_{hz}hz_s'] if hz else
            ['operating_time_50hz_s', 'operating_time_60hz_s', 'operating_time_unqualified_s'])
    found = [(key, values[key]) for key in keys if values.get(key) is not None]
    if not found:
        return None
    key, value = min(found, key=lambda pair: pair[1])
    label = ('Operating time at ' + key.split('_')[2].removesuffix('hz') + ' Hz'
             if 'unqualified' not in key else 'Operating time')
    return label, value


def fla_used(product, filters):
    values = product['measurements']
    hz = filters.get('frequency_hz')
    keys = ([f'fla_{hz}hz_a'] if hz else ['fla_50hz_a', 'fla_60hz_a', 'fla_unqualified_a'])
    found = [(key, values[key]) for key in keys if values.get(key) is not None]
    if not found:
        return None
    key, value = min(found, key=lambda pair: pair[1])
    if 'unqualified' not in key:
        return 'FLA ' + key.split('_')[1].removesuffix('hz') + ' Hz', value, ''
    if any(f.get('frequency_scope') == 'not_applicable' for f in product.get('frequencies', [])):
        return 'FLA (DC)', value, ''
    return 'FLA', value, ''


def rank(products, filters, by='closest_torque'):
    threshold = filters.get('min_torque_nm')
    if threshold is None:
        threshold = filters.get('min_torque_in_lb')
    threshold = bound_value(threshold) if threshold is not None else None

    def missing(value):
        return (value is None, value if value is not None else 0)

    def key(product):
        torque = measurement(product, 'torque', filters)
        fla = measurement(product, 'fla', filters)
        speed = measurement(product, 'operating_time', filters)
        if by == 'lowest_fla':
            primary = missing(fla)
        elif by == 'lowest_lra':
            primary = missing(measurement(product, 'lra', filters))
        elif by == 'fastest':
            primary = missing(speed)
        elif by == 'most_torque':
            primary = (torque is None, -torque if torque is not None else 0)
        elif by == 'lowest_power':
            primary = missing(product['measurements'].get('motor_power_w'))
        elif by in ('most_duty', 'most_cycles'):
            value = measurement(product, 'duty' if by == 'most_duty' else 'cycles', filters)
            primary = (value is None, -value if value is not None else 0)
        else:
            primary = ((torque is None, -torque if torque is not None else 0) if upper_torque_only(filters)
                       else missing(torque)) if threshold is not None else (False, 0)
        return primary, missing(fla), missing(speed), product['base_part_number']

    return sorted(products, key=key)


def ranked_by(filters, by='closest_torque'):
    if by != 'closest_torque':
        tie_breaks = ([] if by == 'fastest' else ['shortest operating time'])
        if by not in ('lowest_fla', 'lowest_lra'):
            tie_breaks.insert(0, 'lowest FLA')
        return ', then '.join(dict.fromkeys([LABELS[by], *tie_breaks]))
    minimum = filters.get('min_torque_nm')
    if minimum is None:
        minimum = filters.get('min_torque_in_lb')
    if minimum is not None:
        direction = 'below' if upper_torque_only(filters) else 'above'
        return f'closest torque at or {direction} {_num(bound_value(minimum))} {torque_unit(filters)}, then lowest FLA'
    return 'lowest FLA, then shortest operating time'


def item(product, filters, reason=None):
    torques = qualifying_torques(product, filters)
    fla = fla_used(product, filters)
    parts = []
    qualifying = (filters.get('min_torque_nm') if filters.get('min_torque_nm') is not None
                  else filters.get('min_torque_in_lb'))
    if qualifying is not None and not filters.get('service') and len(torques) > 1:
        torques = sorted(torques, key=lambda pair: pair[1], reverse=upper_torque_only(filters))
    for index, (label, torque) in enumerate(torques):
        suffix = (' (same torque for On/Off and Modulating)' if label == 'Shared torque' else
                  f' (closest to {_num(bound_value(qualifying))} {torque_unit(filters)})'
                  if index == 0 and qualifying is not None and not filters.get('service') and len(torques) > 1 else '')
        parts.append(f'{label} {_num(torque)} {torque_unit(filters)}{suffix}')
    if fla is not None:
        parts.append(f'{fla[0]} {_num(fla[1])} A{fla[2]}')
    key_values = []
    if filters.get('rank_by') == 'lowest_lra':
        hz = filters.get('frequency_hz')
        lra = measurement(product, 'lra', filters)
        if lra is not None:
            label = f'LRA at {hz} Hz' if hz else 'Lowest published LRA'
            parts.insert(0, f'{label} {_num(lra)} A')
            key_values.insert(0, dict(label=label, value=f'{_num(lra)} A'))
    for label, torque in torques:
        key_values.append(dict(label=label, value=f'{_num(torque)} {torque_unit(filters)}'))
    if filters.get('sort_by', [None])[0] == 'fastest':
        speed = operating_time_used(product, filters)
        if speed:
            label, value = speed
            parts.insert(0, f'{label} {_num(value)} s')
            key_values.insert(0, dict(label=label, value=f'{_num(value)} s'))
    if fla is not None:
        key_values.append(dict(label=fla[0], value=f'{_num(fla[1])} A{fla[2]}'))
    return dict(part_number=product['base_part_number'], reason=reason or '; '.join(parts) or 'Published catalogue model',
                key_values=key_values)


def recommendation(products, filters, by='closest_torque', *, total=None):
    ordered = rank(products, filters, by)
    return dict(ranked_by=ranked_by(filters, by), total=len(ordered) if total is None else total,
                shown=min(3, len(ordered)), items=[item(p, dict(filters, rank_by=by)) for p in ordered[:3]])
