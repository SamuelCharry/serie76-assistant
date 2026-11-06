"""Offline preparation gates; no provider or embedding calls."""
import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from backend.conversation import agent, tool_wire
from backend.conversation.prompt_variants import CONFIG
from scripts.load_example_bank import examples_from_cases

ROOT = Path(__file__).resolve().parents[1]

class PreparedVariantsTests(unittest.TestCase):
    def test_default_byte_identical_to_frozen_baseline(self):
        baseline = json.loads(CONFIG.read_text(encoding='utf-8'))['baseline_sha256']
        for env in ({}, {'AGENT_PROMPT_VARIANT': ''}, {'AGENT_PROMPT_VARIANT': 'current'}):
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(agent.system_prompt().encode(), agent.SYSTEM.encode())
                self.assertEqual(hashlib.sha256(agent.system_prompt().encode()).hexdigest(), baseline)

    def test_every_variant_loads_and_preserves_base(self):
        variants = json.loads(CONFIG.read_text(encoding='utf-8'))['variants']
        self.assertEqual(len(variants), 3)
        for name, variant in variants.items():
            with self.subTest(name=name), patch.dict(os.environ, {'AGENT_PROMPT_VARIANT': name}):
                self.assertTrue(variant['hypothesis'])
                self.assertEqual(agent.system_prompt(), agent.SYSTEM + '\n\n' + variant['append'])

    def test_unknown_variant_rejected(self):
        with patch.dict(os.environ, {'AGENT_PROMPT_VARIANT': 'missing'}), self.assertRaises(ValueError):
            agent.system_prompt()

    def test_sixty_pairs_survive_loader_and_validate(self):
        cases = json.loads((ROOT / 'config/example_bank_contrastive_t10.json').read_text(encoding='utf-8'))
        self.assertEqual(len(cases['scenarios']), 60)
        rows = examples_from_cases(cases)
        self.assertEqual(len(rows), 120)
        models = agent.schemas(['fla'])
        wire = tool_wire.schemas(['fla'])
        for scenario in cases['scenarios']:
            self.assertEqual(len(scenario['turns']), 2)
            self.assertNotEqual(*[t['scripted_decision'] for t in scenario['turns']])
        for row in rows:
            tool, args = row['interpretation']['tool'], row['interpretation']['args']
            with self.subTest(text=row['text']):
                self.assertFalse(set(args) - set(wire[tool]['properties']))
                models[tool].model_validate(tool_wire.canonical_arguments(tool, args))

if __name__ == '__main__':
    unittest.main()
