"""Choose a compact public answer shape from the user's request."""
from dataclasses import dataclass
from decimal import Decimal
import re

from .rendering import _num

# One vocabulary for lookup focus and metric verdicts. Order matters.
METRICS = (
    ('lra', r'\b(?:lra|locked rotor|starting current|inrush|arranque)\b'),
    ('motor_power', r'\b(?:motor power|rated power|electricity|consumption|potencia|power)\b'),
    ('fla', r'\b(?:fla|full load current|current|draws?|amps?|corriente)\b'),
    ('duty', r'\b(?:duty|s4)\b'),
    ('cycles', r'\b(?:cycles?|ciclos?)\b'),
    ('starts', r'\b(?:starts?|arranques?)\b'),
    ('operating_time', r'\b(?:faster|fastest|quicker|quickest|speed|operating time|tiempo|velocidad)\b'),
    ('torque', r'\b(?:stronger|strongest|torque|par)\b'),
)
VERDICT = re.compile(r'\b(?:which|who|most|least|lowest|highest|faster|fastest|quicker|stronger|better|more|less|cu[aá]l|menos|mayor|mejor|m[aá]s)\b', re.I)


@dataclass(frozen=True)
class Plan:
    shape: str
    metrics: tuple[str, ...] = ()
    frequency_hz: int | None = None
    service: str | None = None
    direction: str = 'lower'


def plan(query):
    text = query.lower().strip()
    if text in ('show all', 'show me all', 'all models'):
        return Plan('all')
    if text in ('next', 'more', 'next page', 'show more'):
        return Plan('next')
    if re.search(r'\b(?:full|all|complete)\s+(?:specs?|data|details?)\b|\b(?:specs?|overview)\b', text):
        return Plan('overview')
    hz = re.search(r'\b(50|60)\s*hz\b', text)
    frequency = int(hz.group(1)) if hz else None
    service = ('on_off' if re.search(r'\b(?:on\s*/?\s*off|open.close)\b', text) else
               'modulating' if re.search(r'\bmodulat', text) else None)
    if re.search(r'\b(?:lra\s*/\s*fla|fla\s*/\s*lra|lra\s+to\s+fla)\s+ratio\b|\bratio\b.*\b(?:lra|fla)\b', text):
        return Plan('ratio', ('lra', 'fla'), frequency, service)
    if re.search(r'\b(?:difference|how much (?:higher|lower|more|less))\b', text) and re.search(r'\blra\b', text) and re.search(r'\bfla\b', text):
        return Plan('difference', ('lra', 'fla'), frequency, service)
    found = tuple(name for name, pattern in METRICS if re.search(pattern, text))
    direction = 'higher' if re.search(r'\b(?:more|higher|highest|most|stronger|strongest|mayor|m[aá]s)\b', text) else 'lower'
    verdict_text = re.sub(r'\b(?:at least|at most|more than|less than|no more than|mayor (?:a|que)|menor (?:a|que))\b', '', text)
    if found and VERDICT.search(verdict_text):
        return Plan('verdict', found, frequency, service, direction)
    if found:
        return Plan('fields', found, frequency, service, direction)
    return Plan('overview')


def ratio(product, frequency_hz):
    """Only derive a ratio from published values at the same frequency."""
    values = product['measurements']
    frequencies = [frequency_hz] if frequency_hz else [50, 60]
    for hz in frequencies:
        fla, lra = values.get(f'fla_{hz}hz_a'), values.get(f'lra_{hz}hz_a')
        if fla is not None and lra is not None and fla != 0:
            value = Decimal(str(lra)) / Decimal(str(fla))
            rounded = value.quantize(Decimal('0.001')).normalize()
            code = product['base_part_number']
            return f'{code} LRA/FLA at {hz} Hz: {_num(lra)} A / {_num(fla)} A = {rounded} (unitless).'
    return ('The catalogue does not publish comparable LRA and FLA at the same frequency '
            f'for {product["base_part_number"]}.')


def difference(product, frequency_hz):
    values = product['measurements']
    for hz in ([frequency_hz] if frequency_hz else [50, 60]):
        fla, lra = values.get(f'fla_{hz}hz_a'), values.get(f'lra_{hz}hz_a')
        if fla is not None and lra is not None:
            delta = abs(Decimal(str(lra)) - Decimal(str(fla)))
            return (f'{product["base_part_number"]}: LRA {_num(lra)} A and FLA {_num(fla)} A '
                    f'at {hz} Hz differ by {_num(delta)} A.')
    return f'The catalogue does not publish comparable LRA and FLA for {product["base_part_number"]}.'
