"""Stable ranking of hydrated catalogue rows; missing measurements always sort last."""
from decimal import Decimal
from backend.catalog.models import bound_value, bound_operator
from .rendering import _num


LABELS = {
    'closest_torque': 'closest torque', 'lowest_fla': 'lowest FLA',
    'fastest': 'fastest operating time', 'most_torque': 'most torque',
    'lowest_power': 'lowest motor power',
}


def torque_unit(filters):
    return 'in-lb' if filters.get('min_torque_in_lb') is not None and filters.get('min_torque_nm') is None else 'Nm'


def measurement(product, stem, filters):
    values = product['measurements']
    if stem == 'torque':
        service = filters.get('service')
        unit = 'in_lb' if torque_unit(filters) == 'in-lb' else 'nm'
        keys = ([f'{service}_torque_{unit}', f'shared_torque_{unit}'] if service else
                [f'on_off_torque_{unit}', f'modulating_torque_{unit}', f'shared_torque_{unit}'])
    else:
        frequency = filters.get('frequency_hz')
        keys = ([f'{stem}_{frequency}hz_{"a" if stem == "fla" else "s"}'] if frequency else
                [f'{stem}_{hz}hz_{"a" if stem == "fla" else "s"}' for hz in (50, 60)] +
                [f'{stem}_unqualified_{"a" if stem == "fla" else "s"}'])
    found = [values[k] for k in keys if values.get(k) is not None]
    if stem == 'torque':
        threshold = filters.get('min_torque_nm') if unit == 'nm' else filters.get('min_torque_in_lb')
        if threshold is not None:
            minimum = Decimal(str(bound_value(threshold)))
            strict = bound_operator(threshold, 'gte') == 'gt'
            found = [value for value in found if value > minimum or (not strict and value == minimum)]
    return min(found) if found else None


def qualifying_torques(product, filters):
    """Published service values that satisfy the active torque requirement."""
    unit = 'in_lb' if torque_unit(filters) == 'in-lb' else 'nm'
    values = product['measurements']
    service = filters.get('service')
    keys = ([f'{service}_torque_{unit}', f'shared_torque_{unit}'] if service else
            [f'on_off_torque_{unit}', f'modulating_torque_{unit}', f'shared_torque_{unit}'])
    threshold = filters.get('min_torque_nm') if unit == 'nm' else filters.get('min_torque_in_lb')
    minimum = Decimal(str(bound_value(threshold))) if threshold is not None else None
    strict = bound_operator(threshold, 'gte') == 'gt' if threshold is not None else False
    labels = {'on_off': 'On/Off torque', 'modulating': 'Modulating torque', 'shared': 'Shared torque'}
    result = []
    for key in keys:
        value = values.get(key)
        if value is None or minimum is not None and (value < minimum or strict and value == minimum):
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
        elif by == 'fastest':
            primary = missing(speed)
        elif by == 'most_torque':
            primary = (torque is None, -torque if torque is not None else 0)
        elif by == 'lowest_power':
            primary = missing(product['measurements'].get('motor_power_w'))
        else:
            primary = missing(torque) if threshold is not None else (False, 0)
        return primary, missing(fla), missing(speed), product['base_part_number']

    return sorted(products, key=key)


def ranked_by(filters, by='closest_torque'):
    if by != 'closest_torque':
        tie_breaks = ['lowest FLA', 'shortest operating time']
        return ', then '.join(dict.fromkeys([LABELS[by], *tie_breaks]))
    minimum = filters.get('min_torque_nm')
    if minimum is None:
        minimum = filters.get('min_torque_in_lb')
    if minimum is not None:
        return f'closest torque at or above {_num(bound_value(minimum))} {torque_unit(filters)}, then lowest FLA'
    return 'lowest FLA, then shortest operating time'


def item(product, filters, reason=None):
    torques = qualifying_torques(product, filters)
    fla = measurement(product, 'fla', filters)
    parts = []
    for label, torque in torques:
        parts.append(f'{label} {_num(torque)} {torque_unit(filters)}')
    if fla is not None:
        parts.append(f'FLA {_num(fla)} A')
    key_values = []
    for label, torque in torques:
        key_values.append(dict(label=label, value=f'{_num(torque)} {torque_unit(filters)}'))
    if filters.get('sort_by', [None])[0] == 'fastest':
        speed = operating_time_used(product, filters)
        if speed:
            label, value = speed
            parts.insert(0, f'{label} {_num(value)} s')
            key_values.insert(0, dict(label=label, value=f'{_num(value)} s'))
    if fla is not None:
        key_values.append(dict(label='FLA', value=f'{_num(fla)} A'))
    return dict(part_number=product['base_part_number'], reason=reason or '; '.join(parts) or 'Published catalogue model',
                key_values=key_values)


def recommendation(products, filters, by='closest_torque', *, total=None):
    ordered = rank(products, filters, by)
    return dict(ranked_by=ranked_by(filters, by), total=len(ordered) if total is None else total,
                shown=min(3, len(ordered)), items=[item(p, filters) for p in ordered[:3]])
