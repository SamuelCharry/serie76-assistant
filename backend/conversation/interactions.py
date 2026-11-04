"""Code-owned questions and validated submissions; no provider schema changes."""
import re
from copy import deepcopy
from . import policy
from .rendering import _num


class InvalidInteraction(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__('Choose a published option for the pending question.' if code == 'invalid_answers'
                         else 'Only active search filters can be removed.')


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


def questions(facets, fields):
    prompts = {'service': 'Which service?', 'frequency_hz': 'Which frequency?',
               'supply_voltage_v': 'Which supply voltage?', 'supply_current': 'Which current type?',
               'phase_count': 'How many phases?', 'enclosure': 'Which enclosure?'}
    return [dict(id=f, prompt=prompts[f], options=[option(f, r['value']) for r in facets.get(f, [])])
            for f in fields if f in prompts and facets.get(f)]


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
