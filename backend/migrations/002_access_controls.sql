ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_pending_secret_encrypted TEXT;

CREATE TABLE IF NOT EXISTS org_connector_state (
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    connector_id TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_health TEXT,
    last_checked_at TIMESTAMPTZ,
    last_error TEXT,
    PRIMARY KEY (org_id, connector_id)
);

INSERT INTO schema_migrations (version) VALUES ('002_access_controls');
