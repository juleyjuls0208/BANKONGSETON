---
estimated_steps: 5
estimated_files: 5
---

# T02: Execute physical hardware UAT run and generate S05 evidence bundle

**Slice:** S05 — Physical hardware UAT + evidence bundle
**Milestone:** M006

## Description

Run real-device cashier UAT on port `5010` and generate the final S05 evidence bundle by combining physical capture artifacts with S04+S05 verifier outputs.

Relevant skills to load: `agent-browser`, `test`, `debug-like-expert`.

## Steps

1. Author `.gsd/milestones/M006/slices/S05/S05-UAT.md` with operator prerequisites and exact run order (admin dashboard process OFF, cashier runtime on `:5010`, test accounts/amount safeguards, and artifact capture checklist).
2. Perform hardware UAT flows with real devices: Arduino heartbeat online, RFID card-read sale completion, QR generation + student confirm (with OLED QR screen captured), and NFC-compatible completion route; record timestamps for each phase.
3. Capture evidence assets and request-path traces into S05 artifact locations (screenshots/video/log extracts), including proof that required requests are served by `:5010` and not `:5003`.
4. Write `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json` from the example template, linking each flow to concrete artifact files and resolved endpoints.
5. Run S04 live verifier and then S05 bundle verifier to produce `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.{json,md}`.

## Must-Haves

- [ ] UAT checklist explicitly requires admin dashboard OFF during capture.
- [ ] Manifest includes OLED QR-render capture evidence to support R027 runtime behavior.
- [ ] Manifest ties each required flow to real captured artifacts with timestamps.
- [ ] Request traces show required endpoint hits on port 5010 only.
- [ ] Final bundle artifacts are generated and classify all required flows as `live_success`.

## Verification

- `rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`
- `rtk proxy python scripts/verify-m006-s05-bundle.py --base-url http://127.0.0.1:5010 --s04-evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --manifest .gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json --output .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json --markdown .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md`
- `rtk proxy python -c "import json; d=json.load(open('.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json', encoding='utf-8')); assert d['overall']['live_ready'] is True; assert all(':5003' not in r.get('url','') for r in d.get('request_trace', []))"`

## Observability Impact

- Signals added/changed: physical-check statuses (`heartbeat_online`, `rfid_card_read`, `qr_student_confirm`, `nfc_complete_sale`) and timestamp-correlated request traces.
- How a future agent inspects this: read `S05-UAT.md`, inspect `S05-UAT-MANIFEST.json`, and open `S05-UAT-BUNDLE.{json,md}` for phase-by-phase evidence.
- Failure state exposed: bundle output pinpoints whether failure is missing artifact, offline/degraded checkout, wrong endpoint/port usage, or operator checklist incompleteness.

## Inputs

- `.gsd/milestones/M006/slices/S05/tasks/T01-PLAN.md` — Verifier and manifest contract requirements.
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json` — Baseline runtime proof consumed by S05 bundle logic.
- `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md` — Human-readable summary for flow mapping.
- `backend/dashboard/web_app.py` and `backend/dashboard/cashier/cashier_routes.py` — Active route topology to validate endpoint hits.

## Expected Output

- `.gsd/milestones/M006/slices/S05/S05-UAT.md` — Operator execution checklist with capture protocol.
- `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json` — Completed manifest of physical artifacts and route traces.
- `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json` — Machine-readable S05 closure artifact.
- `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md` — Human-readable S05 evidence summary.
- `.gsd/milestones/M006/slices/S05/evidence/README.md` — Artifact directory index for screenshots/video/log files.
