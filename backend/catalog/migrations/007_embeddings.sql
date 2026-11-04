CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE series76.example_bank (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    text text NOT NULL,
    interpretation jsonb NOT NULL,
    source text NOT NULL,
    model text NOT NULL,
    dim int NOT NULL CHECK (dim = 768),
    embedding vector(768) NOT NULL,
    UNIQUE(text, model)
);

CREATE TABLE series76.concept_anchor (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    concept text NOT NULL,
    phrase text NOT NULL,
    model text NOT NULL,
    embedding vector(768) NOT NULL,
    UNIQUE(concept, phrase, model)
);
