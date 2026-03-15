---
id: S04
parent: M003
milestone: M003
provides:
  - Firmware heartbeat POST loop — lastHeartbeatMs file-scope variable + 4-line timer block in loop() POSTs to /api/arduino/heartbeat every 30s
  - HEARTBEAT_INTERVAL_MS comment updated — stub text removed, authoritative description added
  - arduino/README-wireless.md — complete standalone wireless deployment guide (hardware, wiring, secrets.h field-by-field, flashing, powerbank selection, verification, troubleshooting)
  - scripts/verify-m003-s04.sh — 8-check assertion script, exits 0
requires:
  - slice: S01
    provides: httpPostJson() helper, ensureWiFi() pattern, HEARTBEAT_INTERVAL_MS constant stub
  - slice: S03
    provides: POST /api/arduino/heartbeat backend endpoint; arduino_wifi_status socket emit; #wifiBadge in cashier UI
affects:
  - none (final slice of M003)
key_files:
  - arduino/bankongseton_rfid/bankongseton_rfid.ino
  - arduino/README-wireless.md
  - scripts/verify-m003-s04.sh
key_decisions:
  - Heartbeat block placed after handleIncomingSerial() and before NFC uid[] declaration — fires during idle, not gated by if (!found) return at line 530
  - lastHeartbeatMs static at file scope — plain local would reset to 0 each loop() call and fire every iteration
  - Dual-purpose heartbeat: RF burst keeps powerbank above auto-shutoff threshold; backend receives POST and emits arduino_wifi_status to drive badge
patterns_established:
  - Firmware idle keep-alive: periodic POST during NFC scan idle avoids powerbank current-starve shutoff without dedicated hardware
  - Deployment README pattern: hardware table → wiring tables → libraries → secrets.h field table (with port/key callouts) → flashing steps → verification (Serial Monitor + badge) → powerbank selection → troubleshooting
observability_surfaces:
  - Serial Monitor "HTTP: POST /api/arduino/heartbeat" every 30s during idle — timer firing confirmed
  - Flask access log "POST /api/arduino/heartbeat 200" on each interval — network path confirmed
  - Cashier #wifiBadge turns green within 30s of first heartbeat via arduino_wifi_status socket event
  - bash scripts/verify-m003-s04.sh — 8 grep assertions; single-command exit-0 proof
drill_down_paths:
  - .gsd/milestones/M003/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M003/slices/S04/tasks/T02-SUMMARY.md
duration: ~35m (T01: 15m, T02: 20m)
verification_result: passed
completed_at: 2026-03-15
---

# S04: Powerbank Hardening + Wireless Docs

**Firmware heartbeat loop added and wireless deployment documented — Arduino keeps powerbank alive during idle and drives WiFi badge green via 30-second POST to `/api/arduino/heartbeat`.**

## What Happened

Two tasks, both clean.

**T01 — Firmware heartbeat loop:** Three surgical edits to `bankongseton_rfid.ino`. (1) `static unsigned long lastHeartbeatMs = 0;` declared at file scope before `setup()` — the only placement that persists across `loop()` iterations; a plain local would reset to 0 on every call and fire the POST every loop pass. (2) 4-line timer block inserted immediately after `handleIncomingSerial()` and before the NFC `uid[]` declaration at line 479. This placement is the critical constraint: the heartbeat must fire during idle periods when no card is in range, before the `if (!found) return;` early exit at line 530. Timer comparison uses unsigned long arithmetic for millis() rollover safety. (3) `HEARTBEAT_INTERVAL_MS` constant comment updated from "S04: heartbeat stub — POST not yet implemented" to a description of actual purpose. The heartbeat POST is dual-purpose: the WiFi transmission's RF burst keeps the powerbank above its auto-shutoff current threshold, while the S03-wired `/api/arduino/heartbeat` backend handler emits `arduino_wifi_status` to drive the cashier badge green.

**T02 — README and verify script:** `arduino/README-wireless.md` written following the section structure and table markdown style of the existing R3 README for consistency. Eight sections: Hardware Required, Wiring (PN532 SPI + LCD I2C + Buzzer, with SPI-mode callout note), Required Libraries, secrets.h Configuration (field table naming port `5003` and `ARDUINO_API_KEY` explicitly — not generic placeholders), Flashing (Arduino IDE step-by-step), Verification (Serial Monitor boot line + 30s heartbeat line + badge-goes-green), Powerbank Selection (table + prose on why 2A/10,000mAh/name-brand matters), Troubleshooting (symptom/cause/fix table). `scripts/verify-m003-s04.sh` checks 4 firmware structure patterns (a–d) and 4 README content patterns (e–h) using accumulated PASS/FAIL counters, same pattern as verify-m003-s03.sh.

## Verification

```
bash scripts/verify-m003-s04.sh
→ 8 passed, 0 failed — verify-m003-s04: all 8 checks passed ✓

bash scripts/verify-m003-s03.sh
→ 12 passed, 0 failed — M003/S03 verification PASSED ✓
```

Spot-checks:
- `grep -n "lastHeartbeatMs"` → declaration at line 427, use at lines 481–482 ✓
- `grep -n "httpPostJson.*heartbeat"` → line 484, inside timer block ✓
- `grep "stub\|not yet implemented"` → (no output) — clean ✓
- `grep -n "if (!found) return"` → line 530; heartbeat block (479–485) safely before ✓
- `test -f arduino/README-wireless.md` → OK ✓
- `grep "5003\|ARDUINO_API_KEY\|powerbank" arduino/README-wireless.md` → all three match ✓

## Requirements Advanced

- R023 (Arduino Stable on Powerbank) — heartbeat POST loop implemented; 30s interval provides sustained RF burst above powerbank auto-shutoff threshold; `ensureWiFi()` called before each POST ensures auto-reconnect on WiFi drop

## Requirements Validated

- R023 — contract-level proof: firmware structure verified by 8/8 grep assertions; runtime/operational proof (30-min powerbank idle, WiFi drop/reconnect) requires physical hardware UAT
- R024 — `arduino/README-wireless.md` exists with all required sections; `bash scripts/verify-m003-s04.sh` exits 0 with 8/8 checks

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none — both tasks implemented exactly as specified in their plans

## Known Limitations

- Powerbank operational proof (30-minute idle + WiFi drop/reconnect) cannot be contract-verified; physical hardware UAT is required before M003 is called done
- README documents powerbank selection criteria (≥2A, ≥10,000mAh, name-brand) but cannot guarantee all powerbanks behave correctly; cheap models with very aggressive auto-shutoff may still cut power despite the heartbeat current burst

## Follow-ups

- Flash updated firmware to the hardware Arduino and run UAT: confirm badge turns green within 30s, confirm badge recovers after WiFi drop, confirm 30-minute powerbank idle does not cut power

## Files Created/Modified

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — added lastHeartbeatMs file-scope variable and 4-line heartbeat timer block in loop(); updated HEARTBEAT_INTERVAL_MS constant comment
- `arduino/README-wireless.md` — complete standalone wireless deployment guide (8 sections)
- `scripts/verify-m003-s04.sh` — 8-check assertion script, chmod +x, exits 0

## Forward Intelligence

### What the next slice should know
- M003 is complete at the contract level. S04 closes all structural work. Hardware UAT (flash → badge green → powerbank soak → WiFi drop recovery) is the only remaining gate before the milestone is declared done.
- The heartbeat timer comparison uses `(unsigned long)HEARTBEAT_INTERVAL_MS` — intentional for millis() rollover safety after ~49 days of uptime; do not simplify to a plain int comparison.
- `ensureWiFi()` is called before each heartbeat POST (line 483) and before each card/NFC POST — reconnect logic is in place, but recovery time depends on network; a flaky AP that takes >30s to reassociate will cause one missed heartbeat (badge briefly red) then recover on the next interval.

### What's fragile
- Powerbank keep-alive relies on the RF burst from the POST, not a dedicated hardware signal — cheap powerbanks with sub-100mA auto-shutoff thresholds may still cut power; the PN532 polling loop baseline draw (~180–200mA) is the real current buffer, not the heartbeat burst alone
- `HEARTBEAT_INTERVAL_MS = 30000` is a compile-time constant; changing it requires a re-flash with no runtime configuration path

### Authoritative diagnostics
- Serial Monitor `HTTP: POST /api/arduino/heartbeat` every 30s — most direct proof the firmware timer fires and WiFi is up
- Flask access log `POST /api/arduino/heartbeat 200` — confirms server received it; `401` → `SECRET_API_KEY` in `secrets.h` does not match `ARDUINO_API_KEY` in Flask `.env`
- `#wifiBadge` in cashier UI — turns green within 30s of first successful heartbeat; stays red → heartbeat not reaching backend

### What assumptions changed
- none — all assumptions held
