"""Stable ranking of hydrated catalogue rows; missing measurements always sort last."""
from backend.catalog.models import bound_value
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
    return min(found) if found else None


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
        return LABELS[by] + ', then lowest FLA, then shortest operating time'
    minimum = filters.get('min_torque_nm')
    if minimum is None:
        minimum = filters.get('min_torque_in_lb')
    if minimum is not None:
        return f'closest torque at or above {_num(bound_value(minimum))} {torque_unit(filters)}, then lowest FLA'
    return 'lowest FLA, then shortest operating time'


def item(product, filters, reason=None):
    torque = measurement(product, 'torque', filters)
    fla = measurement(product, 'fla', filters)
    parts = []
    if torque is not None:
        parts.append(f'{_num(torque)} {torque_unit(filters)} torque')
    if fla is not None:
        parts.append(f'FLA {_num(fla)} A')
    key_values = []
    if torque is not None:
        service = filters.get('service')
        label = ('On/Off torque' if service == 'on_off' else 'Modulating torque' if service == 'modulating' else 'Torque')
        key_values.append(dict(label=label, value=f'{_num(torque)} {torque_unit(filters)}'))
    if fla is not None:
        key_values.append(dict(label='FLA', value=f'{_num(fla)} A'))
    return dict(part_number=product['base_part_number'], reason=reason or '; '.join(parts) or 'Published catalogue model',
                key_values=key_values)


def recommendation(products, filters, by='closest_torque', *, total=None):
    ordered = rank(products, filters, by)
    return dict(ranked_by=ranked_by(filters, by), total=len(ordered) if total is None else total,
                shown=min(3, len(ordered)), items=[item(p, filters) for p in ordered[:3]])
