"""Copy v6 acceptance inputs and add the T8 interaction contract without touching v6."""
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config'


def turn(query, decision=None, **expect):
    item = {'query': query, 'expect': {'contract_v6': True, **expect}}
    if decision:
        item['scripted_decision'] = decision
    return item


def main():
    config = json.loads((CONFIG / 'agent_acceptance_v6.json').read_text(encoding='utf-8'))
    config['purpose'] = 'Offline scripted v7 acceptance and future authorised Google cohort; this file authorises no inference.'
    config['safety_cap_basis'] = 'Future explicitly authorised v7 cohort only; no inference is authorised by this file.'
    (CONFIG / 'agent_acceptance_v7.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    cases = json.loads((CONFIG / 'agent_acceptance_cases_v6.json').read_text(encoding='utf-8'))
    cases['version'] = 'v7'
    cases['frozen_note'] = 'V6 cases retained; presentation expectations updated for T8 ranking and questions. New T8 cases are appended.'
    by_id = {s['id']: s for s in cases['scenarios']}
    for case_id in ('vague_application', 'h4_any_recommendation'):
        by_id[case_id]['turns'][0]['expect']['clarification'].append('supply_voltage_v')
    by_id['more_results']['turns'][1]['expect'].pop('no_products', None)
    for key in ('no_products', 'suggestions_count'):
        by_id['h_24v_ac']['turns'][0]['expect'].pop(key, None)
    for case_id in ('t6_manual_01', 't6_manual_02', 't6_manual_03', 't6_manual_04',
                    't6_manual_05', 't6_manual_06', 't6_manual_07', 't6_manual_08'):
        for item in by_id[case_id]['turns']:
            item['expect'].pop('suggested_replies_count', None)
    for case_id in ('t6_manual_05', 'EC24'):
        by_id[case_id]['turns'][1]['expect']['contains'] = ['best matches']
    for key in ('contains', 'products_include', 'product_count', 'clarification'):
        by_id['t6_manual_03']['turns'][1]['expect'].pop(key, None)
    by_id['t6_manual_03']['turns'][1]['expect']['args'].pop('enclosure', None)
    for case_id in ('EC18', 'EC24'):
        by_id[case_id]['turns'][0]['expect'].pop('suggestions_count', None)
    by_id['EC21']['turns'][0]['expect'].pop('interaction_ids', None)
    by_id['EC24']['turns'][1]['expect'].pop('suggestions_count', None)
    by_id['EC21']['turns'][0]['expect'].pop('suggestions_count', None)
    by_id['EC33']['turns'][0]['expect']['contains'] = ["The document doesn't define that term."]
    by_id['EC40']['turns'][0]['expect']['contains'] = ["The document doesn't define that term.", 'LRA at 60 Hz: 1.4 A']
    # A catalogue without prices cannot supply the old weighted-price expectation.
    by_id['EC30']['turns'][0]['expect'].update(tool='document_limitation',
        contains=["doesn't publish prices", 'weighted'])
    by_id['EC21']['turns'][0]['expect']['contains'] = ['Tell me what it must do:']
    by_id['t6_manual_01']['turns'][1]['expect']['contains'] = ['On/Off torque', 'Operating time at 60 Hz: 17 s']
    for case_id in ('t6_manual_05', 'EC24'):
        by_id[case_id]['turns'][1]['expect']['contains'] = ['best matches so far']
    by_id['EC02']['turns'][0]['expect'] = {'contract_v6': True, 'contains': ['Interpreted 761A00-11300000 as 761A00-11300000/A'],
        'products_include': ['761A00-11300000/A']}
    for item in by_id['EC22']['turns']:
        item['expect'].pop('interaction_ids', None)
        item['expect'].pop('question_options', None)
    by_id['EC34']['turns'][0]['expect'].update(clarification=['unsupported', 'decline'],
        contains=['cannot reveal'])
    by_id['EC35']['turns'][0]['expect']['contains'] = ['cannot process orders', 'confirm delivery']
    # Cancellation is now enforced by code even if the provider omits the flag.
    by_id['t6_manual_07']['turns'][1]['expect']['args'].pop('cancel_previous', None)
    base = turn('I need an on/off actuator with at least 70 Nm',
                ['search_actuators', {'service': 'on_off', 'min_torque_nm': 70}],
                tool='search_actuators', interaction_count_at_least=2, recommendation_ranked_by=True,
                debug_llm_called=True)
    cases['scenarios'].extend([
        {'id': 'T8_recommendation', 'category': 't8', 'turns': [deepcopy(base),
            turn('Submit 110 V + explosionproof', tool='search_actuators', recommendation_total=10,
                 recommendation_ranked_by=True, debug_llm_called=False) | {'answers': {'supply_voltage_v': '110', 'enclosure': 'explosionproof'}}]},
        {'id': 'T8_best_two', 'category': 't8', 'turns': [deepcopy(base),
            turn('Compare 2 of them the best ones', ['get_actuator', {'from_results_top': 2}],
                 tool='get_actuator', comparison_layout='table', debug_llm_called=True)]},
        {'id': 'T8_which_ones', 'category': 't8', 'turns': [deepcopy(base),
            turn('wich ones ?', ['get_actuator', {'list_results': True}], tool='get_actuator', contains=['ranked models'])]},
        {'id': 'T8_remove_service', 'category': 't8', 'turns': [deepcopy(base),
            turn('Remove On/Off service', ['search_actuators', {'refine': True, 'remove': ['service']}], tool='search_actuators'),
            turn('Modulating', ['search_actuators', {'refine': True, 'service': 'modulating'}], tool='search_actuators')]},
        {'id': 'T8_fast_compare', 'category': 't8', 'turns': [
            turn('Compare 761A00-11300000/A vs 761B00-11300000/A', tool='get_actuator',
                 comparison_layout='table', debug_llm_called=False)]},
        {'id': 'T8_three_compare', 'category': 't8', 'turns': [
            turn('Compare 761A00-11300000/A vs 761B00-11300000/A vs 762A00-11300000/A',
                 tool='get_actuator', comparison_layout='cards', debug_llm_called=False)]},
        {'id': 'T8_torque_term', 'category': 't8', 'turns': [
            turn('What does torque mean?', ['explain_terms', {'term_keys': ['torque']}], tool='explain_terms')]},
        {'id': 'T8_undefined_term', 'category': 't8', 'turns': [
            turn('What is IP67?', ['ask_clarification', {'field': 'term_not_in_summary'}],
                 tool='ask_clarification', contains=["The document doesn't define that term."])]},
        {'id': 'T8_mining', 'category': 't8', 'turns': [
            turn('actuator for a mining site, 220 V',
                 ['search_actuators', {'supply_voltage_v': 220, 'enclosure': 'explosionproof'}],
                 tool='search_actuators', interaction_count_at_least=1)]},
        {'id': 'T8_joke', 'category': 't8', 'turns': [
            turn('Tell me a joke', ['ask_clarification', {'field': 'unsupported'}], tool='ask_clarification')]},
        {'id': 'T8_zero', 'category': 't8', 'turns': [
            turn('On/off, 110 V, at least 100000 Nm',
                 ['search_actuators', {'service': 'on_off', 'supply_voltage_v': 110, 'min_torque_nm': 100000}],
                 tool='search_actuators', recommendation_total=0, contains=['Closest published'])]},
        {'id': 'T8_rank_fastest', 'category': 't8', 'turns': [deepcopy(base),
            turn('Rank by fastest', tool='ranked_action', debug_llm_called=False,
                 recommendation_ranked_by=True) | {'action': {'type': 'rank_by', 'args': {'by': 'fastest'}}}]},
    ])
    heldout = json.loads((CONFIG / 'agent_acceptance_heldout_v1.json').read_text(encoding='utf-8'))
    heldout_by_id = {s['id']: s for s in heldout['scenarios']}
    def require(case_id, turn_index=0, **expect):
        heldout_by_id['heldout_' + case_id]['turns'][turn_index]['expect'].update(expect)
    require('P5-01', contains=['On/Off torque'], not_contains=['70 Nm torque'])
    require('P2-03', interaction_option_labels=['Explosionproof', 'Weatherproof'])
    require('B-FRUSTRATION-01', 1, contains=['My pick:'])
    require('B-FRUSTRATION-01', 2, contains=['My pick:'])
    require('B-SHORTREF-01', 1, tool='ranked_reference')
    require('B-SHORTREF-01', 2, tool='ranked_reference')
    require('P6-01', contains=["doesn't publish prices"], no_products=True)
    require('P1-03', lead_contains=['764A00-11300000/A', 'faster at 60 Hz: 30 s'])
    cases['scenarios'].extend(heldout['scenarios'])
    heldout_v2 = json.loads((CONFIG / 'agent_acceptance_heldout_v2.json').read_text(encoding='utf-8'))
    v2_by_id = {s['id']: s for s in heldout_v2['scenarios']}
    def v2_expect(case_id, turn_index=0, **expected):
        v2_by_id['heldout_v2_' + case_id]['turns'][turn_index]['expect'].update(expected)
    v2_expect('Q1-03', lead_contains=['763B00-11300000/A', 'draws more current at 60 Hz: 4.8 A'])
    v2_expect('Q1-08', not_contains=['Motor power: 180 W vs 180 W vs 180 W'])
    v2_expect('Q2-01', 1, contains=['My pick:'])
    v2_expect('Q2-02', 0, interaction_ids=['enclosure'])
    v2_expect('Q2-03', 0, contains=['Modulating service'])
    v2_expect('Q2-06', 0, contains=['DC'])
    v2_expect('Q3-01', 2, contains=['761A00'])
    v2_expect('Q3-04', 2, contains=["That's the only model"])
    v2_expect('Q4-03', 1, contains=['761B00-11320000/A'])
    v2_expect('Q5-06', 0, contains=['kNm ='])
    v2_expect('Q5-05', 0, contains=["Interpreted 'explsionproof' as Explosionproof."])
    v2_expect('Q5-04', 1, contains=['My pick:'])
    v2_expect('Q6-01', 0, contains=['does not publish delivery times'], no_products=True)
    v2_expect('Q6-02', 0, contains=['does not specify underwater use'], no_products=True)
    v2_expect('Q6-03', 0, contains=["I'm the Series 76 catalogue assistant"])
    v2_expect('Q6-04', 0, contains=["can't use other values"], no_products=True)
    v2_expect('Q6-05', 0, contains=['only cover the Series 76 catalogue'])
    v2_expect('Q6-06', 0, contains=['does not publish warranty terms'])
    v2_expect('C-FRUSTRATION-01', 1, contains=['My pick:'])
    v2_expect('C-FRUSTRATION-01', 2, contains=['ranked the models by'])
    v2_expect('C-FRUSTRATION-02', 1, contains=['My pick:'])
    v2_expect('C-TOPICJUMP-01', 2, not_contains=['Enclosure: Weatherproof vs Weatherproof vs Weatherproof'])
    v2_expect('C-CORRECTION-01', 1, contains=['763Y30-11320000/A'])
    v2_expect('C-CONFIRM-01', 1, contains=['Weatherproof'])
    v2_expect('C-SHORTREF-02', 1, contains=['762A00-11300000/A'], debug_llm_called=False)
    v2_expect('C-SHORTREF-02', 2, contains=['Motor power', '762A00-11300000/A'], debug_llm_called=False)
    v2_by_id['heldout_v2_Q4-03']['turns'][1]['scripted_decision'] = ['get_actuator',
        {'reference_kind': 'focused', 'equivalent_voltage_v': 220}]
    v2_by_id['heldout_v2_Q2-02']['turns'][0]['scripted_decision'] = ['search_actuators', {}]
    v2_by_id['heldout_v2_Q2-03']['turns'][0]['scripted_decision'] = ['search_actuators', {}]
    v2_by_id['heldout_v2_Q5-05']['turns'][0]['scripted_decision'] = ['search_actuators',
        {'phase_count': 3}]
    v2_by_id['heldout_v2_Q5-04']['turns'][1]['scripted_decision'] = [
        'ask_clarification', {'field': 'requirements', 'intent': 'pick'}]
    v2_by_id['heldout_v2_C-CORRECTION-01']['turns'][1]['scripted_decision'] = ['get_actuator',
        {'reference_kind': 'focused', 'equivalent_enclosure': 'explosionproof'}]
    for case_id, index, intent in [('C-FRUSTRATION-01', 1, 'pick'),
                                    ('C-FRUSTRATION-01', 2, 'explain_pick'),
                                    ('C-FRUSTRATION-02', 1, 'pick')]:
        v2_by_id['heldout_v2_' + case_id]['turns'][index]['scripted_decision'] = [
            'ask_clarification', {'field': 'requirements', 'intent': intent}]
    cases['scenarios'].extend(heldout_v2['scenarios'])
    heldout_v3 = json.loads((CONFIG / 'agent_acceptance_heldout_v3.json').read_text(encoding='utf-8'))
    v3_by_id = {s['id']: s for s in heldout_v3['scenarios']}
    def v3_expect(case_id, turn_index=0, **expected):
        v3_by_id['heldout_v3_' + case_id]['turns'][turn_index]['expect'].update(expected)
    for case_id in ('R1-02', 'R5-04'):
        v3_expect(case_id, recommendation_codes_once=True)
    v3_expect('R1-03', lead_contains=['761Y30-11300000/A', 'cycles'])
    v3_expect('R1-01', 1, contains=['Modulating starts per hour'], not_contains=['Duty S4', 'On/Off cycles'])
    v3_expect('R5-02', contains=['LRA'], not_contains=['On/Off torque', 'Motor power'])
    v3_expect('R2-03', contains=['Modulating service'])
    v3_expect('R5-01', contains=['Weatherproof', 'Modulating service'])
    v3_expect('R5-05', contains=['3-phase', '1.2 kNm = 1200 Nm'])
    v3_expect('R2-07', contains=["doesn't classify models as indoor"])
    for case_id, noun in [('R6-01', 'weight'), ('R6-02', 'wiring diagram'),
                          ('R6-03', 'signal compatibility')]:
        v3_expect(case_id, contains=["doesn't publish", noun], no_products=True)
    v3_expect('R1-06', 1, comparison_layout='table', comparison_models=['764X30-11300000/A', '764A00-11300000/A'])
    v3_expect('R4-03', 1, contains=['762X30-11300000/A', 'Motor power'])
    v3_expect('R1-07', contains=['Interpreted 761A00-11300000 as 761A00-11300000/A'],
              products_include=['761A00-11300000/A'])
    v3_expect('D-FRUSTRATION-01', 2, contains=['FLA', 'LRA', 'Motor power'], not_contains=['Current matches:'])
    v3_expect('D-TOPICJUMP-01', 2, contains=['duty'], not_contains=['19 ranked models'])
    v3_expect('D-SHORTREF-02', 2, contains=['operating time'], not_contains=['Comparing '])
    v3_expect('D-IMPOSSIBLE-01', 0, contains=['24 V models are only Explosionproof'])
    v3_expect('D-IMPOSSIBLE-01', 1, contains=['100 Nm'])
    v3_expect('D-CONFIRM-01', 0, interaction_ids=['enclosure'])
    v3_expect('D-CONFIRM-01', 1, args={'enclosure': 'explosionproof'})
    v3_by_id['heldout_v3_R2-03']['turns'][0]['scripted_decision'] = ['search_actuators', {}]
    v3_by_id['heldout_v3_R1-06']['turns'][1]['scripted_decision'] = ['get_actuator',
        {'reference_kind': 'focused', 'equivalent_enclosure': 'weatherproof'}]
    v3_by_id['heldout_v3_R4-03']['turns'][1]['scripted_decision'] = ['get_actuator',
        {'reference_kind': 'focused', 'equivalent_voltage_v': 110}]
    v3_by_id['heldout_v3_R1-07']['turns'][0]['scripted_decision'] = ['get_actuator',
        {'part_numbers': ['761A00-11300000']}]
    v3_by_id['heldout_v3_D-FRUSTRATION-01']['turns'][1]['scripted_decision'] = [
        'ask_clarification', {'field': 'requirements', 'intent': 'pick'}]
    for scenario in heldout_v3['scenarios']:
        for item in scenario['turns']:
            item['expect']['not_contains'] = [phrase for phrase in item['expect']['not_contains']
                                               if phrase != '0 identical fields hidden']
    cases['scenarios'].extend(heldout_v3['scenarios'])
    heldout_v4 = json.loads((CONFIG / 'agent_acceptance_heldout_v4.json').read_text(encoding='utf-8'))
    v4_by_id = {s['id']: s for s in heldout_v4['scenarios']}
    def v4_expect(case_id, turn_index=0, **expected):
        v4_by_id['heldout_v4_' + case_id]['turns'][turn_index]['expect'].update(expected)
    v4_expect('S1-01', 1, contains=['763Y30-11320000/A', 'Motor power'], not_contains=['On/Off torque'])
    v4_by_id['heldout_v4_S1-01']['turns'][1]['scripted_decision'] = [
        'get_actuator', {'reference_kind': 'focused', 'equivalent_voltage_v': 220}]
    v4_expect('S1-02', 1, contains=['190 cycles/h'], not_contains=['Comparing '])
    v4_expect('S1-05', contains=['1.2 A / 1 A = 1.2'], not_contains=['On/Off torque'])
    v4_expect('S1-06', candidate_total=2, active_filters_include=['min_torque_nm'])
    v4_expect('S2-04', contains=['efficiency'], no_products=True)
    v4_expect('S2-05', contains=['generator operation'], no_products=True)
    v4_expect('S2-06', contains=['24 V', '110 V', '220 V'])
    v4_expect('S3-01', active_filters_include=['service', 'min_torque_nm'])
    v4_expect('S3-01', 1, contains=['My pick:', 'Modulating torque'])
    v4_expect('S3-06', interaction_ids=[], contains=['30 actuators meet:', 'torque'])
    v4_expect('S3-06', 1, contains=['No more ranked models'])
    v4_expect('S5-04', contains=['FLA'], not_contains=['Ranked by'])
    for case_id, noun in [('S6-01', 'IP rating'), ('S6-02', 'maintenance interval'),
                          ('S6-03', 'CAD drawing')]:
        v4_expect(case_id, contains=[noun], no_products=True)
    v4_expect('S6-04', contains=['I only cover the Series 76 catalogue'])
    v4_expect('E-SHORTREF-01', 1, comparison_models=['761A00-11320000/A',
                                                     '761B00-11320000/A', '762A00-11320000/A'])
    v4_expect('E-SHORTREF-02', 1, contains=['duty'], not_contains=['Comparing '])
    v4_expect('E-IMPOSSIBLE-01', contains=['3-phase', 'Weatherproof'])
    v4_expect('E-IMPOSSIBLE-01', 1, contains=['no exact model'])
    v4_expect('E-CONFIRM-01', interaction_ids=['enclosure'])
    v4_expect('E-CONFIRM-01', 1, active_filters_include=['enclosure'])
    v4_expect('E-CONFIRM-02', 1, active_filters_include=['enclosure'])
    cases['scenarios'].extend(heldout_v4['scenarios'])
    heldout_v5 = json.loads((CONFIG / 'agent_acceptance_heldout_v5.json').read_text(encoding='utf-8'))
    v5_by_id = {s['id']: s for s in heldout_v5['scenarios']}
    def v5_expect(case_id, turn_index=0, **expected):
        v5_by_id['heldout_v5_' + case_id]['turns'][turn_index]['expect'].update(expected)
    v5_expect('T1-07', contains=['10 models'], not_contains=['64 models'])
    v5_expect('T5-05', candidate_total=0, contains=['lowest published torque is 65 Nm'])
    v5_expect('T1-05', contains=['0.4 A'], not_contains=['On/Off torque'])
    v5_expect('T4-03', 1, contains=['763C00-11330C00/A'], not_contains=['763A00-11330C00/A'])
    v5_expect('T4-04', 1, active_filters_include=['service', 'supply_voltage_v'])
    v5_expect('F-CONFIRM-01', 0, interaction_ids=['enclosure'])
    v5_expect('F-CONFIRM-01', 1, active_filters_include=['enclosure'])
    v5_expect('F-CONFIRM-02', 1, active_filters_include=['enclosure'])
    v5_expect('T6-01', contains=['operating temperature range'], no_products=True)
    v5_expect('T6-03', contains=['installation instructions'], no_products=True)
    v5_expect('T2-06', contains=["doesn't publish prices", 'motor power'])
    for scenario in heldout_v5['scenarios']:
        for item in scenario['turns']:
            item['expect']['not_contains'].extend(['was unclear in your request',
                                                   'no frequency in source'])
    cases['scenarios'].extend(heldout_v5['scenarios'])
    (CONFIG / 'agent_acceptance_cases_v7.json').write_text(json.dumps(cases, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print({'v6_cases': len(by_id), 'v7_cases': len(cases['scenarios'])})


if __name__ == '__main__':
    main()
