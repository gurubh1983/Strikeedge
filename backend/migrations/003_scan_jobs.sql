CREATE TABLE IF NOT EXISTS scan_jobs (
  id VARCHAR(36) PRIMARY KEY,
  timeframe VARCHAR(8) NOT NULL,
  rules JSON NOT NULL,
  results JSON NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'completed',
  created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scan_jobs_status ON scan_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scan_jobs_created_at ON scan_jobs(created_at);
