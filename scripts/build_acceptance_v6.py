"""Build fixed v6 cases from the approved EC prompts and frozen CSV, without inference.

Scripted decisions are selfcheck inputs, never sent to a model. Expectations are fixed
before execution; no response is used to generate an expected technical value.
"""
import csv
import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A, B, C = '761A00-11300000/A', '761B00-11300000/A', '762A00-11300000/A'
NA, DC = '761A00-11330C00/A', '761X30-11370000/A'


def lookup(codes=(A,), focus=('overview',), **kwargs):
    return ['get_actuator', dict(part_numbers=list(codes), focus=list(focus), **kwargs)]


def search(**kwargs):
    return ['search_actuators', kwargs]


def ask(field):
    return ['ask_clarification', dict(field=field)]


def bound(value, op='gte'):
    return dict(value=value, op=op)


CALLS = {
 1: [lookup(('761a0011300000/a',), ('motor_power',))],
 2: [lookup(('761A00-11300000',))],
 3: [lookup(('769Z99-11300000/A',))],
 4: [lookup((A, B)), ask('which_product')],
 5: [lookup((A, B))],
 6: [search(service='on_off', min_torque_nm=bound(70, 'gt'))],
 7: [search(service='on_off', min_torque_nm=bound(70))],
 8: [search(service='on_off', frequency_hz=60, max_fla_a=bound(1.5, 'lt')),
     search(refine=True, max_fla_a=bound(1.5, 'lte'))],
 9: [search(supply_voltage_v=110, service='on_off', min_torque_nm=bound(70), max_operating_time_s=bound(20, 'lt'), frequency_hz=60)],
 10: [search(service='on_off', bounds=[dict(field='min_torque_nm', **bound(70)), dict(field='min_torque_nm', **bound(100, 'lte'))])],
 11: [search(service='on_off', min_torque_in_lb=bound(2000))],
 12: [lookup((DC,), ('fla',), focus_frequency_hz=60)],
 13: [lookup((NA,), ('motor_power',)), lookup((NA,), ('motor_power',))],
 14: [lookup(focus=('operating_time',), focus_frequency_hz=50), lookup(focus=('operating_time',), focus_frequency_hz=60)],
 15: [search(service='on_off', frequency_hz=60, max_fla_a=bound(1.5, 'lt'))],
 16: [search(enclosure='weatherproof', service='on_off', supply_voltage_v=110, min_torque_nm=bound(70)), search(refine=True, supply_voltage_v=220)],
 17: [search(service='on_off', supply_voltage_v=110, min_torque_nm=bound(70), max_fla_a=bound(1.5, 'lt'), frequency_hz=60),
      search(refine=True, remove=['max_fla_a'])],
 18: [search(min_torque_nm=bound(70)), ask('cancel'), ['explain_terms', dict(term_keys=['fla'])]],
 19: [search(service='on_off', min_torque_nm=bound(70)), lookup(focus=('motor_power',), cancel_previous=True)],
 20: [search(service='on_off', min_torque_nm=bound(70)), search(service='modulating', refine=True)],
 21: [ask('requirements')],
 22: [search(supply_voltage_v=110, service='on_off', max_fla_a=bound(1.5, 'lt')), search(refine=True, frequency_hz=60)],
 23: [search(supply_voltage_v=24, supply_current='DC', frequency_hz=60), search(refine=True, supply_current='DC', remove=['frequency_hz'])],
 24: [search(min_torque_nm=bound(70)), ask('decline')],
 25: [search(service='on_off', supply_voltage_v=110)],
 26: [search(enclosure='weatherproof', sort_by=['fastest', 'lowest_power'])],
 27: [search(sort_by=['lowest_power'])],
 28: [search(service='on_off', min_torque_nm=bound(999999))],
 29: [lookup((A, B)), lookup((B, A))],
 30: [ask('requirements')],
 31: [lookup(focus=('motor_power',))],
 32: [lookup((NA,), ('motor_power',))],
 33: [ask('term_not_in_summary')],
 34: [ask('unsupported')],
 35: [lookup()],
 36: [search(service='on_off', supply_voltage_v=110, min_torque_nm=bound(50), assumptions={'service': 'abrir completo o cerrar completo'})],
 37: [lookup(focus=('motor_power',)), lookup(focus=('operating_time',), focus_frequency_hz=60)],
 38: [lookup(focus=('fla',), focus_frequency_hz=60, explain_terms='fla')],
 39: [lookup(focus=('motor_power',)), lookup(focus=('motor_power',))],
 40: [lookup((A, B), ('torque', 'fla', 'lra', 'operating_time'), explain_terms='fla,lra,duty_cycle')],
}


def build():
    from backend.conversation.tool_wire import canonical_arguments
    from backend.conversation.policy import FILTER_FIELDS
    cases = json.loads((ROOT / 'config/agent_acceptance_cases_v5.json').read_text(encoding='utf-8'))
    cases['version'] = 'acceptance-v6-offline'
    cases['frozen_note'] = 'All 63 v5 scenario IDs and exact queries retained; all 40 approved EC prompts added. Scripted selfcheck is not real-model evidence.'
    cases['review_note'] = 'T7 questions/options, optional suggestions, comparison table/cards and exploratory policies supersede v5 presentation; no paid v6 approval is implied.'
    changes = cases.setdefault('presentation_changes', [])
    for scenario in cases['scenarios']:
        for i, turn in enumerate(scenario['turns']):
            for expected in turn.get('expect_any') or [turn['expect']]:
                expected['contract_v6'] = True
                if expected.get('clarification') == ['requirements'] and scenario['id'] in ('vague_application', 'h4_any_recommendation'):
                    expected['clarification'] = ['service']
                    expected['interaction_ids'] = ['service', 'supply_voltage_v', 'supply_current']
                if 'suggested_replies_count' in expected:
                    count = 3 if scenario['id'] in ('t6_manual_04', 't6_manual_08') and i == 1 else 1 if scenario['id'] == 't6_manual_02' and i == 1 else 0
                    expected['suggested_replies_count'] = count
                if scenario['id'] == 'h_compare_three':
                    expected.pop('clarification', None)
                    expected.pop('contains', None)
                    expected.update(comparison_layout='cards', comparison_models=[A, B, C], lead_required=True)
                if scenario['id'] == 'h4_hello':
                    expected.pop('clarification', None)
                    expected.update(tool='greeting', no_clarification=True, interaction_ids=[], suggestions_count=0,
                                    contains=['Hello.', 'Series 76 actuators'])
                if scenario['id'] == 'h_24v_ac':
                    expected.pop('clarification', None)
                    expected.update(no_clarification=True, interaction_ids=[], suggestions_count=0)
                if scenario['id'] == 't6_manual_05' and i == 1:
                    expected['contains'] = ['service is still open']
                    expected.pop('no_products', None)
                    expected['product_count'] = 3
            if scenario['id'].startswith('t6_manual') or scenario['id'] in ('h_compare_three', 'vague_application', 'h4_any_recommendation', 'h4_hello', 'h_24v_ac'):
                changes.append(dict(scenario=scenario['id'], turn=i+1, reason='Approved T7 replaces forced suggestions, single questions and pair selection with structured interactions and comparison layouts.'))

    with (ROOT / 'data/extracted/series76/catalog.csv').open(encoding='utf-8-sig', newline='') as file:
        rows = {r['base_part_number']: r for r in csv.DictReader(file)}
    source = (ROOT / 'docs/evaluation/edge-case-suite.es.md').read_text(encoding='utf-8')
    for line in source.splitlines():
        match = re.match(r'\| EC(\d+) \|', line)
        if not match:
            continue
        n = int(match[1]); queries = re.findall(r'`([^`]+)`', line.split('|')[3])
        scenario = dict(id=f'EC{n:02}', category='edge_v6', set='edge_v6', turns=[])
        state = {}
        for index, (query, call) in enumerate(zip(queries, CALLS[n], strict=True)):
            name, args = call
            normalized = canonical_arguments(name, args)
            expected = dict(tool=name, contract_v6=True)
            if name == 'search_actuators':
                if not args.get('refine') and not args.get('remove'):
                    state = {}
                for removed in args.get('remove', []):
                    state.pop(removed, None)
                state.update({k:v for k,v in normalized.items() if k in FILTER_FIELDS})
                expected['args'] = deepcopy(state)
                expected['only_filters'] = True
                if n == 23 and index == 0:
                    expected['conflict'] = 'dc_frequency'
                    state.pop('frequency_hz'); state.pop('supply_current')
                if n == 25:
                    expected['args'].pop('supply_voltage_v')
                    expected.update(interaction_ids=['supply_voltage_v'], question_options={'supply_voltage_v': ['110', '220']}, suggestions_count=0)
                if n in (6,7,10,11):
                    field = 'on_off_torque_in_lb' if n == 11 else 'on_off_torque_nm'
                    def eligible(row):
                        value = row[field] or row['shared_torque_in_lb' if n == 11 else 'shared_torque_nm']
                        return bool(value) and (float(value) > 70 if n == 6 else float(value) >= 70 if n == 7 else 70 <= float(value) <= 100 if n == 10 else float(value) >= 2000)
                    expected['eligible_codes'] = [code for code,row in rows.items() if eligible(row)]
                    expected['candidate_total'] = len(expected['eligible_codes'])
                if n == 18 or n == 24 and index == 0:
                    expected.update(interaction_ids=['service'], suggestions_count=0)
                if n == 22 and index == 0:
                    expected.update(interaction_ids=['frequency_hz'], question_options={'frequency_hz': ['50', '60']})
                if n == 20 and index == 1:
                    expected.update(assumption_required=True, contains=['same performance'])
                if n == 17 and index == 1:
                    expected['context_filter_absent'] = ['max_fla_a']
                if n == 28:
                    maximum = max(float(r['on_off_torque_nm'] or r['shared_torque_nm'] or 0) for r in rows.values())
                    expected.update(no_products=True, contains=['No actuator', f'{maximum:g} Nm'], no_clarification=True)
                if n in (26,27):
                    expected['args']['sort_by'] = args['sort_by']
                    expected['contains'] = ['not total electrical consumption']
            elif name == 'get_actuator':
                codes = [A] if n == 1 else args['part_numbers']
                if n != 2:
                    expected['args'] = dict(part_numbers=codes)
                if n == 2:
                    expected.update(clarification=['part_number'], no_products=True, contains=['not a complete Base Part Number'])
                elif n == 3:
                    assert codes[0] not in rows
                    expected.update(no_products=True, contains=['not in the supplied'])
                elif len(codes) > 1:
                    expected.update(comparison_layout='table', comparison_models=codes, lead_required=True, suggestions_count=0)
                else:
                    expected.update(products_include=codes, lead_required=True, suggestions_count=0)
                    focus = args['focus'][0]
                    field = {'motor_power': 'motor_power_w', 'fla': 'fla_unqualified_a' if n == 12 else 'fla_60hz_a',
                             'operating_time': f"operating_time_{args.get('focus_frequency_hz',60)}hz_s"}.get(focus)
                    if field:
                        raw = rows[codes[0]][field]
                        expected['measurements'] = [dict(code=codes[0], field=field, value=float(raw) if raw else None,
                            **({'status':'source_NA'} if not raw else {}))]
                        unit = 'W' if focus == 'motor_power' else 'A' if focus == 'fla' else 's'
                        expected['contains'] = [f'{raw} {unit}'] if raw else ['N/A']
                if n == 5:
                    expected['contains'] = ['cannot identify', 'nameplate']
                if n == 35:
                    expected['contains'] = ['cannot place orders', 'confirm delivery']
                if n in (38,40):
                    expected['terms'] = ['fla'] if n == 38 else ['fla','lra','duty_cycle']
                if n == 40:
                    expected['contains'] = ['Not answered: IP67', 'does not define', 'LRA at 60 Hz: ' + rows[A]['lra_60hz_a'] + ' A']
            elif name == 'ask_clarification':
                expected['args'] = dict(field=args['field'])
                expected['suggestions_count'] = 0
                if args['field'] == 'cancel':
                    expected.update(cancel_cleared=True, no_clarification=True)
                elif args['field'] == 'decline':
                    expected.update(product_count=3, no_clarification=True, contains=['service is still open'])
                elif n == 30:
                    expected['contains'] = ['no prices', 'weighted']
                elif n == 21:
                    expected['interaction_ids'] = ['service','supply_voltage_v','supply_current']
                elif n == 33:
                    expected['contains'] = ['does not define']
                elif n == 34:
                    expected['contains'] = ['Series 76']
                else:
                    expected['clarification'] = [args['field']]
            else:
                expected.update(terms=args['term_keys'], suggestions_count=0)
            if n == 4 and index == 1:
                # EC04 specifies the public ambiguity guard, not the selected tool.
                expected.pop('tool')
                expected.pop('args')
                expected.update(no_products=True, no_comparison=True, interaction_ids=[])
            if n == 30:
                # EC30 permits a limitation: unsupported and requirements both render it.
                expected.pop('args')
                expected.update(no_products=True, no_comparison=True, no_clarification=True, interaction_ids=[])
            scenario['turns'].append(dict(query=query, scripted_decision=call, expect=expected))
        cases['scenarios'].append(scenario)
    assert len(cases['scenarios']) == 103
    (ROOT / 'config/agent_acceptance_cases_v6.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    config = json.loads((ROOT / 'config/agent_acceptance_v5.json').read_text(encoding='utf-8'))
    config['safety_cap_usd'] = 1.00
    config['safety_cap_basis'] = 'Configured maximum for a future explicitly authorised v6 cohort; no inference is authorised by this file.'
    (ROOT / 'config/agent_acceptance_v6.json').write_text(json.dumps(config, indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(ROOT))
    build()
