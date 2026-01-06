
-- Enable Row Level Security (RLS) on all tables

-- 1. Transactions Table
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only see their own transactions"
ON transactions
FOR ALL
USING (auth.uid()::text = user_id);

-- 2. Budgets Table
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only see their own budgets"
ON budgets
FOR ALL
USING (auth.uid()::text = user_id);

-- 3. Merchant Rules Table
ALTER TABLE merchant_rules ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only see their own rules"
ON merchant_rules
FOR ALL
USING (auth.uid()::text = user_id);

-- 4. Import History Table
ALTER TABLE import_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only see their own import history"
ON import_history
FOR ALL
USING (auth.uid()::text = user_id);

-- Verification (Optional)
-- You can verify by running:
-- SELECT COUNT(*) FROM transactions; (Should return your rows)
-- SELECT COUNT(*) FROM transactions WHERE user_id != auth.uid(); (Should return 0)
