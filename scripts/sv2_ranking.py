"""Oracle-filter adapter for the v2 validator and ranker, never language inference."""
from backend.catalog.repository import search_actuators
from backend.conversation import state_v2 as v2


def backend_ranking(connection, query, term_keys):
    clauses, user_parts = [], []
    for field, value in query['filters'].items():
        if field == 'bounds':
            items = [(v['field'], v) for v in value]
        else:
            items = [(field, v) for v in (value if isinstance(value, list) else [value])]
        for field, item in items:
            if item is None:
                continue
            amount = item.get('value') if isinstance(item, dict) else item
            op = item.get('op') if isinstance(item, dict) else ('gte' if field.startswith('min_') else 'lte' if field.startswith('max_') else 'eq')
            unit = v2.UNITS.get(field, '')
            val = str(amount).lower() if isinstance(amount, bool) else str(amount)
            quote = field + ': ' + val + (' ' + unit if unit else '')
            user_parts.append(quote)
            clauses.append(dict(field=field, op=op, value=val, unit=unit, evidence=quote))
    priorities = []
    mapping = {'fastest': ('operating_time', 'lowest'), 'lowest_current': ('fla', 'lowest'),
               'highest_torque': ('torque', 'highest'), 'lowest_power': ('motor_power', 'lowest')}
    if query.get('objective'):
        metric, direction = mapping[query['objective']]
        quote = 'Priority ' + metric + ' ' + direction
        user_parts.append(quote)
        priorities = [dict(metric=metric, direction=direction, evidence=quote)]
    raw = dict(intent='search', filters=clauses, priority=priorities, references=[],
               unsupported_requests=[], pending_question='', site_context={'hazard': 'unknown'})
    _, _, filters, checked, by, _, _, _ = v2.validate(connection, raw, '\n'.join(user_parts), [], {}, [{'term_key': k} for k in term_keys])
    result = search_actuators(connection, checked.model_copy(update={'limit': 100, 'offset': 0}), allow_ambiguous=True)
    if len(result['products']) != result['total'] or any(not v2.integrity.satisfies(row, checked) for row in result['products']):
        raise ValueError('v2 SQL collection failed its independent integrity check')
    ranked = v2.ordered_rows(result['products'], filters, by)
    return [p['base_part_number'] for p in ranked], dict(sql_total=result['total'], postcondition_excluded=0,
                                                       ranked_by=by[0] if by else 'closest_torque',
                                                       schema_default_limit=20, state_mode='v2')
