# S05 Summary — Physical hardware UAT + evidence bundle

**Slice:** M006/S05  
**Status:** complete (bundle gate passed)  
**Final evidence bundle:** `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.{json,md}`

## Outcome

S05 closure evidence was produced for cashier runtime `http://127.0.0.1:5010` with admin dashboard process explicitly documented as OFF in the manifest/runtime notes. The generated bundle reports:

- `overall.live_ready = true`
- `overall.schema_valid = true`
- required flow classifications all `live_success`
- `request_trace` URLs constrained to `:5010` (no `:5003` hits)

## Required Flow → Evidence Mapping

| Required flow | Bundle classification | Endpoint (canonical → resolved) | Status | Evidence refs | Notes |
|---|---|---|---:|---|---|
| `products_live_data` | `live_success` | `/api/products` → `/cashier/api/products` | 200 | Derived from S04 proof + S05 request trace | Live product load proven in closure bundle.
| `arduino_heartbeat` | `live_success` | `/api/arduino/heartbeat` → `/api/arduino/heartbeat` | 200 | `heartbeat-online-badge`, `request-trace-log` | Heartbeat freshness remained online.
| `card_read_sale_completion` | `live_success` | `/api/complete-sale` → `/cashier/api/complete-sale` | 200 | `rfid-card-read-success-video`, `request-trace-log` | Card-read + completion path succeeded.
| `student_qr_confirm` | `live_success` | `/api/qr/confirm` → `/api/qr/confirm` | 200 | `oled-qr-display`, `student-qr-confirm-video`, `request-trace-log` | OLED QR proof captured before student confirm.
| `nfc_compatible_completion` | `live_success` | `/api/complete-sale-nfc` → `/cashier/api/complete-sale-nfc` | 200 | `nfc-compatible-completion-screenshot`, `request-trace-log` | NFC-compatible completion path succeeded.

## Physical Check Verdicts

All required physical checks in `physical_checks.*` are `live_success` with no missing artifacts:

- `arduino_heartbeat`
- `card_read_sale_completion`
- `student_qr_confirm`
- `nfc_compatible_completion`

## Operator and Artifact Notes

- Operator manifest: `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json`
- Runbook and rerun checklist: `.gsd/milestones/M006/slices/S05/S05-UAT.md`
- Artifact inventory (6 total): 3 screenshots, 2 videos, 1 trace log
- Evidence index: `.gsd/milestones/M006/slices/S05/evidence/README.md`
- Redaction constraints were retained in machine-readable artifacts (no raw JWTs/API keys/full card UIDs/unredacted student identifiers)

## Verification Commands Used for Closure

- `rtk proxy python scripts/verify-m006-s05-bundle.py --base-url http://127.0.0.1:5010 --s04-evidence .gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json --manifest .gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json --output .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json --markdown .gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md`
- `rtk proxy python -c "import json; p='.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json'; d=json.load(open(p, encoding='utf-8')); assert d['overall']['live_ready'] is True; req=d['required_flows']; assert all(v.get('classification')=='live_success' for v in req.values()); assert all(':5003' not in hit.get('url','') for hit in d.get('request_trace', []))"`
- `rtk proxy python -c "import json; p='.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json'; d=json.load(open(p, encoding='utf-8')); o=d.get('overall', {}); assert isinstance(o.get('failure_reasons', []), list); pc=d.get('physical_checks', {}); assert pc and all('missing_artifacts' in v and 'failure_reasons' in v for v in pc.values()); print('diagnostics-surface-ok')"`

## Closure Statement

S05 evidence closes the M006 physical-runtime gap for R053 by tying runtime flow outcomes, physical artifacts, and request-path diagnostics into a single auditable bundle, with `live_ready=true` and no degraded/offline classifications.