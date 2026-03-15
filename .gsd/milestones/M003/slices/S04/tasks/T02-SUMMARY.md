---
id: T02
parent: S04
milestone: M003
provides:
  - arduino/README-wireless.md — complete standalone wireless deployment guide (hardware, wiring, secrets.h field-by-field, flashing, powerbank selection, verification, troubleshooting)
  - scripts/verify-m003-s04.sh — 8-check grep assertion script; exits 0; executable; covers firmware heartbeat structure (a–d) and README content (e–h)
key_files:
  - arduino/README-wireless.md
  - scripts/verify-m003-s04.sh
  - .gsd/milestones/M003/slices/S04/tasks/T02-PLAN.md (observability gap fix added)
key_decisions:
  - README follows arduino/bankongseton_nfc_r3/README.md section structure and table markdown exactly — consistent format for anyone maintaining either README
  - Verify script accumulates PASS/FAIL counts (same pattern as verify-m003-s03.sh) rather than exit-on-first-failure — gives full picture of which specific assertions fail rather than stopping at the first miss
patterns_established:
  - Deployment README pattern: hardware table → wiring tables with SPI mode callout note → libraries table → secrets.h field table with port/key callouts → flashing steps → verification (Serial Monitor + UI badge) → powerbank selection table → troubleshooting table
  - Verify script pattern: check() function with eval + PASS/FAIL counters; grouped output by concern (firmware / docs); final Results line + named "all N checks passed" message
observability_surfaces:
  - bash scripts/verify-m003-s04.sh — single-command exit-0 proof; prints ✓/✗ per assertion so future agents see exactly which file or pattern is missing
  - grep "5003\|ARDUINO_API_KEY\|powerbank" arduino/README-wireless.md — spot-check the three deployment-critical callouts without running the full script
  - No runtime signal change — this task produces documentation and a verification script only; T01's Serial/Flask/UI signals are unaffected
duration: ~20m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Write README-wireless.md and verify script

**`arduino/README-wireless.md` written and `scripts/verify-m003-s04.sh` exits 0 — 8/8 checks pass, S03 regression clean.**

## What Happened

Pre-flight: added `## Observability Impact` section to T02-PLAN.md (flagged gap).

Step 1 — README: wrote `arduino/README-wireless.md` following the R3 README's section order and table markdown style. Eight sections: Hardware Required, Wiring (PN532 SPI + LCD I2C + Buzzer), Required Libraries, secrets.h Configuration (field table with port-5003 and ARDUINO_API_KEY callouts), Flashing (Arduino IDE step-by-step), Verification (Serial Monitor boot line + 30s heartbeat line + badge-goes-green), Powerbank Selection (table + prose on why 2A/10Ah/name-brand matters), Troubleshooting (symptom/cause/fix table), Pin Summary. Port 5003 and `ARDUINO_API_KEY` are explicitly named — not generic `<port>` or vague "matches the env var".

Step 2 — Verify script: wrote `scripts/verify-m003-s04.sh` with 8 checks in two groups: Group 1 firmware (a–d: lastHeartbeatMs present, httpPostJson heartbeat call, HEARTBEAT_INTERVAL_MS not stub, ensureWiFi present); Group 2 docs (e–h: README exists, README contains "5003", README contains "ARDUINO_API_KEY", README contains "powerbank" case-insensitive). Same check()/PASS/FAIL pattern as verify-m003-s03.sh.

Step 3 — chmod +x and ran both scripts.

## Verification

```
bash scripts/verify-m003-s04.sh
→ 8 passed, 0 failed — verify-m003-s04: all 8 checks passed ✓

bash scripts/verify-m003-s03.sh
→ 12 passed, 0 failed — M003/S03 verification PASSED ✓
```

Spot-checks:
- `test -f arduino/README-wireless.md` → OK
- `grep "5003" arduino/README-wireless.md` → matches in secrets.h config table and FLASK_HOST callout
- `grep "ARDUINO_API_KEY" arduino/README-wireless.md` → matches in secrets.h config table and troubleshooting table

## Diagnostics

- `bash scripts/verify-m003-s04.sh` — each check prints ✓/✗ with label; FAIL count shows exactly which assertion failed; exit 1 on any failure
- Check (e) fails → README file absent; create it or check working directory
- Checks (a–d) fail → T01 heartbeat loop not applied; re-check bankongseton_rfid.ino
- Check (f) fails → README uses 5000 or generic `<port>`; add explicit "5003"
- Check (g) fails → README doesn't name `ARDUINO_API_KEY`; add Flask env var name to secrets.h section

## Deviations

none — README structure matched the plan section-for-section; verify script uses accumulated counters (same as S03 pattern) rather than `set -e` exit-on-first-failure, which gives better diagnostic output

## Known Issues

none

## Files Created/Modified

- `arduino/README-wireless.md` — complete standalone wireless deployment guide (8 sections, 100+ lines)
- `scripts/verify-m003-s04.sh` — 8-check assertion script, chmod +x, exits 0
- `.gsd/milestones/M003/slices/S04/tasks/T02-PLAN.md` — added `## Observability Impact` section (pre-flight gap fix)
