-- Additive snapshots; historical rows remain readable without fabrication.
ALTER TABLE series76.messages ADD COLUMN lead text;
ALTER TABLE series76.messages ADD COLUMN interaction jsonb;
ALTER TABLE series76.messages ADD COLUMN active_filters jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE series76.messages ADD COLUMN suggestions jsonb NOT NULL DEFAULT '[]'::jsonb;
-- comparison is already JSONB (004); new snapshots carry layout/summary/hidden_rows.
