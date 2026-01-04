-- ============================================
-- 🚨 DANGER: RESET DATABASE SCRIPT 🚨
-- This will DELETE ALL DATA from the application.
-- Run this in Supabase Dashboard → SQL Editor
-- ============================================

-- 1. Delete all transactions
TRUNCATE TABLE transactions;

-- 2. Delete all budgets
TRUNCATE TABLE budgets;

-- 3. Delete all import history
TRUNCATE TABLE import_history;

-- 4. Delete all merchant rules
TRUNCATE TABLE merchant_rules;

-- 5. Delete all registered users (optional, if you want a complete fresh start)
-- Note: This deletes users created via the "Register" tab.
TRUNCATE TABLE app_users;

-- Output confirmation
SELECT 'Database successfully reset. All data cleared.' as status;
