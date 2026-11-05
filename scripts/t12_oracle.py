"""Independent outcome assertions for the offline T12 diagnostic cohort."""
import re
from copy import deepcopy
from decimal import Decimal
from scripts.acceptance_contract import catalogue


def verify(spec, observed):
    from scripts.agent_acceptance import t10_oracle
    normalized = deepcopy(observed)
    filters = (normalized.get('trace') or {}).get('context_after', {}).get('filters', {})
    for key in ('supply_voltage_v', 'frequency_hz'):
        if filters.get(key) is not None:
            filters[key] = Decimal(str(filters[key]))
    errors = t10_oracle().verify(spec.get('state', {}), normalized)
    answer = observed['answer']
    products = observed.get('products', [])
    visible = {p['base_part_number'] for p in products}
    visible.update(p['part_number'] for p in (observed.get('recommendation') or {}).get('items', []))
    rows = catalogue()
    for pattern in spec.get('required_text', []):
        if not re.search(pattern, answer, re.I):
            errors.append('missing answer concept: ' + pattern)
    for pattern in spec.get('forbidden_text', []):
        if re.search(pattern, answer, re.I):
            errors.append('unrequested answer concept: ' + pattern)
    if spec.get('dc_only'):
        for code in visible:
            if rows[code]['supply_current'] != 'DC':
                errors.append('DC-only violation: ' + code)
    if spec.get('empty') and visible:
        errors.append('infeasible request returned models')
    if spec.get('list') and len(visible) < 2:
        errors.append('list replaced by single model or empty answer')
    for code, field in spec.get('published_values', []):
        raw = rows[code][field]
        unit = 'W' if field == 'motor_power_w' else 's'
        if raw and not re.search(r'(?<!\d)' + re.escape(str(Decimal(raw).normalize())) + r'(?:\.0+)?\s*' + unit + r'\b', answer):
            # Decimal scientific notation is inappropriate for text matching.
            if not re.search(r'(?<!\d)' + re.escape(format(Decimal(raw), 'f')) + r'\s*' + unit + r'\b', answer):
                errors.append('published value omitted: ' + code + '/' + field)
    if spec.get('candidate_count') is not None:
        if observed.get('candidate_total') != spec['candidate_count'] or len(set(observed.get('eligible_codes', []))) != spec['candidate_count']:
            errors.append('candidate loss: expected ' + str(spec['candidate_count']))
    return errors
