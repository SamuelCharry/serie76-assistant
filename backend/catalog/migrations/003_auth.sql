CREATE TABLE series76.users (
    id uuid PRIMARY KEY,
    email text NOT NULL UNIQUE CHECK (email = lower(email)),
    name text NOT NULL CHECK (length(name) BETWEEN 1 AND 80),
    password_hash text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE series76.auth_sessions (
    token_hash text PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES series76.users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL
);
CREATE INDEX auth_sessions_expiry ON series76.auth_sessions(expires_at);
CREATE INDEX auth_sessions_user ON series76.auth_sessions(user_id);
CREATE TABLE series76.auth_login_limits (
    scope_hash text PRIMARY KEY,
    window_start timestamptz NOT NULL DEFAULT clock_timestamp(),
    attempts integer NOT NULL
);
CREATE INDEX auth_limits_window ON series76.auth_login_limits(window_start);
-- NULL preserves pre-authentication history in quarantine; never auto-claim it.
ALTER TABLE series76.conversations ADD COLUMN owner_id uuid REFERENCES series76.users(id);
CREATE INDEX conversations_owner_recent ON series76.conversations(owner_id,updated_at DESC,id);
