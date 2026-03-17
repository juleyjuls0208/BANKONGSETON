---
id: S05
parent: M002
milestone: M002
provides:
  - docs/DEPLOY.md — complete PythonAnywhere deployment runbook (11 sections, ~400 lines)
requires:
  - slice: S01
    provides: Final requirements files (env vars documented from what's actually needed)
  - slice: S03
    provides: Single-worker constraint and health check response shapes (documented as-implemented)
  - slice: S04
    provides: Test run instructions (runbook includes how to run the test suite before deploying)
affects: []
key_files:
  - docs/DEPLOY.md
key_decisions:
  - Wrote docs/DEPLOY.md from scratch rather than adapting existing DEPLOYMENT_PYTHONANYHERE.md or DEPLOYMENT_GUIDE.md (both had stale paths, wrong WSGI project_home depth, missing M002 startup guards)
  - Used corrected WSGI sys.path setup (project root → backend → backend/dashboard or backend/api) instead of the too-deep path in existing wsgi.py files
  - Structured as a numbered operator sequence rather than a reference document to make it followable end-to-end
patterns_established:
  - Deployment runbook structured as numbered operator sequence (Prerequisites → Clone → Credentials → Env Vars → Sheets Setup → WSGI → Startup Guards → Migration → Health Check → Constraints → Tests)
  - Startup guard quick-reference table maps env/condition → structured log event name (event=startup_aborted reason=*)
  - Health check failure-interpretation table maps /api/health JSON shapes to root causes
  - grep verification checks serve as machine-readable completeness probe for future agents
observability_surfaces:
  - docs/DEPLOY.md startup guard quick-reference table — maps 5 abort conditions to structured log event names; operators can correlate PythonAnywhere error log to exact startup failure cause
  - docs/DEPLOY.md health check failure-interpretation table — maps /api/health JSON shape variants to root causes and remediation steps
  - grep verification checks — `grep -q "PATTERN" docs/DEPLOY.md` commands serve as machine-readable completeness probes
drill_down_paths:
  - .gsd/milestones/M002/slices/S05/tasks/T01-SUMMARY.md
duration: 25m
verification_result: passed
completed_at: 2026-03-15
---

# S05: Deployment Runbook

**`docs/DEPLOY.md` created — a complete, operator-followable PythonAnywhere deployment runbook covering all 8 required topics: env vars, service account setup, WSGI config, first-run migration, health check sequence, single-worker constraint, E.164 phone format, and offline queue behavior.**

## What Happened

S05 had a single task (T01): write `docs/DEPLOY.md` from scratch using S05-RESEARCH.md as the authoritative source. No existing runbook was salvageable — `DEPLOYMENT_PYTHONANYHERE.md` and `DEPLOYMENT_GUIDE.md` both had stale paths, wrong WSGI `project_home` depth, and were written before M002's startup guards and health check standardization.

The document was written as a numbered operator sequence with 11 sections:

1. **Prerequisites** — Python 3.10+, git, PythonAnywhere account (free tier = one WSGI web app)
2. **Clone & Virtual Environment** — both requirements files, venv setup commands
3. **Credentials Files** — `config/credentials.json` (required, Sheets service account); `config/firebase-credentials.json` (optional, FCM silently disabled if absent)
4. **Environment Variables** — complete audit tables for Dashboard App (22 vars) and API App (10 vars) with required/optional/startup-hard-fail classification; JWT_SECRET match-required note
5. **Google Sheets Setup** — required-vs-auto-created worksheet table; ParentPhone column gap explicitly called out
6. **PythonAnywhere WSGI Configuration** — corrected templates for both apps with YOUR_USERNAME substitution; explains why existing wsgi.py path is wrong (one level too deep)
7. **Startup Guard Quick Reference** — table of 5 abort conditions with structured-log event names for operator diagnosis
8. **First-Run Migration** — `python backend/migrate_transactions.py`; what each of 3 functions does; post-migration verification checklist
9. **Health Check Sequence** — expected JSON shape; 4-row failure-interpretation table mapping JSON variants to root causes
10. **Known Operational Constraints** — 8 numbered constraints (single-worker, E.164, Balance col C, JWT_SECRET stability, offline queue auto-creation, same GOOGLE_SHEETS_ID both apps, firebase optional, ParentPhone required for SMS)
11. **Pre-Deploy Test Suite** — exact command with expected output; structural regression check commands

Pre-flight fixes to S05-PLAN.md and T01-PLAN.md (adding missing Observability sections) were applied before the main work.

## Verification

All slice-level verification checks passed:

```
FILE: OK
OK: FLASK_SECRET_KEY
OK: WEB_CONCURRENCY
OK: E.164
OK: migrate_transactions.py
OK: queue_pending
OK: offline_queue.db
OK: firebase-credentials.json
OK: YOUR_USERNAME
```

- `test -f docs/DEPLOY.md` → exit 0
- All 8 `grep -q` pattern checks → exit 0

## Requirements Advanced

- R019 — `docs/DEPLOY.md` created and complete; all 8 required topics documented; slice verification checks all pass

## Requirements Validated

- R019 — Deployment Runbook: `docs/DEPLOY.md` exists; all 8 grep verification patterns present; document covers PythonAnywhere setup, required env vars, Sheets service account config, first-run migration, health check sequence, and known operational constraints; R019 moves from active → validated

## New Requirements Surfaced

- None

## Requirements Invalidated or Re-scoped

- None

## Deviations

The Google Sheets required-vs-auto-created table (Step 4 of T01-PLAN.md) was placed as Section 5 (before WSGI config) rather than after it. This reads more naturally — operators need to set up Sheets before configuring the apps. No functionality impact.

## Known Limitations

- `docs/DEPLOY.md` documents the as-built system state as of M002 completion. If S03/S04 implementation details change post-M002 (health check JSON shape, test file names, startup guard env var names), the runbook will need updating.
- The WSGI config templates include `YOUR_USERNAME` substitution instructions but do not auto-validate the username. An operator who forgets to replace `YOUR_USERNAME` will get a clear Python ImportError on first web request rather than a silent failure.
- PythonAnywhere free tier limitation (one WSGI web app) means running both Dashboard and API on the same account requires Waitress/gunicorn via `pa_autoconfigure_django` workaround — this is noted in Prerequisites but not fully scripted.

## Follow-ups

- None required for M002 completion. Post-M002: keep `docs/DEPLOY.md` in sync with any env var additions or WSGI path changes.

## Files Created/Modified

- `docs/DEPLOY.md` — created; complete PythonAnywhere deployment runbook (11 sections, ~400 lines)
- `.gsd/milestones/M002/slices/S05/S05-PLAN.md` — added `## Observability / Diagnostics` section (pre-flight fix)
- `.gsd/milestones/M002/slices/S05/tasks/T01-PLAN.md` — added `## Observability Impact` section (pre-flight fix)

## Forward Intelligence

### What the next slice should know
- M002 is now complete. All 5 slices done. The milestone definition of done is fully met.
- `docs/DEPLOY.md` is the canonical deployment reference going forward. Any new env vars, startup guards, or operational constraints added in future milestones should be reflected here.

### What's fragile
- WSGI corrected path templates — The existing `backend/api/wsgi.py` and `backend/dashboard/wsgi.py` still contain the wrong `project_home` depth. The runbook documents the corrected path but the wsgi.py files are not fixed. If an operator copies from wsgi.py rather than the runbook, they'll hit an ImportError.
- `ParentPhone` column gap — the Users worksheet requires a `ParentPhone` column for SMS to work; if the column is absent or mis-cased, SMS silently fails. Documented in constraints but not enforced at startup.

### Authoritative diagnostics
- `grep -q "PATTERN" docs/DEPLOY.md` — the 8 grep checks in the Verification section are the canonical completeness probe for this document
- `/api/health` JSON — the health check failure-interpretation table in Section 9 maps every known bad-state JSON shape to a root cause; this is the first diagnostic surface after deploy

### What assumptions changed
- None — S05 was pure documentation synthesis from prior slices. All assumptions about what was implemented (startup guards, health JSON shape, test file names) were confirmed by reading the actual code in S03/S04 artifacts.
