"""Bounded interpreter metadata. SQL remains the only catalogue value source."""
import re
from pydantic import BaseModel, ConfigDict, field_validator

METRICS = {'torque', 'operating_time', 'fla', 'motor_power', 'duty', 'cycles', 'starts'}
KNOWN_KEYS = {('torque', 'highest'): 'most_torque', ('operating_time', 'lowest'): 'fastest',
              ('fla', 'lowest'): 'lowest_fla', ('motor_power', 'lowest'): 'lowest_power',
              ('duty', 'highest'): 'most_duty', ('cycles', 'highest'): 'most_cycles'}


class Priority(BaseModel):
    model_config = ConfigDict(extra='forbid')
    metric: str
    direction: str
    frequency_hz: int | None = None

    @field_validator('metric')
    @classmethod
    def metric_known(cls, value):
        if value not in METRICS:
            raise ValueError('Unknown priority metric')
        return value

    @field_validator('direction')
    @classmethod
    def direction_known(cls, value):
        if value not in ('highest', 'lowest'):
            raise ValueError('Unknown priority direction')
        return value

    @field_validator('frequency_hz', mode='before')
    @classmethod
    def valid_frequency(cls, value):
        if value is not None and (type(value) is not int or value not in (50, 60)):
            raise ValueError('Unknown frequency')
        return value


def priority_key(priority):
    p = Priority.model_validate(priority)
    return KNOWN_KEYS.get((p.metric, p.direction), p.direction + '_' + p.metric)


def list_value(value):
    if isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    return value


def unsupported_items(value):
    """Only short noun labels can cross the renderer boundary, never model prose."""
    values = list_value(value)
    if not isinstance(values, list) or len(values) > 8:
        raise ValueError('Invalid unsupported requests')
    result = []
    for item in values:
        if not isinstance(item, str):
            raise ValueError('Invalid unsupported item')
        clean = re.sub(r'[^a-zA-Z -]', '', item).strip()[:40].strip()
        clean = ' '.join(clean.split())
        if clean and clean.lower() not in METRICS | {'voltage', 'supply', 'enclosure', 'service', 'frequency'}:
            result.append(clean)
    return list(dict.fromkeys(result))


def keep_fields(value):
    from .policy import FILTER_FIELDS
    values = list_value(value)
    if not isinstance(values, list) or len(values) > len(FILTER_FIELDS) or any(v not in FILTER_FIELDS for v in values):
        raise ValueError('Invalid retained fields')
    return list(dict.fromkeys(values))


TOPICS = {'', 'source_na', 'enclosure_guidance', 'supply_overview', 'catalogue_overview', 'supply_services'}


def topic_value(value):
    if value not in TOPICS:
        raise ValueError('Unknown catalogue topic')
    return value
