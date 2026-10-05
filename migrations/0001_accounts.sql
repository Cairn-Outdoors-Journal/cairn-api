-- Accounts exist only for people who choose Cairn Cloud, shared trips or printing.
-- No journal content is ever stored in Postgres: see ARCHITECTURE.md in cairn-product-hub.

CREATE TABLE accounts (
    id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at timestamptz NOT NULL DEFAULT now()
);
