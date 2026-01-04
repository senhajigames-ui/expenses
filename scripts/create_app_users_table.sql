-- Create app_users table for self-registration
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS app_users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username text UNIQUE NOT NULL,
    email text NOT NULL,
    name text NOT NULL,
    password_hash text NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);

-- Enable RLS
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;

-- Allow anyone to insert (register)
CREATE POLICY "Allow public registration" ON app_users
    FOR INSERT WITH CHECK (true);

-- Allow read for authentication (checking username)
CREATE POLICY "Allow public read for auth" ON app_users
    FOR SELECT USING (true);
