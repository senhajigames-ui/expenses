-- Database Optimization Script
-- Improves performance (Indexes) and data integrity (Unique Constraints)

-- 1. Performance Indexes (Speed up queries)
-- Use IF NOT EXISTS to avoid errors if re-running

CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_desc ON transactions USING btree(description); -- Prefix search optimization

CREATE INDEX IF NOT EXISTS idx_budgets_user_id ON budgets(user_id);
CREATE INDEX IF NOT EXISTS idx_merchant_rules_user_id ON merchant_rules(user_id);
CREATE INDEX IF NOT EXISTS idx_import_history_user_id ON import_history(user_id);

-- 2. Unique Constraints (Required for "Upsert" logic to work correctly)
-- These prevent duplicate budgets or rules for the same user.
-- NOTE: If you already have duplicates, these commands might fail. You would need to clean duplicates first.

-- Budgets: One budget per category per user
ALTER TABLE budgets 
ADD CONSTRAINT unique_user_category UNIQUE (user_id, category);

-- Merchant Rules: One rule per merchant pattern per user
ALTER TABLE merchant_rules 
ADD CONSTRAINT unique_user_merchant_pattern UNIQUE (user_id, merchant_pattern);

-- Import History: Prevent importing exact same file hash twice
ALTER TABLE import_history 
ADD CONSTRAINT unique_import_hash UNIQUE (user_id, file_hash);
