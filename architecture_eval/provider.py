"""One-controller, durable pre-call reservations including failed requests.

Prices are token estimates, not invoices. Uncertain charges retain the full
reservation. The run-level lock is held by the CLI for its entire lifetime.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from unittest.mock import patch

from model_eval.google import GeminiRouter, request_json, API_ROOT


class BudgetStop(Exception):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def append(path, value):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(canonical(value) + "\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())


class Budget:
    def __init__(self, folder, config):
        self.path = Path(folder) / "ledger.jsonl"
        self.config = config
        self.last = 0.0
        self.label = {}
        self.blocked = False

    def events(self):
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines()] if self.path.exists() else []

    def spent(self):
        charges = {}
        for event in self.events():
            charges[event["id"]] = event["charged_usd"]
        return sum(charges.values())

    def reserve(self, endpoint, payload):
        embedding = endpoint.endswith(":embedContent")
        rate = self.config["embedding_usd_per_million" if embedding else "input_usd_per_million"]
        # Conservative UTF-8 byte bound + allowance for server/tool overhead.
        input_bound = len(canonical(payload).encode("utf-8")) + 4096
        output_bound = 0 if embedding else self.config["max_output_tokens"]
        amount = (input_bound * rate + output_bound * self.config["output_usd_per_million"]) / 1e6
        if self.spent() + amount > self.config["budget_usd"]:
            self.blocked = True
            raise BudgetStop("Insufficient budget for the next worst-case reservation")
        call_id = len(self.events()) + 1
        event = dict(id=call_id, state="reserved", charged_usd=amount, reserved_usd=amount,
                     endpoint=endpoint.removeprefix(API_ROOT), payload_sha256=hashlib.sha256(canonical(payload).encode()).hexdigest(),
                     label=dict(self.label))
        append(self.path, event)
        return event

    def request(self, endpoint, key, payload=None):
        if not endpoint.startswith(API_ROOT + "models/"):
            raise ValueError("Only Google model calls are permitted")
        event = self.reserve(endpoint, payload)
        wait = self.config["min_interval_seconds"] - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)
        start = time.perf_counter()
        try:
            result = request_json(endpoint, key, payload)
        except Exception as exc:
            append(self.path, dict(event, state="failed", error=type(exc).__name__,
                                   status=getattr(exc, "status", None), latency_s=time.perf_counter()-start))
            raise
        finally:
            self.last = time.monotonic()
        usage = result.get("usageMetadata", {})
        if endpoint.endswith(":embedContent"):
            # Some embedContent versions omit usage. Keep full reservation then.
            actual = usage.get("promptTokenCount")
            charge = actual * self.config["embedding_usd_per_million"] / 1e6 if actual is not None else event["reserved_usd"]
        elif usage.get("promptTokenCount") is not None:
            actual = (usage["promptTokenCount"] * self.config["input_usd_per_million"] +
                      (usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)) * self.config["output_usd_per_million"]) / 1e6
            charge = actual
        else:
            charge = event["reserved_usd"]
        append(self.path, dict(event, state="completed", charged_usd=charge, usage=usage,
                               model_version=result.get("modelVersion"), latency_s=time.perf_counter()-start))
        if self.spent() > self.config["budget_usd"]:
            raise BudgetStop("Provider usage exceeded the conservative reservation; stopped")
        return result


class PaidRouter(GeminiRouter):
    def __init__(self, budget, key):
        super().__init__(budget.config["model"], key, max_output_tokens=budget.config["max_output_tokens"])
        self.budget = budget

    def invoke(self, chat, config=None):
        with patch("model_eval.google.request_json", self.budget.request):
            return super().invoke(chat, config)
