"""Catalogue-wide counts come directly from the active PostgreSQL import."""
import re
from backend.catalog.models import SearchFilters
from backend.catalog.repository import active_import, search_actuators
from .policy import colloquial_requirements


def answer(connection, query):
    text = query.lower()
    if re.search(r'\b(?:what|which|available|have|list|show)\b.*\b(?:voltages?|supply voltages?)\b', text):
        rows = connection.execute(
            "SELECT supply_voltage_v AS value,count(DISTINCT base_part_number) AS n "
            "FROM series76.entries WHERE import_id=%s AND data_status='reported' "
            "GROUP BY supply_voltage_v ORDER BY supply_voltage_v", (active_import(connection),)).fetchall()
        return 'Published supply voltages: ' + ', '.join(f'{r["value"]:g} V ({r["n"]} models)' for r in rows) + '.'
    if re.search(r'\b(?:what|which|available|have|list|show)\b.*\benclosures?\b', text):
        rows = connection.execute(
            "SELECT enclosure AS value,count(DISTINCT base_part_number) AS n "
            "FROM series76.entries WHERE import_id=%s AND data_status='reported' "
            "GROUP BY enclosure ORDER BY enclosure", (active_import(connection),)).fetchall()
        return 'Published enclosures: ' + ', '.join(f'{r["value"].capitalize()} ({r["n"]} models)' for r in rows) + '.'
    if re.search(r'\b(?:what|which|available|have|list|show)\b.*\bservices?\b', text):
        counts = [(label, search_actuators(connection, SearchFilters(service=service, limit=1),
                                          allow_ambiguous=True)['total'])
                  for service, label in [('on_off', 'On/Off'), ('modulating', 'Modulating')]]
        return 'Published services: ' + ', '.join(f'{label} ({count} models)' for label, count in counts) + '.'
    if re.search(r'\bhow many\b.*\b(?:models?|actuators?)\b', text):
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
