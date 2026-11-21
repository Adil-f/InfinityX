CREATE TABLE schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'free',
    credits_balance INTEGER NOT NULL DEFAULT 50,
    stripe_customer_id TEXT,
    retention_days INTEGER NOT NULL DEFAULT 365,
    is_fixture BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT organizations_plan_check CHECK (plan IN ('free', 'pro', 'enterprise')),
    CONSTRAINT organizations_retention_check CHECK (retention_days BETWEEN 7 AND 3650)
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret_encrypted TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    failed_logins INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    is_fixture BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT users_role_check CHECK (role IN ('owner', 'admin', 'investigator', 'analyst', 'viewer', 'billing')),
    CONSTRAINT users_status_check CHECK (status IN ('active', 'disabled', 'deleted'))
);

CREATE TABLE teams (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    is_fixture BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE team_members (
    team_id UUID NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    member_role TEXT NOT NULL DEFAULT 'member',
    PRIMARY KEY (team_id, user_id)
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    scopes TEXT NOT NULL,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    org_id UUID,
    user_id UUID,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    ip TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_org_created ON audit_logs (org_id, created_at DESC);

CREATE TABLE consent_records (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    purpose TEXT NOT NULL,
    lawful_basis TEXT NOT NULL,
    subject_type TEXT,
    text_version TEXT NOT NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at TIMESTAMPTZ
);

CREATE TABLE investigations (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    purpose TEXT NOT NULL,
    lawful_basis TEXT NOT NULL,
    classification TEXT NOT NULL DEFAULT 'internal',
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    retention_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT investigations_status_check CHECK (status IN ('open', 'closed', 'expired'))
);

CREATE TABLE search_jobs (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    investigation_id UUID REFERENCES investigations (id) ON DELETE SET NULL,
    user_id UUID REFERENCES users (id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    normalized_query TEXT NOT NULL,
    query_type TEXT NOT NULL,
    module TEXT NOT NULL,
    status TEXT NOT NULL,
    credit_cost INTEGER NOT NULL DEFAULT 0,
    external_attempted BOOLEAN NOT NULL DEFAULT FALSE,
    result_meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_search_jobs_org ON search_jobs (org_id, created_at DESC);

CREATE TABLE findings (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    investigation_id UUID REFERENCES investigations (id) ON DELETE CASCADE,
    search_job_id UUID REFERENCES search_jobs (id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    value TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT,
    collected_at TIMESTAMPTZ NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    verified BOOLEAN NOT NULL,
    kind TEXT NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_fixture BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT findings_kind_check CHECK (kind IN ('fact', 'reference')),
    CONSTRAINT findings_confidence_check CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT findings_not_fixture_check CHECK (is_fixture = FALSE)
);

CREATE INDEX idx_findings_investigation ON findings (investigation_id);
CREATE INDEX idx_findings_job ON findings (search_job_id);

CREATE TABLE graph_nodes (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    investigation_id UUID NOT NULL REFERENCES investigations (id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    label TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    source_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (investigation_id, entity_type, normalized_value)
);

CREATE TABLE graph_edges (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    investigation_id UUID NOT NULL REFERENCES investigations (id) ON DELETE CASCADE,
    from_node UUID NOT NULL REFERENCES graph_nodes (id) ON DELETE CASCADE,
    to_node UUID NOT NULL REFERENCES graph_nodes (id) ON DELETE CASCADE,
    relation TEXT NOT NULL,
    evidence_summary TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_url TEXT,
    confidence DOUBLE PRECISION NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (investigation_id, from_node, to_node, relation)
);

CREATE TABLE reports (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    investigation_id UUID NOT NULL REFERENCES investigations (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body_markdown TEXT NOT NULL,
    created_by UUID REFERENCES users (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE connector_state (
    id TEXT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_health TEXT,
    last_checked_at TIMESTAMPTZ,
    last_error TEXT
);

CREATE TABLE credit_ledger (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    delta INTEGER NOT NULL,
    reason TEXT NOT NULL,
    search_job_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations (version) VALUES ('001_init');
