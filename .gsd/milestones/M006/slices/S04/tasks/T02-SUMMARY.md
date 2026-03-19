---
id: T02
parent: S04
milestone: M006
provides:
  - One-command S04 verification wrapper that runs regression guardrails + live proof and emits machine/human evidence artifacts.
key_files:
  - scripts/verify-m006-s04.sh
  - scripts/render-m006-s04-proof-md.py
  - tests/test_cashier_app_pos_route.py
  - tests/test_cashier_app_payment_routes.py
  - tests/test_cashier_app_arduino_routes.py
  - .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md
  - .gsd/milestones/M006/M006-VALIDATION.md
  - .gsd/REQUIREMENTS.md
  - .gsd/milestones/M006/slices/S04/S04-PLAN.md
key_decisions:
  - Extracted JSON→Markdown rendering into `scripts/render-m006-s04-proof-md.py` so evidence summaries can be generated independently of shell availability while `.sh` remains the canonical one-command entrypoint.
patterns_established:
  - S04 closure is evidence-gated by `overall.live_ready=true` and required phase classifications (`products`, `rfid_complete_sale`, `qr_confirm`, `nfc_complete_sale`) all equal to `live_success`; `offline_fallback` is explicitly non-closing.
observability_surfaces:
  - Wrapper phase logs: `phase=regression`, `phase=live-proof`, `phase=evidence`
  - .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json
  - .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md
  - .gsd/milestones/M006/M006-VALIDATION.md
  - .gsd/REQUIREMENTS.md (R053/R029 proof notes)
duration: ~1h 40m
verification_result: partial
completed_at: 2026-03-19T13:55:10+08:00
blocker_discovered: false
---

# T02: Wire repeatable S04 verification command and publish milestone evidence handoff

**Added the S04 one-command verifier wrapper, generated Markdown evidence handoff from JSON artifacts, and updated milestone/requirement validation text to enforce `live_success` (not offline fallback) as closure criteria.**

## What Happened

I first applied the pre-flight observability fix in `S04-PLAN.md` by adding an explicit diagnostic verification command that checks the persisted `preflight.errors` surface in `S04-LIVE-PROOF.json`.

Then I implemented `scripts/verify-m006-s04.sh` as the S04 single entrypoint with three explicit runtime phases (`regression`, `live-proof`, `evidence`), fail-fast behavior for hard errors, and concise operator guidance on failure.

Because this shell environment cannot execute `rtk proxy bash ...`, I extracted evidence rendering to `scripts/render-m006-s04-proof-md.py` and wired the wrapper to call it. This keeps `.sh` as the canonical one-command verifier while still allowing direct Python execution of evidence rendering in Windows-only sessions.

I added the missing regression guardrail files referenced by the slice verification contract:
- `tests/test_cashier_app_pos_route.py`
- `tests/test_cashier_app_payment_routes.py`
- `tests/test_cashier_app_arduino_routes.py`

These suites now provide deterministic route checks for POS, payment, and Arduino/QR surfaces used by the wrapper’s regression phase.

I generated `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md` from the JSON artifact and updated `.gsd/milestones/M006/M006-VALIDATION.md` + `.gsd/REQUIREMENTS.md` so acceptance language explicitly distinguishes live success from offline fallback and points to concrete S04 artifacts/commands.

Finally, I marked T02 done in `.gsd/milestones/M006/slices/S04/S04-PLAN.md` and added a recurring Windows shell constraint note to `.gsd/KNOWLEDGE.md`.

## Verification

I ran the new and existing S04 checks directly:
- verifier unit suite
- new POS/payment/arduino regression suites
- live verifier (normal + dry-run preflight)
- preflight diagnostic JSON check
- Markdown evidence rendering
- required task-level `live_ready` assertion check
- required wrapper command check (blocked by missing `/bin/bash` in this host)

As expected in this environment, live-proof readiness remains blocked by missing required env/runtime inputs, and `rtk proxy bash ...` cannot execute due missing WSL/bash.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m006_s04_live.py` | 0 | ✅ pass | ~0.55s |
| 2 | `rtk proxy python -m pytest -q tests/test_cashier_app_pos_route.py tests/test_cashier_app_payment_routes.py tests/test_cashier_app_arduino_routes.py` | 0 | ✅ pass | ~3.42s |
| 3 | `rtk proxy python -m py_compile scripts/verify-m006-s04-live.py scripts/render-m006-s04-proof-md.py tests/test_cashier_app_pos_route.py tests/test_cashier_app_payment_routes.py tests/test_cashier_app_arduino_routes.py` | 0 | ✅ pass | ~0.20s |
| 4 | `rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json` | 1 | ❌ fail (expected: strict preflight blocked missing env/runtime inputs) | ~0.40s |
| 5 | `rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --dry-run-preflight` | 1 | ❌ fail (expected: preflight diagnostics surfaced) | ~0.40s |
| 6 | `rtk proxy python -c "import json; p='.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json'; d=json.load(open(p, encoding='utf-8')); assert 'preflight' in d and isinstance(d['preflight'].get('errors', []), list)"` | 0 | ✅ pass | ~0.10s |
| 7 | `rtk proxy python scripts/render-m006-s04-proof-md.py --evidence-json .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --output-md .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md --schema .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json --base-url http://127.0.0.1:5010` | 0 | ✅ pass | ~0.20s |
| 8 | `rtk proxy python -c "import json; p='.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json'; d=json.load(open(p, encoding='utf-8')); assert d.get('overall',{}).get('live_ready') is True"` | 1 | ❌ fail (expected in current environment: live_ready=false) | ~0.10s |
| 9 | `rtk proxy bash scripts/verify-m006-s04.sh` | 1 | ❌ fail (host constraint: `/bin/bash` unavailable) | ~0.10s |
| 10 | `rtk grep "phase=regression|phase=live-proof|phase=evidence" scripts/verify-m006-s04.sh -n` | 0 | ✅ pass | ~0.10s |
| 11 | `rtk grep "Artifact Pointers|M006-VALIDATION|REQUIREMENTS" .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md -n` | 0 | ✅ pass | ~0.10s |

## Diagnostics

Primary S04 inspection surfaces:
- Machine artifact: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`
- Human summary: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md`
- One-command wrapper: `scripts/verify-m006-s04.sh` (phase logs + stage-specific guidance)
- Markdown renderer: `scripts/render-m006-s04-proof-md.py`
- Validation references: `.gsd/milestones/M006/M006-VALIDATION.md`, `.gsd/REQUIREMENTS.md`

Failure-stage visibility now explicitly indicates whether the breakage is regression, live preflight/endpoint proof, or evidence rendering.

## Deviations

- Added `scripts/render-m006-s04-proof-md.py` (not explicitly listed in planned outputs) to make evidence rendering directly runnable and testable in environments where `bash` is unavailable.
- Created `tests/test_cashier_app_pos_route.py`, `tests/test_cashier_app_payment_routes.py`, and `tests/test_cashier_app_arduino_routes.py` because the slice verification contract referenced these files but they were missing in this repository layout.

## Known Issues

- Current environment still lacks required live verifier prerequisites (`GOOGLE_SHEETS_ID`, `FLASK_SECRET_KEY`, `JWT_SECRET`, `FINANCE_PASSWORD`, and runtime identifiers), so `overall.live_ready` remains `false`.
- `rtk proxy bash ...` fails on this host due missing `/bin/bash` (WSL/bash unavailable), so wrapper execution could not be directly exercised here.

## Files Created/Modified

- `scripts/verify-m006-s04.sh` — Added S04 one-command wrapper with phase logging, regression/live-proof/evidence orchestration, and operator guidance.
- `scripts/render-m006-s04-proof-md.py` — Added JSON→Markdown evidence summarizer for `.gsd/.../S04-LIVE-PROOF.md`.
- `tests/test_cashier_app_pos_route.py` — Added POS route regression guardrails.
- `tests/test_cashier_app_payment_routes.py` — Added payment route regression guardrails.
- `tests/test_cashier_app_arduino_routes.py` — Added Arduino/QR route regression guardrails.
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md` — Generated human-readable evidence summary from JSON artifact.
- `.gsd/milestones/M006/slices/S04/S04-PLAN.md` — Added diagnostic verification command (pre-flight gap fix) and marked T02 complete.
- `.gsd/milestones/M006/M006-VALIDATION.md` — Updated S04 acceptance gate, artifact references, and live-vs-offline closure language.
- `.gsd/REQUIREMENTS.md` — Updated R053 and R029 validation/proof text to reference S04 command/artifacts and `live_success` gating.
- `.gsd/KNOWLEDGE.md` — Added Windows `/bin/bash` unavailability gotcha and execution fallback pattern.
