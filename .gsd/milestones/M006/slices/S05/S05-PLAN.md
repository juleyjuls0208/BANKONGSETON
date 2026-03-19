# S05: Physical hardware UAT + evidence bundle

**Goal:** Retire the final standalone cashier closure gap by proving real hardware-assisted payment behavior on port `5010` (with admin dashboard process OFF) and producing an auditable evidence bundle.
**Demo:** Operator runs cashier runtime on `localhost:5010`, performs Arduino heartbeat + RFID card-read, student QR confirm, and NFC-compatible completion paths with real devices/accounts, then generates `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.{json,md}` linking screenshots/video/request traces and S04 live-proof artifacts.

## Must-Haves

- Directly advance active **R053** closure with physical UAT evidence, not contract-only assertions.
- Support active **R027** evidence by capturing OLED QR display proof during the real student QR confirmation flow.
- Execute required runtime flows on port `5010` while admin dashboard process is not used: Arduino heartbeat online, Arduino card-read sale completion, student QR confirmation, and NFC-compatible sale completion endpoint.
- Treat current runtime topology as authoritative (`backend/dashboard/web_app.py` + `/cashier/api/*` fallback), while preserving canonical `/api/*` contract names in persisted evidence.
- Persist a durable S05 evidence bundle with machine-readable verdicts, operator artifact manifest, and timestamped request-path traces.
- Enforce D066 closure semantics: any required flow classified as `offline_fallback` or failed keeps S05 open.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m006_s05_bundle.py`
- `rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`
- `rtk proxy python scripts/verify-m006-s05-bundle.py --base-url http://127.0.0.1:5010 --s04-evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --manifest .gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json --output .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json --markdown .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md`
- `rtk proxy python -c "import json; p='.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json'; d=json.load(open(p, encoding='utf-8')); assert d['overall']['live_ready'] is True; req=d['required_flows']; assert all(v.get('classification')=='live_success' for v in req.values()); assert all(':5003' not in hit.get('url','') for hit in d.get('request_trace', []))"`
- Operator check from `.gsd/milestones/M006/slices/S05/S05-UAT.md`: screenshots/video artifacts exist and timestamps match verifier phases.

## Observability / Diagnostics

- Runtime signals: Arduino heartbeat freshness/status, `card_read` / `qr_payment` / sale completion path outcomes, and per-flow classifier states (`live_success`, `offline_fallback`, `failed`).
- Inspection surfaces: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`, `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json`, `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.{json,md}`, and captured request-trace logs.
- Failure visibility: bundle records failing phase, resolved endpoint, HTTP status, offline/degraded reason, and missing-artifact diagnostics.
- Redaction constraints: never persist raw JWTs, API keys, full card UIDs, or unredacted student identifiers in evidence artifacts.

## Integration Closure

- Upstream surfaces consumed: `scripts/verify-m006-s04-live.py`, `scripts/verify-m006-s04.sh`, `backend/dashboard/web_app.py`, `backend/dashboard/cashier/cashier_routes.py`, and S04 evidence contract (`S04-LIVE-PROOF.schema.json`).
- New wiring introduced in this slice: S05 bundle verifier + schema, operator UAT checklist/manifest, and milestone validation/requirements references to S05 artifacts.
- What remains before the milestone is truly usable end-to-end: nothing if S05 bundle reports `live_ready=true` and all required flows are `live_success`.

## Tasks

- [ ] **T01: Build S05 evidence contract and verifier tests** `est:1h 15m`
  - Why: S05 needs deterministic closure logic that combines S04 live-proof output with physical UAT artifact requirements.
  - Files: `scripts/verify-m006-s05-bundle.py`, `tests/test_verify_m006_s05_bundle.py`, `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.schema.json`, `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.example.json`
  - Do: Define S05 bundle schema and implement verifier that ingests S04 proof + S05 manifest, validates required flow classifications and endpoint trace evidence, enforces degraded/offline failure semantics, and emits redacted JSON/markdown outputs. Relevant skills: `test`, `fullstack-developer`, `debug-like-expert`.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m006_s05_bundle.py`
  - Done when: Verifier + schema + tests exist, tests pass, and bundle generation fails predictably for missing artifacts or any non-live required flow.

- [ ] **T02: Execute physical hardware UAT run and generate S05 evidence bundle** `est:1h 45m`
  - Why: The milestone cannot close until real devices prove heartbeat/card-read/QR confirm behavior with admin dashboard off and request traces on `:5010`.
  - Files: `.gsd/milestones/M006/slices/S05/S05-UAT.md`, `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json`, `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json`, `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md`, `.gsd/milestones/M006/slices/S05/evidence/README.md`
  - Do: Run the operator UAT checklist against the live cashier runtime on port 5010, perform RFID/QR/NFC-compatible flows with real hardware/accounts, capture screenshots/video/request traces with timestamps (including OLED QR-on-screen evidence), then run S04 + S05 verifiers to produce final bundle artifacts. Relevant skills: `agent-browser`, `test`, `debug-like-expert`.
  - Verify: `rtk proxy python scripts/verify-m006-s05-bundle.py --base-url http://127.0.0.1:5010 --s04-evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --manifest .gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json --output .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json --markdown .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md`
  - Done when: Bundle artifacts are generated, all required flows classify `live_success`, and evidence includes traceable hardware screenshots/video + request-path proof without `:5003` dependency.

- [ ] **T03: Publish S05 closure evidence into milestone and requirement traceability docs** `est:50m`
  - Why: Closure must be visible to future agents/operators in milestone and requirement records, not only raw artifacts.
  - Files: `.gsd/milestones/M006/slices/S05/S05-SUMMARY.md`, `.gsd/milestones/M006/M006-VALIDATION.md`, `.gsd/REQUIREMENTS.md`, `.gsd/milestones/M006/slices/S05/S05-ASSESSMENT.md`
  - Do: Summarize S05 run outcomes, link artifact files/commands, and update validation + R053 traceability notes (status change only if bundle gate passes); explicitly document any residual blockers if gate fails. Relevant skills: `test`, `fullstack-developer`.
  - Verify: `rtk proxy python -c "from pathlib import Path; files=['.gsd/milestones/M006/slices/S05/S05-SUMMARY.md','.gsd/milestones/M006/M006-VALIDATION.md','.gsd/REQUIREMENTS.md'];
for f in files:
    t=Path(f).read_text(encoding='utf-8');
    assert 'S05-UAT-BUNDLE.json' in t"`
  - Done when: Milestone + requirement docs reference S05 evidence bundle and clearly state pass/fail closure status for R053.

## Files Likely Touched

- `scripts/verify-m006-s05-bundle.py`
- `tests/test_verify_m006_s05_bundle.py`
- `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.schema.json`
- `.gsd/milestones/M006/slices/S05/S05-UAT.md`
- `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json`
- `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json`
- `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md`
- `.gsd/milestones/M006/M006-VALIDATION.md`
- `.gsd/REQUIREMENTS.md`
