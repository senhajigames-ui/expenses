
-- Fix warnings reported by Supabase linter

-- 1. Fix "Function Search Path Mutable"
-- Set a fixed search_path for the update_updated_at_column function to prevent hijacking.
ALTER FUNCTION public.update_updated_at_column() SET search_path = public;


-- 2. Fix "RLS Policy Always True" for app_users
-- The previous policy "Allow public registration" allowed anyone to insert anything into app_users.
-- We will replace this with a SECURITY DEFINER function (RPC) that handles registration securely.

-- A. Revoke direct INSERT access to anon/authenticated on app_users
REVOKE INSERT ON TABLE public.app_users FROM anon, authenticated;

-- B. Drop the lax policy if it exists (or we can just leave it since permissions are revoked, but cleaner to drop)
DROP POLICY IF EXISTS "Allow public registration" ON public.app_users;

-- C. Create a secure registration function
-- SECURITY DEFINER means it runs with the privileges of the creator (postgres/admin),
-- bypassing RLS and table permissions for the user calling it.
CREATE OR REPLACE FUNCTION public.register_user(
    username text,
    email text,
    name text,
    password_hash text
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Basic validation (optional but good)
    IF username IS NULL OR length(username) < 3 THEN
        RAISE EXCEPTION 'Invalid username';
    END IF;

    -- Insert the user
    INSERT INTO public.app_users (username, email, name, password_hash)
    VALUES (username, email, name, password_hash);

    RETURN true;
EXCEPTION
    WHEN unique_violation THEN
        RETURN false; -- Duplicate username
    WHEN OTHERS THEN
        RETURN false;
END;
$$;

-- D. Grant Execute permission to everyone (since it's for public registration)
GRANT EXECUTE ON FUNCTION public.register_user(text, text, text, text) TO anon, authenticated;

-- E. Ensure Select policy still exists for login checks (from previous script)
-- "Allow public read of users" should still be there. If not:
-- CREATE POLICY "Allow public read of users" ON app_users FOR SELECT TO anon, authenticated USING (true);
