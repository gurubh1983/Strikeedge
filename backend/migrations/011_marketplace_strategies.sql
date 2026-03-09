CREATE TABLE IF NOT EXISTS marketplace_strategies (
  id VARCHAR(36) PRIMARY KEY,
  strategy_id VARCHAR(36) NOT NULL,
  owner_id VARCHAR(128) NOT NULL,
  title VARCHAR(256) NOT NULL,
  description TEXT NOT NULL,
  tags JSON NOT NULL,
  share_code VARCHAR(36) NOT NULL UNIQUE,
  created_at TIMESTAMP NOT NULL
);
