"""Prepared prompt experiments; selecting a variant never invokes a provider."""
import json
import os
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[2] / 'config/prompt_variants_t10.json'

def select_prompt(base):
    name = os.getenv('AGENT_PROMPT_VARIANT', '').strip()
    if name in ('', 'current'):
        return base
    variants = json.loads(CONFIG.read_text(encoding='utf-8'))['variants']
    if name not in variants:
        raise ValueError('Unknown AGENT_PROMPT_VARIANT')
    return base + '\n\n' + variants[name]['append']
