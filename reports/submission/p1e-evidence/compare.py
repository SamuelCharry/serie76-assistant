"""Compare the three unmodified offline replay outputs; no DB/provider access.

Run from the repository root after the reproduction commands in P1-E.md.
Only generated identity/timing fields are omitted from semantic comparisons.
All product values, provenance, traces and scoring failures remain compared.
"""
import difflib
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LABELS = ("4906b62", "95d0a50", "head")
VOLATILE = {"elapsed_s", "latency_ms", "session_id", "message_id"}


def stable(value):
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if k not in VOLATILE}
    if isinstance(value, list):
        return [stable(v) for v in value]
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def changes(before, after, path=""):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(before.keys() | after.keys()):
            child = f"{path}.{key}"
            if key not in before:
                result.append({"path": child, "added": after[key]})
            elif key not in after:
                result.append({"path": child, "removed": before[key]})
            else:
                result.extend(changes(before[key], after[key], child))
        return result
    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        return [change for i, (a, b) in enumerate(zip(before, after))
                for change in changes(a, b, f"{path}[{i}]")]
    if before == after:
        return []
    if isinstance(before, str) and isinstance(after, str):
        return [{"path": path, "diff": list(difflib.unified_diff(
            before.splitlines(), after.splitlines(), fromfile="before", tofile="after", lineterm="", n=0))}]
    return [{"path": path, "before": before, "after": after}]


def main():
    runs = {label: json.loads((ROOT / f"{label}.json").read_text(encoding="utf-8")) for label in LABELS}
    indexed = {label: {s["scenario"]: s for s in run["examples"]} for label, run in runs.items()}
    ids = list(indexed[LABELS[0]])
    assert all(set(indexed[label]) == set(ids) for label in LABELS)
    rows = []
    for sid in ids:
        scenarios = [indexed[label][sid] for label in LABELS]
        assert len({len(s["turns"]) for s in scenarios}) == 1
        turns = []
        for i, values in enumerate(zip(*(s["turns"] for s in scenarios)), 1):
            assert len({t["query"] for t in values}) == 1
            cleaned = [stable(t) for t in values]
            turns.append({
                "turn": i, "query": values[0]["query"],
                "passed": {label: t["passed"] for label, t in zip(LABELS, values)},
                "failures": {label: t["failures"] for label, t in zip(LABELS, values)},
                "semantic_sha256": dict(zip(LABELS, map(digest, cleaned))),
                "4906b62_to_95d0a50": changes(cleaned[0], cleaned[1]),
                "95d0a50_to_head": changes(cleaned[1], cleaned[2]),
            })
        rows.append({"scenario": sid, "status": {label: s["status"] for label, s in zip(LABELS, scenarios)},
                     "turns": turns})
    summary = {label: {"passed_conversations": run["scenarios"] - len(run["failing"]),
                       "failed_conversations": len(run["failing"]),
                       "passed_turns": sum(t["passed"] for s in run["examples"] for t in s["turns"]),
                       "turns": sum(len(s["turns"]) for s in run["examples"])}
               for label, run in runs.items()}
    summary["newly_failing_conversations"] = sorted(set(runs["head"]["failing"]) - set(runs["4906b62"]["failing"]))
    result = {"summary": summary, "ignored_fields": sorted(VOLATILE), "conversations": rows}
    (ROOT / "comparison.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
