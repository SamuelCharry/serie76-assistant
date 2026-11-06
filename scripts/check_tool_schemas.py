"""Offline production-tool complexity audit; --live makes ONE billable preflight call.

No .env loader or database access. Live credentials come only from process env;
responses, keys and exception bodies are never printed. No automatic retries.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NUMERIC_RANGES = {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"}


def production_tools():
    import os
    from backend.conversation import agent
    from langchain_core.utils.function_calling import convert_to_openai_tool
    terms = json.loads((ROOT / "data/extracted/series76_summary/terms.json").read_text(encoding="utf-8"))["terms"]
    if os.environ.get('AGENT_STATE_MODE', 'v1') == 'v2':
        from backend.conversation.state_v2 import declarations
        tools = declarations()
    else:
        tools = agent.declarations(agent.schemas([term["term_key"] for term in terms]))
    return [convert_to_openai_tool(tool) for tool in tools]


def metrics(tools):
    result = dict(enum_values=0, arrays=0, required=0, depth=0, numeric_ranges=0,
                  forbidden_nodes=0, get_actuator_object_arrays=0)

    def visit(value, depth=0, lookup=False):
        if isinstance(value, dict):
            result["depth"] = max(result["depth"], depth)
            result["enum_values"] += len(value.get("enum", []))
            result["required"] += len(value.get("required", []))
            result["numeric_ranges"] += len(NUMERIC_RANGES & value.keys())
            result["forbidden_nodes"] += len({"anyOf", "$defs", "$ref"} & value.keys())
            if value.get("type") == "array":
                result["arrays"] += 1
                if lookup and value.get("items", {}).get("type") == "object":
                    result["get_actuator_object_arrays"] += 1
            for child in value.values():
                visit(child, depth + 1, lookup)
        elif isinstance(value, list):
            for child in value:
                visit(child, depth, lookup)
    for tool in tools:
        visit(tool, lookup=tool["function"]["name"] == "get_actuator")
    result["bytes"] = len(json.dumps(tools, ensure_ascii=True, separators=(",", ":")).encode("ascii"))
    return result


def live_preflight():
    import os
    from backend.conversation import agent
    from langchain_core.messages import HumanMessage, SystemMessage
    from langsmith import tracing_context
    tools = production_tools()
    try:
        # Production client: max_retries=0 and require_parameters retained.
        client = agent.create_model_client().bind_tools(tools, tool_choice="required")
        agent.reserve_agent_call()
        terms = json.loads((ROOT / "data/extracted/series76_summary/terms.json").read_text(encoding="utf-8"))["terms"]
        with tracing_context(enabled=False):
            prompt = agent.SYSTEM + "\n" + agent.PLAN_B_GUIDANCE
            if os.environ.get('AGENT_STATE_MODE', 'v1') == 'v2':
                from backend.conversation.state_v2 import system_prompt
                prompt = system_prompt()
            response = client.invoke([SystemMessage(content=prompt + "\n" + agent.glossary_block(terms)),
                                      HumanMessage(content="Explain FLA.")])
        if len(response.tool_calls) != 1:
            print("FAIL: provider accepted the request but did not return exactly one tool decision")
            return 1
        print(f"Live preflight: accepted {len(tools)} tools; one decision received (not executed)")
        return 0
    except Exception as exc:
        # Status only; provider bodies may contain prompt fragments or credentials.
        status = getattr(exc, "status_code", None)
        code = exc.code if isinstance(exc, agent.AgentUnavailable) else agent.provider_error_code(exc)
        print(f"FAIL: live preflight status={status or 'unavailable'} code={code}; details suppressed")
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="ONE paid request using OPENROUTER_* process env only")
    args = parser.parse_args(argv)
    result = metrics(production_tools())
    print(json.dumps(result, sort_keys=True))
    if (result["enum_values"] > 108 or result["arrays"] > 6 or result["required"] > 5 or result["depth"] > 7
            or result["numeric_ranges"] or result["forbidden_nodes"] or result["get_actuator_object_arrays"]):
        print("FAIL: offline schema complexity guard")
        return 1
    return live_preflight() if args.live else 0


if __name__ == "__main__":
    raise SystemExit(main())
