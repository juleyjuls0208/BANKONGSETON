---
id: T01
parent: S04
milestone: M006
provides:
  - Deterministic S04 live-proof verifier with strict preflight gating, per-phase observability, offline-fallback classification, and redacted evidence output.
key_files:
  - scripts/verify-m006-s04-live.py
  - tests/test_verify_m006_s04_live.py
  - .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json
  - .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json
  - .env.example
  - .gsd/milestones/M006/slices/S04/S04-PLAN.md
key_decisions:
  - Added endpoint candidate probing (`/api/*` then `/cashier/api/*`) so runtime execution matches current app wiring while evidence stays aligned to canonical `/api/*` contracts.
patterns_established:
  - `offline=true` is always classified as `offline_fallback` and cannot satisfy live-proof gates.
  - Verifier emits machine-readable failure reasons for preflight/env/input gaps before any endpoint flow executes.
observability_surfaces:
  - .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json
  - per-phase fields: phase/endpoint/status_code/success/offline/latency_ms/error/classification
  - top-level overall.live_ready + diagnostics.queue_status
  - preflight error list for env/input/credential readiness
  - schema contract: .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json
duration: ~2h
verification_result: partial
completed_at: 2026-03-19T13:45:00+08:00
blocker_discovered: false
---

# T01: Build live-proof verifier with preflight gates and endpoint-flow evidence

**Added the S04 live-proof verifier, schema, and regression tests so live readiness is explicitly gated by strict preflight + non-offline endpoint outcomes in persisted redacted evidence.**

## What Happened

I first fixed the pre-task observability gap in `S04-PLAN.md` by adding a dedicated dry-run preflight verification command.

Then I implemented `scripts/verify-m006-s04-live.py` with: CLI args (`--base-url`, `--evidence`, `--schema`, timeout knobs, runtime inputs), strict preflight validation (required env vars + credentials file + required runtime identifiers), one-session authenticated flow execution (login, products, RFID completion, QR completion, NFC completion, queue status), and deterministic classification (`live_success` / `offline_fallback` / `failed`) with `live_ready` gating.

I added evidence contract validation and redaction logic, plus persisted schema at `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json`. Evidence now writes to `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json` with required per-phase observability fields and overall verdict metadata.

I also added `tests/test_verify_m006_s04_live.py` to assert preflight failure behavior, offline classification semantics, schema-required keys, and exit-code semantics (dry-run vs live readiness).

Finally, I updated `.env.example` with non-secret verifier knobs and marked T01 complete in `S04-PLAN.md`.

## Verification

Task-level verification was run directly:
- `rtk proxy python -m pytest -q tests/test_verify_m006_s04_live.py` (pass)
- `rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --dry-run-preflight` (expected fail in current environment due missing required env vars/runtime identifiers; confirms fail-fast preflight diagnostics)

Slice-level verification commands were also run (intermediate task; partial passes expected): new verifier tests passed, while remaining slice checks currently fail due missing prerequisite files/env/runtime in this workspace.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m006_s04_live.py` | 0 | ✅ pass | ~0.40s |
| 2 | `rtk proxy python -m py_compile scripts/verify-m006-s04-live.py tests/test_verify_m006_s04_live.py` | 0 | ✅ pass | ~0.20s |
| 3 | `rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --dry-run-preflight` | 1 | ❌ fail (expected: preflight blocked on missing env/inputs) | ~0.40s |
| 4 | `rtk proxy python -m pytest -q tests/test_cashier_app_pos_route.py tests/test_cashier_app_payment_routes.py tests/test_cashier_app_arduino_routes.py` | 4 | ❌ fail (files not present in current workspace) | ~0.10s |
| 5 | `rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json` | 1 | ❌ fail (expected: preflight blocked on missing env/inputs) | ~0.40s |
| 6 | `rtk proxy bash scripts/verify-m006-s04.sh` | 1 | ❌ fail (`/bin/bash` unavailable in this Windows shell; script not yet present) | ~0.10s |

## Diagnostics

Primary inspection artifact: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`.

It now exposes:
- `preflight` readiness state (`missing_env`, `missing_inputs`, `missing_files`, human-readable `errors`)
- `phases[*]` structured runtime evidence (`phase`, `endpoint`, `resolved_endpoint`, `status_code`, `success`, `offline`, `latency_ms`, `classification`, `error`)
- `overall.live_ready` + required-phase classification map
- `overall.schema_valid` and `overall.schema_errors`
- `diagnostics.queue_status` when runtime reaches queue inspection

Schema contract for tooling: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json`.

## Deviations

- Planned input paths referenced `backend/cashier_app/*` route modules that are not present in the current repository layout; implementation was aligned to active runtime routes in `backend/dashboard/cashier/cashier_routes.py` and `backend/dashboard/web_app.py`.
- To keep contract naming intact while executing real runtime flows, verifier endpoint calls use candidate probing (`/api/*` then `/cashier/api/*`) and persist canonical `/api/*` endpoint names in evidence.

## Known Issues

- Current environment is missing required live-proof prerequisites (`GOOGLE_SHEETS_ID`, `FLASK_SECRET_KEY`, `JWT_SECRET`, `FINANCE_PASSWORD`, and runtime flow identifiers), so preflight intentionally blocks live execution.
- Slice verification references route test files (`tests/test_cashier_app_*`) that do not currently exist in this workspace.
- `rtk proxy bash ...` fails in this shell due missing `/bin/bash` (Windows runtime constraint).

## Files Created/Modified

- `scripts/verify-m006-s04-live.py` — Added full live-proof verifier CLI with strict preflight, authenticated one-session flow runner, phase classification, redaction, schema validation, and evidence persistence.
- `tests/test_verify_m006_s04_live.py` — Added regression tests for preflight failure detection, offline classification, schema-required keys, and exit-code semantics.
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json` — Added evidence JSON schema contract used by verifier validation.
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json` — Generated verifier evidence artifact (current state: preflight-blocked with explicit diagnostics).
- `.env.example` — Added non-secret verifier configuration knobs (`VERIFY_S04_BASE_URL`, timeout settings, `VERIFY_S04_SALE_TOTAL`).
- `.gsd/milestones/M006/slices/S04/S04-PLAN.md` — Added missing dry-run-preflight verification step and marked T01 as done (`[x]`).
- `.gsd/DECISIONS.md` — Appended D067 documenting endpoint probing strategy for verifier runtime alignment.
- `.gsd/KNOWLEDGE.md` — Added Python 3.14/importlib dataclass-loading gotcha for future test module loading.
