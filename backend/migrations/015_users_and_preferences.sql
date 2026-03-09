CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(36) PRIMARY KEY,
  clerk_user_id VARCHAR(128) NOT NULL UNIQUE,
  email VARCHAR(256),
  display_name VARCHAR(128),
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS user_preferences (
  id VARCHAR(36) PRIMARY KEY,
  clerk_user_id VARCHAR(128) NOT NULL UNIQUE,
  default_timeframe VARCHAR(16) NOT NULL DEFAULT '5m',
  default_indicator VARCHAR(32) NOT NULL DEFAULT 'rsi_14',
  theme VARCHAR(16) NOT NULL DEFAULT 'dark',
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
