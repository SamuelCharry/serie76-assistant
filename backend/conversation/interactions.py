"""Code-owned questions and validated submissions; no provider schema changes."""
import re
from copy import deepcopy
from . import policy
from .rendering import _num


class InvalidInteraction(ValueError):
    def __init__(self, code, detail=None):
        self.code = code
        super().__init__(detail or ('Choose a published option for the pending question.' if code == 'invalid_answers'
                         else 'Only active search filters can be removed.'))


def greeting(query, name):
    bare = re.sub(r'[^\w\s]', '', query.lower()).strip()
    if bare not in ('hi', 'hello', 'hey', 'hola', 'buenas', 'buenos dias', 'buenos días'):
        return None
    first = str(name or '').strip().split()
    return ('Hello, ' + first[0] + '.' if first else 'Hello.') + (
        ' I can look up Series 76 actuators, find models for your requirements, compare models or explain catalogue terms.')


def option(field, value):
    text = _num(value) if isinstance(value, (int, float)) else str(value)
    label = {'on_off': 'On/Off', 'modulating': 'Modulating',
             'weatherproof': 'Weatherproof', 'explosionproof': 'Explosionproof'}.get(text, text)
    label += {'supply_voltage_v': ' V', 'frequency_hz': ' Hz', 'phase_count': ' phase'}.get(field, '')
    return dict(value=text, label=label)


def free_text_answer(query, pending):
    """Apply only a complete, unambiguous reply to a published option."""
    def normalized(text):
        text = str(text).strip().lower()
        text = re.sub(r'\bvolts?\b|\bv\b', 'v', text)
        text = re.sub(r'\bhertz\b', 'hz', text)
        text = re.sub(r'\bon\s*[/ -]?\s*off?\b|\bon\s+or\s+off\b', 'on/off', text)
        return re.sub(r'\s+', ' ', text.strip(' .!?')).strip()
    given = normalized(query)
    options = [(question['id'], entry) for question in pending for entry in question['options']]
    if given == 'yes' and len(options) == 1:
        return {options[0][0]: options[0][1]['value']}
    matches = []
    for field, entry in options:
        label = normalized(entry['label'])
        value = normalized(entry['value'])
        variants = {label, value}
        if field == 'supply_voltage_v':
            variants |= {value + ' v', value + ' volts', value + ' volt'}
        if field == 'frequency_hz':
            variants |= {value + ' hz'}
        if given in variants:
            matches.append((field, entry['value']))
    return {matches[0][0]: matches[0][1]} if len(matches) == 1 else None


def questions(facets, fields):
    prompts = {'service': 'Which service?', 'frequency_hz': 'Which frequency?',
               'supply_voltage_v': 'Which supply voltage?', 'supply_current': 'Which current type?',
               'phase_count': 'How many phases?', 'enclosure': 'Which enclosure?'}
    ranked = []
    for field in fields:
        rows = facets.get(field, [])
        if field not in prompts or len(rows) <= 1:
            continue
        universe = set().union(*(set(row.get('codes', [])) for row in rows))
        if universe and all(row['n'] > 0.85 * len(universe) for row in rows):
            continue
        ranked.append(field)
    ranked.sort(key=lambda f: max(r['n'] for r in facets[f]))
    selected = []
    for field in ranked:
        current = facets[field]
        # Service and frequency establish the measurement scope. Their values
        # are not inferred from a coincidentally equal candidate set.
        if field not in ('service', 'frequency_hz') and selected and all('codes' in row for previous in selected for row in facets[previous]) and all('codes' in row for row in current):
            earlier = [set(row['codes']) for previous in selected for row in facets[previous]]
            choices = [set(row['codes']) for row in current]
            universe = set().union(*earlier, *choices)
            atoms = {}
            for code in universe:
                atoms.setdefault(tuple(code in group for group in earlier), set()).add(code)
            if all(all(atom <= choice or atom.isdisjoint(choice) for atom in atoms.values()) for choice in choices):
                continue
        selected.append(field)
    return [dict(id=f, prompt=prompts[f],
                 options=[dict(option(f, r['value']), count=r['n']) for r in facets[f]]) for f in selected]


def question_summary(items):
    names = {'service': 'service', 'frequency_hz': 'frequency', 'supply_voltage_v': 'supply voltage',
             'supply_current': 'current type', 'phase_count': 'number of phases', 'enclosure': 'enclosure'}
    labels = [names[q['id']] for q in items]
    if not labels:
        return 'Tell me which requirement matters next.'
    joined = labels[0] if len(labels) == 1 else ', '.join(labels[:-1]) + ' and ' + labels[-1]
    return 'To narrow it down: ' + joined + '.'


def apply_submission(context, answers, remove_filters):
    context = deepcopy(context)
    pending = {q['id']: q for q in context.get('pending_questions', [])}
    for field, value in answers.items():
        if field not in pending or value not in [o['value'] for o in pending[field]['options']]:
            raise InvalidInteraction('invalid_answers')
    filters = context.get('filters', {})
    if any(f not in policy.FILTER_FIELDS or f not in filters or filters[f] is None or filters[f] is False
           for f in remove_filters) or len(set(remove_filters)) != len(remove_filters) or set(answers) & set(remove_filters):
        raise InvalidInteraction('invalid_filter')
    delta = {f: int(v) if f in ('frequency_hz', 'phase_count') else v for f, v in answers.items()}
    merged, notes = policy.merge_filters(filters, delta, refine=True, remove=remove_filters, more=False)
    context['filters'] = merged
    context['pending_questions'] = [q for q in pending.values() if q['id'] not in answers and q['id'] not in remove_filters]
    return context, notes


def active_filters(context):
    return [dict(field=f, label=policy.describe({f: v})) for f, v in context.get('filters', {}).items()
            if f in policy.FILTER_FIELDS and v is not None and v is not False]
