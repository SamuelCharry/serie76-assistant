"""Catalogue-wide counts come directly from the active PostgreSQL import."""
import re
from backend.catalog.models import SearchFilters
from backend.catalog.repository import active_import, search_actuators, source_na_count
from .policy import colloquial_requirements, codes_in_text, describe


def count_scope(filters):
    scope = describe(filters) or 'the whole catalogue (no additional filters)'
    if filters.get('supply_current') in ('AC', 'DC') and not filters.get('dc_only'):
        scope += ' (including AC/DC models)'
    return scope


def unavailable_note(connection, filters):
    missing = source_na_count(connection, SearchFilters.model_validate(filters))
    if not missing['count']:
        return ''
    return (f" {missing['count']} more models within {count_scope(missing['filters'])} are listed with N/A, "
            "without published values, and excluded from the published-data count; their performance eligibility is unverified.")


def search_count(total, filters):
    """Every search aggregate names both the applied filters and publication scope."""
    noun = 'actuator meets' if total == 1 else 'actuators meet'
    return f"{total} {noun}: {count_scope(filters)}; with published electrical data."


def facet_counts(connection, field):
    # Field identifiers are a closed internal vocabulary, never user SQL.
    if field not in ('supply_voltage_v', 'enclosure'):
        raise ValueError('Unknown catalogue facet')
    return connection.execute(
        f"SELECT {field} AS value, count(DISTINCT base_part_number) FILTER "
        "(WHERE data_status='reported') AS n, count(DISTINCT base_part_number) FILTER "
        "(WHERE data_status='source_NA') AS na, count(*) OVER () AS groups "
        "FROM series76.entries WHERE import_id=%s "
        f"GROUP BY {field} ORDER BY {field}", (active_import(connection),)).fetchall()


def facet_text(row, label):
    return (f"{label} ({row['n']} models) with published data; "
            f"{row['na']} more {label} models listed with N/A, excluded from that count")


def all_requested(query):
    return bool(re.search(r'\b(?:all|every|todos|todas)\b', query, re.I))


def limitations(query):
    """Independent request parts, so a compound question loses none of them."""
    patterns = (
        (r'\b(?:prices?|pricing|costs?|precios?|cuesta|coste)\b', "The catalogue doesn't publish prices. A weighted price score is unavailable."),
        (r'\b(?:lead[ -]?times?|delivery|ships?|shipping|dispatch|entrega(?!\s+(?:(?:m[a\u00e1]s|mayor)\s+)?(?:de\s+)?(?:torque|par)\b)|env[ií]o)\b',
         "The catalogue does not publish delivery times or lead times."),
        (r'\b(?:weigh(?:s|t)?|weight|mass|peso|pesa)\b', "The catalogue doesn't publish weight."),
        (r'\b(?:SIL|safety integrity)\b', "The catalogue does not publish SIL ratings or certification."),
        (r'\b(?:stock|availability|inventory|disponibilidad|existencias)\b', "The catalogue does not publish current stock or availability."),
        (r'\b(?:mounting|dimensions?|dimensiones)\b', "The catalogue does not publish mounting dimensions."),
        (r'\b(?:installation instructions|how to install|install it)\b', "The catalogue does not publish installation instructions."),
        (r'\b(?:series?|serie)\s+(?!76\b)\d+\b', "Other series are outside this catalogue; I only cover the Series 76 catalogue."),
    )
    return [message for pattern, message in patterns if re.search(pattern, query, re.I)]


def relative_operation(query):
    """Closed relative search phrasing, distinct from comparisons of displayed models."""
    if not re.search(r'\b(?:find|search|need|busc\w*|necesito)\b|\b(?:give|show)\s+me\b[^.!?;]*\bthan\b', query, re.I):
        return ''
    for operation, pattern in (
        ('stronger', r'\bstronger\b|\b(?:more|m[aá?]s)\b[^.!?;]*\b(?:torque|par)\b'),
        ('faster', r'\bfaster\b|\bm[aá?]s\s+r[aá?]pid[oa]\b'),
        ('smaller', r'\bsmaller\b|\bmenor\s+(?:torque|par)\b'),
    ):
        if re.search(pattern, query, re.I):
            return operation
    return ''


def answer(connection, query):
    text = query.lower()
    # An explicit part number requests that product, never a catalogue aggregate.
    if codes_in_text(query):
        return None
    # Multi-facet and voltage-scoped service questions require structured intent;
    # catalogue-wide statistics would silently answer only one request part.
    if (re.search(r'\bvoltages?\b', text) and re.search(r'\benclosures?\b', text)
            or re.search(r'\d+\s*v\b', text) and re.search(r'\bservices?\b', text)):
        return None
    supply_overview = re.search(r'\b(?:tipos? de (?:alimentaci[óo?]n|suministro(?: el[ée]ctrico)?)|supply types|types of (?:power )?supply)\b', text)
    if supply_overview:
        from backend.catalog.context import published_supplies
        from .rendering import supplies_text
        return supplies_text(published_supplies(connection))
    # A request for products with a property is not a request for facet statistics.
    product_search = bool(re.search(r'\b(?:models?|actuators?|modelos?|actuadores?)\b', text))
    if re.search(r'\btorque range\b.*\b(?:catalogue|series 76)\b|\b(?:catalogue|series 76)\b.*\btorque range\b', text):
        rows = connection.execute(
            "SELECT s.service,min(s.torque_nm) AS low,max(s.torque_nm) AS high "
            "FROM series76.service_specs s JOIN series76.entries e ON e.id=s.entry_id "
            "WHERE e.import_id=%s AND e.data_status='reported' AND s.torque_nm IS NOT NULL "
            "GROUP BY s.service", (active_import(connection),)).fetchall()
        by_service = {row['service']: row for row in rows}
        low = min(row['low'] for row in rows)
        high = max(row['high'] for row in rows)
        def span(name):
            relevant = [by_service[key] for key in (name, 'shared') if key in by_service]
            return f"{min(row['low'] for row in relevant):g}–{max(row['high'] for row in relevant):g} Nm"
        return (f"The catalogue covers {low:g}–{high:g} Nm: "
                f"On/Off {span('on_off')}, Modulating {span('modulating')}.")
    if not product_search and re.search(r'\b(?:voltages?|voltajes?|tensiones?)\b', text) and re.search(
            r'\b(?:what|which|available|have|list|show|how many|count|distinct|different|disponibles|diferentes|cu[aá?]ntos|cu[aá?]les)\b', text):
        rows = facet_counts(connection, 'supply_voltage_v')
        return f"{rows[0]['groups'] if rows else 0} published supply voltages across the whole catalogue: " + ', '.join(
            facet_text(r, f"{r['value']:g} V") for r in rows) + '.'
    if not product_search and re.search(r'\b(?:what|which|available|have|list|show)\b.*\benclosures?\b', text):
        rows = facet_counts(connection, 'enclosure')
        return 'Published enclosures across the whole catalogue: ' + ', '.join(
            facet_text(r, r['value'].capitalize()) for r in rows) + '.'
    if not product_search and re.search(r'\b(?:what|which|available|have|list|show)\b.*\bservices?\b', text):
        return ' '.join(search_count(search_actuators(connection, SearchFilters(service=service, limit=1),
                           allow_ambiguous=True)['total'], {'service': service}) +
                        unavailable_note(connection, {'service': service})
                        for service in ('on_off', 'modulating'))
    if re.search(r'\b(?:how many|count|number of|cu[aá]ntos)\b.*\b(?:models?|actuators?|modelos?|actuadores?)\b', text):
        from .requirement_coverage import apply
        stated, _ = colloquial_requirements(query)
        phase = re.search(r'\b([13])[-\s]*phase\b', text)
        if phase:
            stated['phase_count'] = int(phase.group(1))
        stated, issues = apply(query, stated, stated)
        if issues:
            return None
        try:
            filters = SearchFilters.model_validate(dict(stated, limit=1))
        except ValueError:
            return None
        count = search_actuators(connection, filters, allow_ambiguous=True)['total']
        return (f'The catalogue has {count} models with published electrical data within {count_scope(stated)}.'
                + unavailable_note(connection, stated))
    return None
