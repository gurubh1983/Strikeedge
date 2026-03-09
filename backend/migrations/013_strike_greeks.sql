CREATE TABLE IF NOT EXISTS strike_greeks (
  id VARCHAR(36) PRIMARY KEY,
  underlying VARCHAR(64) NOT NULL,
  expiry VARCHAR(32) NOT NULL,
  symbol VARCHAR(128) NOT NULL,
  token VARCHAR(64) NOT NULL,
  option_type VARCHAR(8) NOT NULL,
  strike_price FLOAT NOT NULL,
  spot FLOAT NOT NULL,
  time_to_expiry_years FLOAT NOT NULL,
  risk_free_rate FLOAT NOT NULL,
  volatility FLOAT NOT NULL,
  delta FLOAT NOT NULL,
  gamma FLOAT NOT NULL,
  theta FLOAT NOT NULL,
  vega FLOAT NOT NULL,
  rho FLOAT NOT NULL,
  calculated_at TIMESTAMP NOT NULL
);
