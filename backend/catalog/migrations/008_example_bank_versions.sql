-- Retain vectors and durable provenance when an authoritative dataset withdraws a row.
ALTER TABLE series76.example_bank ADD COLUMN active boolean NOT NULL DEFAULT true;
ALTER TABLE series76.example_bank ADD COLUMN dataset_version text;

CREATE TABLE series76.example_dataset (
    model text NOT NULL,
    version text NOT NULL,
    fingerprint text NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (model, version)
);
