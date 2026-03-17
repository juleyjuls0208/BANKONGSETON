# S02: OLED Driver + QR Polling on R4

**Goal:** Activate the SSD1306 OLED in `bankongseton_r4.ino` and add a 500ms poll loop that fetches `/api/arduino/qr-pending`, renders the returned URL as a QR bitmap, and returns to "Ready" idle when no QR is pending.
**Demo:** `bash scripts/verify-m005-s02.sh` exits 0. On real hardware: OLED shows "Ready" on boot; hardcoded test QR renders and is scannable by a phone camera.

## Must-Haves

- `arduino/bankongseton_r4/bankongseton_r4.ino` includes `Adafruit_SSD1306.h`, initialises the display in `setup()`, and calls `oledShowReady()` at idle
- `renderQr(url)` auto-scales (2px/module if `size*2 ≤ OLED_HEIGHT`, else 1px), draws each QR module with `display.drawPixel()`, calls `display.display()` once after all pixels
- `httpGetBody(path)` sends GET with X-API-Key header, reads through all response headers (until blank line), returns body string
- `parseQrUrl(json)` extracts `url` field from `{"token":"...","url":"..."}` or returns empty string for `{"token":null}`
- QR poll fires every 500ms in main `loop()` AND inside the cooldown `while` loop; OLED redraws only when URL changes (`lastQrUrl` guard)
- `scripts/verify-m005-s02.sh` exits 0 on the completed firmware (9 checks)

## Proof Level

- This slice proves: contract
- Real runtime required: no (firmware and verify script are the deliverable; hardware scan is human UAT)
- Human/UAT required: yes — flash to R4, confirm OLED shows "Ready" on boot, uncomment hardcoded test URL, scan with phone camera

## Verification

- `bash scripts/verify-m005-s02.sh` — exits 0 with all 9 checks passing
- Human UAT: flash firmware → Serial Monitor shows `BANKONGSETON RFID reader ready` → OLED shows "Ready" → uncomment hardcoded test URL call in `setup()` → scan with Android/iOS camera → confirms scannable → re-flash without stub
- **Failure-path / diagnostic check:** If OLED is absent or mis-wired, Arduino Serial Monitor at 9600 baud must print `OLED: init failed 0x3C — check I2C wiring (non-fatal)` and continue booting (RFID still works). Verify by disconnecting OLED I2C lines and checking Serial output. If a URL exceeds 154 chars, Serial must print `QR: version too small for URL length — max 154 chars (V7 ECC-L)` and fall back to "Ready" display. If `/api/arduino/qr-pending` is unreachable, `httpGetBody` returns "" → `parseQrUrl` returns "" → `oledShowReady()` is called — no crash.

## Observability / Diagnostics

- Runtime signals: Serial at 9600 baud — `OLED: init failed 0x3C — check I2C wiring (non-fatal)` on OLED fault; `QR: rendering v<N> scale=<N>px url=<url>` on each new QR; `QR: idle (Ready)` on each clear; `QR: version too small for URL length` if URL exceeds V7 capacity
- Failure visibility: OLED init failure is non-fatal and logged clearly; `qrcode_initText` failure per version logged so wiring and URL-length faults are diagnosable from Serial Monitor without oscilloscope
- Redaction constraints: none (no secrets rendered to OLED or Serial)

## Integration Closure

- Upstream surfaces consumed: `arduino/bankongseton_r4/bankongseton_r4.ino` (S01 firmware — RC522 loop, WiFi helpers, heartbeat, OLED constants, `Wire.begin()`); `arduino/bankongseton_r4/secrets.h` (`FLASK_HOST` used by `httpGetBody`)
- New wiring introduced: OLED display activated; `GET /api/arduino/qr-pending` poll loop wired to display render path
- What remains before end-to-end: S03 must implement `GET /api/arduino/qr-pending` and `POST /cashier/api/qr-generate`; S04 apps must scan the rendered QR

## Tasks

- [x] **T01: Add OLED driver, QR render, and poll loop to R4 firmware** `est:1h`
  - Why: Core S02 deliverable — activates the OLED and implements the QR polling/rendering loop that R027 and R028 require
  - Files: `arduino/bankongseton_r4/bankongseton_r4.ino`
  - Do: Replace `// TODO S02` comment with `Adafruit_SSD1306.h`/`qrcode.h` includes and display global; add `oledShowReady()`, `renderQr()`, `httpGetBody()`, `parseQrUrl()` functions; add OLED init to `setup()`; add QR poll block to main `loop()` and inside cooldown `while` loop; add QR poll globals — see T01-PLAN.md for full steps and constraints
  - Verify: `grep -q 'Adafruit_SSD1306.h' arduino/bankongseton_r4/bankongseton_r4.ino && grep -q 'qr-pending' arduino/bankongseton_r4/bankongseton_r4.ino && grep -q 'renderQr' arduino/bankongseton_r4/bankongseton_r4.ino`
  - Done when: All 4 new functions present, poll loop in main loop AND cooldown loop, OLED init in setup(), auto-scale in renderQr(), `// TODO S02` comment removed

- [ ] **T02: Write and run the S02 contract verify script** `est:20m`
  - Why: Provides the automated stopping condition for this slice; the same numbered-check pattern as S01's verify script
  - Files: `scripts/verify-m005-s02.sh`
  - Do: Write a 9-check bash script (same structure as `scripts/verify-m005-s01.sh`) that greps the firmware for all new S02 symbols; make it executable; run it — see T02-PLAN.md for exact checks
  - Verify: `bash scripts/verify-m005-s02.sh` exits 0
  - Done when: Script exits 0, all 9 checks print PASS

## Files Likely Touched

- `arduino/bankongseton_r4/bankongseton_r4.ino`
- `scripts/verify-m005-s02.sh`
