"""The final, route-independent eligibility postcondition for user-visible products."""
import re
from pydantic import ValidationError

from backend.catalog.models import SearchFilters
from backend.catalog.repository import get_actuator
from . import integrity, interactions, policy, requirement_coverage, shown_recommendation


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
