CREATE TABLE IF NOT EXISTS idempotency_records (
  id VARCHAR(36) PRIMARY KEY,
  actor_id VARCHAR(128) NOT NULL,
  idempotency_key VARCHAR(256) NOT NULL,
  endpoint VARCHAR(256) NOT NULL,
  response_payload JSON NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_idem_actor_key_endpoint
  ON idempotency_records(actor_id, idempotency_key, endpoint);
