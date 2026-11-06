"""Explicit Google-only masked-bank experiment; bounded, resumable, no chat calls.

The supplied with_google.py wrapper injects credentials without displaying them.
Write a separate inactive model namespace; never modify the production namespace.
Each unique masked text is embedded once and reused as its leave-one-out query.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.conversation.retrieval_ranking import mask_values

MODEL = 'gemini-embedding-2'
TAG = 'gemini-embedding-2/masked-t9s2-v1'
URL = 'https://generativelanguage.googleapis.com/v1beta/openai/'
CACHE = ROOT / 'reports/behavior/masked-v1-cache.json'


def save(data):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    temporary = CACHE.with_suffix('.tmp')
    temporary.write_text(json.dumps(data), encoding='utf-8')
    temporary.replace(CACHE)


def embed_one(client, text):
    """Google compatibility returns one row; its zero index may be omitted."""
    from backend.conversation.embeddings import vector_literal
    response = client.embeddings.create(model=MODEL, input=text, dimensions=768, encoding_format='float')
    if not response.data or len(response.data) != 1 or response.data[0].index not in (None, 0):
        raise ValueError('Provider returned an incomplete single-text embedding')
    vector = response.data[0].embedding
    vector_literal(vector)
    return vector, getattr(response.usage, 'prompt_tokens', None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume-after-local-error', action='store_true',
                        help='Retain failed reservations; never exceed 800 submitted texts (about 749 authorized)')
    parser.add_argument('--probe-one', action='store_true', help='Checkpoint one missing text to verify the response format')
    options = parser.parse_args()
    from openai import OpenAI
    from psycopg.types.json import Jsonb
    from backend.catalog.cli import local_environment
    from backend.catalog.db import connect
    from backend.conversation.embeddings import vector_literal
    if os.getenv('OPENROUTER_EMBEDDING_MODEL') != MODEL or os.getenv('EMBEDDING_BASE_URL') != URL:
        raise ValueError('This experiment permits only the explicitly authorized Google endpoint/model')
    local_environment(ROOT / '.env')
    with connect() as connection:
        connection.execute('SET TRANSACTION READ ONLY')
        rows = list(connection.execute('''SELECT id,text,interpretation,source,dataset_version
            FROM series76.example_bank WHERE active AND model=%s ORDER BY id''', (MODEL,)))
    fingerprint = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    texts = list(dict.fromkeys(mask_values(r['text']) for r in rows))
    if not rows or len(texts) > 749 or sum(len(t) for t in texts) > 100_000:
        raise ValueError('Input exceeds the authorized bounded experiment')
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else dict(
        version=TAG, source_sha256=fingerprint, vectors={}, batches=[], prompt_tokens=0)
    if cache['source_sha256'] != fingerprint or cache['version'] != TAG:
        raise ValueError('Cached dataset is different; do not silently replace it')
    if any(b['state'] == 'reserved' for b in cache['batches']):
        if not options.resume_after_local_error:
            raise ValueError('An earlier request has unknown billing status; do not retry automatically')
        for batch in cache['batches']:
            if batch['state'] == 'reserved':
                batch['state'] = 'failed_unknown_charge'
        save(cache)
    missing = [t for t in texts if t not in cache['vectors']]
    if sum(b['texts'] for b in cache['batches']) + len(missing) > 800:
        raise ValueError('Retry would exceed the bounded experiment')
    # No provider client is needed on a completed-cache rerun.
    client = OpenAI(api_key=os.environ['GOOGLE_API_KEY'], base_url=URL, max_retries=0, timeout=60) if missing else None
    pending = missing[:1] if options.probe_one else missing
    # Small bounded concurrency, one text per HTTP request; never retry transport.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for start in range(0, len(pending), 4):
            batch = pending[start:start+4]
            entries = [dict(state='reserved', texts=1) for _ in batch]
            cache['batches'].extend(entries)
            save(cache)
            futures = [pool.submit(embed_one, client, text) for text in batch]
            try:
                for text, ledger, future in zip(batch, entries, futures):
                    vector, tokens = future.result()
                    cache['vectors'][text] = vector
                    ledger.update(state='completed', prompt_tokens=tokens)
                    cache['prompt_tokens'] += tokens or 0
            finally:
                save(cache)
            if start % 32 == 0:
                print(f"Stored {len(cache['vectors'])}/{len(texts)} masked vectors", flush=True)
    if options.probe_one:
        return
    with connect() as connection:
        previous = connection.execute('SELECT fingerprint FROM series76.example_dataset WHERE model=%s AND version=%s',
                                      (TAG, TAG)).fetchone()
        if previous and previous['fingerprint'] != fingerprint:
            raise ValueError('Model namespace already contains a different dataset')
        connection.execute('INSERT INTO series76.example_dataset(model,version,fingerprint) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',
                           (TAG, TAG, fingerprint))
        for row in rows:
            connection.execute('''INSERT INTO series76.example_bank
                (text,interpretation,source,model,dim,embedding,active,dataset_version)
                VALUES (%s,%s,%s,%s,768,%s::vector,false,%s) ON CONFLICT(text,model) DO NOTHING''',
                (row['text'], Jsonb(row['interpretation']), row['source'], TAG,
                 vector_literal(cache['vectors'][mask_values(row['text'])]), TAG))
    summary = dict(version=TAG, active=False, source_sha256=fingerprint, examples=len(rows),
                   unique_masked_texts=len(texts), requests=len(cache['batches']),
                   prompt_tokens=(cache['prompt_tokens'] if all(b.get('prompt_tokens') is not None
                                  for b in cache['batches']) else None),
                   provider='Google', openrouter_calls=0, chat_calls=0)
    summary.update(attempted_texts=sum(b['texts'] for b in cache['batches']),
                   usage_complete=all(b.get('prompt_tokens') is not None for b in cache['batches']),
                   completed_requests=sum(b['state'] == 'completed' for b in cache['batches']),
                   failed_reservations=[b for b in cache['batches'] if b['state'] != 'completed'])
    (ROOT / 'reports/behavior/masked-v1-manifest.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Masked embedding experiment stopped ({type(error).__name__}); details suppressed to protect credentials.', file=sys.stderr)
        print('Locations: ' + ', '.join(f'{Path(f.filename).name}:{f.lineno}' for f in traceback.extract_tb(error.__traceback__)), file=sys.stderr)
        raise SystemExit(1)
