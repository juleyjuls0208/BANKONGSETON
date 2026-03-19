# S05 Physical UAT Evidence Bundle Summary

## Run Metadata

- Summary generated at: `2026-03-19T10:15:22Z`
- Bundle generated at: `2026-03-19T10:15:22Z`
- Base URL: `http://127.0.0.1:5010`
- Output JSON: `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json`
- Output Markdown: `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.md`

## Overall Verdict

- `live_ready`: ✅ true
- `schema_valid`: ✅ true
- Flow counts: `live_success=5`, `offline_fallback=0`, `failed=0`

## Required Flow Outcomes

| Flow | Endpoint | Resolved Endpoint | Status | Classification | Artifact refs |
|---|---|---|---:|---|---:|
| products_live_data | `/api/products` | `/cashier/api/products` | 200 | `live_success` | 0 |
| arduino_heartbeat | `/api/arduino/heartbeat` | `/api/arduino/heartbeat` | 200 | `live_success` | 2 |
| card_read_sale_completion | `/api/complete-sale` | `/cashier/api/complete-sale` | 200 | `live_success` | 2 |
| student_qr_confirm | `/api/qr/confirm` | `/api/qr/confirm` | 200 | `live_success` | 3 |
| nfc_compatible_completion | `/api/complete-sale-nfc` | `/cashier/api/complete-sale-nfc` | 200 | `live_success` | 2 |

## Physical Checks

| Check | Classification | Observed at | Missing artifacts |
|---|---|---|---|
| arduino_heartbeat | `live_success` | `2026-03-19T06:23:12Z` | none |
| card_read_sale_completion | `live_success` | `2026-03-19T06:25:20Z` | none |
| student_qr_confirm | `live_success` | `2026-03-19T06:28:48Z` | none |
| nfc_compatible_completion | `live_success` | `2026-03-19T06:30:27Z` | none |

## Artifact Inventory

```json
{
  "total": 6,
  "screenshot": 3,
  "video": 2,
  "trace": 1
}
```
