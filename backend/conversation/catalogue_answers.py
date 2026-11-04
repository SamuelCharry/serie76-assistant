"""Catalogue-wide counts come directly from the active PostgreSQL import."""
import re
from backend.catalog.models import SearchFilters
from backend.catalog.repository import active_import, search_actuators


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
        count = connection.execute(
            "SELECT count(DISTINCT base_part_number) AS n FROM series76.entries "
            "WHERE import_id=%s AND data_status='reported'", (active_import(connection),)).fetchone()['n']
        return f'The catalogue has {count} models with published electrical data.'
    return None
