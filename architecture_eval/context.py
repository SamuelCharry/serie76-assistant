"""Page-bound paragraph extraction and exact pgvector retrieval.

No reference/manual catalogue is read. Context is not numeric authority.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from psycopg.types.json import Jsonb
from model_eval.google import API_ROOT
from .provider import canonical


def extract_chunks(pdf):
    import pymupdf
    import tiktoken
    tokenizer = tiktoken.get_encoding("cl100k_base")
    chunks = []
    sha = hashlib.sha256(Path(pdf).read_bytes()).hexdigest()
    with pymupdf.open(pdf) as document:
        for page_no, page in enumerate(document, 1):
            section = "Series 76"
            for block in sorted(page.get_text("blocks"), key=lambda b: (b[1], b[0])):
                text = block[4].strip()
                if not text:
                    continue
                if len(text.split()) < 8 and not text.endswith("."):
                    section = text
                tokens = tokenizer.encode(text)
                for start in range(0, len(tokens), 260):
                    part = tokenizer.decode(tokens[start:start+300])
                    identity = hashlib.sha256(f"{sha}:{page_no}:{len(chunks)}:{part}".encode()).hexdigest()
                    chunks.append(dict(id=identity, document="series_76_summary.pdf", sha256=sha,
                                       page=page_no, section=section, text=part,
                                       token_count=len(tokenizer.encode(part))))
                    if start + 300 >= len(tokens):
                        break
    return chunks


class ContextStore:
    def __init__(self, connection, budget, key, folder):
        self.connection, self.budget, self.key = connection, budget, key
        self.folder = Path(folder)
        self.signature = None

    def embed(self, text, task):
        model = self.budget.config["embedding_model"]
        dimension = self.budget.config["embedding_dimensions"]
        identity = hashlib.sha256(canonical([model, dimension, task, text]).encode()).hexdigest()
        cache = self.folder / "embedding_cache" / (identity + ".json")
        if cache.exists():
            return json.loads(cache.read_text())["values"]
        result = self.budget.request(API_ROOT + f"models/{model}:embedContent", self.key, {
            "model": "models/" + model, "content": {"parts": [{"text": text}]},
            "taskType": task, "outputDimensionality": dimension})
        vector = result["embedding"]["values"]
        if len(vector) != dimension or not all(math.isfinite(x) for x in vector) or not any(vector):
            raise ValueError("Invalid embedding")
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(canonical(dict(values=vector)), encoding="utf-8")
        return vector

    def prepare(self, chunks):
        self.signature = hashlib.sha256(canonical([chunks, self.budget.config["embedding_model"],
                                                   self.budget.config["embedding_dimensions"], "paragraph-300-overlap40-v1"]).encode()).hexdigest()
        self.connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
        self.connection.execute("CREATE SCHEMA IF NOT EXISTS architecture_eval")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS architecture_eval.chunks (
          index_signature text NOT NULL, id text NOT NULL, metadata jsonb NOT NULL,
          embedding vector(768) NOT NULL, PRIMARY KEY(index_signature,id))""")
        self.connection.commit()
        for chunk in chunks:
            if self.connection.execute("SELECT 1 FROM architecture_eval.chunks WHERE index_signature=%s AND id=%s", (self.signature, chunk["id"])).fetchone():
                continue
            self.budget.label = dict(stage="document_embedding", chunk=chunk["id"])
            vector = self.embed(chunk["text"], "RETRIEVAL_DOCUMENT")
            self.connection.execute("INSERT INTO architecture_eval.chunks VALUES (%s,%s,%s,%s::vector)",
                                    (self.signature, chunk["id"], Jsonb(chunk), json.dumps(vector)))
            self.connection.commit()

    def search(self, query):
        vector = self.embed(query, "RETRIEVAL_QUERY")
        rows = self.connection.execute("""SELECT metadata, embedding <=> %s::vector AS distance
            FROM architecture_eval.chunks WHERE index_signature=%s
            ORDER BY embedding <=> %s::vector, id LIMIT %s""",
            (json.dumps(vector), self.signature, json.dumps(vector), self.budget.config["top_k"])).fetchall()
        return [dict(row["metadata"], distance=float(row["distance"])) for row in rows]
