---
id: T01
parent: S02
milestone: M005
provides:
  - OLED driver activation in R4 firmware (Adafruit SSD1306 + Adafruit GFX)
  - QR code rendering via ricmoo/qrcode library with auto-scale and centered display
  - 500ms QR poll loop hitting /api/arduino/qr-pending in both main loop and cooldown while loop
  - httpGetBody() GET helper with header-skip and X-API-Key auth
  - parseQrUrl() JSON field extractor for the qr-pending response
  - oledShowReady() idle screen function
  - Non-fatal OLED init with Serial error log
  - scripts/verify-m005-s02.sh — 9-check contract verification script
key_files:
  - arduino/bankongseton_r4/bankongseton_r4.ino
  - scripts/verify-m005-s02.sh
key_decisions:
  - Placed Adafruit_GFX.h and Adafruit_SSD1306.h includes between Wire.h and WiFiS3.h (Wire must precede OLED; WiFiS3 last to avoid namespace conflicts)
  - display.display() called exactly once per renderQr() invocation, outside the pixel loop — avoids I2C bus saturation
  - OLED init failure is explicitly non-fatal: Serial message printed, execution continues with RFID-only mode
  - Used now2 variable in cooldown loop (not now) to avoid shadowing the outer loop's now variable
patterns_established:
  - QR poll guard pattern: check `qrUrl != lastQrUrl` before redrawing OLED to prevent flicker on unchanged state
  - httpGetBody() header-skip pattern: read lines until blank line (\r\n trimmed to empty) to consume all HTTP response headers before body
observability_surfaces:
  - Serial @ 9600 baud: "OLED: init failed 0x3C — check I2C wiring (non-fatal)" on OLED absence/fault
  - Serial @ 9600 baud: "QR: rendering v<N> scale=<N>px url=<url>" on each new QR render
  - Serial @ 9600 baud: "QR: idle (Ready)" on each QR clear (transition to Ready state)
  - Serial @ 9600 baud: "QR: version too small for URL length — max 154 chars (V7 ECC-L)" on URL capacity overflow
duration: ~30m
verification_result: passed
completed_at: 2026-03-17
blocker_discovered: false
---

# T01: Add OLED driver, QR render, and poll loop to R4 firmware

**Added Adafruit SSD1306 OLED driver, ricmoo QR rendering, and 500ms /api/arduino/qr-pending poll loop to R4 firmware; all 9 contract checks pass.**

## What Happened

Replaced the `// TODO S02` comment block in `bankongseton_r4.ino` with the full OLED + QR implementation:

1. **Header comment** — added the three new library names; removed the "deferred to S02" line.
2. **Includes** — inserted `<Adafruit_GFX.h>`, `<Adafruit_SSD1306.h>`, and `"qrcode.h"` between `<Wire.h>` and `<WiFiS3.h>`.
3. **Display global** — replaced the OLED placeholder comment with `Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1)`.
4. **QR poll globals** — added `QR_POLL_INTERVAL_MS = 500`, `lastQrPollMs`, and `lastQrUrl` near `lastHeartbeatMs`.
5. **Four new functions** (`oledShowReady`, `renderQr`, `httpGetBody`, `parseQrUrl`) added before `setup()`.
6. **OLED init in `setup()`** — after `Wire.begin()`, calls `display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)` with non-fatal failure logging; on success calls `oledShowReady()`.
7. **QR poll in main `loop()`** — inserted after heartbeat block, before the RFID early-exit; uses existing `now` variable.
8. **QR poll in cooldown `while` loop** — same logic with `now2` to avoid shadowing.
9. **Verify script** — wrote `scripts/verify-m005-s02.sh` with all 9 grep checks plus diagnostic signal documentation.
10. **S02-PLAN.md observability gap** — added a failure-path verification step to the Verification section.

## Verification

Ran all 9 checks manually and via `bash scripts/verify-m005-s02.sh` (from project root):

```
[1/9] Adafruit_SSD1306.h included...     PASS
[2/9] qrcode.h included...               PASS
[3/9] display.begin() called...          PASS
[4/9] oledShowReady() present...         PASS
[5/9] renderQr() present...              PASS
[6/9] httpGetBody() present...           PASS
[7/9] qr-pending wired...                PASS
[8/9] parseQrUrl() present...            PASS
[9/9] TODO S02 removed...                PASS
✓ All S02 contract checks passed.
```

## Diagnostics

- Connect Arduino Serial Monitor at 9600 baud after flashing.
- **OLED absent/fault:** prints `OLED: init failed 0x3C — check I2C wiring (non-fatal)` then boots normally.
- **QR rendered:** prints `QR: rendering v<N> scale=<N>px url=<url>` for each new URL.
- **QR cleared:** prints `QR: idle (Ready)`.
- **URL too long:** prints `QR: version too small for URL length — max 154 chars (V7 ECC-L)` and falls back to Ready.
- **Backend unreachable:** `httpGetBody` returns `""` → `parseQrUrl` returns `""` → `oledShowReady()` called, no crash.

## Deviations

None — implementation follows T01-PLAN.md exactly.

## Known Issues

None. Hardware UAT (flash → scan QR with phone) is deferred to human tester per slice plan.

## Files Created/Modified

- `arduino/bankongseton_r4/bankongseton_r4.ino` — Added OLED driver, QR render, poll loop, 4 new functions; removed TODO S02; updated library header comment
- `scripts/verify-m005-s02.sh` — New 9-check contract verification script with diagnostic signal documentation
- `.gsd/milestones/M005/slices/S02/S02-PLAN.md` — Added failure-path diagnostic verification step (pre-flight fix)
