---
phase: 18-arduino-uno-r4-wifi-upgrade
verified: 2026-03-07T06:30:00Z
status: gaps_found
score: 9/10 must-haves verified
re_verification: false
gaps:
  - truth: "REQUIREMENTS.md reflects ARDW-02 and ARDW-03 as complete"
    status: failed
    reason: "ARDW-02 and ARDW-03 checkboxes remain unchecked ([ ]) and their status rows say 'Pending' in the tracking table, despite both being fully implemented and human-verified. Phase 18 close commits (f2a7368, caea071) updated STATE.md and ROADMAP.md but skipped REQUIREMENTS.md."
    artifacts:
      - path: ".planning/REQUIREMENTS.md"
        issue: "Lines 37-38: ARDW-02 and ARDW-03 still show `- [ ]` (unchecked). Lines 101-102: status column shows 'Pending' instead of 'Complete'."
    missing:
      - "Change `- [ ] **ARDW-02**` to `- [x] **ARDW-02**` in REQUIREMENTS.md"
      - "Change `- [ ] **ARDW-03**` to `- [x] **ARDW-03**` in REQUIREMENTS.md"
      - "Change ARDW-02 row status from 'Pending' to 'Complete' in the tracking table"
      - "Change ARDW-03 row status from 'Pending' to 'Complete' in the tracking table"
human_verification:
  - test: "Upload bankongseton_rfid.ino to Arduino UNO R4 WiFi hardware and confirm end-to-end card scan → Flask → cashier UI"
    expected: "Card tap triggers POST to Flask, cashier sees card_read SocketIO event with correct UID"
    why_human: "Hardware test requires physical Arduino UNO R4 WiFi board, MFRC522 reader, and school LAN — cannot be automated from CI"
---

# Phase 18: Arduino UNO R4 WiFi Upgrade — Verification Report

**Phase Goal:** Update Arduino firmware to POST card UID events over WiFi to Flask API, eliminating the serial USB dependency for card reading.
**Verified:** 2026-03-07T06:30:00Z
**Status:** gaps_found — 9/10 must-haves verified; 1 documentation gap in REQUIREMENTS.md
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Flask accepts `POST /api/arduino/card-read` with valid `X-API-Key` and emits `card_read` SocketIO event | ✓ VERIFIED | `arduino_card_read()` at web_app.py:1446; `socketio.emit("card_read", {"success": True, "uid": uid})` at line 1474 |
| 2 | Flask returns 401 when `X-API-Key` is missing or wrong | ✓ VERIFIED | Guard at web_app.py:1456: `if not ARDUINO_API_KEY or api_key != ARDUINO_API_KEY: return jsonify({"error": "Unauthorized"}), 401` |
| 3 | Flask returns 401 when `ARDUINO_API_KEY` env var is empty (no open-door vulnerability) | ✓ VERIFIED | Empty-key guard at line 1456: `if not ARDUINO_API_KEY` short-circuits before comparison; `ARDUINO_API_KEY = os.environ.get("ARDUINO_API_KEY", "")` at line 278 |
| 4 | Flask returns 400 when `uid` is missing or doesn't match 8-char hex `UID_PATTERN` | ✓ VERIFIED | `if not UID_PATTERN.match(uid): return jsonify({"error": "..."}), 400` at web_app.py:1467-1470 |
| 5 | Cashier UI receives `card_read` SocketIO event identically to serial path (zero frontend changes) | ✓ VERIFIED | Emission shape `{"success": True, "uid": uid}` matches arduino_bridge.py:75-78 exactly; git diff confirms no cashier/template files changed across all phase 18 commits |
| 6 | Arduino connects to school WiFi on boot and auto-reconnects between scans | ✓ VERIFIED | `connectWiFi()` called in `setup()` at sketch:196; `ensureWiFi()` called before each delivery attempt at sketch:156 + between retries at sketch:172 |
| 7 | Arduino reads MFRC522 card UID and POSTs JSON to Flask over LAN | ✓ VERIFIED | `httpPost()` at sketch:89; HTTP POST with `X-API-Key` header and JSON body; `Content-Length` header present at sketch:111 |
| 8 | Arduino retries up to 3 times on HTTP failure, then falls back to `Serial.println` | ✓ VERIFIED | `MAX_RETRIES = 3` at sketch:27; retry loop in `deliverUID()` at sketch:159; fallback `Serial.print("CARD|")` at sketch:178 |
| 9 | `secrets.h` is gitignored; `secrets.h.example` provides a committed template | ✓ VERIFIED | `.gitignore` line 77: `arduino/bankongseton_rfid/secrets.h`; `git ls-files` confirms only `.ino` and `.h.example` are tracked |
| 10 | REQUIREMENTS.md reflects all ARDW IDs as complete after phase closure | ✗ FAILED | ARDW-01 ✓ and ARDW-04 ✓ correctly checked; ARDW-02 and ARDW-03 remain `- [ ]` (unchecked) and show 'Pending' in tracking table — not updated during phase 18 close |

**Score: 9/10 truths verified**

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/dashboard/web_app.py` | POST /api/arduino/card-read route + ARDUINO_API_KEY validation | ✓ VERIFIED | Route at line 1446; `ARDUINO_API_KEY` constant at line 278; full 401/400/200 logic present; syntax check passes |
| `.env.example` | `ARDUINO_API_KEY` documented for operators | ✓ VERIFIED | Line 22: `ARDUINO_API_KEY=` with comment linking to `secrets.h` |
| `config/.env.example` | `ARDUINO_API_KEY` documented for config-dir env | ✓ VERIFIED | Line 22: `ARDUINO_API_KEY=` with identical comment |
| `arduino/bankongseton_rfid/bankongseton_rfid.ino` | Main Arduino sketch — WiFi + MFRC522 + HTTP POST + serial fallback | ✓ VERIFIED | 220-line sketch with all required sections; `WiFiS3.h` include; `deliverUID()`; `httpPost()`; `CARD\|` fallback |
| `arduino/bankongseton_rfid/secrets.h.example` | Template for operators to copy to `secrets.h` | ✓ VERIFIED | Contains `SECRET_SSID`, `SECRET_PASS`, `FLASK_HOST`, `SECRET_API_KEY` with descriptive comments |
| `.gitignore` | Prevents `secrets.h` from being committed | ✓ VERIFIED | Line 77: `arduino/bankongseton_rfid/secrets.h` entry present |
| `.planning/REQUIREMENTS.md` | ARDW-02 and ARDW-03 marked complete | ✗ STUB/STALE | ARDW-02 (`- [ ]`) and ARDW-03 (`- [ ]`) unchecked; tracking table shows both as 'Pending'; ARDW-01 and ARDW-04 correctly marked complete |

---

## Key Link Verification

### Plan 01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `arduino_card_read()` | `socketio.emit('card_read', ...)` | Same emission as `ArduinoBridge._read_card_thread` | ✓ WIRED | web_app.py:1474 emits `{"success": True, "uid": uid}` — exact match to arduino_bridge.py:75-78 |
| `arduino_card_read()` | `ARDUINO_API_KEY` env var | `os.environ.get` check + empty-string guard | ✓ WIRED | Module-level constant at line 278; empty-key guard at line 1456 prevents open-door bug |

### Plan 02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `connectWiFi()` | `WL_CONNECTED` | `WiFi.begin(SECRET_SSID, SECRET_PASS)` + status poll loop | ✓ WIRED | sketch:48; poll loop at sketch:51-54 with 20 attempts |
| `httpPost()` | `POST /api/arduino/card-read` | `WiFiClient` + raw HTTP with `Content-Length` header | ✓ WIRED | sketch:111: `client.println("Content-Length: " + String(body.length()))` |
| `postUID()` on failure | `Serial.println` fallback | 3-retry loop then `CARD|UID` serial output | ✓ WIRED | sketch:159-179: loop exhausts `MAX_RETRIES=3` then `Serial.print("CARD|")` |

### Plan 03 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `curl POST /api/arduino/card-read` | cashier UI `card_read` SocketIO event | Flask `socketio.emit` | ✓ WIRED | Human-verified per 18-03-SUMMARY.md; all 4 curl checks passed (401/401/400/200) |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| ARDW-01 | 18-02 | Arduino UNO R4 firmware sends card read events over WiFi directly to Flask API (no serial USB dependency) | ✓ SATISFIED | `bankongseton_rfid.ino` uses `WiFiS3.h`; `deliverUID()` POSTs to Flask; `secrets.h` isolates credentials; correctly marked `[x]` in REQUIREMENTS.md |
| ARDW-02 | 18-01 | Flask backend has a dedicated WiFi card-read endpoint that accepts Arduino POST requests | ✓ SATISFIED (code) ⚠️ STALE (docs) | `POST /api/arduino/card-read` exists at web_app.py:1446 with full auth + validation; however REQUIREMENTS.md still shows `[ ]` unchecked and 'Pending' — documentation not updated at phase close |
| ARDW-03 | 18-01 | Cashier computer UI still handles order entry — Arduino WiFi only handles card UID delivery | ✓ SATISFIED (code) ⚠️ STALE (docs) | No cashier/frontend files changed in any phase 18 commit; SocketIO event shape identical to serial path; however REQUIREMENTS.md still shows `[ ]` unchecked and 'Pending' |
| ARDW-04 | 18-02 | Fallback: system can still operate in serial/USB mode if WiFi is unavailable | ✓ SATISFIED | `deliverUID()` falls back to `CARD|UID` serial format after `MAX_RETRIES=3` exhausted; correctly marked `[x]` in REQUIREMENTS.md |

**Note on ARDW-03 interpretation:** The requirement says "Cashier computer UI still handles order entry." The implementation satisfies the intent — cashier UI is unchanged, receives identical `card_read` SocketIO events from both WiFi and serial paths. No frontend changes were needed or made.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `.planning/REQUIREMENTS.md` | 37-38, 101-102 | Stale status — ARDW-02/ARDW-03 checkboxes not updated at phase close | ⚠️ Warning | Documentation drift; tracking table and checklist disagree with actual implementation state; blocks accurate phase status reporting |

No anti-patterns found in code artifacts (`web_app.py`, `.ino`, `secrets.h.example`, `.gitignore`, `.env.example`).

---

## Human Verification Required

### 1. Hardware End-to-End Test

**Test:** Flash `bankongseton_rfid.ino` to an Arduino UNO R4 WiFi board wired to an MFRC522 reader. Configure `secrets.h` with school LAN credentials and a matching `ARDUINO_API_KEY` in Flask `.env`. Tap a student card.
**Expected:** Serial monitor shows "HTTP: card delivered — {UID}"; cashier UI receives and displays the `card_read` SocketIO event identically to a serial USB scan.
**Why human:** Requires physical hardware (Arduino UNO R4 WiFi + MFRC522), school LAN, and running Flask instance — cannot be automated from the development machine. Note: operator already confirmed Arduino IDE compilation (0 errors) in Plan 03 checkpoint.

---

## Gaps Summary

The phase goal is **functionally achieved**: all code artifacts are substantive and wired, all 4 requirements are implemented in the codebase, and human verification confirmed correct HTTP behavior (401/401/400/200) and successful Arduino IDE compilation.

**Single documentation gap:** `REQUIREMENTS.md` was not updated when Phase 18 closed. The phase-close commits (`f2a7368`, `caea071`) updated `STATE.md` and `ROADMAP.md` correctly but left ARDW-02 and ARDW-03 as `- [ ]` unchecked with 'Pending' status in the tracking table. This is a 2-line fix: flip the two checkboxes and update the two status cells.

This gap does not affect runtime behavior — it is purely a tracking document inconsistency.

---

## Commit Verification

All 4 code commits documented in summaries verified present in git history:

| Hash | Summary Description | Verified |
|------|---------------------|---------|
| `50c281d` | feat(18-01): add ARDUINO_API_KEY to env examples | ✓ exists |
| `8c4b3bf` | feat(18-01): add POST /api/arduino/card-read WiFi endpoint | ✓ exists |
| `6e8ce8b` | chore(18-02): update .gitignore to exclude Arduino secrets.h | ✓ exists |
| `3e28f11` | feat(18-02): create Arduino UNO R4 WiFi RFID firmware and secrets template | ✓ exists |

---

_Verified: 2026-03-07T06:30:00Z_
_Verifier: Claude (gsd-verifier)_
