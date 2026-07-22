-- ===========================================================================
-- BANKONGSETON — Enable Row Level Security (RLS) on all public tables
-- ---------------------------------------------------------------------------
-- Supabase security alert: the following tables were public with RLS disabled,
-- meaning the Supabase *public anon/authenticated* keys had unrestricted
-- read/write access to sensitive student/financial data:
--
--     public.transactions_log   public.virtual_cards     public.scheduler_log
--     public.money_accounts     public.cashier_accounts  public.users
--     public.lost_card_reports  public.student_budgets   public.products
--     public.settings
--
-- Architecture note (why this is safe to apply):
--   * The Flask backend connects to Postgres via psycopg2 as the `postgres`
--     SUPERUSER role, which BYPASSES RLS entirely — enabling RLS here does
--     NOT affect the backend's own queries.
--   * No client (iOS / Android / web dashboard) talks to Supabase through the
--     public anon/authenticated keys. They reach the database only through the
--     Flask REST API over HTTPS. So once RLS is on, the only roles that can
--     read/write these tables via the PostgREST surface are the trusted
--     server roles (postgres / service_role), which the backend already uses.
--   * There is no Supabase Auth integration, so per-row (auth.uid()) policies
--     are not applicable; a server-role-only allow policy is the correct,
--     minimal protection.
--
-- Result: anonymous/public API access to every table is denied (alert cleared
-- + real protection), and the application keeps working unchanged.
--
-- Idempotent: safe to re-run. `ENABLE ROW LEVEL SECURITY` is a no-op if already
-- enabled, and the policy is dropped before being recreated.
--
-- How to apply:
--   * Easiest: paste this file into the Supabase Dashboard → SQL Editor → Run.
--   * Or, with the Supabase CLI installed: `supabase db push`.
--   * Or: do nothing — the Flask backend runs the equivalent automatically at
--     startup (see backend/sheets_adapter.py :: _enable_rls_for_all_tables()).
-- ===========================================================================

-- Helper: a DO block that enables RLS on every base table in the public
-- schema and grants full access to the trusted server roles only.
-- Scanning information_schema (instead of hardcoding the 10 names) also covers
-- any ad-hoc tables the app creates at runtime (e.g. scheduler_log,
-- cashier_accounts, student_budgets) and any table added later.
DO $$
DECLARE
    t text;
    pol text;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
    LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);

        pol := 'allow_service_role_' || t;
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', pol, t);
        EXECUTE format(
            'CREATE POLICY %I ON public.%I '
            'FOR ALL TO postgres, service_role '
            'USING (true) WITH CHECK (true)',
            pol, t
        );
    END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- Explicit, named coverage of the 10 tables flagged by the Supabase alert.
-- The DO block above already handles these (it scans information_schema and
-- covers any future table), so this duplicate manifest is intentionally
-- omitted to avoid drift — the 10 names are documented here for auditability:
--   transactions_log, virtual_cards, scheduler_log, money_accounts,
--   cashier_accounts, users, lost_card_reports, student_budgets, products,
--   settings.
-- ---------------------------------------------------------------------------
