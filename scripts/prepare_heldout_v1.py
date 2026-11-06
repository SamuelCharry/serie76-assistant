"""Import read-only held-out HTTP transcripts as a compact offline scripted fixture.

This is a one-time fixture builder. Its output contains queries and idealized tool
choices, never provider credentials, session IDs, or the live answers.
"""
import json
import re
import sys
from pathlib import Path


def filters_from_labels(labels):
    result = {}
    for entry in labels:
        field, label = entry.get('field'), entry.get('label', '')
        low = label.lower()
        number = re.search(r'\d+(?:\.\d+)?', label)
        if field == 'enclosure':
            result[field] = 'explosionproof' if 'explosion' in low else 'weatherproof'
        elif field == 'service':
            result[field] = 'on_off' if 'on/off' in low else 'modulating'
        elif field == 'supply_current':
            result[field] = 'AC/DC' if 'ac/dc' in low else 'DC' if 'dc' in low else 'AC'
        elif field in ('supply_voltage_v', 'phase_count', 'frequency_hz', 'min_torque_nm',
                       'min_torque_in_lb', 'max_operating_time_s', 'max_fla_a', 'max_lra_a',
                       'max_motor_power_w') and number:
            result[field] = float(number.group()) if '.' in number.group() else int(number.group())
    return result


def decision(turn):
    query = turn['request']['query']
    response = turn.get('response') or {}
    comparison = response.get('comparison') or {}
    products = response.get('products') or []
    terms = response.get('terms') or []
    if comparison.get('models'):
        return ['get_actuator', {'part_numbers': comparison['models'], 'focus': ['overview']}]
    if response.get('recommendation'):
        args = filters_from_labels(response.get('active_filters') or [])
        ranked = (response['recommendation'].get('ranked_by') or '').lower()
        if 'most torque' in ranked:
            args['sort_by'] = ['highest_torque']
        elif 'lowest motor power' in ranked:
            args['sort_by'] = ['lowest_power']
        elif 'fastest operating time' in ranked:
            args['sort_by'] = ['fastest']
        elif ranked.startswith('lowest fla'):
            args['sort_by'] = ['lowest_current']
        return ['search_actuators', args]
    if products:
        codes = [p['base_part_number'] for p in products[:4]]
        focus = []
        lower = query.lower()
        for word, key in [('torque', 'torque'), ('fla', 'fla'), ('lra', 'lra'),
                          ('operating time', 'operating_time'), ('motor power', 'motor_power')]:
            if word in lower:
                focus.append(key)
        args = {'part_numbers': codes, 'focus': focus or ['overview']}
        if terms:
            args['explain_terms'] = [t['term_key'] for t in terms[:3]]
        return ['get_actuator', args]
    if terms:
        return ['explain_terms', {'term_keys': [t['term_key'] for t in terms[:3]]}]
    clarification = response.get('clarification') or {}
    return ['ask_clarification', {'field': clarification.get('field') or 'unsupported'}]


def main():
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    prefix = sys.argv[3] if len(sys.argv) > 3 else 'heldout_'
    raw = json.loads(source.read_text(encoding='utf-8'))
    scenarios = []
    for conversation in raw['results']:
        turns = []
        for original in conversation['turns']:
            item = {'query': original['request']['query'], 'scripted_decision': decision(original),
                    'expect': {'contract_v6': True,
                               'not_contains': ['I left out an unstated requirement',
                                                'I will not pick one for you',
                                                'not published in this table layout',
                                                '0 identical fields hidden',
                                                'I cannot place orders']}}
            for key in ('answers', 'action', 'remove_filters'):
                if key in original['request']:
                    item[key] = original['request'][key]
            turns.append(item)
        scenarios.append({'id': prefix + conversation['id'],
                          'category': 'heldout_scripted', 'turns': turns})
    output.write_text(json.dumps({'source_set': raw['set'], 'source_sha256': raw['set_sha256'],
                                  'scenarios': scenarios}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print({'conversations': len(scenarios), 'turns': sum(len(s['turns']) for s in scenarios)})


if __name__ == '__main__':
    main()
