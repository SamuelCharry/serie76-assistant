"""Glossary (business context) storage. Definitions only; never catalogue magnitudes.

A single glossary is active: loading a new summary version replaces it atomically.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

TERM_FIELDS = ("term_key", "label", "definition", "section", "group", "page", "ordinal", "aliases", "catalog_fields")


def _validated(payload, source_pdf):
    if payload.get("kind") != "business_context" or not payload.get("terms"):
        raise ValueError("terms.json is not a business-context glossary")
    sha = hashlib.sha256(Path(source_pdf).read_bytes()).hexdigest()
    if payload.get("document_sha256") != sha:
        raise ValueError("Glossary was not extracted from the supplied summary PDF")
    keys = set()
    for term in payload["terms"]:
        if set(term) != set(TERM_FIELDS):
            raise ValueError("Unexpected glossary term fields")
        if not re.fullmatch(r"[a-z0-9_]{2,40}", term["term_key"]) or term["term_key"] in keys:
            raise ValueError("Invalid or duplicate term key")
        if "�" in term["definition"] or not term["definition"].strip():
            raise ValueError("Invalid definition text")
        keys.add(term["term_key"])
    return sha


def load_context(connection, folder, source_pdf):
    payload = json.loads((Path(folder) / "terms.json").read_text(encoding="utf-8"))
    sha = _validated(payload, source_pdf)
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(760003)")
        current = list_terms(connection)
        wanted = [{k: t[k] for k in TERM_FIELDS} for t in payload["terms"]]
        if current and current[0]["document_sha256"] == sha and current[0]["extractor"] == payload["extractor"] \
                and [{k: t[k] for k in TERM_FIELDS} for t in current] == wanted:
            return dict(status="already_loaded", terms=len(current), document_sha256=sha)
        connection.execute(
            "INSERT INTO series76.documents(sha256,filename,kind) VALUES (%s,%s,'business_context') ON CONFLICT DO NOTHING",
            (sha, payload["document"]),
        )
        connection.execute("DELETE FROM series76.context_terms")
        for term in payload["terms"]:
            connection.execute(
                """INSERT INTO series76.context_terms
                (document_sha256,extractor,term_key,label,definition,section,term_group,page,ordinal,aliases,catalog_fields)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (sha, payload["extractor"], term["term_key"], term["label"], term["definition"], term["section"],
                 term["group"], term["page"], term["ordinal"], term["aliases"], term["catalog_fields"]),
            )
    return dict(status="loaded", terms=len(payload["terms"]), document_sha256=sha)


def list_terms(connection):
    return connection.execute(
        """SELECT t.term_key,t.label,t.definition,t.section,t.term_group AS "group",t.page,t.ordinal,
        t.aliases,t.catalog_fields,t.document_sha256,t.extractor,d.filename AS document
        FROM series76.context_terms t JOIN series76.documents d ON d.sha256=t.document_sha256
        ORDER BY t.ordinal""").fetchall()


def published_supplies(connection):
    """Supply combinations actually published in the active electrical catalogue."""
    return connection.execute(
        """SELECT DISTINCT e.supply_voltage_v,e.supply_current,e.phase_count
        FROM series76.entries e JOIN series76.catalog_state c ON c.active_import_id=e.import_id
        ORDER BY 1,2,3""").fetchall()
