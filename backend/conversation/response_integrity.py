"""The final, route-independent eligibility postcondition for user-visible products."""
import re
from pydantic import ValidationError

from backend.catalog.models import SearchFilters, bounds, bound_value, bound_operator
from backend.catalog.repository import get_actuator
from . import catalogue_answers, integrity, interactions, policy, ranking, requirement_coverage, shown_recommendation


def _bounds_equal(field, left, right):
    def canonical(value):
        reduced = policy.intersect_bounds(field, value)
        return sorted((float(bound_value(b)), bound_operator(b, 'gte' if field.startswith('min_') else 'lte')) for b in bounds(reduced)) if reduced is not None else []
    return canonical(left) == canonical(right)


def _reference_postcondition(turn, filters):
    """Re-derive obligations from the prior display and SQL, not route arguments."""
    previous = turn.trace.get('context_before') or {}
    prior_filters = dict(previous.get('filters') or {})
    written, _ = requirement_coverage.apply(turn.query, {}, prior_filters)
    changed = set()
    for field, side in policy.removed_bound_sides(turn.query, prior_filters).items():
        remaining = policy.prune_bound_side(prior_filters[field], field, side)
        if remaining is None:
            prior_filters.pop(field)
        else:
            prior_filters[field] = remaining
        changed.add(field)
    expected, _ = policy.merge_filters(prior_filters, written, refine=True, remove=[], more=False, query=turn.query)
    operation = catalogue_answers.relative_operation(turn.query)
    ordinal = policy.ordinal_position(turn.query)
    order = previous.get('last_shown_list') or previous.get('last_comparison_models') or previous.get('on_screen') or []
    requested = order[ordinal-1] if ordinal and ordinal <= len(order) else None
    issues, reference = [], None
    if operation:
        named = policy.codes_in_text(turn.query)
        position = re.search(r'\b(?:the\s+)?(first|second|third|fourth)\b', turn.query, re.I)
        index = ('first', 'second', 'third', 'fourth').index(position.group(1).lower()) if position else -1
        numbered = re.search(r'\b(?:item|model|position)\s*#?\s*([1-9]\d*)\b', turn.query, re.I)
        if numbered:
            index = int(numbered.group(1)) - 1
        if index >= len(order):
            order = previous.get('last_ranked_list') or order
        reference = (named[0] if len(named) == 1 else
                     order[index] if 0 <= index < len(order) else
                     previous.get('focused_model') or (order[0] if len(order) == 1 else None))
        row = get_actuator(turn.connection, reference) if reference else None
        scope = dict(prior_filters, **{k:v for k,v in written.items() if k in ('service','frequency_hz')})
        if previous.get('reference_service'):
            scope['service'] = previous['reference_service']
        explicit, _ = policy.colloquial_requirements(turn.query)
        scope.update({k:v for k,v in explicit.items() if k in ('service','frequency_hz')})
        if row and scope.get('service'):
            if operation == 'faster' and not scope.get('frequency_hz'):
                frequencies = {f.get('frequency_hz') for f in row.get('frequencies', []) if f.get('frequency_hz')}
                if len(frequencies) > 1:
                    issues.append('Confirm the frequency for the relative operating-time requirement')
            field = 'max_operating_time_s' if operation == 'faster' else 'min_torque_nm'
            metric = 'operating_time' if operation == 'faster' else 'torque'
            # An existing selection bound must neither hide the reference value
            # nor switch an Nm obligation to the separately published in-lb column.
            measurement_scope = {k:v for k,v in scope.items() if k not in ('min_torque_nm','min_torque_in_lb')}
            value = ranking.measurement(row, metric, measurement_scope)
            if value is not None:
                requirement = dict(value=value, op='gt' if operation == 'stronger' else 'lt')
                expected[field] = policy.merge_bounds(field, prior_filters[field], requirement) if field in prior_filters else requirement
                # A separately written numeric condition is also an obligation.
                if field in written:
                    expected[field] = policy.intersect_bounds(field, expected[field], written[field])
                changed.add(field)
            else:
                issues.append('The reference has no published value for this relative requirement')
        else:
            issues.append('Confirm the reference model and service for the relative requirement')
    mismatched = [field for field in changed if not _bounds_equal(field, expected.get(field), filters.get(field))]
    for field in changed:
        if field in expected:
            filters[field] = expected[field]
        else:
            filters.pop(field, None)
    if mismatched:
        issues.append('The presented selection did not preserve the requested relative or withdrawn limits')
    return requested if not operation else None, reference, changed, issues


def enforce(turn, result):
    """Validate SQL rows, never trust a card, cached ranking, or renderer's claim.

    Invalid selections fail closed as a whole (including their prose and UI state).
    Informational lookups/comparisons may retain specifications, but each ineligible
    model is explicitly labelled with its failed requirements, never as a match.
    """
    selected = {p['base_part_number'] for p in result.products}
    selected.update((result.comparison or {}).get('models', []))
    selected.update(item['part_number'] for item in (result.recommendation or {}).get('items', []))
    mentioned = set(policy.codes_in_text(result.answer + '\n' + (result.lead or '')))
    codes = selected | mentioned
    if not codes:
        return
    positive_pick = bool(re.search(r'\b(?:I recommend|My pick|best matches|ranked models)\b', result.answer, re.I))
    informational = (turn.trace.get('name') in ('get_actuator', 'metric_difference', 'comparison_difference',
                                               'document_limitation', 'nearest_alternative')
                     and not result.recommendation and not positive_pick)
    filters = dict(result.context.get('filters') or {})
    issues = []
    # The independent quantity ledger survives an accidentally omitted filter.
    for field, value in (result.context.get('quantity_requirements') or {}).items():
        filters.setdefault(field, value)
    # The state transition already owns categorical removals and inferred
    # defaults. Only repair *missing* written quantities here, without replaying
    # that transition or normalizing an equivalent bound a second time.
    # Even an informational lookup must label a newly stated unmet bound.
    quantity_query = policy.CODE_RE.sub('', turn.query)
    written, issues = requirement_coverage.apply(quantity_query, {}, filters)
    if informational:
        # An informational question can ask about unsupported/alternative units;
        # it does not assert that a candidate satisfies that ambiguous quantity.
        issues = []
        requirement_intent = re.search(
            r'\b(?:needs?|requires?|requirements?|meets?|meeting|minimum|maximum|min|max|'
            r'at least|at most|no more than|no less than|under|below|above|over|'
            r'necesito|requiere|cumple|m[ií]nimo|m[aá]ximo|al menos|como mucho)\b|'
            r'[<>]=?|\b(?:for|para)\s+\d', quantity_query, re.I)
        if not requirement_intent or turn.trace.get('name') == 'document_limitation':
            # "Confirm this model has 999 Nm" is a factual claim to verify,
            # not permission to store 999 as an active minimum or echo it as one.
            written = {}
    missing = requirement_coverage.missing(written, filters)
    delta = {key: written[key] for key in missing}
    if delta:
        filters, _ = policy.merge_filters(filters, delta, refine=True, more=False,
                                           remove=policy.removed_fields(turn.query), query=turn.query)
    if not informational and result.context.get('unresolved_reference'):
        issues.append('The service for the relative torque or speed requirement has not been confirmed')
    requested, reference, changed, contract_issues = _reference_postcondition(turn, filters)
    issues.extend(contract_issues)
    if reference:
        # A search for a stronger/faster alternative is a selection even if a
        # faulty interpreter routes it through informational product lookup.
        informational = False
    # Identity is part of the contract even when two catalogue rows happen to
    # publish identical figures. Do not keep a wrong informational lookup.
    wrong_identity = bool(requested and (selected | mentioned) - {requested})
    if wrong_identity or contract_issues:
        informational = False
        if wrong_identity:
            issues.append('The response does not identify the requested displayed model')
        turn.trace.setdefault('validation', []).append('reference_postcondition_failed')
    if changed:
        ledger = result.context.setdefault('quantity_requirements', {})
        for field in changed:
            if field in filters:
                ledger[field] = filters[field]
            else:
                ledger.pop(field, None)
    try:
        validated = SearchFilters.model_validate(filters)
    except ValidationError:
        validated = None
        issues.append('The active requirements conflict; please clarify the limits.')
    rows = {code: get_actuator(turn.connection, code) for code in sorted(codes)}
    failures = {}
    previous = turn.trace.get('context_before') or {}
    allowed = set(previous.get('on_screen') or previous.get('last_comparison_models') or [])
    restricted = bool(re.search(r'\b(?:shown|displayed|those two|these two|on screen)\b', turn.query, re.I))
    for code, row in rows.items():
        if row is None:
            # A missing code in an informational lookup is already an explicit
            # not-found result, not a catalogue recommendation.
            if code in selected or not informational:
                failures[code] = ['No published catalogue row verifies the requirements']
        elif validated is None or issues:
            failures[code] = issues
        elif not integrity.satisfies(row, validated):
            failures[code] = shown_recommendation.failures(row, filters)[0]
        if not informational and restricted and allowed and code not in allowed:
            failures.setdefault(code, []).append('The model is not among the shown choices requested')
    if not informational or any(key.startswith(('min_', 'max_')) for key in written):
        # Match the agent's JSON state contract and preserve view/pagination keys;
        # requirement merging must not reset the page on its way out.
        old_filters = result.context.get('filters') or {}
        if validated is not None:
            canonical = validated.model_dump(mode='json')
            previous = SearchFilters.model_validate(old_filters).model_dump(mode='json')
            result.context['filters'] = dict(old_filters)
            for key in policy.FILTER_FIELDS:
                if canonical[key] != previous[key]:
                    if canonical[key] is None:
                        result.context['filters'].pop(key, None)
                    else:
                        result.context['filters'][key] = canonical[key]
        result.active_filters = interactions.active_filters(result.context)
    if not failures:
        return
    turn.trace.setdefault('validation', []).append('response_integrity_exclusions')
    turn.trace['integrity_exclusions'] = failures
    labels = {code: code + ' does not meet the active requirements: ' + '; '.join(reasons) + '.'
              for code, reasons in failures.items()}
    invalid_selection = set(failures) & selected
    unlabelled_mentions = {
        code for code in failures
        if code + ' is out: ' + '; '.join(failures[code]) + '.' not in result.answer
        and 'Using ' + code + ' as the reference;' not in result.answer
    }
    alternatives = (result.recommendation is not None and result.recommendation.get('total') == 0
                    and not positive_pick)
    if alternatives:
        # The API uses total=0 for explicitly relaxed alternatives. Independently
        # replace their reasons with the exact failed requirements, including
        # failures that the original nearest-neighbour renderer did not name.
        for item in result.recommendation.get('items', []):
            if item['part_number'] in labels:
                item['reason'] += '; fails active requirements: ' + '; '.join(failures[item['part_number']])
    # Prose-only paths (ranked lists and metric verdicts included) are also picks;
    # there is no exemption just because they forgot a recommendation payload.
    if not informational and not alternatives and (invalid_selection or unlabelled_mentions):
        result.answer = 'I could not verify every presented model against the active requirements; no model is recommended.'
        result.lead = result.answer
        result.products = []
        result.recommendation = result.comparison = None
        if result.clarification:
            result.answer += '\n' + result.clarification['message']
        result.suggestions = result.suggested_replies = []
        for field in ('last_ranked_list', 'last_shown_list', 'on_screen', 'part_numbers'):
            result.context[field] = []
        result.context.pop('focused_model', None)
        result.context.pop('pagination', None)
    # These are explicit exclusions, not alternative recommendations. Annotate the
    # comparison summary too: clients may display it without the full answer.
    disclosure = '\n'.join(label for code, label in labels.items()
        if code + ' is out: ' + '; '.join(failures[code]) + '.' not in result.answer)
    if not disclosure:
        return
    result.answer += '\n' + disclosure
    result.lead = (result.lead or '') + '\n' + disclosure
    if result.comparison:
        result.comparison['summary'] = disclosure + '\n' + result.comparison.get('summary', '')
