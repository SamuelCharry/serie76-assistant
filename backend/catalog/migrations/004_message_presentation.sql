ALTER TABLE series76.messages
    ADD COLUMN suggested_replies jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN comparison jsonb;
