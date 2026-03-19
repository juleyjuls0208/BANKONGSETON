# S05 Physical Hardware UAT Runbook (Port 5010)

**Milestone:** M006  
**Slice:** S05  
**Purpose:** Capture auditable physical-runtime proof that required cashier flows execute on `http://127.0.0.1:5010` with **admin dashboard process OFF**.

## Operator Preconditions

1. **Admin dashboard process must be OFF** during all captures.
   - Confirm no active runtime on `:5003`.
   - Confirm all cashier traces resolve to `:5010` only.
2. Cashier runtime is started and reachable at `http://127.0.0.1:5010`.
3. Real hardware is available and connected:
   - Arduino UNO R4 WiFi heartbeat transmitter
   - RFID card for card-read completion flow
   - OLED QR display capture device (camera/phone)
   - NFC-compatible phone/token for `complete-sale-nfc`
4. Use **test-only cashier and student accounts** (never production balances).
5. Use low-value safety amount (`₱1.00`) per verifier sale run.
6. Redaction rule in evidence: never store raw JWTs, full card UID, API keys, or unredacted student IDs.

## Runtime Guard Checklist (must pass before capture)

- [ ] Admin dashboard process OFF (no separate dashboard runtime)
- [ ] Cashier runtime ON at `:5010`
- [ ] Arduino heartbeat online indicator visible
- [ ] Request trace sink prepared (`.gsd/milestones/M006/slices/S05/evidence/request-trace.log`)

## Capture Sequence (strict order)

1. **Heartbeat Online (Arduino WiFi)**
   - Observe heartbeat online badge/state.
   - Capture screenshot: `heartbeat-online-badge.png`.
   - Record request hit for `POST /api/arduino/heartbeat` on `:5010`.

2. **RFID Card-Read Sale Completion**
   - Start cashier sale (`process-sale`) and tap RFID card.
   - Verify completion response path for card-read sale.
   - Capture video: `rfid-card-read-success.mp4`.
   - Record request hits for `POST /api/arduino/card-read` and completion path on `:5010`.

3. **QR Generation + Student Confirm (OLED required)**
   - Generate QR from cashier flow.
   - Capture OLED showing active QR token: `oled-qr-display.png` (**required for R027 evidence**).
   - Complete student confirmation on device.
   - Capture video: `student-qr-confirm.mp4`.
   - Record request hit for `POST /api/qr/confirm` on `:5010`.

4. **NFC-Compatible Completion Route**
   - Start cashier sale (`process-sale`) and complete via NFC-compatible path.
   - Capture screenshot: `nfc-compatible-completion.png`.
   - Record request hit for `POST /api/complete-sale-nfc` on `:5010`.

5. **Trace and Bundle Generation**
   - Persist request-path evidence in `request-trace.log`.
   - Update `S05-UAT-MANIFEST.json` with artifact refs + timestamps.
   - Run S04 verifier command, then S05 bundle verifier command.
   - Confirm `S05-UAT-BUNDLE.json` shows:
     - `overall.live_ready = true`
     - all required flow classifications = `live_success`
     - no `:5003` in `request_trace[].url`

## Artifact Checklist

- [ ] `.gsd/milestones/M006/slices/S05/evidence/heartbeat-online-badge.png`
- [ ] `.gsd/milestones/M006/slices/S05/evidence/rfid-card-read-success.mp4`
- [ ] `.gsd/milestones/M006/slices/S05/evidence/oled-qr-display.png`
- [ ] `.gsd/milestones/M006/slices/S05/evidence/student-qr-confirm.mp4`
- [ ] `.gsd/milestones/M006/slices/S05/evidence/nfc-compatible-completion.png`
- [ ] `.gsd/milestones/M006/slices/S05/evidence/request-trace.log`

## Timestamp Correlation Log

Use UTC timestamps in ISO-8601 (`YYYY-MM-DDTHH:MM:SSZ`) and keep artifact captures within seconds of corresponding request-trace entries.

| Phase | Required endpoint | Evidence artifact | Timestamp captured? |
|---|---|---|---|
| heartbeat_online | `/api/arduino/heartbeat` | `heartbeat-online-badge.png` | [ ] |
| rfid_card_read | `/api/arduino/card-read` + sale completion path | `rfid-card-read-success.mp4` | [ ] |
| qr_student_confirm | `/api/qr/confirm` | `oled-qr-display.png`, `student-qr-confirm.mp4` | [ ] |
| nfc_complete_sale | `/api/complete-sale-nfc` | `nfc-compatible-completion.png` | [ ] |

## Failure Signals to Capture

If any flow fails, capture and retain:
- endpoint and resolved endpoint
- HTTP status
- offline/degraded indicator
- missing artifact reference (if any)
- timestamp of failed phase

These signals must appear in `S05-UAT-BUNDLE.json` (`overall.failure_reasons`, `required_flows.*`, `physical_checks.*`).
