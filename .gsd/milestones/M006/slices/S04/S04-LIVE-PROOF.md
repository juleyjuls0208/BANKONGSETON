# S04 Live Runtime Proof Summary

## Run Metadata

- Summary generated at: `2026-03-19T08:39:40Z`
- Evidence generated at: `2026-03-19T08:39:24Z`
- Base URL: `http://127.0.0.1:5011`
- Wrapper command: `rtk proxy bash scripts/verify-m006-s04.sh`
- Evidence JSON: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`
- Evidence Schema: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json`

## Overall Verdict

- `live_ready`: ✅ true
- `schema_valid`: ✅ true
- `dry_run_preflight`: `false`
- Breakdown: `live_success=10`, `offline_fallback=0`, `failed=0`

## Required Flow Outcomes (live_success required)

| Flow | Canonical Endpoint | Resolved Endpoint | Status | Success | Offline | Classification | Error |
|---|---|---|---:|:---:|:---:|---|---|
| products | `/api/products` | `/cashier/api/products` | 200 | ✅ | ❌ | `live_success` | - |
| rfid_complete_sale | `/api/complete-sale` | `/cashier/api/complete-sale` | 200 | ✅ | ❌ | `live_success` | - |
| qr_confirm | `/api/qr/confirm` | `/api/qr/confirm` | 200 | ✅ | ❌ | `live_success` | - |
| nfc_complete_sale | `/api/complete-sale-nfc` | `/cashier/api/complete-sale-nfc` | 200 | ✅ | ❌ | `live_success` | - |

## Preflight

- `ok`: ✅ true
- `missing_env`: none
- `missing_inputs`: none
- `missing_files`: none

## Diagnostics

- Queue status snapshot:

```json
{}
```

## Artifact Pointers

- Machine-readable evidence: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`
- Human-readable evidence: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md`
- Milestone validation reference: `.gsd/milestones/M006/M006-VALIDATION.md`
- Requirement traceability reference: `.gsd/REQUIREMENTS.md` (R053)
