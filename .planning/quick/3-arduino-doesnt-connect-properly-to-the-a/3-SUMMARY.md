---
phase: quick-3
plan: 3
subsystem: arduino-serial-bridge
tags: [bug-fix, arduino, serial-protocol, card-scanning, cashier, admin-dashboard]
key-files:
  modified:
    - backend/dashboard/arduino_bridge.py
    - backend/dashboard/admin_dashboard.py
decisions:
  - "No angle brackets in firmware CARD| format — all card-scan parsing updated to CARD|{UID}"
  - "Accept len(uid) in (8, 14) to support both 4-byte MIFARE Classic (8 hex) and 7-byte cards (14 hex)"
metrics:
  duration: ~3min
  completed: "2026-03-08T05:09:11Z"
  tasks_completed: 2
  files_modified: 2
---

# Quick Task 3: Fix Arduino Serial Format Mismatch — SUMMARY

**One-liner:** Fixed silent card-scan drop by replacing legacy `<CARD|…>` bracket format with firmware-emitted `CARD|{UID}` in both arduino_bridge.py and admin_dashboard.py, also widening UID acceptance to 8 or 14 hex chars.

## What Was Done

The Arduino firmware (`bankongseton_nfc_r3.ino`) emits `CARD|ABCD1234` on the serial line.  
Both Python files checked for `<CARD|…>` (with angle brackets), so **every card scan was silently dropped** — cashier POS hung waiting for a card, and admin card-assignment never fired.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Fix arduino_bridge.py — `_parse_line` + `_read_card_thread` | `9e60acf` | `arduino_bridge.py` |
| 2 | Fix admin_dashboard.py — card scan loop + UID_PATTERN | `ba0af74` | `admin_dashboard.py` |

## Changes Detail

### Task 1 — arduino_bridge.py

**`_parse_line` (line 66-68):**
- OLD: `elif line.startswith("<CARD|") and line.endswith(">"):` + `uid = line[6:-1]` + `if len(uid) == 8:`
- NEW: `elif line.startswith("CARD|"):` + `uid = line[5:]` + `if len(uid) in (8, 14):`

**`_read_card_thread` (line 150-152):**
- OLD: Same bracket format check
- NEW: Same fix as `_parse_line` — `startswith("CARD|")`, `line[5:]`, `in (8, 14)`

### Task 2 — admin_dashboard.py

**UID_PATTERN (line 287):**
- OLD: `re.compile(r"^[0-9A-Fa-f]{8}$")`
- NEW: `re.compile(r"^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$")`

**Card scan loop (line 1845-1846):**
- OLD: `if line.startswith("<CARD|") and line.endswith(">"):` + `uid = line[6:-1]`
- NEW: `if line.startswith("CARD|"):` + `uid = line[5:]`

**Length guard (line 1883):**
- OLD: `if len(uid) == 8:`
- NEW: `if len(uid) in (8, 14):`

## Verification

```
PASS: no <CARD| in either file
PASS: no line[6:-1] in either file
PASS: startswith("CARD|") present in 3 locations across both files
PASS: len(uid) in (8, 14) present in 3 locations across both files
PASS: python syntax ok — arduino_bridge.py
PASS: python syntax ok — admin_dashboard.py
```

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `backend/dashboard/arduino_bridge.py` ✓ exists, modified
- `backend/dashboard/admin_dashboard.py` ✓ exists, modified  
- Commit `9e60acf` ✓ Task 1 — arduino_bridge.py
- Commit `ba0af74` ✓ Task 2 — admin_dashboard.py
