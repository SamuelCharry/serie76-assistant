CREATE TABLE series76.conversations (
    id uuid PRIMARY KEY,
    title text NOT NULL CHECK (length(title) BETWEEN 1 AND 100),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX conversations_recent ON series76.conversations(updated_at DESC, id);

CREATE TABLE series76.messages (
    sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id uuid NOT NULL UNIQUE,
    session_id uuid NOT NULL REFERENCES series76.conversations(id),
    role text NOT NULL CHECK (role IN ('user', 'assistant')),
    content text NOT NULL,
    products jsonb NOT NULL DEFAULT '[]'::jsonb,
    tool_calls jsonb NOT NULL DEFAULT '[]'::jsonb,
    context jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX messages_session_sequence ON series76.messages(session_id, sequence);
