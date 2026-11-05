"""T10 outcome oracle and mutation tests; no backend fixes or model inference.

Catalogue fixtures are resolved from the validated CSV at execution time. Semantic
checks use concept/negation patterns only where the public API exposes no typed
decline, catalogue-aggregate, interpretation, or suitability result.
"""
import json
import re
import unittest
from decimal import Decimal
from pathlib import Path

from scripts.acceptance_contract import catalogue, eligible_codes

ROOT = Path(__file__).resolve().parents[1]


def resolve(value):
    reference = catalogue()['761A00-11300000/A']
    if isinstance(value, dict):
        if set(value) == {'catalogue_value'}:
            raw = reference[value['catalogue_value']]
            return float(raw) if value['catalogue_value'] in ('supply_voltage_v', 'on_off_torque_nm') else raw
        return {k: resolve(v) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v) for v in value]
    if isinstance(value, str):
        return value.replace('{{reference}}', reference['base_part_number'])
    return value


def norm(value, field):
    if field.startswith(('min_', 'max_')):
        values = value if isinstance(value, list) else [value]
        return sorted((v['op'], Decimal(str(v['value']))) if isinstance(v, dict)
                      else ('gte' if field.startswith('min_') else 'lte', Decimal(str(v))) for v in values)
    return value


NEGATION = r"(?:not|no|never|cannot|can't|doesn't|isn't|unavailable|unpublished|absent|missing)"
CONCEPTS = {'price': r'\b(?:prices?|cost|pricing)\b',
            'lead_time': r'\b(?:lead\s*times?|delivery|shipping|dispatch)\b',
            'sil': r'\b(?:sil|safety integrity)\b', 'weight': r'\b(?:weight|mass)\b'}


def declined(answer, concept):
    return any(re.search(NEGATION, sentence, re.I) and re.search(CONCEPTS[concept], sentence, re.I)
               for sentence in re.split(r'[.!?;\n]+', answer))


def verify(spec, observed):
    allowed = {'filters', 'absent', 'questions_absent', 'products_satisfy', 'nonempty',
               'objective', 'rank', 'declined', 'published', 'all_or_cap', 'voltage_facts',
               'hazard_confirmation', 'hazard_clear', 'weatherproof_suitability',
               'ranking_label', 'interpretation'}
    if set(spec) - allowed:
        raise ValueError('Unknown T10 expectations: ' + str(set(spec) - allowed))
    errors = []
    context = (observed.get('trace') or {}).get('context_after') or {}
    actual = context.get('filters') or {}
    tags = {x['field']: x.get('label', '') for x in observed.get('active_filters', [])}
    expected = spec.get('filters', {})
    for field, value in expected.items():
        if field not in actual or norm(actual[field], field) != norm(value, field):
            errors.append(f'state {field}: {actual.get(field)!r} != {value!r}')
        if field != 'sort_by' and field not in tags:
            errors.append('active filter missing: ' + field)
    for field in spec.get('absent', []):
        if field in actual or field in tags:
            errors.append('removed filter remains: ' + field)
    questions = {q['id'] for q in (observed.get('interaction') or {}).get('questions', [])}
    clarification = observed.get('clarification') or {}
    questions.add(clarification.get('field'))
    for field in spec.get('questions_absent', []):
        if field in questions:
            errors.append('already stated/removed field asked: ' + field)
    products = observed.get('products', [])
    codes = [p['base_part_number'] for p in products]
    recommendation = observed.get('recommendation') or {}
    ranked = [p['part_number'] for p in recommendation.get('items', [])]
    visible = set(codes + ranked)
    answer = observed.get('answer', '')
    if 'products_satisfy' in spec:
        eligible = set(eligible_codes(spec['products_satisfy']))
        for code in sorted(visible - eligible):
            errors.append('shown product violates expected constraints: ' + code)
    else:
        eligible = set(eligible_codes(expected))
    if spec.get('nonempty') and not visible:
        errors.append('no matching products shown')
    if spec.get('objective') and actual.get('sort_by') != [spec['objective']]:
        errors.append('ranking objective not persisted: ' + str(actual.get('sort_by')))
    if spec.get('rank'):
        ordered = ranked or codes
        field = 'motor_power_w' if spec['rank'] == 'lowest_power' else 'on_off_torque_nm'
        values = {c: Decimal(catalogue()[c][field]) for c in eligible if catalogue()[c].get(field)}
        if not ordered or not values:
            errors.append('ranking has no checkable winner')
        elif ordered[0] not in values or values[ordered[0]] != min(values.values()):
            errors.append('winner is not optimal under expected constraints: ' + ordered[0])
        sequence = [values[c] for c in ordered if c in values]
        if sequence != sorted(sequence):
            errors.append('shown ranking is not ascending: ' + field)
    for concept in spec.get('declined', []):
        if not declined(answer, concept):
            errors.append('requested part not explicitly declined: ' + concept)
    if spec.get('published'):
        if not products or not any(p.get('measurements') for p in products):
            errors.append('published specifications not shown')
    if spec.get('all_or_cap'):
        eligible = set(eligible_codes(spec['products_satisfy']))
        if visible != eligible:
            n, total = len(visible), len(eligible)
            explicit = re.search(rf'\b(?:show(?:ing|n)?|display(?:ing|ed)?|first|top|limited to)\s+(?:only\s+)?{n}\b', answer, re.I)
            total_stated = re.search(rf'\b{total}\b', answer)
            if not n or not explicit or not total_stated or not visible <= eligible:
                errors.append(f'all-matches request silently truncated: shown {n}/{total}')
    if spec.get('voltage_facts'):
        from collections import Counter
        counts = Counter(Decimal(r['supply_voltage_v']) for r in catalogue().values()
                         if r['data_status'] == 'reported' and r['supply_voltage_v'])
        # Count of distinct voltages OR complete published voltage enumeration.
        count_ok = re.search(rf'\b{len(counts)}\s+(?:(?:different|distinct|available|published)\s+)*(?:supply\s+)?voltages?\b', answer, re.I)
        listed = {Decimal(n) for n in re.findall(r'\b(\d+(?:\.\d+)?)\s*V\b', answer)}
        if not count_ok and listed != set(counts):
            errors.append('SQL voltage count/list missing or incorrect')
    if spec.get('hazard_confirmation'):
        if 'enclosure' not in questions:
            errors.append('hazard enclosure confirmation missing')
        if any(catalogue()[c]['enclosure'] != 'explosionproof' for c in visible):
            errors.append('hazard preview includes weatherproof model')
    if spec.get('hazard_clear') and context.get('hazard_signal'):
        errors.append('cleared hazard still active')
    if spec.get('weatherproof_suitability'):
        if not re.search(r'\bweatherproof\b', answer, re.I):
            errors.append('known enclosure not stated')
        if not re.search(r'\b(?:not|isn.t)\s+(?:an?\s+)?explosion[- ]?proof\b', answer, re.I):
            errors.append('weatherproof not explicitly distinguished from explosionproof')
        alternatives = [c for c in visible if catalogue()[c]['enclosure'] == 'explosionproof']
        if not alternatives and not re.search(r'\b(?:equivalent|alternative|find|show|look for|offer)\w*\b[^.!?\n]*\bexplosion[- ]?proof\b|\bexplosion[- ]?proof\b[^.!?\n]*\b(?:equivalent|alternative)\w*', answer, re.I):
            errors.append('explosionproof equivalents not offered')
    if spec.get('ranking_label'):
        label = recommendation.get('ranked_by') or ''
        bounds = expected.get('min_torque_nm') or expected.get('min_torque_in_lb')
        limits = bounds if isinstance(bounds, list) else [bounds] if bounds else []
        if not label:
            errors.append('ranking label missing')
        elif spec.get('objective') == 'lowest_power':
            if not re.match(r'(?:lowest|least|minimum)\s+(?:motor\s+)?power', label, re.I):
                errors.append('ranking label does not name lowest motor power first')
        elif limits:
            target = str(limits[0]['value'])
            if not re.search(r'(?<!\d)' + re.escape(target) + r'(?:\.0+)?(?!\d)', label):
                errors.append('ranking label omits or changes torque boundary')
            unit = 'Nm' if 'min_torque_nm' in expected else 'in-lb'
            if unit.lower() not in label.lower():
                errors.append('ranking label omits or changes torque unit')
            upper_only = all(x['op'].startswith('l') for x in limits)
            if upper_only and re.search(r'\babove\b|\bat least\b', label, re.I):
                errors.append('ranking label reverses upper bound')
            if any(x['op'] in ('gt', 'lt') for x in limits) and re.search(r'\bat or\b', label, re.I):
                errors.append('ranking label incorrectly includes strict boundary')
    if spec.get('interpretation'):
        if re.search(r'\bread as\s*(?:[.;\n]|$)|\binterpretation\s*:\s*(?:[.;\n]|$)', answer, re.I):
            errors.append('empty interpretation clause')
    return errors


class T10OracleTests(unittest.TestCase):
    def observed(self, **updates):
        data = dict(trace={'context_after': {'filters': {}}}, products=[], active_filters=[],
                    answer='', clarification=None, interaction=None, recommendation=None)
        data.update(updates)
        return data

    def test_suite_covers_all_defects_with_three_variants(self):
        cases = json.loads((ROOT / 'config/agent_acceptance_cases_t10.json').read_text(encoding='utf-8'))
        for i in range(1, 17):
            scenarios = [s for s in cases['scenarios'] if s['t10_defect'] == f'D{i}']
            self.assertEqual(len(scenarios), 3)
            self.assertEqual(len({s['turns'][-1]['query'] for s in scenarios}), 3)
            for scenario in scenarios:
                for turn in scenario['turns']:
                    self.assertIn('scripted_decision', turn)
                    self.assertIn('t10_oracle', turn['expect'])

    def test_retained_opposite_bound_is_rejected(self):
        expected = {'min_torque_nm': {'op': 'lte', 'value': 50}}
        o = self.observed(trace={'context_after': {'filters': expected}}, active_filters=[{'field': 'min_torque_nm'}])
        self.assertEqual(verify({'filters': expected}, o), [])
        o['trace']['context_after']['filters'] = {'min_torque_nm': [{'op': 'gte', 'value': 50}, expected['min_torque_nm']]}
        self.assertTrue(verify({'filters': expected}, o))

    def test_product_check_uses_expected_not_broken_actual_filters(self):
        code = next(c for c, row in catalogue().items() if row['enclosure'] == 'explosionproof')
        o = self.observed(products=[{'base_part_number': code}])
        self.assertTrue(verify({'products_satisfy': {'enclosure': 'weatherproof'}}, o))

    def test_no_results_cannot_pass_nonempty(self):
        self.assertTrue(verify({'nonempty': True}, self.observed()))

    def test_compound_declines_require_both_concepts(self):
        spec = {'declined': ['price', 'lead_time']}
        self.assertTrue(verify(spec, self.observed(answer='No prices are published.')))
        self.assertEqual(verify(spec, self.observed(answer='Prices and delivery times are not published.')), [])

    def test_reasked_field_is_rejected(self):
        self.assertTrue(verify({'questions_absent': ['phase_count']}, self.observed(
            interaction={'questions': [{'id': 'phase_count'}]})))

    def test_missing_objective_is_rejected(self):
        self.assertTrue(verify({'objective': 'lowest_power'}, self.observed()))

    def test_strict_boundary_label_is_rejected(self):
        self.assertTrue(verify({'ranking_label': True, 'filters': {'min_torque_nm': {'op': 'lt', 'value': 100}}},
                               self.observed(recommendation={'ranked_by': 'closest torque at or below 100 Nm'})))

    def test_blank_interpretation_is_rejected_but_omission_allowed(self):
        self.assertTrue(verify({'interpretation': True}, self.observed(answer="'outside' read as .")))
        self.assertEqual(verify({'interpretation': True}, self.observed(answer='Weatherproof models.')), [])

    def test_unknown_expectation_fails_closed(self):
        with self.assertRaises(ValueError):
            verify({'typo': True}, self.observed())

    def test_fixture_values_come_from_csv(self):
        value = resolve({'catalogue_value': 'on_off_torque_nm'})
        self.assertEqual(Decimal(str(value)), Decimal(catalogue()['761A00-11300000/A']['on_off_torque_nm']))


if __name__ == '__main__':
    unittest.main()
