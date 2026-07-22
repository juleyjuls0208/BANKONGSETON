-- ===========================================================================
-- BANKONGSETON — Close the RLS gap on public.student_auth
-- ---------------------------------------------------------------------------
-- Supabase security alert (2026-07-22): public.student_auth had RLS disabled
-- and was reachable via the public PostgREST surface (anon/authenticated keys).
--
-- Why it slipped through: the original 20260707000000_enable_rls.sql migration
-- scans information_schema at the moment it runs. student_auth was added to the
-- backend's _TABLES registry AFTER that migration executed, so the one-shot
-- scan never saw it. Because the Flask backend creates tables lazily with
-- `CREATE TABLE IF NOT EXISTS` on every startup, student_auth was created
-- fresh — without RLS.
--
-- Two fixes applied:
--   1. (this file) Clear the live alert now by enabling RLS + a server-role
--      allow policy on student_auth. Idempotent / safe to re-run.
--   2. (root cause) backend/sheets_adapter.py :: _supabase_init() now enables
--      RLS + the allow policy on EVERY table in _TABLES at creation time, so
--      no future table can ship with RLS off.
--
-- Safety: the backend connects as the postgres superuser, which BYPASSES RLS,
-- so enabling RLS here does not affect the Flask REST API. No client talks to
-- PostgREST directly. Allow policy is server-role-only (no Supabase Auth, so
-- per-row auth.uid() policies are not applicable).
-- ===========================================================================

ALTER TABLE public.student_auth ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS allow_service_role_student_auth ON public.student_auth;
CREATE POLICY allow_service_role_student_auth ON public.student_auth
    FOR ALL TO postgres, service_role
    USING (true) WITH CHECK (true);
