CREATE TABLE IF NOT EXISTS notification_preferences (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,
  channel VARCHAR(32) NOT NULL,
  destination VARCHAR(256) NOT NULL,
  enabled INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS notification_outbox (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,
  channel VARCHAR(32) NOT NULL,
  destination VARCHAR(256) NOT NULL,
  subject VARCHAR(256) NOT NULL,
  body TEXT NOT NULL,
  status VARCHAR(32) NOT NULL,
  error_message TEXT NULL,
  created_at TIMESTAMP NOT NULL,
  sent_at TIMESTAMP NULL
);
