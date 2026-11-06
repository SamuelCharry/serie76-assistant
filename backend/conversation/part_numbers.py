"""Resolve user-written identifiers against the active catalogue, never model guesses."""

import re
from dataclasses import dataclass, field


# A Series-style six-character head is required: ordinary quantities are not codes.
# Presentation separators may occur between characters. Stop before natural language.
MENTION = re.compile(
    r"(?<!\w)(?:\d[-\s]*){3}[a-z][-\s]*\d[-\s]*\d"
    r"(?:[-\s]*[0-9c]){0,8}(?:[-\s]*/?[-\s]*a\b)?(?![\w/-])", re.I
)


def identity(value):
    return re.sub(r"[-/\s]", "", value).upper()


def one_edit(left, right):
    """One substitution/insertion/deletion; no fuzzy numerical/specification lookup."""
    if len(left) == len(right):
        return sum(a != b for a, b in zip(left, right)) == 1
    if len(left) > len(right):
        left, right = right, left
    if len(right) != len(left) + 1:
        return False
    index = next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), len(left))
    return left[index:] == right[index + 1:]


@dataclass
class Resolution:
    query: str
    assumptions: list = field(default_factory=list)
    unresolved: str | None = None
    candidates: list = field(default_factory=list)
    partial: bool = False


def resolve_query(connection, query):
    result = Resolution(query)
    mentions = list(MENTION.finditer(query))
    if not mentions:
        return result
    codes = [row['base_part_number'] for row in connection.execute(
        """SELECT DISTINCT e.base_part_number FROM series76.entries e
        JOIN series76.catalog_state c ON c.active_import_id=e.import_id ORDER BY 1"""
    ).fetchall()]
    identities = {code: identity(code) for code in codes}
    replacements = []
    for match in mentions:
        raw = match.group()
        compact = identity(raw)
        exact = [code for code, key in identities.items() if key == compact]
        prefixes = [code for code, key in identities.items() if key.startswith(compact)]
        candidates = exact or prefixes
        if len(candidates) == 1:
            code = candidates[0]
            replacements.append((match.start(), match.end(), code))
            if raw != code:
                result.assumptions.append(dict(field='part_number', user_phrase=raw, value=code))
            continue
        # A near spelling is a question, never automatic substitution of another model.
        near = [code for code, key in identities.items() if one_edit(compact, key)]
        result.unresolved = raw
        result.candidates = (candidates or near)[:3]
        result.partial = bool(prefixes)
        return result
    for start, end, code in reversed(replacements):
        result.query = result.query[:start] + code + result.query[end:]
    return result
