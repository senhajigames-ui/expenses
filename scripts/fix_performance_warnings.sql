
-- Fix Performance Warnings from Supabase Linter

-- 1. Fix "Auth RLS Initialization Plan" (auth_rls_initplan)
-- Wrapping auth.uid() in (select ...) prevents re-evaluation for every row.

-- Transactions
DROP POLICY IF EXISTS "Users can only see their own transactions" ON public.transactions;
CREATE POLICY "Users can only see their own transactions"
ON public.transactions
FOR ALL
USING ((select auth.uid()::text) = user_id);

-- Budgets
DROP POLICY IF EXISTS "Users can only see their own budgets" ON public.budgets;
CREATE POLICY "Users can only see their own budgets"
ON public.budgets
FOR ALL
USING ((select auth.uid()::text) = user_id);

-- Merchant Rules
DROP POLICY IF EXISTS "Users can only see their own rules" ON public.merchant_rules;
CREATE POLICY "Users can only see their own rules"
ON public.merchant_rules
FOR ALL
USING ((select auth.uid()::text) = user_id);

-- Import History
DROP POLICY IF EXISTS "Users can only see their own import history" ON public.import_history;
CREATE POLICY "Users can only see their own import history"
ON public.import_history
FOR ALL
USING ((select auth.uid()::text) = user_id);


-- 2. Fix "Duplicate Index" (duplicate_index)
-- We have overlapping unique constraints/indexes. We'll drop the redundant ones.
-- Keeping the named constraints 'unique_user_category' and 'unique_user_merchant_pattern' 
-- and dropping the potential auto-generated keys.

-- Budgets: Drop redundant uniqueness constraint/index if it exists
ALTER TABLE public.budgets DROP CONSTRAINT IF EXISTS budgets_user_id_category_key;
DROP INDEX IF EXISTS budgets_user_id_category_key;

-- Merchant Rules: Drop redundant uniqueness constraint/index if it exists
ALTER TABLE public.merchant_rules DROP CONSTRAINT IF EXISTS merchant_rules_user_id_merchant_pattern_key;
DROP INDEX IF EXISTS merchant_rules_user_id_merchant_pattern_key;
