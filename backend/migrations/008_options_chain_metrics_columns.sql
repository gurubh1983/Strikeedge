ALTER TABLE options_chain ADD COLUMN call_oi INTEGER;
ALTER TABLE options_chain ADD COLUMN call_iv FLOAT;
ALTER TABLE options_chain ADD COLUMN put_oi INTEGER;
ALTER TABLE options_chain ADD COLUMN put_iv FLOAT;
ALTER TABLE options_chain ADD COLUMN put_call_ratio FLOAT;
ALTER TABLE options_chain ADD COLUMN total_oi_change INTEGER;
