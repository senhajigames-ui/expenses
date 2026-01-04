-- ============================================
-- Row Level Security (RLS) Setup for Expense Tracker
-- Run this in Supabase Dashboard → SQL Editor
-- ============================================

-- Enable RLS on all tables
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE merchant_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE import_history ENABLE ROW LEVEL SECURITY;

-- Create policies for transactions table
CREATE POLICY "anon_transactions_all" ON transactions 
    FOR ALL USING (true);

-- Create policies for budgets table  
CREATE POLICY "anon_budgets_all" ON budgets 
    FOR ALL USING (true);

-- Create policies for merchant_rules table
CREATE POLICY "anon_merchant_rules_all" ON merchant_rules 
    FOR ALL USING (true);

-- Create policies for import_history table
CREATE POLICY "anon_import_history_all" ON import_history 
    FOR ALL USING (true);

-- Verify RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('transactions', 'budgets', 'merchant_rules', 'import_history');
