---
id: T02
parent: S01
milestone: M005
provides:
  - arduino/bankongseton_nfc_r3/README.md — R3 README rewritten for RC522 hardware (no PN532 references)
  - scripts/verify-m005-s01.sh — executable S01 contract verification script (all 9 checks pass)
key_files:
  - arduino/bankongseton_nfc_r3/README.md
  - scripts/verify-m005-s01.sh
key_decisions:
  - Kept "BANKONGSETON NFC reader ready" startup line in README unchanged — ArduinoBridge depends on this exact string; only hardware description sections updated
patterns_established:
  - Pre-flight observability gap fix: T02-PLAN.md lacked Observability Impact section; added before executing deliverables
observability_surfaces:
  - bash scripts/verify-m005-s01.sh — exits 0 = all S01 contracts met; each check prints [N/9] description so failures are immediately pinpointed
duration: 10m
verification_result: passed
completed_at: 2026-03-17
blocker_discovered: false
---

# T02: Fix R3 README and Write Verify Script

**Rewrote R3 README to accurately describe RC522/MFRC522 hardware (replacing all PN532 references), and wrote `scripts/verify-m005-s01.sh` which exits 0 with all 9 S01 contract checks passing.**

## What Happened

1. **Pre-flight fix:** Added `## Observability Impact` section to `T02-PLAN.md` as required by the pre-flight check — documents verify script exit code signals and per-step stdout pinpointing.

2. **R3 README rewrite:** Replaced all PN532 content with accurate RC522 descriptions:
   - Title updated to `BANKONGSETON RFID Registration Reader — Arduino UNO R3 (RC522 over SPI)`
   - Opening description updated to reference RC522 and card registrations
   - Hardware table: PN532 row → RC522 RFID module row
   - Wiring section: PN532 table → RC522 table with SDA/SS→D10, RST→D8, SPI lines D11/D12/D13; "SPI mode selection" DIP switch note removed
   - Libraries table: Adafruit PN532 + Adafruit BusIO rows → MFRC522 (miguelbalboa/rfid) row
   - Pin summary: D10 row updated to `RC522 SDA/SS (SPI)`; D8 row added as `RC522 RST`
   - Serial Output Format and LCD I2C Address sections kept unchanged (format and startup string are the same)

3. **Verify script written:** `scripts/verify-m005-s01.sh` with all 9 checks from the task plan, made executable, runs from project root.

## Verification

```
$ bash scripts/verify-m005-s01.sh
=== S01: RC522 Firmware Swap — contract verification ===
[1/9] R4 firmware file exists...
[2/9] R4 secrets.h exists...
[3/9] Old bankongseton_rfid/ directory is gone...
[4/9] R4 uses MFRC522...
[5/9] R4 has no PN532/LCD/APDU code...
[6/9] R4 WiFi path preserved (httpPostCard, heartbeat, ensureWiFi)...
[7/9] R4 OLED placeholder present (Wire.h, OLED_ADDR)...
[8/9] R4 MFRC522 read pattern present...
[9/9] R3 README and firmware have no PN532 references...

✓ All S01 contract checks passed.
```

All 9 checks pass. Exit code 0.

Additional spot checks:
- `! grep -qE 'PN532|pn532' arduino/bankongseton_nfc_r3/README.md` — passes (no PN532 text in README)
- `! grep -qE 'PN532|pn532' arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino` — passes (firmware already used RC522)

## Diagnostics

- **Verify script:** `bash scripts/verify-m005-s01.sh` from project root — each step prints `[N/9] <description>...` then asserts; failure is pinpointed to numbered step
- **README accuracy:** `grep -n 'RC522\|MFRC522\|RST\|D10\|D8' arduino/bankongseton_nfc_r3/README.md` — confirms correct wiring entries
- **No PN532 leakage:** `grep -rn 'PN532\|pn532' arduino/bankongseton_nfc_r3/` — should return no output

## Deviations

None — all steps executed exactly as planned.

## Known Issues

None.

## Files Created/Modified

- `arduino/bankongseton_nfc_r3/README.md` — fully rewritten; all PN532 references replaced with RC522/MFRC522 descriptions
- `scripts/verify-m005-s01.sh` — new executable S01 contract verification script (9 checks, exits 0)
- `.gsd/milestones/M005/slices/S01/tasks/T02-PLAN.md` — added Observability Impact section (pre-flight fix)
