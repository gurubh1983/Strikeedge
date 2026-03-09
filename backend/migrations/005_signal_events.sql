CREATE TABLE IF NOT EXISTS signal_events (
  id VARCHAR(36) PRIMARY KEY,
  token VARCHAR(64) NOT NULL,
  timeframe VARCHAR(8) NOT NULL,
  signal_type VARCHAR(64) NOT NULL,
  indicator VARCHAR(64) NOT NULL,
  message VARCHAR(256) NOT NULL,
  created_at TIMESTAMP NOT NULL
);
