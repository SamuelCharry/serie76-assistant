"""Audit visible answer/label/reply text; machine IDs in structured data are allowed."""
import re
from backend.catalog.loader import NUMERIC_FIELDS

SNAKE_CASE = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b")
INTERNAL = re.compile(r"\b(?:Not applied|get_actuator|search_actuators|ask_clarification|explain_terms|on_off|explosionproof|weatherproof|modulating)\b|[{}]")
RATINGS = re.compile(r"\b(?:NEMA|IP\s*\d+)\b", re.I)
STALE = re.compile(r"I left out an unstated requirement|These are the top 3 candidates|"
                   r"unresolved scopes are not assumed|I will not pick one for you|"
                   r"not published in this table layout|\b0 identical fields hidden|I cannot place orders")


def public_text_issues(answer, comparison=None, suggested_replies=()):
    texts = [("answer", answer)]
    texts += [("comparison label", row["label"]) for row in (comparison or {}).get("rows", [])]
    texts += [("suggested reply", reply) for reply in suggested_replies]
    issues = [f"internal identifier in {where}: {match.group()}"
              for where, text in texts for match in SNAKE_CASE.finditer(text)]
    issues += [f"internal term in {where}: {match.group()}" for where, text in texts
               for match in INTERNAL.finditer(text)]
    issues += [f"unsupported rating in {where}: {match.group()}" for where, text in texts
               for match in RATINGS.finditer(text)]
    issues += [f"stale public phrase in {where}: {match.group()}" for where, text in texts
               for match in STALE.finditer(text)]
    # Also reject the former mechanically expanded labels, e.g. "fla 60 Hz a".
    # Natural labels such as "cycles per hour" remain valid English.
    fields = [key for key in NUMERIC_FIELDS if key.endswith(("_nm", "_in_lb", "_w", "_a", "_s", "_percent"))]
    for where, text in texts:
        normalized = re.sub(r"(\d)\s+hz\b", r"\1hz", text.lower())
        for key in fields:
            if re.search(r"\b" + re.escape(key.replace("_", " ")) + r"\b", normalized):
                issues.append(f"internal field label in {where}: {key}")
    return issues


def response_text_issues(response):
    """Scan public prose in every scripted response; structured IDs remain machine data."""
    texts = [response.get('answer') or '', response.get('lead') or '']
    texts += response.get('suggested_replies') or []
    texts += [item.get('label', '') if isinstance(item, dict) else item
              for item in response.get('suggestions') or []]
    texts += [item.get('label', '') for item in response.get('active_filters') or []]
    interaction = response.get('interaction') or {}
    texts += [q.get('prompt', '') for q in interaction.get('questions', [])]
    texts += [o.get('label', '') for q in interaction.get('questions', []) for o in q.get('options', [])]
    texts += [o.get('description', '') for q in interaction.get('questions', []) for o in q.get('options', [])]
    clarification = response.get('clarification') or {}
    texts.append(clarification.get('message', ''))
    comparison = response.get('comparison') or {}
    texts += [comparison.get('summary', ''), comparison.get('assumptions', ''), comparison.get('key_fields_reason', '')]
    texts += [r.get('label', '') for r in comparison.get('rows', []) + comparison.get('hidden_rows', [])]
    texts += [value for r in comparison.get('rows', []) + comparison.get('hidden_rows', []) for value in r.get('values', [])]
    recommendation = response.get('recommendation') or {}
    texts.append(recommendation.get('ranked_by', ''))
    texts += [item.get('reason', '') for item in recommendation.get('items', [])]
    texts += [value for item in recommendation.get('items', []) for field in item.get('key_values', [])
              for value in (field.get('label', ''), field.get('value', ''))]
    return [issue for value in texts for issue in public_text_issues(value)]
