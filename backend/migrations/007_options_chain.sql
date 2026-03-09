CREATE TABLE IF NOT EXISTS options_chain (
  id VARCHAR(36) PRIMARY KEY,
  underlying VARCHAR(64) NOT NULL,
  expiry VARCHAR(32) NOT NULL,
  strike_price FLOAT NOT NULL,
  call_token VARCHAR(64) NULL,
  call_symbol VARCHAR(128) NULL,
  put_token VARCHAR(64) NULL,
  put_symbol VARCHAR(128) NULL,
  lot_size INTEGER NOT NULL,
  fetched_at TIMESTAMP NOT NULL
);
