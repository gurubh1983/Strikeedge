CREATE TABLE IF NOT EXISTS screeners (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,
  name VARCHAR(256) NOT NULL,
  description TEXT NULL,
  timeframe VARCHAR(8) NOT NULL,
  conditions JSON NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_results (
  id VARCHAR(36) PRIMARY KEY,
  scan_id VARCHAR(36) NOT NULL,
  token VARCHAR(64) NOT NULL,
  matched INTEGER NOT NULL,
  reason VARCHAR(256) NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_jobs (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,
  job_type VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL,
  request_payload JSON NOT NULL,
  output_payload JSON NULL,
  error_message TEXT NULL,
  created_at TIMESTAMP NOT NULL
);
