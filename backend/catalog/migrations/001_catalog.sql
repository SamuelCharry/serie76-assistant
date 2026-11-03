CREATE TABLE series76.documents (
    sha256 text PRIMARY KEY CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    filename text NOT NULL,
    kind text NOT NULL CHECK (kind IN ('electrical', 'business_context'))
);
CREATE TABLE series76.imports (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_sha256 text NOT NULL REFERENCES series76.documents,
    pipeline_signature text NOT NULL CHECK (pipeline_signature ~ '^[0-9a-f]{64}$'),
    artifact_fingerprint text NOT NULL,
    artifact_hashes jsonb NOT NULL,
    manifest jsonb NOT NULL,
    imported_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_sha256, pipeline_signature)
);
CREATE TABLE series76.catalog_state (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    active_import_id bigint NOT NULL REFERENCES series76.imports
);
CREATE TABLE series76.source_tables (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    import_id bigint NOT NULL REFERENCES series76.imports,
    source_table text NOT NULL,
    source_page integer NOT NULL CHECK (source_page > 0),
    title text NOT NULL,
    layout text NOT NULL CHECK (layout IN ('mixed', 'shared', 'on_off', 'modulating')),
    header jsonb NOT NULL,
    page_metadata jsonb NOT NULL,
    notes jsonb NOT NULL,
    shared_services_confirmed boolean NOT NULL DEFAULT false,
    UNIQUE (import_id, source_table),
    UNIQUE (id, import_id)
);
CREATE TABLE series76.entries (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    import_id bigint NOT NULL REFERENCES series76.imports,
    table_id bigint NOT NULL,
    source_row integer NOT NULL CHECK (source_row > 0),
    base_part_number text NOT NULL CHECK (base_part_number ~ '^[A-Z0-9]{6}-[A-Z0-9]{8}/A$'),
    source_part_number text NOT NULL,
    enclosure text NOT NULL CHECK (enclosure IN ('weatherproof', 'explosionproof')),
    supply_voltage_v numeric NOT NULL CHECK (supply_voltage_v > 0),
    supply_current text NOT NULL CHECK (supply_current IN ('AC', 'DC', 'AC/DC')),
    phase_count integer CHECK (phase_count IN (1, 3)),
    data_status text NOT NULL CHECK (data_status IN ('reported', 'source_NA')),
    motor_power_w numeric CHECK (motor_power_w >= 0),
    field_status jsonb NOT NULL,
    certification_header_raw text NOT NULL,
    source_footnote text,
    csa_status text NOT NULL CHECK (csa_status IN ('reported_in_header', 'explicitly_not_CSA_certified', 'not_reported')),
    UNIQUE (table_id, source_row),
    FOREIGN KEY (table_id, import_id) REFERENCES series76.source_tables (id, import_id),
    CHECK ((field_status->>'motor_power_w' = 'reported') = (motor_power_w IS NOT NULL))
);
CREATE INDEX entries_import_code ON series76.entries (import_id, base_part_number);
CREATE INDEX entries_supply ON series76.entries (import_id, supply_voltage_v, enclosure, supply_current);
CREATE TABLE series76.service_specs (
    entry_id bigint NOT NULL REFERENCES series76.entries,
    service text NOT NULL CHECK (service IN ('on_off', 'modulating', 'shared')),
    torque_in_lb numeric CHECK (torque_in_lb >= 0),
    torque_nm numeric CHECK (torque_nm >= 0),
    duty_s4_percent numeric CHECK (duty_s4_percent BETWEEN 0 AND 100),
    cycles_per_hour integer CHECK (cycles_per_hour >= 0),
    starts_per_hour integer CHECK (starts_per_hour >= 0),
    PRIMARY KEY (entry_id, service),
    CHECK (service = 'on_off' OR cycles_per_hour IS NULL),
    CHECK (service = 'modulating' OR starts_per_hour IS NULL)
);
CREATE INDEX service_torque ON series76.service_specs (service, torque_nm, entry_id);
CREATE TABLE series76.frequency_specs (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entry_id bigint NOT NULL REFERENCES series76.entries,
    frequency_hz integer CHECK (frequency_hz IN (50, 60)),
    frequency_scope text NOT NULL CHECK (frequency_scope IN ('specified', 'not_specified', 'not_applicable')),
    operating_time_s numeric CHECK (operating_time_s >= 0),
    fla_a numeric CHECK (fla_a >= 0),
    lra_a numeric CHECK (lra_a >= 0),
    UNIQUE NULLS NOT DISTINCT (entry_id, frequency_hz),
    CHECK ((frequency_scope = 'specified') = (frequency_hz IS NOT NULL))
);
CREATE TABLE series76.source_cells (
    entry_id bigint NOT NULL REFERENCES series76.entries,
    field text NOT NULL,
    status text NOT NULL CHECK (status IN ('reported', 'source_NA')),
    unit text,
    evidence jsonb NOT NULL,
    PRIMARY KEY (entry_id, field)
);
