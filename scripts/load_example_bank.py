"""Idempotent, bounded embedding load; secrets stay in the process environment."""
from __future__ import annotations

import argparse
import hashlib
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


def source_associations(cases):
    """Include ambiguous/withdrawn labels too: provenance is never a training verdict."""
    associations = {}
    for scenario in cases['scenarios']:
        for turn in scenario['turns']:
            text = turn.get('query', '').strip()
            if text:
                associations.setdefault(text, set()).add(scenario['id'])
    return {text: sorted(sources) for text, sources in associations.items()}


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
                    or isinstance(expected, list) or turn.get('expect_any') or turn.get('answers') or turn.get('action')):
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


def load(connection, examples, anchors, model, embed=embeddings.embed_documents, *, batch_size=32,
         dataset_version=None, authoritative=False, provenance=None):
    if not 1 <= batch_size <= 64:
        raise ValueError('Batch size must be 1..64')
    if authoritative and not dataset_version or dataset_version and not authoritative:
        raise ValueError('Authoritative replacement requires an explicit dataset version')
    examples = [dict(row, sources=sorted(set(row['sources']))) for row in examples]
    provenance = {text: set(sources) for text, sources in (provenance or {}).items()}
    for row in examples:
        provenance.setdefault(row['text'], set()).update(row['sources'])
    provenance = {text: sorted(sources) for text, sources in provenance.items()}
    fingerprint = hashlib.sha256(json.dumps(dict(
        examples=sorted(examples, key=lambda row: row['text']), provenance=provenance),
        sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    count = 0
    # Serializes loaders so concurrent runs cannot pay twice for the same text.
    with connection.transaction():
        connection.execute('SELECT pg_advisory_xact_lock(760009)')
        if authoritative:
            prior = connection.execute('SELECT fingerprint FROM series76.example_dataset WHERE model=%s AND version=%s',
                                       (model, dataset_version)).fetchone()
            if prior and prior['fingerprint'] != fingerprint:
                raise ValueError('Dataset version already identifies a different authoritative payload')
            connection.execute('''INSERT INTO series76.example_dataset(model,version,fingerprint)
                VALUES (%s,%s,%s) ON CONFLICT DO NOTHING''', (model, dataset_version, fingerprint))
            connection.execute('UPDATE series76.example_bank SET active=false WHERE model=%s', (model,))
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
        existing = {r['text']: r for r in connection.execute(
            'SELECT text,source,interpretation FROM series76.example_bank WHERE model=%s', (model,))}
        incoming = {row['text']: row for row in examples}
        for text, sources in provenance.items():
            if text not in existing:
                continue
            # Durable union: a subset reload cannot erase a held-out association.
            union = sorted(set(json.loads(existing[text]['source'])) | set(sources))
            connection.execute('UPDATE series76.example_bank SET source=%s WHERE text=%s AND model=%s',
                               (json.dumps(union), text, model))
            if text not in incoming:
                connection.execute('UPDATE series76.example_bank SET active=false WHERE text=%s AND model=%s', (text, model))
        for text, row in incoming.items():
            if authoritative:
                connection.execute('''UPDATE series76.example_bank SET interpretation=%s,active=true,dataset_version=%s
                    WHERE text=%s AND model=%s''', (Jsonb(row['interpretation']), dataset_version, text, model))
            elif existing[text]['interpretation'] != row['interpretation']:
                # Conflicting incremental labels must not silently overwrite a training decision.
                connection.execute('UPDATE series76.example_bank SET active=false WHERE text=%s AND model=%s', (text, model))
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=ROOT / 'config/agent_acceptance_cases_v7.json')
    parser.add_argument('--anchors', type=Path, default=ROOT / 'config/concept_anchors.json')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--usd-per-million-tokens', type=float, default=.20)
    parser.add_argument('--replace-dataset', action='store_true', help='Reconcile the complete authoritative dataset; deactivate omitted/ambiguous examples')
    parser.add_argument('--dataset-version', help='Immutable identifier required with --replace-dataset')
    args = parser.parse_args()
    if bool(args.dataset_version) != args.replace_dataset:
        parser.error('--replace-dataset and --dataset-version must be supplied together')
    cases = json.loads(args.cases.read_text(encoding='utf-8'))
    examples = examples_from_cases(cases)
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
                         lambda texts: embeddings.embed_documents(texts, timeout=30), batch_size=args.batch_size,
                         authoritative=args.replace_dataset, dataset_version=args.dataset_version,
                         provenance=source_associations(cases))
        except Exception as exc:
            # Never output provider exception payloads.
            print(json.dumps(dict(status='failed', error_type=type(exc).__name__)), file=sys.stderr)
            return 1
        print(json.dumps(dict(status='loaded', texts_embedded=count, estimated_usd=round(estimate, 6))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
