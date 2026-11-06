"""T11 oracle-filter ranking evaluation: PostgreSQL and real ranker, no inference.

Formulas: Manning, Raghavan & Schuetze (2008), Introduction to Information
Retrieval, sections 8.3-8.4:
https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html
https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html
Binary relevance = grade >= 1 (hard compliance). P@k = hits/k, R@k = hits/R;
AP@k = sum_{i<=k} P@i * relevant(i) / R, with the FULL relevant-set denominator
(not min(R,k)). AP uses the full returned ranking; MAP is the macro mean AP.
DCG@k = sum_{i<=k} (2**grade_i - 1)/log2(i+1), NDCG@k = DCG@k/IDCG@k.
IDCG uses all 68 judgments. Missing result positions have zero gain. A query with
no relevant products has R/AP/NDCG=0 by explicit convention, never perfect 1.

Also report compliance among returned top-k rows (hits/min(k,returned)), null for
empty results, separately from standard P@k: short safe lists cannot have P@5=1.
The safety gate requires every returned item to have grade >=1 and retrieval of
at least one product whenever the independent judgments contain compliant rows.

The backend path is canonical_arguments -> SearchInput -> SearchFilters -> real
search_actuators(SQL, all 68 candidates) -> integrity.satisfies -> ranking.rank,
the same deterministic components used by Turn.search. The objective-name adapter
mirrors Turn.search's public sort mapping; JUDGMENTS never import that adapter.
This isolates ranking from language parsing, clarification and rendering. k=3 is
the recommendation card depth; k=5 measures additional rank depth, not Android UI.
Only process PG*/DATABASE_URL settings are used. No .env reader is called.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.ranking_judgments import (CATALOG, TERMS, NUMERIC, load_catalog,
                                      judge_query, glossary_evidence)


def ranking_metrics(ranked, grades, k):
    """Return standard IR metrics and a separately named returned-row safety rate."""
    if type(k) is not int or k < 1:
        raise ValueError('k must be a positive integer')
    if len(ranked) != len(set(ranked)):
        raise ValueError('Duplicate products would inflate retrieval metrics')
    if any(code not in grades for code in ranked):
        raise ValueError('Unjudged product in ranking')
    if any(type(g) is not int or not 0 <= g <= 3 for g in grades.values()):
        raise ValueError('Grades must be integers in [0,3]')
    relevant = sum(g > 0 for g in grades.values())
    top = ranked[:k]
    hits, ap_sum = 0, 0.0
    for position, code in enumerate(top, 1):
        if grades[code] > 0:
            hits += 1
            ap_sum += hits / position
    dcg = sum((2 ** grades[c] - 1) / math.log2(i + 1) for i, c in enumerate(top, 1))
    ideal = sorted(grades.values(), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(i + 1) for i, g in enumerate(ideal, 1))
    return {'precision': hits / k, 'recall': hits / relevant if relevant else 0.0,
            'ap': ap_sum / relevant if relevant else 0.0,
            'ndcg': dcg / idcg if idcg else 0.0,
            'compliance_returned': hits / len(top) if top else None,
            'returned': len(top), 'relevant': relevant}


def verify_collection(connection, rows):
    """Reject DB drift before interpreting scores as a test of this CSV collection."""
    from backend.catalog.repository import export_rows
    exported = {r['base_part_number']: r for r in export_rows(connection)}
    if set(exported) != {r['base_part_number'] for r in rows}:
        raise ValueError('Database product set differs from the 68-product CSV')
    for row in rows:
        actual = exported[row['base_part_number']]
        for key, value in row.items():
            other = actual[key]
            if key in NUMERIC or key.startswith(('on_off_', 'modulating_', 'shared_',
                                                 'operating_time_', 'fla_', 'lra_')):
                equal = value == (Decimal(str(other)) if other is not None else None)
            else:
                equal = str(value or '') == str(other or '')
            if not equal:
                raise ValueError(f"DB/CSV mismatch: {row['base_part_number']} {key}")


def backend_ranking(connection, query, term_keys):
    import os
    if os.environ.get('AGENT_STATE_MODE', 'v1') == 'v2':
        from scripts.sv2_ranking import backend_ranking as state_ranking
        return state_ranking(connection, query, term_keys)
    from backend.catalog.models import SearchFilters
    from backend.catalog.repository import search_actuators
    from backend.conversation.agent import schemas
    from backend.conversation.tool_wire import canonical_arguments
    from backend.conversation import integrity, ranking
    wire = dict(query['filters'])
    if query.get('objective'):
        wire['sort_by'] = [query['objective']]
    args = schemas(term_keys)['search_actuators'].model_validate(
        canonical_arguments('search_actuators', wire)).model_dump(exclude_none=True)
    filters = SearchFilters.model_validate({k: v for k, v in args.items()
                                           if k in SearchFilters.model_fields})
    filters = filters.model_copy(update={'limit': 100, 'offset': 0})
    result = search_actuators(connection, filters, allow_ambiguous=True)
    if len(result['products']) != result['total']:
        raise ValueError('Incomplete SQL candidate collection')
    safe = [p for p in result['products'] if integrity.satisfies(p, filters)]
    by = {'fastest': 'fastest', 'lowest_current': 'lowest_fla',
          'highest_torque': 'most_torque', 'lowest_power': 'lowest_power'}.get(
              query.get('objective'), 'closest_torque')
    ranked = ranking.rank(safe, filters.model_dump(exclude_none=True), by)
    return [p['base_part_number'] for p in ranked], {
        'sql_total': result['total'], 'postcondition_excluded': len(result['products']) - len(safe),
        'ranked_by': by, 'schema_default_limit': args['limit']}


def evaluate(connection, config):
    from backend.catalog.context import list_terms
    rows = load_catalog()
    verify_collection(connection, rows)
    terms = [t['term_key'] for t in list_terms(connection)]
    results = []
    for query in config['queries']:
        judged = judge_query(rows, query)
        grades = {code: item['grade'] for code, item in judged.items()}
        ranked, trace = backend_ranking(connection, query, terms)
        scores = {str(k): ranking_metrics(ranked, grades, k) for k in (3, 5)}
        full = ranking_metrics(ranked, grades, max(1, len(ranked)))
        best = [code for code, grade in grades.items() if grade == 3]
        results.append(dict(query, judgments=judged, ranked=ranked, best_fit_codes=best,
                            scores=scores, ap=full['ap'], trace=trace,
                            top5_grades=[grades[c] for c in ranked[:5]]))
    def macro_mean(group):
        summary = {}
        for k in (3, 5):
            summary[str(k)] = {}
            for name in ('precision', 'compliance_returned', 'recall', 'ap', 'ndcg'):
                values = [q['scores'][str(k)][name] for q in group
                          if q['scores'][str(k)][name] is not None]
                summary[str(k)][name] = statistics.mean(values) if values else None
        return summary

    feasible = [q for q in results if q['scores']['3']['relevant'] > 0]
    unsafe = [q['id'] for q in results if any(q['judgments'][c]['grade'] == 0 for c in q['ranked'])]
    empty = [q['id'] for q in feasible if not q['ranked']]
    return {'scope': config['scope'], 'collection_size': len(rows), 'query_count': len(results),
            'judgment_count': len(rows) * len(results), 'visible_k': 3,
            'comparison_depth_k': 5, 'binary_relevance': 'grade >= 1',
            'glossary_evidence': glossary_evidence(), 'means': macro_mean(results),
            'feasible_query_count': len(feasible), 'means_feasible_only': macro_mean(feasible),
            'empty_gold_query_ids': [q['id'] for q in results if q not in feasible],
            'nonempty_returned_query_count': sum(bool(q['ranked']) for q in results),
            'map_full': statistics.mean(q['ap'] for q in results),
            'map_full_feasible_only': statistics.mean(q['ap'] for q in feasible) if feasible else None,
            'safety_failures': unsafe, 'unexpected_empty_results': empty,
            'worst_query_ids': [q['id'] for q in sorted(results, key=lambda q: (
                q['scores']['3']['ndcg'], q['scores']['5']['ndcg'], q['id']))[:3]],
            'queries': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config/ranking_eval_t11.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'reports/submission/T11-B-ranking.json')
    args = parser.parse_args()
    from backend.catalog.db import connect
    config = json.loads(args.config.read_text(encoding='utf-8'))
    if len({q['id'] for q in config['queries']}) != len(config['queries']):
        raise ValueError('Duplicate query IDs')
    with connect() as connection, connection.transaction(force_rollback=True):
        connection.execute('SET TRANSACTION READ ONLY')
        report = evaluate(connection, config)
    sources = [CATALOG, TERMS, args.config, Path(__file__), ROOT / 'scripts/ranking_judgments.py',
               ROOT / 'backend/conversation/ranking.py', ROOT / 'backend/catalog/repository.py',
               ROOT / 'backend/conversation/agent.py', ROOT / 'backend/conversation/integrity.py',
               ROOT / 'backend/conversation/tool_wire.py', ROOT / 'backend/catalog/models.py']
    report['sha256'] = {str(p.resolve().relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sources}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('queries', 'glossary_evidence', 'sha256')}, indent=2))
    return 1 if report['safety_failures'] or report['unexpected_empty_results'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
