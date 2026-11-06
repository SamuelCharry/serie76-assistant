"""Provider schema budget; no DB, credentials, provider or inference needed."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.utils.function_calling import convert_to_openai_tool
from backend.conversation import agent
from scripts.check_tool_schemas import metrics, main, live_preflight


# Computed once from git show 0152ed6:{backend/conversation/agent.py,
# backend/catalog/models.py,backend/conversation/policy.py}, executing only schema
# declarations using the locked runtime and the retained 16 glossary term keys.
# Complete four-tool list: ASCII json.dumps(..., separators=(",", ":")): 5522 bytes.
BASELINE_0152ED6_BYTES = 5522


def production_tools():
    terms = json.loads((Path(__file__).resolve().parents[1] / "data/extracted/series76_summary/terms.json").read_text(encoding="utf-8"))
    return agent.declarations(agent.schemas([term["term_key"] for term in terms["terms"]]))


class ToolSchemaBudgetTests(unittest.TestCase):
    def test_complexity_stays_within_pre_t6_counts_and_has_no_lookup_object_arrays(self):
        # Coordinator measured 0152ed6: 108 enum values, 6 arrays, 5 required,
        # depth 7. Bytes alone did not predict Gemini's cumulative budget.
        result = metrics([convert_to_openai_tool(tool) for tool in production_tools()])
        for key, maximum in {"enum_values": 108, "arrays": 6, "required": 5, "depth": 7}.items():
            self.assertLessEqual(result[key], maximum, key)
        for key in ("numeric_ranges", "forbidden_nodes", "get_actuator_object_arrays"):
            self.assertEqual(result[key], 0, key)

    def test_default_preflight_is_offline(self):
        with patch("scripts.check_tool_schemas.live_preflight", side_effect=AssertionError("unexpected inference")):
            self.assertEqual(main([]), 0)

    def test_live_preflight_calls_once_and_suppresses_provider_error_body(self):
        from types import SimpleNamespace
        import io
        from contextlib import redirect_stdout
        from unittest.mock import Mock
        client = Mock()
        client.bind_tools.return_value = client
        client.invoke.return_value = SimpleNamespace(tool_calls=[{"name": "explain_terms"}])
        with patch.object(agent, "create_model_client", return_value=client), patch.object(agent, "reserve_agent_call"), redirect_stdout(io.StringIO()):
            self.assertEqual(live_preflight(), 0)
        self.assertEqual(client.invoke.call_count, 1)
        self.assertEqual(len(client.bind_tools.call_args.args[0]), 4)
        self.assertEqual(client.bind_tools.call_args.kwargs["tool_choice"], "required")
        class Rejected(Exception):
            status_code = 400
        client.invoke.reset_mock()
        client.invoke.side_effect = Rejected("PRIVATE_RESPONSE_FIXTURE")
        output = io.StringIO()
        with patch.object(agent, "create_model_client", return_value=client), patch.object(agent, "reserve_agent_call"), redirect_stdout(output):
            self.assertEqual(live_preflight(), 1)
        self.assertEqual(client.invoke.call_count, 1)
        self.assertIn("status=400", output.getvalue())
        self.assertNotIn("PRIVATE_RESPONSE_FIXTURE", output.getvalue())

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
