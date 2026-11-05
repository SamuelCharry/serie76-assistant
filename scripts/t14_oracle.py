"""Independent T14 assertions; expected ranking values come from the CSV oracle."""
import re
from decimal import Decimal
from scripts.acceptance_contract import catalogue, eligible_codes
from scripts.t12_oracle import verify as verify_base


def verify(spec, observed):
    errors = verify_base(spec, observed)
    rec = observed.get('recommendation') or {}
    if spec.get('clarify') and not observed.get('clarification'):
        errors.append('contradiction was not clarified')
    if spec.get('pick') and not re.match(r'I recommend ', observed['answer']):
        errors.append('no explicit selection from the shown models')
    if spec.get('ranking'):
        rule = spec['ranking']
        rows = catalogue()
        codes = rule.get('among') or eligible_codes(spec.get('state', {}).get('filters', {}))
        values = {c: Decimal(rows[c][rule['column']]) for c in codes if rows[c].get(rule['column'])}
        items = rec.get('items', [])
        optimum = (max if rule['direction'] == 'highest' else min)(values.values()) if values else None
        if not items or values.get(items[0]['part_number']) != optimum:
            errors.append('winner does not optimize the requested published metric')
        if not re.search(rule['label'], rec.get('ranked_by', ''), re.I):
            errors.append('ranking label does not describe the applied priority')
    return errors
