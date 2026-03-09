---
phase: 29-android-security-p1-bugs
plan: "01"
subsystem: mobile/nfc
tags: [security, android, nfc, backup, pin-hashing, migration]
dependency_graph:
  requires: []
  provides: [REQ-SEC-04, REQ-SEC-05]
  affects: [NfcManager, backup_rules, data_extraction_rules]
tech_stack:
  added: []
  patterns: [SHA-256 pin hashing, plaintext-to-hash migration, Android backup exclusion rules]
key_files:
  created:
    - mobile/student_app_v2/app/src/main/res/xml/backup_rules.xml
    - mobile/student_app_v2/app/src/main/res/xml/data_extraction_rules.xml
  modified:
    - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt
decisions:
  - Use SHA-256 hex digest for PIN storage — no salt needed (PIN is validated server-side; local hash is for offline biometric fallback only)
  - Migration done transparently in verifyPin() — no one-time migration job needed
  - setPin() called after the token/registered edit().apply() block — avoids double-editing EncryptedSharedPreferences in the same call chain
metrics:
  duration: ~30 min
  completed: "2026-03-09"
  tasks_completed: 2
  files_changed: 3
---

# Phase 29 Plan 01: Android NFC Security — Backup Exclusion & PIN Hashing Summary

> SHA-256 PIN hashing with transparent plaintext migration, plus Android backup exclusion rules committed for banko_nfc_secure preferences.

## What Was Built

### Task 1 — Backup Exclusion Rules (REQ-SEC-04)
Both XML files already existed on disk from planning but were **untracked**. Committed them as-is:

- `backup_rules.xml` — `<exclude domain="sharedpref" path="banko_nfc_secure.xml" />` (Android 11 and below)
- `data_extraction_rules.xml` — same exclusion for both `<cloud-backup>` and `<device-transfer>` sections (Android 12+)

This ensures the NFC virtual card token and PIN are never backed up to Google Drive or transferred to a new device.

### Task 2 — PIN Hashing with Migration (REQ-SEC-05)
Three changes to `NfcManager.kt`:

1. **`hashPin(pin: String): String`** — Private helper. SHA-256 via `java.security.MessageDigest`, returns lowercase hex string. No new imports.

2. **`setPin(pin: String)`** — Public helper. Stores `hashPin(pin)` into `EncryptedSharedPreferences[KEY_NFC_PIN]`.

3. **`registerDevice()`** — Removed inline `.putString(KEY_NFC_PIN, pin)` from the chained `edit().apply()` block. Now calls `setPin(pin)` separately after the block completes.

4. **`verifyPin(enteredPin: String): Boolean`** — Migration-aware:
   - If stored value equals `hashPin(enteredPin)` → normal hash match, authorize
   - If stored value equals `enteredPin` literally → legacy plaintext detected, transparently re-save as `setPin(enteredPin)`, authorize
   - Otherwise → `false`

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Observations

- The XML files were already present on disk (likely created during planning/research phase) but were untracked by git. Task 1 was purely a `git add` + commit operation.
- The plan described adding `setPin()` and updating `registerDevice()` to "call `setPin(pin)` instead of `.putString(KEY_NFC_PIN, pin)`". The inline `putString` was inside a chained `.edit()...apply()` block. Moving `setPin(pin)` outside that block (after `.apply()`) was the correct approach since `setPin` opens its own `.edit()` internally.

## Commits

| Task | Commit  | Message |
|------|---------|---------|
| 1    | d91c7c3 | fix(29-01): add backup exclusion rules for banko_nfc_secure (REQ-SEC-04) |
| 2    | 9416215 | fix(29-01): hash NFC PIN with SHA-256, add plaintext migration (REQ-SEC-05) |

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| backup_rules.xml exists | ✅ FOUND |
| data_extraction_rules.xml exists | ✅ FOUND |
| NfcManager.kt exists | ✅ FOUND |
| Commit d91c7c3 exists | ✅ FOUND |
| Commit 9416215 exists | ✅ FOUND |
