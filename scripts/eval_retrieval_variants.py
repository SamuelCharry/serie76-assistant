"""Compare retrieval variants without any API call; tune on a fixed query split."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.conversation import retrieval_ranking as ranking
from scripts.eval_retrieval import rank_bank, signature, prompt_useful, metrics

SEED = 20261104
WEIGHTS = [.02, .05, .1, .2, .4]  # Weight zero is already variant A.
LAMBDAS = [.5, .6, .7, .8, .9]


def summarize(bank, rankings, indices, threshold=None):
    by_id = {r['id']: r for r in bank}
    result = {}
    for definition in ('strict', 'prompt_useful'):
        rows = []
        for i in indices:
            query = bank[i]['interpretation']
            neighbors = []
            for row in rankings[i][:5]:
                other = by_id[row['id']]['interpretation']
                relevant = signature(query) == signature(other) if definition == 'strict' else prompt_useful(query, other)
                neighbors.append((row['similarity'], row['id'], relevant))
            rows.append(neighbors)
        values = [metrics(rows, k, threshold) for k in (1, 3, 5)]
        result[definition] = dict(p1=values[0]['precision'], p3=values[1]['precision'],
                                  p5=values[2]['precision'], mrr5=values[2]['mrr'])
    return result


def score(result):
    return result['prompt_useful']['p5'], result['strict']['p5']


def evaluate(bank, masked=None):
    by_id = {r['id']: r for r in bank}
    started = time.perf_counter()
    raw = rank_bank(bank)
    dense_ms = (time.perf_counter()-started)*1000/len(bank)
    dense = [[dict(by_id[identifier], similarity=similarity) for similarity, identifier, _ in rows] for rows in raw]
    # Keep vectors out of candidate dictionaries: ranking only reads text and stored metadata.
    for rows in dense:
        for row in rows:
            row.pop('vector', None)
    all_indices = list(range(len(bank)))
    shuffled = all_indices.copy()
    random.Random(SEED).shuffle(shuffled)
    tune = sorted(shuffled[:max(1, len(bank)//5)])
    validation = sorted(set(all_indices)-set(tune))
    variants, ranks = {}, {}

    def add(name, ranked, elapsed_ms=0, parameters=None):
        ranks[name] = ranked
        variants[name] = dict(parameters=parameters or {},
                             all=summarize(bank, ranked, all_indices),
                             tuning=summarize(bank, ranked, tune),
                             validation=summarize(bank, ranked, validation),
                             extra_local_ms=elapsed_ms, extra_api_calls=0)

    def run(function, candidates):
        start = time.perf_counter()
        result = [function(bank[i]['text'], rows) for i, rows in enumerate(candidates)]
        return result, (time.perf_counter()-start)*1000/len(bank)

    add('A dense', dense)
    grid = {}
    for weight in WEIGHTS:
        rows, elapsed = run(lambda text, ns: ranking.rerank(text, ns[:20], weight), dense)
        name = f'B w={weight}'
        add(name, rows, elapsed, dict(weight=weight))
        grid[name] = variants[name]['tuning']
    best_b = max(grid, key=lambda n: score(grid[n]))
    lexical = ranking.BM25(bank)
    rows, elapsed = run(lambda text, ns: ranking.hybrid(text, ns, lexical), dense)
    add('C hybrid', rows, elapsed, dict(rrf_k=60, bm25_k1=1.5, bm25_b=.75))
    best_ac = max(['A dense', best_b, 'C hybrid'], key=lambda n: score(variants[n]['tuning']))
    similarities = {(bank[i]['id'], identifier): similarity for i, rows in enumerate(raw) for similarity, identifier, _ in rows}
    mmr_grid = {}
    for weight in LAMBDAS:
        rows, elapsed = run(lambda text, ns: ranking.mmr(ns, similarities, weight), ranks[best_ac])
        name = f'D lambda={weight}'
        add(name, rows, elapsed+variants[best_ac]['extra_local_ms'], dict(base=best_ac, lambda_=weight))
        mmr_grid[name] = variants[name]['tuning']
    best_d = max(mmr_grid, key=lambda n: score(mmr_grid[n]))
    table_names = ['A dense', best_b, 'C hybrid', best_d]
    masked_grid = {}
    if masked:
        masked_rank = rank_bank(masked)
        e_rows = [[dict(by_id[identifier], similarity=similarity) for similarity, identifier, _ in rows] for rows in masked_rank]
        for rows in e_rows:
            for row in rows:
                row.pop('vector', None)
        _, masking_ms = run(lambda text, _: ranking.mask_values(text), dense)
        add('E masked', e_rows, masking_ms, dict(dataset='gemini-embedding-2/masked-t9s2-v1'))
        for weight in WEIGHTS:
            rows, elapsed = run(lambda text, ns: ranking.rerank(text, ns[:20], weight), e_rows)
            name = f'E+B w={weight}'
            add(name, rows, elapsed+masking_ms, dict(weight=weight))
            masked_grid[name] = variants[name]['tuning']
        best_eb = max(masked_grid, key=lambda n: score(masked_grid[n]))
        table_names += ['E masked', best_eb]
    # Adoption has to improve both definitions on all queries AND the untuned split.
    eligible = []
    for name in table_names[1:]:
        if all(variants[name][split]['prompt_useful']['p5'] >= variants['A dense'][split]['prompt_useful']['p5'] + .05
               and variants[name][split]['strict']['p5'] >= variants['A dense'][split]['strict']['p5'] + .02
               for split in ('all', 'validation')):
            eligible.append(name)
    # Prefer a single deterministic rerank over a lexical index, diversity or a new embedding dataset.
    simplest = next((name for name in [best_b, 'C hybrid', best_d, *table_names[4:]] if name in eligible), 'A dense')
    return dict(seed=SEED, examples=len(bank), tuning_queries=len(tune), validation_queries=len(validation),
                bank_sha256=hashlib.sha256(json.dumps(bank, sort_keys=True).encode()).hexdigest(),
                tuning_ids=[bank[i]['id'] for i in tune], dense_local_ms=dense_ms,
                table={name: variants[name] for name in table_names},
                grids=dict(metadata=grid, mmr=mmr_grid, masked_metadata=masked_grid),
                eligibility_rule='prompt-useful P@5 +5pp and strict P@5 +2pp, on all and validation queries',
                eligible=eligible, decision=simplest,
                caveat='Query split is within the bank, not an independent corpus; related phrases can remain in training.')


def table(result, split='all'):
    lines = ['| Variant | Strict P@1 | P@3 | P@5 | MRR@5 | Useful P@1 | P@3 | P@5 | MRR@5 | Extra ms/query | Extra API calls |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name, row in result['table'].items():
        a, b = row[split]['strict'], row[split]['prompt_useful']
        values = [f'{100*r[k]:.1f}%' for r in (a, b) for k in ('p1', 'p3', 'p5')]
        lines.append(f"| {name} | {' | '.join(values[:3])} | {a['mrr5']:.3f} | {' | '.join(values[3:])} | {b['mrr5']:.3f} | {row['extra_local_ms']:.2f} | {row['extra_api_calls']} |")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'reports/behavior/retrieval-variants.json')
    args = parser.parse_args()
    from backend.catalog.cli import local_environment
    from backend.catalog.db import connect
    local_environment(ROOT/'.env')
    with connect() as connection:
        connection.execute('SET TRANSACTION READ ONLY')
        bank = list(connection.execute('''SELECT id,text,interpretation,model,dataset_version,embedding::text AS vector
            FROM series76.example_bank WHERE active AND model='gemini-embedding-2' ORDER BY id'''))
        masked_rows = list(connection.execute('''SELECT text,embedding::text AS vector FROM series76.example_bank
            WHERE model='gemini-embedding-2/masked-t9s2-v1' ORDER BY id'''))
    for row in bank:
        row['vector'] = json.loads(row['vector'])
    vectors = {r['text']: json.loads(r['vector']) for r in masked_rows}
    masked = [dict(r, vector=vectors[r['text']]) for r in bank] if vectors else None
    result = evaluate(bank, masked)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(table(result))
    print('Decision:', result['decision'])
    print('Validation query split:')
    print(table(result, 'validation'))


if __name__ == '__main__':
    main()
