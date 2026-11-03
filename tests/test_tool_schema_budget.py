"""Provider schema budget; no DB, credentials, provider or inference needed."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.utils.function_calling import convert_to_openai_tool
from backend.conversation import agent


# Computed once from git show 0152ed6:{backend/conversation/agent.py,
# backend/catalog/models.py,backend/conversation/policy.py}, executing only schema
# declarations using the locked runtime and the retained 16 glossary term keys.
# Complete four-tool list: ASCII json.dumps(..., separators=(",", ":")): 5522 bytes.
BASELINE_0152ED6_BYTES = 5522


def production_tools():
    terms = json.loads((Path(__file__).resolve().parents[1] / "data/extracted/series76_summary/terms.json").read_text(encoding="utf-8"))
    return agent.declarations(agent.schemas([term["term_key"] for term in terms["terms"]]))


class ToolSchemaBudgetTests(unittest.TestCase):
    def test_combined_production_tools_fit_baseline_without_schema_unions_or_references(self):
        tools = [convert_to_openai_tool(tool) for tool in production_tools()]
        self.assertEqual(len(tools), 4)
        def check(value):
            if isinstance(value, dict):
                self.assertFalse({"anyOf", "$defs", "$ref"} & value.keys())
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)
        check(tools)
        size = len(json.dumps(tools, ensure_ascii=True, separators=(",", ":")).encode("ascii"))
        self.assertLessEqual(size, BASELINE_0152ED6_BYTES)

    def test_production_client_binds_the_same_four_compact_tools_without_invocation(self):
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "synthetic-offline-fixture", "OPENROUTER_CHAT_MODEL": "fixture",
                                       "OPENROUTER_BASE_URL": "http://127.0.0.1:9/v1"}):
            bound = agent.create_model_client().bind_tools(production_tools(), tool_choice="required")
        self.assertEqual(bound.kwargs["tools"], [convert_to_openai_tool(tool) for tool in production_tools()])
        self.assertEqual(bound.kwargs["tool_choice"], "required")
