"""Catalogue-wide counts come directly from the active PostgreSQL import."""
import re
from backend.catalog.models import SearchFilters
from backend.catalog.repository import active_import, search_actuators
from .policy import colloquial_requirements


def all_requested(query):
    return bool(re.search(r'\b(?:all|every|todos|todas)\b', query, re.I))


def limitations(query):
    """Independent request parts, so a compound question loses none of them."""
    patterns = (
        (r'\b(?:prices?|pricing|costs?|precios?|cuesta|coste)\b', "The catalogue doesn't publish prices. A weighted price score is unavailable."),
        (r'\b(?:lead[ -]?times?|delivery|ships?|shipping|dispatch|entrega|env[ií]o)\b',
         "The catalogue does not publish delivery times or lead times."),
        (r'\b(?:weigh(?:s|t)?|weight|mass|peso|pesa)\b', "The catalogue doesn't publish weight."),
        (r'\b(?:SIL|safety integrity)\b', "The catalogue does not publish SIL ratings or certification."),
        (r'\b(?:series?|serie)\s+(?!76\b)\d+\b', "Other series are outside this catalogue; I only cover the Series 76 catalogue."),
    )
    return [message for pattern, message in patterns if re.search(pattern, query, re.I)]


def relative_operation(query):
    """Closed relative search phrasing, distinct from comparisons of displayed models."""
    if not re.search(r'\b(?:find|search|need|busc\w*|necesito)\b', query, re.I):
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
        rows = connection.execute(
            "SELECT supply_voltage_v AS value,count(DISTINCT base_part_number) AS n "
            "FROM series76.entries WHERE import_id=%s AND data_status='reported' "
            "GROUP BY supply_voltage_v ORDER BY supply_voltage_v", (active_import(connection),)).fetchall()
        return f'{len(rows)} published supply voltages: ' + ', '.join(f'{r["value"]:g} V ({r["n"]} models)' for r in rows) + '.'
    if not product_search and re.search(r'\b(?:what|which|available|have|list|show)\b.*\benclosures?\b', text):
        rows = connection.execute(
            "SELECT enclosure AS value,count(DISTINCT base_part_number) AS n "
            "FROM series76.entries WHERE import_id=%s AND data_status='reported' "
            "GROUP BY enclosure ORDER BY enclosure", (active_import(connection),)).fetchall()
        return 'Published enclosures: ' + ', '.join(f'{r["value"].capitalize()} ({r["n"]} models)' for r in rows) + '.'
    if not product_search and re.search(r'\b(?:what|which|available|have|list|show)\b.*\bservices?\b', text):
        counts = [(label, search_actuators(connection, SearchFilters(service=service, limit=1),
                                          allow_ambiguous=True)['total'])
                  for service, label in [('on_off', 'On/Off'), ('modulating', 'Modulating')]]
        return 'Published services: ' + ', '.join(f'{label} ({count} models)' for label, count in counts) + '.'
    if re.search(r'\bhow many\b.*\b(?:models?|actuators?)\b', text):
        if re.search(r'\b3[-\s]*phase\b', text):
            rows = connection.execute(
                "SELECT data_status,count(DISTINCT base_part_number) AS n FROM series76.entries "
                "WHERE import_id=%s AND phase_count=3 GROUP BY data_status",
                (active_import(connection),)).fetchall()
            counts = {row['data_status']: row['n'] for row in rows}
            return (f"The catalogue lists {counts.get('reported', 0)} three-phase models with published data; "
                    f"{counts.get('source_NA', 0)} more listed without published values.")
        stated, _ = colloquial_requirements(query)
        voltage = re.search(r'\b(24|110|220)\s*(?:v|volts?)\b', text)
        if voltage:
            stated['supply_voltage_v'] = int(voltage.group(1))
        if stated:
            count = search_actuators(connection, SearchFilters.model_validate(dict(stated, limit=1)),
                                     allow_ambiguous=True)['total']
            scope = ', '.join(f'{value} V' if field == 'supply_voltage_v' else
                              'Explosionproof' if value == 'explosionproof' else
                              'Weatherproof' if value == 'weatherproof' else
                              'On/Off' if value == 'on_off' else
                              'Modulating' if value == 'modulating' else str(value)
                              for field, value in stated.items())
            return f'The catalogue has {count} models at {scope}.'
        count = connection.execute(
            "SELECT count(DISTINCT base_part_number) AS n FROM series76.entries "
            "WHERE import_id=%s AND data_status='reported'", (active_import(connection),)).fetchone()['n']
        return f'The catalogue has {count} models with published electrical data.'
    return None
