"""Idempotent, bounded embedding load; secrets stay in the process environment."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from psycopg.types.json import Jsonb
from backend.catalog.cli import local_environment
from backend.catalog.db import connect
from backend.conversation import embeddings

TOOLS = {'get_actuator', 'search_actuators', 'explain_terms', 'ask_clarification'}


def examples_from_cases(cases):
    """Never invent missing labels; conflicting duplicate queries are excluded."""
    rows, conflicts = {}, set()
    for scenario in cases['scenarios']:
        for turn in scenario['turns']:
            text = turn.get('query', '').strip()
            expected = turn.get('expect', {})
            decision = turn.get('scripted_decision')
            if not decision and isinstance(expected, dict) and 'tool' in expected and 'args' in expected:
                decision = [expected['tool'], expected['args']]
            if (not text or not isinstance(decision, (list, tuple)) or len(decision) != 2
                    or decision[0] not in TOOLS or not isinstance(decision[1], dict)
                    or isinstance(expected, list) or turn.get('answers') or turn.get('action')):
                continue
            interpretation = dict(tool=decision[0], args=decision[1])
            if text in rows and rows[text]['interpretation'] != interpretation:
                conflicts.add(text)
            else:
                row = rows.setdefault(text, dict(text=text, interpretation=interpretation, sources=[]))
                if scenario['id'] not in row['sources']:
                    row['sources'].append(scenario['id'])
    return [row for text, row in rows.items() if text not in conflicts]


def pending(connection, examples, anchors, model):
    existing = {r['text'] for r in connection.execute('SELECT text FROM series76.example_bank WHERE model=%s', (model,))}
    known = {(r['concept'], r['phrase']) for r in connection.execute(
        'SELECT concept,phrase FROM series76.concept_anchor WHERE model=%s', (model,))}
    return ([('example', row) for row in examples if row['text'] not in existing] +
            [('anchor', dict(concept=concept, text=phrase)) for concept, phrases in anchors.items()
             for phrase in dict.fromkeys(phrases) if (concept, phrase) not in known])


def load(connection, examples, anchors, model, embed=embeddings.embed_documents, *, batch_size=32):
    if not 1 <= batch_size <= 64:
        raise ValueError('Batch size must be 1..64')
    count = 0
    # Serializes loaders so concurrent runs cannot pay twice for the same text.
    with connection.transaction():
        connection.execute('SELECT pg_advisory_xact_lock(760009)')
        missing = pending(connection, examples, anchors, model)
        for start in range(0, len(missing), batch_size):
            batch = missing[start:start + batch_size]
            vectors = embed([row['text'] for _, row in batch])
            if len(vectors) != len(batch):
                raise ValueError('Incomplete embedding batch')
            for (kind, row), vector in zip(batch, vectors):
                literal = embeddings.vector_literal(vector)
                if kind == 'example':
                    connection.execute('''INSERT INTO series76.example_bank
                        (text,interpretation,source,model,dim,embedding) VALUES (%s,%s,%s,%s,768,%s::vector)
                        ON CONFLICT(text,model) DO NOTHING''',
                        (row['text'], Jsonb(row['interpretation']), json.dumps(sorted(row['sources'])), model, literal))
                else:
                    connection.execute('''INSERT INTO series76.concept_anchor
                        (concept,phrase,model,embedding) VALUES (%s,%s,%s,%s::vector)
                        ON CONFLICT(concept,phrase,model) DO NOTHING''', (row['concept'], row['text'], model, literal))
                count += 1
        # Keep source exclusions accurate when the same labeled text gains a scenario.
        for row in examples:
            connection.execute('''UPDATE series76.example_bank SET source=%s,interpretation=%s
                WHERE text=%s AND model=%s''',
                (json.dumps(sorted(row['sources'])), Jsonb(row['interpretation']), row['text'], model))
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=ROOT / 'config/agent_acceptance_cases_v7.json')
    parser.add_argument('--anchors', type=Path, default=ROOT / 'config/concept_anchors.json')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--usd-per-million-tokens', type=float, default=.20)
    args = parser.parse_args()
    examples = examples_from_cases(json.loads(args.cases.read_text(encoding='utf-8')))
    anchors = json.loads(args.anchors.read_text(encoding='utf-8'))
    model = os.getenv('OPENROUTER_EMBEDDING_MODEL', '')
    if not model:
        parser.error('Set OPENROUTER_EMBEDDING_MODEL in the process environment')
    local_environment()
    with connect() as connection:
        missing = pending(connection, examples, anchors, model)
        # UTF-8 bytes is a conservative token-count estimate, not a billed usage claim.
        estimated_tokens = sum(len(row['text'].encode('utf-8')) for _, row in missing)
        estimate = estimated_tokens * args.usd_per_million_tokens / 1_000_000
        print(json.dumps(dict(pending_texts=len(missing), examples=len(examples),
                              anchors=sum(map(len, anchors.values())), estimated_tokens=estimated_tokens,
                              estimated_usd=round(estimate, 6), estimate_basis='UTF-8 byte upper estimate',
                              batches=math.ceil(len(missing) / args.batch_size))), flush=True)
        if args.dry_run:
            return 0
        try:
            count = load(connection, examples, anchors, model,
                         lambda texts: embeddings.embed_documents(texts, timeout=30), batch_size=args.batch_size)
        except Exception as exc:
            # Never output provider exception payloads.
            print(json.dumps(dict(status='failed', error_type=type(exc).__name__)), file=sys.stderr)
            return 1
        print(json.dumps(dict(status='loaded', texts_embedded=count, estimated_usd=round(estimate, 6))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
