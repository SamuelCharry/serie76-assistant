"""Minimal Google-only routing adapter. Never reads or calls OpenRouter."""

from __future__ import annotations

import json
import os
from pathlib import Path
import time
from types import SimpleNamespace
import urllib.error
import urllib.request

API_ROOT = "https://generativelanguage.googleapis.com/v1beta/"


class ProviderFailure(Exception):
    def __init__(self, status, category):
        super().__init__(f"Google API {category} ({status})")
        self.status = status
        self.category = category


def api_key(path=Path(".env")):
    values = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                if key.strip() in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
                    values[key.strip()] = value.strip().strip("\"'")
    value = (
        os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or values.get("GOOGLE_API_KEY")
        or values.get("GEMINI_API_KEY")
    )
    if not value:
        raise ValueError(
            "Configure GOOGLE_API_KEY or GEMINI_API_KEY in the local .env; never paste it into reports."
        )
    return value


def request_json(endpoint, key, payload=None):
    # Constant Google host. API keys are headers, never query strings or logs.
    if not endpoint.startswith(API_ROOT):
        raise ValueError("Only the Google Gemini API is allowed in this evaluator")
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Deliberately do not expose provider bodies; they may contain private identifiers.
        category = {
            400: "invalid_request",
            401: "authentication",
            402: "payment_required",
            403: "access_denied",
            404: "model_unavailable",
            429: "quota_exhausted",
        }.get(exc.code, "upstream_error")
        raise ProviderFailure(exc.code, category) from None
    except (OSError, ValueError):
        raise ProviderFailure(0, "network_or_response_error") from None


def available_models(key):
    result = request_json(API_ROOT + "models?pageSize=1000", key)
    return sorted(
        m["name"].removeprefix("models/")
        for m in result.get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    )


def message_content(message):
    if isinstance(message, tuple):
        role, content = message
    else:
        role, content = message.type, message.content
    if not isinstance(content, str):
        raise ValueError("This benchmark supports only text conversation inputs")
    return role, content


class GeminiRouter:
    """Implements the model interface consumed by run_agent, with one request."""

    def __init__(self, model, key, *, max_output_tokens=2048):
        self.model, self._key = model, key
        self.max_output_tokens = max_output_tokens
        self.declarations = []
        self.metadata = {}
        self.calls = []
        self.provider_failure = None
        self.request_count = 0

    def bind_tools(self, tools, *, tool_choice, parallel_tool_calls):
        if tool_choice != "required" or parallel_tool_calls:
            raise ValueError("Evaluation requires exactly one tool-routing turn")
        self.declarations = [
            {
                "name": t.name,
                "description": t.description,
                "parametersJsonSchema": t.args_schema.model_json_schema(),
            }
            for t in tools
        ]
        return self

    def invoke(self, chat, config=None):
        systems, contents = [], []
        for message in chat:
            role, text = message_content(message)
            if role == "system":
                systems.append(text)
            else:
                role = "user" if role in ("human", "user") else "model"
                if contents and contents[-1]["role"] == role:
                    contents[-1]["parts"].append({"text": text})
                else:
                    contents.append({"role": role, "parts": [{"text": text}]})
        payload = {
            "systemInstruction": {"parts": [{"text": "\n\n".join(systems)}]},
            "contents": contents,
            "tools": [{"functionDeclarations": self.declarations}],
            "toolConfig": {
                "functionCallingConfig": {
                    "mode": "ANY",
                    "allowedFunctionNames": [d["name"] for d in self.declarations],
                }
            },
            # Common documented level; sampling parameters intentionally left at defaults.
            "generationConfig": {
                "maxOutputTokens": self.max_output_tokens,
                "thinkingConfig": {"thinkingLevel": "low"},
            },
        }
        if len(json.dumps(payload)) > 60000:
            raise ValueError("Routing prompt exceeds this benchmark budget")
        start = time.perf_counter()
        self.request_count += 1
        try:
            response = request_json(
                API_ROOT + "models/" + self.model + ":generateContent",
                self._key,
                payload,
            )
        except ProviderFailure as exc:
            self.provider_failure = exc
            self.metadata = dict(latency_s=round(time.perf_counter() - start, 4))
            raise
        candidates = response.get("candidates", [])
        candidate = candidates[0] if candidates else {}
        parts = candidate.get("content", {}).get("parts", [])
        self.calls = [
            {
                "name": part["functionCall"].get("name"),
                "args": part["functionCall"].get("args", {}),
            }
            for part in parts
            if "functionCall" in part
        ]
        self.metadata = {
            "latency_s": round(time.perf_counter() - start, 4),
            "model_version": response.get("modelVersion"),
            "finish_reason": candidate.get("finishReason"),
            "usage": {
                k: response.get("usageMetadata", {}).get(k, 0)
                for k in (
                    "promptTokenCount",
                    "candidatesTokenCount",
                    "thoughtsTokenCount",
                    "totalTokenCount",
                )
            },
            "text_returned_instead_of_tool": any(
                p.get("text") for p in parts if not p.get("thought")
            ),
        }
        return SimpleNamespace(tool_calls=self.calls)
