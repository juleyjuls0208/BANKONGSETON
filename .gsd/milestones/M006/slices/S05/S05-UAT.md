# S05: Physical hardware UAT + evidence bundle — UAT

**Milestone:** M006  
**Written:** 2026-03-19

## UAT Type

- UAT mode: mixed (artifact-driven + live-runtime + human-experience)
- Why this mode is sufficient: S05 closure requires both machine-verifiable flow/status evidence and human-captured physical hardware proof (heartbeat badge, RFID tap, OLED QR display, student confirm, NFC-compatible completion).

## Preconditions

- Cashier runtime available at `http://127.0.0.1:5010`.
- Admin dashboard runtime/process remains OFF during evidence capture.
- S04 prerequisite evidence file exists: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`.
- S05 manifest exists with physical checks and artifact refs: `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json`.
- Required evidence files exist in `.gsd/milestones/M006/slices/S05/evidence/`:
  - `heartbeat-online-badge.png`
  - `rfid-card-read-success.mp4`
  - `oled-qr-display.png`
  - `student-qr-confirm.mp4`
  - `nfc-compatible-completion.png`
  - `request-trace.log`
- Redaction policy enforced (no raw JWT/API keys/full UID/unredacted student identifiers in persisted artifacts).

## Smoke Test

Run bundle generation once and confirm `overall.live_ready=true`:

1. `rtk proxy python scripts/verify-m006-s05-bundle.py --base-url http://127.0.0.1:5010 --s04-evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --manifest .gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json --output .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json --markdown .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md`
2. **Expected:** command exits `0`, and JSON bundle sets `overall.live_ready` to `true`.

## Test Cases

### 1. Required flow gate passes with physical evidence + request topology checks

1. Run the S05 bundle generator command (same as Smoke Test).
2. Run `rtk proxy python -c "import json; p='.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json'; d=json.load(open(p, encoding='utf-8')); assert d['overall']['live_ready'] is True; req=d['required_flows']; assert all(v.get('classification')=='live_success' for v in req.values()); assert all(':5003' not in hit.get('url','') for hit in d.get('request_trace', []))"`.
3. **Expected:** all required flows (`products_live_data`, `arduino_heartbeat`, `card_read_sale_completion`, `student_qr_confirm`, `nfc_compatible_completion`) are `live_success`, and no request trace points to `:5003`.

### 2. Diagnostics surface is complete for failure investigations

1. Run `rtk proxy python -c "import json; p='.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json'; d=json.load(open(p, encoding='utf-8')); o=d.get('overall', {}); assert isinstance(o.get('failure_reasons', []), list); pc=d.get('physical_checks', {}); assert pc and all('missing_artifacts' in v and 'failure_reasons' in v for v in pc.values()); print('diagnostics-surface-ok')"`.
2. **Expected:** command prints `diagnostics-surface-ok`; bundle contains structured diagnostics for every physical check even on pass-state.

### 3. Manifest artifact correlation is auditable

1. Run `rtk proxy python -c "import json,pathlib; m=json.load(open('.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json', encoding='utf-8')); b=json.load(open('.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json', encoding='utf-8')); arts={a['artifact_id']:a for a in m['artifacts']}; assert all(pathlib.Path(a['path']).exists() for a in m['artifacts']); checks=m['physical_checks']; required=['arduino_heartbeat','card_read_sale_completion','student_qr_confirm','nfc_compatible_completion']; assert all(name in checks for name in required); assert all((refs:=p.get('artifact_refs',[])) and any(arts[r]['captured_at']<=p['observed_at'] for r in refs if r in arts) for p in checks.values()); assert b['overall']['live_ready'] is True"`.
2. **Expected:** all referenced artifacts exist, each required physical check maps to artifacts with timestamp compatibility, and bundle remains live-ready.

## Edge Cases

### S04 preflight overwrite risk

1. Run `rtk proxy python scripts/verify-m006-s04-live.py --base-url http://127.0.0.1:5010 --evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json` in an environment missing required runtime env/inputs.
2. **Expected:** command exits non-zero and may overwrite S04 evidence to failing preflight state; S05 bundle must then be regenerated only after restoring/regenerating pass-state S04 evidence.

### Missing artifact or offline fallback classification

1. Run `rtk proxy python -m pytest -q tests/test_verify_m006_s05_bundle.py -k "offline or missing_artifact"`.
2. **Expected:** tests pass, proving verifier rejects closure when required flows are offline/degraded or artifact refs are missing.

## Failure Signals

- `overall.live_ready=false` in `S05-UAT-BUNDLE.json`.
- Any `required_flows.*.classification` != `live_success`.
- Any `request_trace[].url` includes `:5003`.
- `artifacts.missing_references` is non-empty.
- Any `physical_checks.*.missing_artifacts` or `physical_checks.*.failure_reasons` contains entries.
- Bundle generator exits non-zero or schema errors appear in `overall.schema_errors`.

## Not Proven By This UAT

- It does not prove continuous long-duration uptime behavior of hardware over an entire school day.
- It does not validate unrelated active M005 requirements (R030, R032, R033) outside standalone cashier closure scope.

## Notes for Tester

- Always run S05 bundle generation before assertion commands; parallel execution can create file-read races.
- If S04 verifier is rerun on a host missing runtime env/inputs, regenerate or restore S04 pass-state evidence before concluding S05 status.
- Keep all persisted evidence redacted and store only the artifact paths, timestamps, and classification metadata needed for auditability.
