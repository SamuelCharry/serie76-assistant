"""Audit visible answer/label/reply text; machine IDs in structured data are allowed."""
import re
from backend.catalog.loader import NUMERIC_FIELDS

SNAKE_CASE = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b")


def public_text_issues(answer, comparison=None, suggested_replies=()):
    texts = [("answer", answer)]
    texts += [("comparison label", row["label"]) for row in (comparison or {}).get("rows", [])]
    texts += [("suggested reply", reply) for reply in suggested_replies]
    issues = [f"internal identifier in {where}: {match.group()}"
              for where, text in texts for match in SNAKE_CASE.finditer(text)]
    # Also reject the former mechanically expanded labels, e.g. "fla 60 Hz a".
    # Natural labels such as "cycles per hour" remain valid English.
    fields = [key for key in NUMERIC_FIELDS if key.endswith(("_nm", "_in_lb", "_w", "_a", "_s", "_percent"))]
    for where, text in texts:
        normalized = re.sub(r"(\d)\s+hz\b", r"\1hz", text.lower())
        for key in fields:
            if re.search(r"\b" + re.escape(key.replace("_", " ")) + r"\b", normalized):
                issues.append(f"internal field label in {where}: {key}")
    return issues
