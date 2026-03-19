# S05 Physical UAT Evidence Index

This directory stores operator-captured artifacts referenced by:
- `.gsd/milestones/M006/slices/S05/S05-UAT-MANIFEST.json`
- `.gsd/milestones/M006/slices/S05/S05-UAT-BUNDLE.json`

## Artifact Inventory

| Artifact ID | File | Type | Captured At (UTC) | Purpose |
|---|---|---|---|---|
| `heartbeat-online-badge` | `heartbeat-online-badge.png` | screenshot | 2026-03-19T06:23:12Z | Proves Arduino heartbeat online indicator during cashier runtime on `:5010`. |
| `rfid-card-read-success-video` | `rfid-card-read-success.mp4` | video | 2026-03-19T06:25:20Z | Shows RFID tap through successful sale completion flow. |
| `oled-qr-display` | `oled-qr-display.png` | screenshot | 2026-03-19T06:27:02Z | Shows OLED QR render during student QR flow (R027 evidence). |
| `student-qr-confirm-video` | `student-qr-confirm.mp4` | video | 2026-03-19T06:28:48Z | Shows student-side QR confirm completion. |
| `nfc-compatible-completion-screenshot` | `nfc-compatible-completion.png` | screenshot | 2026-03-19T06:30:27Z | Shows NFC-compatible completion route success. |
| `request-trace-log` | `request-trace.log` | trace | 2026-03-19T06:31:10Z | Endpoint trace proving required requests stayed on `:5010` and not `:5003`. |

## Redaction Policy

Do not store raw JWT values, API keys, full card UIDs, or unredacted student identifiers in any artifact file.
