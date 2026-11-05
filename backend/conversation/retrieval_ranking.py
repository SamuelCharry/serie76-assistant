"""Small, local example rankers. They never add or edit a product filter."""
from collections import Counter
import math
import re
import unicodedata

from . import policy, requirement_coverage


def torque_operators(args):
    operators = []
    for field in ('min_torque_nm', 'min_torque_in_lb'):
        value = args.get(field)
        if value is not None:
            for bound in value if isinstance(value, list) else [value]:
                operators.append(bound['op'] if isinstance(bound, dict) else 'gte')
    return tuple(sorted(operators))


def metadata(args):
    result = {key: args[key] for key in ('service', 'enclosure', 'supply_voltage_v', 'phase_count')
              if args.get(key) is not None}
    if operators := torque_operators(args):
        result['torque_operators'] = operators
    return result


def detected_fields(text):
    """Use the existing deterministic parsers, with no semantic suggestions."""
    fields, _ = policy.colloquial_requirements(text)
    fields, _ = requirement_coverage.apply(text, fields)
    return metadata(fields)


def rerank(query, candidates, weight):
    """Missing neighbor fields neither agree nor conflict; only detected fields vote."""
    detected = detected_fields(query)
    scored = []
    for row in candidates:
        neighbor = metadata(row['interpretation']['args'])
        agreement = sum(1 if neighbor[key] == value else -1
                        for key, value in detected.items() if key in neighbor)
        scored.append(dict(row, rank_score=row['similarity'] + weight * agreement))
    return sorted(scored, key=lambda row: (-row['rank_score'], row['id']))


def tokens(text):
    text = ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))
    text = re.sub(r'\bon[\s_/-]*off\b', 'on/off', text)
    text = re.sub(r'\b(\d+(?:[.,]\d+)?)\s*(v|volts?)\b', r'\1v', text)
    return re.findall(r'on/off|\d+(?:[.,]\d+)?[a-z]+|[a-z0-9]+', text)


class BM25:
    """BM25 with k1=1.5, b=0.75; document counts are local to this bank."""
    def __init__(self, rows):
        self.counts = {r['id']: Counter(tokens(r['text'])) for r in rows}
        self.lengths = {key: sum(counts.values()) for key, counts in self.counts.items()}
        self.average = sum(self.lengths.values()) / max(1, len(rows)) or 1
        frequency = Counter(token for counts in self.counts.values() for token in counts)
        self.idf = {t: math.log(1 + (len(rows)-df+.5)/(df+.5)) for t, df in frequency.items()}

    def rank(self, text, allowed):
        query = set(tokens(text))
        allowed = list(allowed)
        # Excluded query/duplicate/source rows must not influence lexical statistics.
        average = sum(self.lengths[i] for i in allowed) / max(1, len(allowed)) or 1
        idf = self.idf if len(allowed) == len(self.counts) else {
            t: math.log(1 + (len(allowed)-df+.5)/(df+.5))
            for t in query for df in [sum(t in self.counts[i] for i in allowed)]}
        scored = []
        for identifier in allowed:
            counts = self.counts[identifier]
            length = self.lengths[identifier]
            score = sum(idf.get(t, 0) * counts[t] * 2.5 /
                        (counts[t] + 1.5 * (.25 + .75 * length/average))
                        for t in query if counts[t])
            scored.append((identifier, score))
        return sorted(scored, key=lambda row: (-row[1], row[0]))


def hybrid(query, dense, lexical):
    """RRF k=60; zero lexical scores cast no vote, and ties use stable IDs."""
    scores = {r['id']: 1/(60+i) for i, r in enumerate(dense, 1)}
    for i, (identifier, score) in enumerate(lexical.rank(query, scores), 1):
        if score > 0:
            scores[identifier] += 1/(60+i)
    return sorted((dict(r, rank_score=scores[r['id']]) for r in dense),
                  key=lambda r: (-r['rank_score'], r['id']))


def mmr(candidates, similarities, diversity_weight, k=5):
    """MMR over top 20: min-max rank score minus redundancy in original cosine."""
    pending = list(candidates[:20])
    if not pending:
        return []
    values = [r.get('rank_score', r['similarity']) for r in pending]
    lower, upper = min(values), max(values)
    relevance = {r['id']: (v-lower)/(upper-lower) if upper > lower else 1
                 for r, v in zip(pending, values)}
    selected = []
    while pending and len(selected) < k:
        def score(row):
            redundancy = max((similarities.get((row['id'], s['id']), 1) for s in selected), default=0)
            return diversity_weight*relevance[row['id']] - (1-diversity_weight)*redundancy
        chosen = min(pending, key=lambda r: (-score(r), r['id']))
        selected.append(chosen)
        pending.remove(chosen)
    return selected


def mask_values(text):
    """Mask quantities with explicit units; leave part numbers and bare numbers alone."""
    patterns = [(r'v(?:olts?)?', 'VOLTAGE'), (r'(?:k\s*)?n\s*-?\s*m|in\s*-?\s*lbs?', 'TORQUE'),
                (r'hz', 'FREQ')]
    for unit, label in patterns:
        text = re.sub(r'(?<![\w/.-])\d+(?:[.,]\d+)?\s*(?:' + unit + r')(?![a-z])',
                      f'<{label}>', text, flags=re.I)
    return text
