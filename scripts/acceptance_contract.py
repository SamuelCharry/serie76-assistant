"""Independent offline v6 oracle: frozen CSV values and public contract invariants."""
import csv
import re
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def catalogue():
    with (ROOT / 'data/extracted/series76/catalog.csv').open(encoding='utf-8-sig', newline='') as file:
        return {r['base_part_number']: r for r in csv.DictReader(file)}


def number(value):
    return Decimal(str(value))


def components(field):
    if field.endswith('_torque'):
        return [(field + '_in_lb', 'in-lb'), (field + '_nm', 'Nm')]
    units = {'supply_voltage_v': 'V', 'motor_power_w': 'W', 'cycles_per_hour': '/h', 'starts_per_hour': '/h'}
    unit = units.get(field, 'A' if field.endswith('_a') else 's' if field.endswith('_s') else '%' if field.endswith('_percent') else '')
    return [(field, unit)]


def public_cell_matches(text, row, field):
    pieces = components(field)
    if all(row.get(k, '') for k, _ in pieces):
        expected = ' / '.join(row[k] + (' ' + unit if unit else '') for k, unit in pieces)
        # Mixed AC/DC comparisons append the published frequency scope to a cell.
        return text == expected or (field == 'enclosure' and text.lower() == expected.lower()) or ('_unqualified_' in field and text.startswith(expected + ' ('))
    if row['data_status'] == 'source_NA':
        return 'N/A' in text and not re.search(r'\b0(?:\.0)?\s*(?:W|A|s|Nm|in-lb)\b', text)
    return text == '—' or 'not' in text.lower() and not re.search(r'\d', text)


def eligible_codes(filters):
    """Independent CSV evaluation of the published AND/scope semantics."""
    comparisons = {'gt': lambda x,y:x>y, 'gte': lambda x,y:x>=y, 'lt': lambda x,y:x<y, 'lte': lambda x,y:x<=y}
    def check_bound(raw, bound, field):
        if not raw:
            return False
        limits = bound if isinstance(bound, list) else [bound]
        for item in limits:
            op = item['op'] if isinstance(item, dict) else 'gte' if field.startswith('min_') else 'lte'
            value = item['value'] if isinstance(item, dict) else item
            if not comparisons[op](number(raw), number(value)):
                return False
        return True
    found = []
    for code, row in catalogue().items():
        if row['data_status'] != 'reported':
            continue
        if filters.get('enclosure') and filters['enclosure'] != row['enclosure']:
            continue
        if any(filters.get(f) is not None and (not row[f] or number(filters[f]) != number(row[f])) for f in ('supply_voltage_v','phase_count')):
            continue
        current = filters.get('supply_current')
        if filters.get('dc_only') and row['supply_current'] != 'DC':
            continue
        if current and row['supply_current'] != current and not (current in ('AC','DC') and row['supply_current'] == 'AC/DC'):
            continue
        if filters.get('csa_required') and row['csa_status'] != 'reported_in_header':
            continue
        service = filters.get('service')
        if service and row['service_layout'] not in (service, 'mixed', 'shared'):
            continue
        services = [service] if service else ['on_off', 'modulating', 'shared']
        service_ok = False
        for scope in services:
            valid = True
            for field,value in filters.items():
                if not field.startswith('min_') or value is None:
                    continue
                name = field[4:]
                column = name if name in ('starts_per_hour','cycles_per_hour') else scope + '_' + name
                raw = row.get(column) or row.get('shared_' + name, '')
                if not check_bound(raw, value, field):
                    valid = False
            service_ok |= valid
        if not service_ok:
            continue
        if filters.get('max_motor_power_w') is not None and not check_bound(row['motor_power_w'], filters['max_motor_power_w'], 'max_motor_power_w'):
            continue
        frequency_fields = [f for f in ('max_operating_time_s','max_fla_a','max_lra_a') if filters.get(f) is not None]
        if frequency_fields or filters.get('frequency_hz'):
            scopes = [str(filters['frequency_hz'])+'hz'] if filters.get('frequency_hz') else ['50hz','60hz','unqualified']
            def frequency_ok(scope):
                if not any(row.get(prefix+'_'+scope+'_'+unit) for prefix,unit in [('operating_time','s'),('fla','a'),('lra','a')]):
                    return False
                for field in frequency_fields:
                    base, unit = field[4:].rsplit('_', 1)
                    if not check_bound(row.get(base+'_'+scope+'_'+unit), filters[field], field):
                        return False
                return True
            if not any(frequency_ok(scope) for scope in scopes):
                continue
        found.append(code)
    return sorted(found)


def verify(expect, observed):
    failures = []
    comp = observed.get('comparison')
    interaction = observed.get('interaction')
    suggestions = observed.get('suggestions', [])
    labels = [s.get('label') if isinstance(s, dict) else s for s in suggestions] if isinstance(suggestions, list) else []
    if not isinstance(suggestions, list) or not 0 <= len(suggestions) <= 3 or len(set(labels)) != len(labels):
        failures.append('invalid suggestions shape')
    if labels != observed.get('suggested_replies'):
        failures.append('suggestion alias differs')
    if any(s in ('Cancel', 'Find an actuator for my requirements', 'Explain Base Part Number') for s in labels):
        failures.append('generic or cancel suggestion')
    if interaction:
        if interaction.get('kind') != 'question' or not interaction.get('questions'):
            failures.append('invalid question/suggestion separation')
        ids = []
        for q in interaction.get('questions', []):
            ids.append(q.get('id'))
            if not q.get('prompt') or not q.get('options') or any(not {'value', 'label'} <= set(o) or not isinstance(o['value'], str) for o in q.get('options', [])):
                failures.append('invalid question options')
        if len(set(ids)) != len(ids):
            failures.append('duplicate questions')
    if 'interaction_ids' in expect and [q['id'] for q in (interaction or {}).get('questions', [])] != expect['interaction_ids']:
        failures.append('question ids differ')
    for field, values in expect.get('question_options', {}).items():
        actual = next((q for q in (interaction or {}).get('questions', []) if q['id'] == field), {})
        if [o['value'] for o in actual.get('options', [])] != values:
            failures.append('question options differ: ' + field)
    if 'suggestions_count' in expect and len(suggestions) != expect['suggestions_count']:
        failures.append('suggestions count differs')
    if 'comparison_layout' in expect and (comp or {}).get('layout') != expect['comparison_layout']:
        failures.append('comparison layout differs')
    if expect.get('no_comparison') and comp is not None:
        failures.append('unexpected comparison')
    if expect.get('lead_required') and not observed.get('lead'):
        failures.append('lead missing')
    if expect.get('assumption_required') and not observed.get('assumptions'):
        failures.append('assumption missing')
    rows = catalogue()
    for product in observed.get('products', []):
        code = product['base_part_number']
        source = rows.get(code)
        if source is None:
            failures.append('unknown product code: ' + code)
            continue
        if str(product.get('source', {}).get('page')) != source['source_page']:
            failures.append('wrong source page: ' + code)
        for field, value in product.get('measurements', {}).items():
            original = source.get(field, '')
            if original:
                if value is None or number(value) != number(original):
                    failures.append('catalogue measurement differs: ' + field)
            elif value is not None:
                failures.append('absent catalogue value replaced: ' + field)
        if source['data_status'] == 'source_NA':
            if any(v is not None for v in product.get('measurements', {}).values()) or 'N/A' not in observed['answer']:
                failures.append('source N/A was not preserved')
    for check in expect.get('measurements', []):
        product = next((p for p in observed.get('products', []) if p['base_part_number'] == check['code']), {})
        actual = product.get('measurements', {})
        if check['field'] not in actual or actual[check['field']] != check['value']:
            failures.append('required measurement missing/different: ' + check['field'])
        if check.get('status') and product.get('field_status', {}).get(check['field']) != check['status']:
            failures.append('required absence status differs')
    if comp:
        models = comp.get('models', [])
        if len(models) not in (2, 3, 4) or len(set(models)) != len(models) or any(m not in rows for m in models):
            failures.append('invalid comparison models')
            return failures
        if not comp.get('summary') or not isinstance(comp.get('assumptions'), str):
            failures.append('comparison summary/assumptions missing')
        if comp.get('layout') != ('table' if len(models) == 2 else 'cards'):
            failures.append('wrong comparison layout')
        if len(models) > 2 and len(comp.get('key_fields', [])) != 4:
            failures.append('cards require four key fields')
        all_rows = comp.get('rows', []) + comp.get('hidden_rows', [])
        fields = [r.get('field') for r in all_rows]
        if len(set(fields)) != len(fields) or any(f not in fields for f in comp.get('key_fields', [])):
            failures.append('comparison fields missing/duplicated')
        for row in all_rows:
            if len(row.get('values', [])) != len(models) or row.get('better') not in (None, 0, 1):
                failures.append('invalid comparison row shape')
                continue
            if len(models) > 2 and row.get('better') is not None:
                failures.append('cards cannot have winners')
            for code, text in zip(models, row['values']):
                if not public_cell_matches(text, rows[code], row['field']):
                    failures.append('comparison unit/value differs: ' + row['field'])
            if len(models) == 2:
                identical = row['values'][0] == row['values'][1]
                if (row in comp.get('hidden_rows', [])) != identical:
                    failures.append('identical/differing row partition wrong')
                field = row['field']
                direction = 'higher' if 'torque' in field or field == 'cycles_per_hour' else 'lower' if field.startswith(('operating_time','fla','lra','motor_power')) else None
                raw_pairs = [(rows[models[0]].get(k), rows[models[1]].get(k)) for k,_ in components(field)]
                winner = None
                if direction and all(x and y for x,y in raw_pairs):
                    winners = {0 if (number(x)>number(y) if direction=='higher' else number(x)<number(y)) else 1 for x,y in raw_pairs if number(x)!=number(y)}
                    if len(winners) == 1:
                        winner = winners.pop()
                if row.get('better') != winner:
                    failures.append('comparison numeric winner differs: ' + field)
    for field in expect.get('active_filters_include', []):
        if field not in [f['field'] for f in observed.get('active_filters', [])]:
            failures.append('active filter missing: ' + field)
    if 'candidate_total' in expect and observed.get('candidate_total') != expect['candidate_total']:
        failures.append('SQL candidate total differs')
    if 'eligible_codes' in expect and sorted(observed.get('eligible_codes', [])) != sorted(expect['eligible_codes']):
        failures.append('full eligible candidate set differs')
    trace = observed.get('trace', {})
    if trace.get('name') == 'search_actuators' and observed.get('eligible_codes') is not None:
        filters = (trace.get('context_after') or {}).get('filters') or {}
        if sorted(observed['eligible_codes']) != eligible_codes(filters):
            failures.append('SQL eligibility disagrees with independent CSV oracle')
    from backend.conversation.policy import FILTER_FIELDS
    filters = (trace.get('context_after') or {}).get('filters') or {}
    expected_tags = {f for f,v in filters.items() if f in FILTER_FIELDS and v is not None and v is not False}
    if {f['field'] for f in observed.get('active_filters', [])} != expected_tags:
        failures.append('active filter tags disagree with persisted search')
    visible = [observed['answer'], observed.get('lead') or '', *labels]
    visible += [comp.get('summary', ''), comp.get('assumptions', '')] if comp else []
    visible += [r['label'] for r in (comp or {}).get('hidden_rows', [])]
    visible += [q['prompt'] for q in (interaction or {}).get('questions', [])]
    visible += [o['label'] for q in (interaction or {}).get('questions', []) for o in q['options']]
    visible += [f['label'] for f in observed.get('active_filters', [])]
    recommendation = observed.get('recommendation') or {}
    visible += [recommendation.get('ranked_by', '')]
    visible += [item.get('reason', '') for item in recommendation.get('items', [])]
    visible += [field.get('label', '') for item in recommendation.get('items', []) for field in item.get('key_values', [])]
    from scripts.check_public_text import public_text_issues
    failures += public_text_issues('\n'.join(visible))
    if re.search(r'\b(?:Hola|Necesito|actuadores|potencia|requisitos|cancelado|servicio)\b', '\n'.join(visible), re.I):
        failures.append('non-English output')
    meta = observed.get('trace', {}).get('model') or {}
    if meta.get('decision_calls') not in (0, 1):
        failures.append('invalid decision count')
    return failures
