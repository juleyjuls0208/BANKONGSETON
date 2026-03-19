---
estimated_steps: 4
estimated_files: 4
---

# T02: Wire repeatable S04 verification command and publish milestone evidence handoff

**Slice:** S04 — Live Google Sheets runtime proof (non-mocked)
**Milestone:** M006

## Description

Package the S04 live proof into a single repeatable verification command, then publish machine + human-readable evidence so milestone validation and requirement status can be updated without ambiguity.

Relevant skills to load: `test`, `fullstack-developer`, `agent-browser` (optional for UI sanity checks).

## Steps

1. Create `scripts/verify-m006-s04.sh` that runs route-regression suites (`pos/payment/arduino`) plus the live verifier, failing on the first hard error and printing concise operator guidance.
2. Add evidence summarization to produce `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md` from the JSON artifact (required endpoints, live/degraded/failed breakdown, timestamped run metadata, and artifact pointers).
3. Update `.gsd/milestones/M006/M006-VALIDATION.md` to reference the S04 verifier command + artifact paths and define acceptance as all required flows `live_success` (not merely `success:true`).
4. Update `.gsd/REQUIREMENTS.md` validation notes for R053 (and any directly impacted active requirement evidence line) with the S04 proof command/output location once run data exists.

## Must-Haves

- [ ] One command executes both regression guardrails and live proof.
- [ ] Markdown evidence summary is generated from machine-readable output (no manual copy/paste).
- [ ] Validation docs explicitly distinguish live success from offline fallback.
- [ ] Requirement traceability text points to concrete S04 proof artifacts.

## Verification

- `rtk proxy bash scripts/verify-m006-s04.sh`
- `rtk proxy python -c "import json; p='.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json'; d=json.load(open(p, encoding='utf-8')); assert d.get('overall',{}).get('live_ready') is True"`

## Observability Impact

- Signals added/changed: verifier wrapper status phases (regression/live-proof/evidence) and documented artifact links in milestone validation.
- How a future agent inspects this: run `scripts/verify-m006-s04.sh`, then inspect `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.{json,md}` and M006 validation section.
- Failure state exposed: wrapper identifies whether failure came from regression, preflight, endpoint proof phase, or evidence generation.

## Inputs

- `.gsd/milestones/M006/slices/S04/tasks/T01-PLAN.md` — Verifier contract and artifact schema from T01.
- `tests/test_cashier_app_pos_route.py` — Existing standalone POS regression guardrail.
- `tests/test_cashier_app_payment_routes.py` — Existing standalone payment regression guardrail.
- `tests/test_cashier_app_arduino_routes.py` — Existing Arduino/QR regression guardrail.

## Expected Output

- `scripts/verify-m006-s04.sh` — Single-command S04 verification entrypoint.
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md` — Human-readable proof summary generated from JSON evidence.
- `.gsd/milestones/M006/M006-VALIDATION.md` — Updated closure criteria and artifact references for S04.
- `.gsd/REQUIREMENTS.md` — Updated active-requirement proof notes reflecting S04 runtime evidence.