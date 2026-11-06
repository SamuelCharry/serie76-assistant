-- Additive T8 public snapshots and diagnostics; historical messages remain nullable.
ALTER TABLE series76.messages ADD COLUMN recommendation jsonb;
ALTER TABLE series76.messages ADD COLUMN debug jsonb;
ALTER TABLE series76.conversations ADD COLUMN deleted_at timestamptz;
