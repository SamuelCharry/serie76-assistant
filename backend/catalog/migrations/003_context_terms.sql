-- Glossary from series_76_summary.pdf. Definitions only: no FK to entries, because a
-- general definition never certifies or quantifies a specific catalogue entry.
CREATE TABLE series76.context_terms (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_sha256 text NOT NULL REFERENCES series76.documents,
    extractor text NOT NULL,
    term_key text NOT NULL CHECK (term_key ~ '^[a-z0-9_]{2,40}$'),
    label text NOT NULL CHECK (length(label) BETWEEN 1 AND 120),
    definition text NOT NULL CHECK (length(definition) BETWEEN 1 AND 2000),
    section text,
    term_group text,
    page integer NOT NULL CHECK (page > 0),
    ordinal integer NOT NULL CHECK (ordinal > 0),
    aliases text[] NOT NULL DEFAULT '{}',
    catalog_fields text[] NOT NULL DEFAULT '{}',
    UNIQUE (document_sha256, term_key)
);
