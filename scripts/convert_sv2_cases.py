"""Offline oracle authoring: v1 validated state snapshots -> explicit full v2 decisions.

This is NOT a runtime adapter or language parser for v2. All expected assertions and
user turns are copied unchanged. The snapshots describe ideal interpretation, not
a live-model score. Reference-derived numeric constraints become symbolic clauses.
"""
from copy import deepcopy
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.conversation import state_v2 as v2
from backend.conversation import policy, quality
from scripts.agent_acceptance import t10_oracle


SORT_PRIORITY = {'fastest': ('operating_time', 'lowest'), 'lowest_power': ('motor_power', 'lowest'),
                 'highest_torque': ('torque', 'highest'), 'lowest_current': ('fla', 'lowest')}


def evidence_for(field, value, texts):
    unit = v2.UNITS.get(field, '')
    if not unit:
        return texts[-1]
    for text in reversed(texts):
        try:
            v2.quantity_ok(str(value), unit, text, field)
            return text
        except v2.Rejected:
            pass
    # Preserve ungrounded fixture values as rejected decisions, never forge a quote.
    return texts[-1]


def convert(scenario, observed):
    scenario = t10_oracle().resolve(deepcopy(scenario))
    texts = []
    for index, (turn, old) in enumerate(zip(scenario['turns'], observed['turns'])):
        texts.append(turn['query'])
        trace = old['trace']
        context = trace.get('context_after') or {}
        prior = trace.get('context_before') or {}
        raw_name, raw = turn.get('scripted_decision') or (trace['name'], trace.get('raw_parameters') or {})
        filters = context.get('filters', {})
        clauses = []
        for field, value in filters.items():
            if field not in policy.FILTER_FIELDS or value is None:
                continue
            for item in value if isinstance(value, list) else [value]:
                amount = item.get('value') if isinstance(item, dict) else item
                op = item.get('op') if isinstance(item, dict) else ('gte' if field.startswith('min_') else 'lte' if field.startswith('max_') else 'eq')
                clauses.append(dict(field=field, op=op, value=str(amount).lower() if isinstance(amount, bool) else str(amount),
                                    unit=v2.UNITS.get(field, ''), evidence=evidence_for(field, amount, texts)))
        relative = raw.get('reference_operation') or ('stronger' if scenario.get('t10_defect') == 'D9' and index else '')
        if relative:
            reference = (prior.get('part_numbers') or prior.get('on_screen') or [None])[0]
            for clause in clauses:
                if clause['field'] in ('min_torque_nm', 'supply_voltage_v', 'enclosure'):
                    clause.update(reference=reference, value='', unit='', evidence=texts[-1])
        selection = context.get('selection_priority')
        priorities = []
        if selection:
            p = dict(selection)
            p['evidence'] = evidence_for('frequency_hz', p['frequency_hz'], texts) if p.get('frequency_hz') else texts[-1]
            priorities.append(p)
        else:
            for objective in filters.get('sort_by', []):
                if objective in SORT_PRIORITY:
                    metric, direction = SORT_PRIORITY[objective]
                    priorities.append(dict(metric=metric, direction=direction, evidence=texts[-1]))
        name = trace['name']
        intent = ('search' if name in ('search_actuators', 'ranked_list', 'ranked_page') else
                  'recommend_from_shown' if name == 'ranked_pick' else
                  'explain' if name == 'explain_terms' else 'lookup' if old.get('products') else 'clarify')
        if raw.get('intent') in ('pick', 'explain_pick') and prior.get('on_screen'):
            intent = 'recommend_from_shown'
        if raw_name == 'get_actuator' and intent == 'clarify' and not old.get('clarification'):
            intent = 'lookup'
        if old['answer'].startswith('I recommend ') and prior.get('on_screen'):
            intent = 'recommend_from_shown'
        refs = (prior.get('on_screen') or []) if intent == 'recommend_from_shown' else (
            old.get('products') or (context.get('part_numbers') or []) if intent == 'lookup' else [])
        if intent == 'lookup' and not refs:
            refs = (old.get('comparison') or {}).get('models') or raw.get('part_numbers') or prior.get('part_numbers') or []
        if intent == 'lookup' and len(refs) >= 2:
            intent = 'compare'
        unsupported = []
        patterns = {
            'price': r'price|cost|precio|cheapest', 'lead time': r'lead time|delivery|shipping',
            'stock': r'stock|availability', 'mounting dimensions': r'mounting|dimensions',
            'installation': r'install', 'wiring': r'wiring', 'bolt pattern': r'bolt|bracket hole',
            'warranty': r'warranty', 'SIL': r'\bSIL\b', 'weight': r'weight|mass',
            'imputation': r'fill.*N/A|borrow|substitut|transfer',
        }
        for label, pattern in patterns.items():
            if re.search(pattern, texts[-1], re.I):
                unsupported.append(label)
        for label, template in v2.LIMITATIONS.items():
            if template in old['answer'] and label not in unsupported:
                unsupported.append(label)
        if re.search(r'\b(?:buy|order|purchase)\b', texts[-1], re.I) and 'cannot process orders' in old['answer']:
            unsupported.append('orders')
        if 'nameplate' in old['answer']:
            unsupported.append('installed identity')
        if "doesn't define that term" in old['answer']:
            unsupported.append('unknown term')
        unsupported = list(dict.fromkeys(unsupported))
        for label in raw.get('unsupported_requests', []):
            if label in v2.LIMITATIONS and label not in unsupported:
                unsupported.append(label)
        for concept in turn.get('expect', {}).get('t10_oracle', {}).get('declined', []):
            label = {'lead_time': 'lead time', 'sil': 'SIL'}.get(concept, concept)
            if label not in unsupported:
                unsupported.append(label)
        focus = raw.get('focus') or context.get('focus') or ['overview']
        focus = quality.normalized_focus(focus)
        view = dict(focus=list(dict.fromkeys(f['field'] for f in focus)), limit=3)
        for f in focus:
            if f.get('frequency_hz'):
                view.update(frequency_hz=f['frequency_hz'], evidence=evidence_for('frequency_hz', f['frequency_hz'], texts))
            if f.get('service'):
                view.update(service=f['service'], evidence=texts[-1])
        hz = re.search(r'\b(50|60)\s*Hz', texts[-1], re.I)
        if hz and intent in ('lookup', 'compare'):
            view.update(frequency_hz=int(hz.group(1)), evidence=texts[-1])
        pending = ''
        topic = raw.get('topic', '')
        is_core_oracle = any(k in scenario for k in ('t10_defect', 't12_class', 't14_class'))
        if old.get('clarification') and (name not in ('search_actuators', 'ranked_pick') or not is_core_oracle):
            pending = old['clarification']['field']
            if name != 'search_actuators':
                intent = 'clarify'
        if name in ('greeting', 'courtesy', 'ranking_explanation'):
            topic = 'ranking' if name == 'ranking_explanation' else name
        if name == 'document_limitation':
            if "I'm the Series 76 catalogue assistant" in old['answer']:
                topic = 'identity'
            else:
                intent, pending, refs = 'explain', '', []
                view['focus'] = []
                if not unsupported:
                    unsupported = ['other']
        if 'cannot reveal' in old['answer']:
            topic = 'privacy'
        if name == 'catalogue_answer' or scenario.get('t10_defect') == 'D13':
            topic = 'voltage_counts'
        if scenario.get('t12_class') == 'supply_overview':
            topic = 'supply_overview'
        if scenario.get('t14_class') == 'capabilities':
            topic = 'capabilities'
        if topic:
            intent, pending = 'explain', ''
            view['topic'] = topic
        if raw_name == 'ask_clarification' and not topic:
            pending = raw.get('field', 'requirements')
            if pending in ('cancel', 'decline'):
                view['topic'], pending = pending, ''
        if scenario.get('t10_defect') in ('D10', 'D11'):
            refs = raw['part_numbers']
            intent, pending = 'lookup', ''
            view['focus'] = []
        if scenario.get('t12_class') == 'no_imputation' and index:
            intent, pending, refs = 'explain', '', []
            unsupported = ['imputation']
        terms = raw.get('explain_terms') or raw.get('term_keys') or []
        if isinstance(terms, str):
            terms = [t.strip() for t in terms.split(',') if t.strip()]
        if terms:
            view['terms'] = terms
        if scenario.get('t10_defect') == 'D12':
            view['limit'] = 100
        if topic == 'supply_services' and not clauses:
            voltage = re.search(r'\b(24|110|220)\s*V', texts[-1], re.I)
            if voltage:
                clauses.append(dict(field='supply_voltage_v', value=voltage.group(1), op='eq', unit='V', evidence=texts[-1]))
        if scenario.get('t14_class') in ('single_reference',) and not refs:
            refs = prior.get('part_numbers') or []
            intent, pending = 'lookup', ''
        hazard = 'yes' if context.get('hazard_signal') or policy.hazard_signal(texts[-1]) else 'no' if policy.nonhazard_signal(texts[-1]) else 'unknown'
        if hazard == 'unknown' and index and not prior.get('hazard_signal'):
            earlier_clearance = next((t for t in reversed(texts) if policy.nonhazard_signal(t)), None)
            if earlier_clearance:
                hazard = 'no'
        site_evidence = next((t for t in reversed(texts) if (policy.hazard_signal(t) if hazard == 'yes' else policy.nonhazard_signal(t))), texts[-1]) if hazard != 'unknown' else ''
        decision = dict(intent=intent, filters=clauses, priority=priorities, references=refs,
                        unsupported_requests=unsupported, pending_question=pending,
                        site_context=dict(hazard=hazard, evidence=site_evidence), view=view)
        turn['scripted_decision'] = [v2.TOOL, decision]
    return scenario


def main():
    scenarios = []
    for label in ('t10', 't12', 't14'):
        source = json.loads((ROOT / f'config/agent_acceptance_cases_{label}.json').read_text(encoding='utf8'))
        path = ROOT / f'reports/agent_acceptance/sv2_v1/{label}.json'
        if not path.exists():
            path = ROOT / f'reports/agent_acceptance/t14_final/{label}.json'
        evidence = {e['scenario']: e for e in json.loads(path.read_text(encoding='utf8'))['examples']}
        for s in source['scenarios']:
            scenarios.append(convert(s, evidence[s['id']]))
    output = dict(version='sv2-oracle', cohort='sv2',
                  note='Offline authored full-state decisions from validated v1 oracle snapshots; original assertions unchanged.', scenarios=scenarios)
    (ROOT / 'config/agent_acceptance_cases_sv2.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print('Converted', len(scenarios), 'scenarios; original expectations unchanged.')


if __name__ == '__main__':
    main()
