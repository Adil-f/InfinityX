ALTER TABLE organizations ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS organizations_stripe_customer_id_key
    ON organizations (stripe_customer_id)
    WHERE stripe_customer_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS organizations_stripe_subscription_id_key
    ON organizations (stripe_subscription_id)
    WHERE stripe_subscription_id IS NOT NULL;

INSERT INTO schema_migrations (version) VALUES ('003_billing_subscription');
