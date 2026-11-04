"""Stable ranking of hydrated catalogue rows; missing measurements always sort last."""
from backend.catalog.models import bound_value
from .rendering import _num


LABELS = {
    'closest_torque': 'Closest torque', 'lowest_fla': 'Lowest FLA',
    'fastest': 'Fastest operating time', 'most_torque': 'Most torque',
}


def measurement(product, stem, filters):
    values = product['measurements']
    if stem == 'torque':
        service = filters.get('service')
        keys = ([f'{service}_torque_nm', 'shared_torque_nm'] if service else
                ['on_off_torque_nm', 'modulating_torque_nm', 'shared_torque_nm'])
    else:
        frequency = filters.get('frequency_hz')
        keys = ([f'{stem}_{frequency}hz_{"a" if stem == "fla" else "s"}'] if frequency else
                [f'{stem}_{hz}hz_{"a" if stem == "fla" else "s"}' for hz in (50, 60)] +
                [f'{stem}_unqualified_{"a" if stem == "fla" else "s"}'])
    found = [values[k] for k in keys if values.get(k) is not None]
    return min(found) if found else None


def rank(products, filters, by='closest_torque'):
    threshold = filters.get('min_torque_nm')
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
        else:
            primary = missing(torque) if threshold is not None else (False, 0)
        return primary, missing(fla), missing(speed), product['base_part_number']

    return sorted(products, key=key)


def ranked_by(filters, by='closest_torque'):
    if by != 'closest_torque':
        return LABELS[by] + ', then lowest FLA, then shortest operating time'
    minimum = filters.get('min_torque_nm')
    if minimum is not None:
        return f'Closest torque at or above {_num(bound_value(minimum))} Nm, then lowest FLA'
    return 'Lowest FLA, then shortest operating time'


def item(product, filters, reason=None):
    torque = measurement(product, 'torque', filters)
    fla = measurement(product, 'fla', filters)
    parts = []
    if torque is not None:
        parts.append(f'{_num(torque)} Nm torque')
    if fla is not None:
        parts.append(f'FLA {_num(fla)} A')
    key_values = []
    if torque is not None:
        service = filters.get('service')
        label = ('On/Off torque' if service == 'on_off' else 'Modulating torque' if service == 'modulating' else 'Torque')
        key_values.append(dict(label=label, value=f'{_num(torque)} Nm'))
    if fla is not None:
        key_values.append(dict(label='FLA', value=f'{_num(fla)} A'))
    return dict(part_number=product['base_part_number'], reason=reason or '; '.join(parts) or 'Published catalogue model',
                key_values=key_values)


def recommendation(products, filters, by='closest_torque', *, total=None):
    ordered = rank(products, filters, by)
    return dict(ranked_by=ranked_by(filters, by), total=len(ordered) if total is None else total,
                shown=min(3, len(ordered)), items=[item(p, filters) for p in ordered[:3]])
