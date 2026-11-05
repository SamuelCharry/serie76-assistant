"""Leave-one-out evaluation using stored vectors only; no embedding calls.

Relevant means identical tool, service, enclosure, supply_voltage_v and torque
operators (gt/gte/lt/lte/eq, including both bounds). Missing fields must also agree.
A scalar minimum means gte. Torque magnitude/unit is ignored: this measures an
interpretation pattern, not a correct product or interchangeable requirements.
For other tools this deliberately coarse label does not compare codes or terms.
Self and exact duplicate text are excluded; models are never mixed. Cosine ranking
is exact, with ID breaking ties. Precision@k divides by k even if fewer return;
MRR@5 is 1 / first relevant rank, or zero. All queries remain in denominators.
This is an internal bank diagnostic, not an unseen-query or end-to-end benchmark.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def signature(interpretation):
    args = interpretation['args']
    operators = []
    for field in ('min_torque_nm', 'min_torque_in_lb'):
        value = args.get(field)
        if value is not None:
            for bound in value if isinstance(value, list) else [value]:
                operators.append(bound['op'] if isinstance(bound, dict) else 'gte')
    return (interpretation['tool'], args.get('service'), args.get('enclosure'),
            args.get('supply_voltage_v'), tuple(sorted(operators)))


def rank_bank(bank):
    """Normalize stored vectors once, then compute exact cosine without a service."""
    normalized = []
    dimensions = {}
    for row in bank:
        vector = row['vector']
        norm = math.sqrt(sum(x*x for x in vector))
        model = row['model']
        if not vector or not math.isfinite(norm) or norm == 0:
            raise ValueError('Invalid stored vector')
        if dimensions.setdefault(model, len(vector)) != len(vector):
            raise ValueError('Different dimensions within a model')
        normalized.append([x/norm for x in vector])
    ranked = [[] for _ in bank]
    for i, query in enumerate(bank):
        for j in range(i + 1, len(bank)):
            other = bank[j]
            if query['model'] != other['model'] or query['id'] == other['id'] or query['text'] == other['text']:
                continue
            score = sum(a*b for a, b in zip(normalized[i], normalized[j]))
            relevant = signature(query['interpretation']) == signature(other['interpretation'])
            ranked[i].append((score, other['id'], relevant))
            ranked[j].append((score, query['id'], relevant))
    return [sorted(rows, key=lambda r: (-r[0], r[1])) for rows in ranked]


def metrics(ranked, k, threshold=None):
    if not ranked or k < 1:
        raise ValueError('Need queries and positive k')
    selected = [[r for r in rows if threshold is None or r[0] >= threshold][:k] for rows in ranked]
    relevant = sum(sum(r[2] for r in rows) for rows in selected)
    returned = sum(len(rows) for rows in selected)
    return dict(k=k, threshold=threshold, precision=relevant/(len(ranked)*k),
                mrr=sum(next((1/i for i, r in enumerate(rows, 1) if r[2]), 0) for rows in selected)/len(ranked),
                coverage=sum(bool(rows) for rows in selected)/len(ranked),
                mean_returned=returned/len(ranked),
                returned_precision=relevant/returned if returned else None)


def evaluate(bank, threshold):
    if not bank:
        raise ValueError('No active examples')
    ranked = rank_bank(bank)
    # This fingerprint detects a changed bank without publishing vectors or text.
    fingerprint = hashlib.sha256(json.dumps(bank, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    results = []
    for model in sorted({r['model'] for r in bank}):
        rows = [neighbors for r, neighbors in zip(bank, ranked) if r['model'] == model]
        sweep = [metrics(rows, k, t) for t in [None, *sorted({.50, .60, .70, .75, .80, .85, .90, threshold})]
                 for k in (1, 3, 5, 8)]
        baseline = [metrics(rows, k) for k in (1, 3, 5, 8)]
        current = metrics(rows, 5, threshold)
        recommendation = (
            f"k=5 adds {100*(baseline[2]['mrr']-baseline[0]['mrr']):.1f} MRR points over k=1; "
            f"k=8 adds {100*(baseline[3]['mrr']-baseline[2]['mrr']):.1f} more. "
            f"Threshold {threshold:.2f} covers {100*current['coverage']:.1f}% of queries. "
            'k=5 and the threshold remain provisional: this sweep exposes the trade-off, '
            'but does not establish an optimum or a downstream quality benefit; validate on fresh queries before changing them.')
        results.append(dict(model=model, queries=len(rows),
                            queries_without_relevant_neighbor=sum(not any(r[2] for r in ns) for ns in rows),
                            unfiltered=baseline, current=current, sweep=sweep, recommendation=recommendation))
    return dict(bank_sha256=fingerprint, active_examples=len(bank),
                dataset_versions=dict(Counter(str(r.get('dataset_version')) for r in bank)),
                current_k=5, current_threshold=threshold, models=results)


def readable(result):
    lines = [f"Stored bank: {result['active_examples']} active examples; sha256={result['bank_sha256']}",
             'Exact cosine; self/same text excluded; relevance is tool + search-field pattern, not product correctness.',
             'Precision uses k slots per query; missing slots count as misses. MRR is truncated at k.']
    for model in result['models']:
        lines.append(f"Model: {model['model']}; queries={model['queries']}; "
                     f"no relevant neighbor anywhere={model['queries_without_relevant_neighbor']}")
        lines.append('threshold  k  precision@k  MRR@k  coverage  mean returned  precision among returned')
        for row in model['sweep']:
            threshold = 'none' if row['threshold'] is None else f"{row['threshold']:.2f}"
            rp = 'N/A' if row['returned_precision'] is None else f"{row['returned_precision']:.4f}"
            lines.append(f"{threshold:>9} {row['k']:2} {row['precision']:12.4f} {row['mrr']:6.4f} "
                         f"{row['coverage']:9.4f} {row['mean_returned']:14.2f} {rp:>25}")
        lines.append(model['recommendation'])
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'reports/behavior/retrieval.json')
    args = parser.parse_args()
    # Load only database settings through the approved helper; never display them.
    from backend.catalog.cli import local_environment
    from backend.catalog.db import connect
    from backend.conversation.embeddings import MIN_SIMILARITY
    local_environment(ROOT / '.env')
    try:
        with connect() as connection:
            connection.execute('SET TRANSACTION READ ONLY')
            bank = list(connection.execute('''SELECT id,text,interpretation,model,dataset_version,
                embedding::text AS vector FROM series76.example_bank WHERE active ORDER BY id'''))
        for row in bank:
            row['vector'] = json.loads(row['vector'])
        result = evaluate(bank, MIN_SIMILARITY)
    except Exception:
        # Database exceptions may contain connection details; never echo them.
        print('Retrieval evaluation failed; check local DB availability and active stored vectors.', file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(readable(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
