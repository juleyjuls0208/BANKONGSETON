---
status: testing
phase: 21-21
source: [21-01-SUMMARY.md, 21-02-SUMMARY.md, 21-03-SUMMARY.md, 21-04-SUMMARY.md, 21-05-SUMMARY.md]
started: 2026-03-08T02:45:46Z
updated: 2026-03-08T02:45:46Z
---

## Current Test

<!-- OVERWRITE each test - shows where we are -->

number: 3
name: FLASK_DEBUG Default Off
expected: |
  Start admin_dashboard.py and web_app.py without setting FLASK_DEBUG env var. Flask should NOT show its interactive debugger or expose debug info on errors. The Werkzeug banner should not say "debug mode".
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server/service. Start the backend servers from scratch (admin_dashboard.py, web_app.py, api_server.py). All three should boot without errors. A basic health check or homepage request should return a live response.
result: pass

### 2. Dashboard: No [DEBUG] Console Logs
expected: Open the admin dashboard in a browser. Open DevTools console. Perform normal actions (load stats, check serial ports). The console should have zero lines containing "[DEBUG]" — no debug noise from dashboard.html.
result: pass

### 3. FLASK_DEBUG Default Off
expected: Start admin_dashboard.py and web_app.py without setting FLASK_DEBUG env var. Flask should NOT show its interactive debugger or expose debug info on errors. The Werkzeug banner should not say "debug mode".
result: pass

### 4. Parent Login: Error Transparency (Sheets Down)
expected: When the Google Sheets backend is unavailable (network cut, bad credentials, or simulated), attempting parent login should return a 503 (connection/timeout) or 500 (unexpected error) response with a real error message — NOT a silent 401. The error should appear in server logs.
result: [pending]

### 5. NFC Payment: Station ID in Transaction
expected: Make a test NFC payment (or call POST /api/nfc/pay with an X-Station-ID header). Check the Transactions Log in Google Sheets. The transaction row should include a StationID column with the value from the X-Station-ID header (default "main" if header absent).
result: [pending]

### 6. NFC Payment: Low-Balance Email Alert
expected: Make an NFC payment that brings a student's balance below the LOW_BALANCE_THRESHOLD (default: 50). An email alert should be sent to the parent's email address on record. Server logs should show the email attempt. If SMTP is not configured, logs show a warning (no crash).
result: [pending]

### 7. NFC Payment: Low-Balance SMS Alert
expected: Make an NFC payment that brings balance below threshold AND the student has a PhoneNumber on record. If TWILIO_ACCOUNT_SID/AUTH_TOKEN/FROM_NUMBER are configured, an SMS is sent. If Twilio is unconfigured, the request still completes normally (no 500 error) and logs show a warning.
result: [pending]

### 8. Arduino Serial Auto-Connect
expected: Start the dashboard with STATION_SERIAL_PORT env var set to a valid port. ArduinoBridge should connect to the Arduino automatically on startup — no manual "connect" action needed. Logs should show the connection attempt. If the port is absent, a warning is logged and the dashboard still starts.
result: [pending]

### 9. Bulk CSV Student Import
expected: POST a CSV file to /api/students/import (via admin dashboard or curl). The CSV should have student rows. The endpoint should return JSON: {"imported": N, "skipped": M, "errors": [...]}. Duplicate StudentIDs in the CSV should be skipped (not cause errors). An Excel-exported CSV with BOM should import correctly.
result: [pending]

### 10. HCE Card After Process Kill (hardware required)
expected: On a physical Android device, open the student app and tap the NFC card at a reader to confirm it works. Then force-kill the app (via Android Recent Apps → swipe to kill, or adb shell am kill). WITHOUT reopening the app, tap the NFC card at the reader again. The payment should still process — the card token should be restored automatically from storage.
result: [pending]

### 11. FCM Push Notification After Token Rotation (network/device required)
expected: After a FCM token rotation event (can be simulated by clearing app data or forcing token refresh), push notifications should still arrive on the device. The new token should have been sent to the backend automatically on rotation. A subsequent NFC payment notification should appear on the device.
result: [pending]

## Summary

total: 11
passed: 3
issues: 0
pending: 10
skipped: 0

## Gaps

[none yet]
