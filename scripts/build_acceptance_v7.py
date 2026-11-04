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
    require('P1-03', lead_contains=['is faster at 60 Hz: 30 s vs 88 s'])
    cases['scenarios'].extend(heldout['scenarios'])
    (CONFIG / 'agent_acceptance_cases_v7.json').write_text(json.dumps(cases, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print({'v6_cases': len(by_id), 'v7_cases': len(cases['scenarios'])})


if __name__ == '__main__':
    main()
