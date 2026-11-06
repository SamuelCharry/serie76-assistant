"""Independent T11 level-1 judgments from the electrical CSV, never backend ranks.

Rule (fixed before evaluation): an unpublished or hard-constraint-failing product
gets 0. All numeric bounds must be satisfied by published values at the requested
service/frequency; absent values never count as zero. The CSV's shared service
columns are used for either service, without converting published torque units.
Among compliant products, grade 3 goes to ALL ties on the stated objective alone
(minimum time, motor power or FLA, or maximum torque). Without an objective, grade
3 minimizes adequate torque then FLA, lexicographically. Remaining compliant rows
get 1 if torque exceeds twice a stated positive minimum, their objective value is
missing, or they are more than twice the optimum (less than half for max torque);
otherwise they get 2. Objective winners take precedence over oversizing penalties.
The factor two is an explicit evaluation policy, not a catalogue safety claim.

Only catalog.csv and summary/terms.json are evidence. No backend modules, rank
functions, SQL output, part-number preferences or backend tie breakers are used.
Queries must specify service and frequency for frequency-qualified supplies.
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'data/extracted/series76/catalog.csv'
TERMS = ROOT / 'data/extracted/series76_summary/terms.json'
NUMERIC = {'supply_voltage_v', 'phase_count', 'cycles_per_hour', 'starts_per_hour',
           'motor_power_w'}
OPERATORS = {'gt': lambda a, b: a > b, 'gte': lambda a, b: a >= b,
             'lt': lambda a, b: a < b, 'lte': lambda a, b: a <= b}
OBJECTIVES = {'fastest': 'operating_time', 'lowest_power': 'motor_power',
              'highest_torque': 'torque', 'lowest_current': 'fla'}
BOUND_METRICS = {'min_torque_nm': 'torque', 'min_torque_in_lb': 'torque_in_lb',
                 'min_duty_s4_percent': 'duty', 'min_cycles_per_hour': 'cycles',
                 'min_starts_per_hour': 'starts', 'max_operating_time_s': 'operating_time',
                 'max_fla_a': 'fla', 'max_lra_a': 'lra', 'max_motor_power_w': 'motor_power'}


def load_catalog(path=CATALOG):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for key, value in row.items():
            if key in NUMERIC or key.startswith(('on_off_', 'modulating_', 'shared_',
                                               'operating_time_', 'fla_', 'lra_')):
                row[key] = Decimal(value) if value and value != 'N/A' else None
    if len(rows) != 68 or len({row['base_part_number'] for row in rows}) != 68:
        raise ValueError('Expected the complete 68-product collection')
    return rows


def glossary_evidence(path=TERMS):
    keys = {'on_off', 'modulating', 'fla', 'lra', 'weatherproof', 'explosionproof'}
    terms = json.loads(Path(path).read_text(encoding='utf-8'))['terms']
    return {t['term_key']: t['definition'] for t in terms if t['term_key'] in keys}


def measurement(row, filters, metric):
    if metric in ('torque', 'torque_in_lb', 'duty'):
        stem = {'torque': 'torque_nm', 'torque_in_lb': 'torque_in_lb',
                'duty': 'duty_s4_percent'}[metric]
        service = 'shared' if row['service_layout'] == 'shared' else filters['service']
        return row.get(f'{service}_{stem}')
    if metric in ('cycles', 'starts', 'motor_power'):
        return row[{'cycles': 'cycles_per_hour', 'starts': 'starts_per_hour',
                    'motor_power': 'motor_power_w'}[metric]]
    hz = filters.get('frequency_hz')
    scope = f'{hz}hz' if hz else 'unqualified'
    unit = 's' if metric == 'operating_time' else 'a'
    return row.get(f'{metric}_{scope}_{unit}')


def violations(row, filters):
    failures = []
    if row['data_status'] != 'reported':
        failures.append('catalogue values not reported')
    for field in ('enclosure', 'supply_voltage_v', 'phase_count'):
        if field in filters and row[field] != filters[field]:
            failures.append(field)
    current = filters.get('supply_current')
    if current and row['supply_current'] != current and not (
            current in ('AC', 'DC') and row['supply_current'] == 'AC/DC'):
        failures.append('supply_current')
    if row['service_layout'] not in ('mixed', 'shared', filters['service']):
        failures.append('service')
    if filters.get('csa_required') and row['csa_status'] != 'reported_in_header':
        failures.append('CSA not reported in header')
    if filters.get('frequency_hz') and measurement(row, filters, 'operating_time') is None:
        failures.append('frequency not published')
    for bound in filters.get('bounds', []):
        value = measurement(row, filters, BOUND_METRICS[bound['field']])
        if value is None or not OPERATORS[bound['op']](value, Decimal(str(bound['value']))):
            failures.append(f"{bound['field']} {bound['op']} {bound['value']}")
    return failures


def judge_query(rows, query):
    """Grade all 68 rows with the independent, tie-aware policy above."""
    filters, objective = query['filters'], query.get('objective')
    if objective not in (None, *OBJECTIVES):
        raise ValueError('Unknown objective')
    if filters.get('service') not in ('on_off', 'modulating'):
        raise ValueError('Judgments require an explicit service')
    if filters.get('supply_current') == 'AC' and 'frequency_hz' not in filters:
        raise ValueError('AC judgments require explicit frequency')
    results = {r['base_part_number']: {'grade': 0, 'reasons': violations(r, filters)} for r in rows}
    compliant = [r for r in rows if not results[r['base_part_number']]['reasons']]
    torque_metric = 'torque_in_lb' if any(b['field'] == 'min_torque_in_lb'
                                        for b in filters.get('bounds', [])) else 'torque'
    lower = [Decimal(str(b['value'])) for b in filters.get('bounds', [])
             if b['field'] == ('min_torque_in_lb' if torque_metric == 'torque_in_lb' else 'min_torque_nm')
             and b['op'] in ('gt', 'gte') and b['value'] > 0]
    metric = OBJECTIVES.get(objective, torque_metric)
    if metric == 'torque':
        metric = torque_metric
    infinity = Decimal('Infinity')

    def score(row):
        value = measurement(row, filters, metric)
        if objective:
            return infinity if value is None else -value if objective == 'highest_torque' else value
        current = measurement(row, filters, 'fla')
        return (value if value is not None else infinity,
                current if current is not None else infinity)

    scores = [score(r) for r in compliant]
    best = min(scores) if scores else None
    for row in compliant:
        reasons = []
        value = measurement(row, filters, metric)
        torque = measurement(row, filters, torque_metric)
        if value is not None and score(row) == best:
            grade, reasons = 3, ['best objective value (all ties)' if objective else 'smallest adequate torque, then lower FLA']
        else:
            if lower and torque is not None and torque > 2 * max(lower):
                reasons.append('torque more than twice required minimum')
            if value is None:
                reasons.append('objective value not published')
            elif objective and best != infinity:
                optimum = -best if objective == 'highest_torque' else best
                if (value * 2 < optimum if objective == 'highest_torque' else value > 2 * optimum):
                    reasons.append('objective more than factor two worse than optimum')
            grade = 1 if reasons else 2
            reasons = reasons or ['compliant, good fit']
        results[row['base_part_number']] = {'grade': grade, 'reasons': reasons}
    return results
