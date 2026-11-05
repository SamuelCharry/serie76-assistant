"""Independent post-condition for published catalogue search rows."""
from decimal import Decimal
from backend.catalog.models import bound_operator, bound_value, bounds

SERVICE_FIELDS = {
    'min_torque_nm': 'torque_nm', 'min_torque_in_lb': 'torque_in_lb',
    'min_duty_s4_percent': 'duty_s4_percent',
    'min_cycles_per_hour': 'cycles_per_hour', 'min_starts_per_hour': 'starts_per_hour',
}
FREQUENCY_FIELDS = {
    'max_operating_time_s': 'operating_time_s',
    'max_fla_a': 'fla_a', 'max_lra_a': 'lra_a',
}


def hazard_recommendation_safe(items, *, hazard):
    """No weatherproof recommendation or pick may survive a hazard signal."""
    return not hazard or all(item.get('enclosure') == 'explosionproof' for item in items)


def _passes(value, requirement, default):
    if value is None:
        return False
    for item in bounds(requirement):
        op = bound_operator(item, default)
        target = Decimal(str(bound_value(item)))
        actual = Decimal(str(value))
        if not {'gt': actual > target, 'gte': actual >= target,
                'lt': actual < target, 'lte': actual <= target}[op]:
            return False
    return True


def satisfies(product, filters):
    """Combine confirmed shared fields with ONE requested service, never two services."""
    for field in ('enclosure', 'supply_voltage_v', 'phase_count'):
        wanted = getattr(filters, field)
        if wanted is not None and product.get(field) != wanted:
            return False
    if filters.supply_current and product.get('supply_current') not in (filters.supply_current, 'AC/DC'):
        return False
    if filters.dc_only and product.get('supply_current') != 'DC':
        return False
    if filters.csa_required and product.get('certification', {}).get('csa_status') != 'reported_in_header':
        return False
    if filters.max_motor_power_w is not None and not _passes(
            product['measurements'].get('motor_power_w'), filters.max_motor_power_w, 'lte'):
        return False
    service_limits = [(column, getattr(filters, field)) for field, column in SERVICE_FIELDS.items()
                      if getattr(filters, field) is not None]
    if filters.service or service_limits:
        rows = product.get('services', [])
        shared = next((r for r in rows if r['service'] == 'shared'), {}) if (
            product.get('provenance', {}).get('shared_services_confirmed')) else {}
        service_rows = [r for r in rows if r['service'] != 'shared'
                        and (filters.service is None or r['service'] == filters.service)]
        if shared and not service_rows:
            service_rows = [{}]
        def service_value(row, column):
            value = row.get(column)
            # SQL only coalesces shared torque/duty. Rates belong to the service.
            if value is None and column in ('torque_nm', 'torque_in_lb', 'duty_s4_percent'):
                value = shared.get(column)
            return value
        if not any(all(_passes(service_value(row, column), requirement, 'gte')
                       for column, requirement in service_limits) for row in service_rows):
            return False
    frequency_limits = [(column, getattr(filters, field)) for field, column in FREQUENCY_FIELDS.items()
                        if getattr(filters, field) is not None]
    if filters.frequency_hz or frequency_limits:
        frequency_rows = [row for row in product.get('frequencies', [])
                          if filters.frequency_hz is None or row['frequency_hz'] == filters.frequency_hz]
        if not any(all(_passes(row.get(column), requirement, 'lte')
                       for column, requirement in frequency_limits) for row in frequency_rows):
            return False
    return True
