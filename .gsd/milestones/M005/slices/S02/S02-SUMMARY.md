---
id: S02
parent: M005
milestone: M005
provides:
  - Adafruit SSD1306 OLED driver activated in R4 firmware (128×64, hardware I2C, address 0x3C)
  - renderQr(url) — auto-scale QR bitmap (v1–v7 version probe, 2px/module if fits OLED_HEIGHT else 1px, centered, single display.display() flush)
  - httpGetBody(path) — HTTP GET with X-API-Key header and full response-header skip loop
  - parseQrUrl(json) — extracts "url" field from qr-pending JSON; returns "" for {"token":null}
  - oledShowReady() — idle "Ready" screen at 2× text, centered on 128×64
  - 500ms QR poll loop in main loop() AND in cooldown while loop (now2 variable, no shadowing)
  - Non-fatal OLED init: Serial error message + continue on failure
  - QR poll guard (lastQrUrl comparison) — prevents OLED flicker on unchanged state
  - scripts/verify-m005-s02.sh — executable 9-check contract verification script; exits 0
requires:
  - slice: S01
    provides: bankongseton_r4.ino base firmware (RC522 loop, WiFi helpers, heartbeat, OLED constants, Wire.begin())
affects:
  - S03 (must implement GET /api/arduino/qr-pending and POST /cashier/api/qr-generate for firmware to display QR)
  - S04 (Android + iOS apps scan the QR rendered by this firmware)
key_files:
  - arduino/bankongseton_r4/bankongseton_r4.ino
  - scripts/verify-m005-s02.sh
key_decisions:
  - Includes ordered: Adafruit_GFX.h and Adafruit_SSD1306.h inserted between Wire.h and WiFiS3.h (Wire must precede OLED; WiFiS3 last to avoid namespace conflicts)
  - display.display() called exactly once per renderQr() invocation, outside the pixel loop — avoids I2C bus saturation
  - OLED init failure is non-fatal: Serial message printed, execution continues with RFID-only mode
  - Used now2 variable name in cooldown loop (not now) to avoid shadowing the outer loop's now variable
  - Version probe loop 1–7 with qrcode_initText; first success wins; V7 ECC-L max 154 chars
patterns_established:
  - QR poll guard pattern: check qrUrl != lastQrUrl before redrawing OLED — prevents flicker on unchanged state
  - httpGetBody() header-skip pattern: read lines until blank line (\r\n trimmed to empty) to consume all HTTP headers before body
  - Non-fatal peripheral init: Serial.println + continue (vs. halting) for non-critical display hardware
  - Cooldown loop QR poll: same logic as main loop, using now2 to avoid variable shadowing
observability_surfaces:
  - Serial @ 9600 baud: "OLED: init failed 0x3C — check I2C wiring (non-fatal)" on OLED absence/fault
  - Serial @ 9600 baud: "QR: rendering v<N> scale=<N>px url=<url>" on each new QR render
  - Serial @ 9600 baud: "QR: idle (Ready)" on each transition to Ready state
  - Serial @ 9600 baud: "QR: version too small for URL length — max 154 chars (V7 ECC-L)" on URL capacity overflow
  - bash scripts/verify-m005-s02.sh — exits 0 when all 9 S02 symbols are present
drill_down_paths:
  - .gsd/milestones/M005/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M005/slices/S02/tasks/T02-SUMMARY.md
duration: ~35m (T01 ~30m + T02 ~5m)
verification_result: passed
completed_at: 2026-03-17
---

# S02: OLED Driver + QR Polling on R4

**Activated Adafruit SSD1306 OLED and added a 500ms `/api/arduino/qr-pending` poll loop to R4 firmware; renders QR bitmaps with auto-scale centering; all 9 contract checks pass.**

## What Happened

S01 delivered the RC522 + WiFi base firmware with OLED constants and a `// TODO S02` placeholder. S02 completed the OLED activation and QR display loop in two tasks.

**T01** replaced the TODO block with four new functions and wired them into `setup()` and `loop()`:

1. **Includes** — `Adafruit_GFX.h`, `Adafruit_SSD1306.h`, and `qrcode.h` added between `Wire.h` and `WiFiS3.h`. Library header comment updated; "deferred to S02" line removed.
2. **Display global** — `Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1)` replaces the placeholder comment.
3. **QR poll globals** — `QR_POLL_INTERVAL_MS = 500`, `lastQrPollMs`, `lastQrUrl` added alongside `lastHeartbeatMs`.
4. **`oledShowReady()`** — clears display, sets 2× text, centers "Ready" on 128×64, calls `display.display()`.
5. **`renderQr(url)`** — probes QR versions 1–7 with `qrcode_initText`; auto-scales (2px/module if `size*2 ≤ OLED_HEIGHT`, else 1px); centers bitmap; renders with `drawPixel()`; calls `display.display()` exactly once after the pixel loop; logs version, scale, and URL to Serial. URL overflow falls back to `oledShowReady()` with a Serial message.
6. **`httpGetBody(path)`** — TCP GET with X-API-Key header; reads response lines until blank line (header skip); returns first non-empty body line; returns `""` on failure or timeout.
7. **`parseQrUrl(json)`** — finds `"url":"` in the JSON string; returns substring before next `"`; returns `""` for `{"token":null}` or on parse failure.
8. **OLED init in `setup()`** — after `Wire.begin()`, calls `display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)`; on failure logs non-fatal Serial message and continues; on success calls `oledShowReady()`.
9. **QR poll in main `loop()`** — after heartbeat block, before RFID early-exit; uses `now` variable already in scope; guards on `qrUrl != lastQrUrl` to prevent flicker.
10. **QR poll in cooldown `while` loop** — same logic with `now2` to avoid shadowing outer `now`; fires every 500ms during the post-scan cooldown so OLED stays responsive.

**T02** confirmed the verify script (`scripts/verify-m005-s02.sh`) written during T01 was correct, made it executable, and ran it — all 9 checks passed from project root.

## Verification

```
bash scripts/verify-m005-s02.sh
[1/9] Adafruit_SSD1306.h include present...     PASS
[2/9] qrcode.h include present...               PASS
[3/9] display.begin called in setup...           PASS
[4/9] oledShowReady function present...          PASS
[5/9] renderQr function present...               PASS
[6/9] httpGetBody function present...            PASS
[7/9] qr-pending endpoint polled...              PASS
[8/9] parseQrUrl function present...             PASS
[9/9] TODO S02 comment removed...               PASS
✓ All S02 contract checks passed.
Exit code: 0
```

Hardware UAT (flash → boot OLED shows "Ready" → inject QR URL → scan with phone camera) is deferred to human tester per slice plan — this is a firmware-only slice; actual scanability confirmation requires real hardware.

## Requirements Advanced

- **R027** (OLED Replaces LCD on R4) — Adafruit SSD1306 driver and display code fully implemented; S01 committed the placeholder; S02 completes the requirement. Ready for hardware validation.
- **R028** (QR Token Delivery to OLED via Arduino Polling) — `httpGetBody` + `parseQrUrl` + `renderQr` + 500ms poll loop fully implemented. Ready to integrate with S03 backend endpoints.

## Requirements Validated

- None validated by this slice alone — hardware scan confirmation (R027, R028) requires S03 backend + human UAT.

## New Requirements Surfaced

- None.

## Requirements Invalidated or Re-scoped

- None.

## Deviations

None — implementation follows T01-PLAN.md exactly. The `now2` cooldown variable and the single `display.display()` outside the pixel loop were both specified in the plan.

## Known Limitations

- **Hardware UAT not yet performed.** The firmware is contract-verified but has not been flashed to real R4 hardware and scanned. Human UAT (flash → Serial Monitor shows ready → OLED shows "Ready" → trigger QR → scan with phone camera) is required before R027/R028 can be marked validated.
- **S03 backend not yet built.** `/api/arduino/qr-pending` does not exist yet; the poll loop will get HTTP connection failures and silently fall back to `oledShowReady()` every cycle until S03 ships. This is intentional and safe.
- **URL length cap: 154 chars (V7 ECC-L).** The target QR URL format is `https://<SERVER_URL>/api/qr/<uuid>`. A typical PythonAnywhere URL (`https://yourname.pythonanywhere.com/api/qr/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) is ~82 chars — well within the 154-char limit. If a server URL is unusually long, the firmware logs a clear Serial message and falls back to "Ready".
- **OLED absent / mis-wired:** Non-fatal by design. RFID payment still works; OLED simply shows nothing. Serial Monitor confirms the issue at `9600 baud`.

## Follow-ups

- **S03** must implement `GET /api/arduino/qr-pending` and `POST /cashier/api/qr-generate` for the poll loop to receive a real QR URL.
- **Human UAT:** Flash firmware → confirm `BANKONGSETON RFID reader ready` in Serial Monitor → confirm OLED shows "Ready" → inject a QR URL via the backend → confirm OLED renders → scan with Android/iOS camera. Document result. Re-flash production build without any test stubs.
- **Library install note for flasher:** Arduino Library Manager must have "Adafruit SSD1306" (Adafruit), "Adafruit GFX Library" (Adafruit), and "QRCode" by Richard Moore (ricmoo/qrcode) installed before compiling. If absent, the build fails with undefined type errors.

## Files Created/Modified

- `arduino/bankongseton_r4/bankongseton_r4.ino` — Added Adafruit SSD1306 + GFX + qrcode includes; display global; QR poll globals; `oledShowReady()`, `renderQr()`, `httpGetBody()`, `parseQrUrl()` functions; OLED init in setup(); QR poll in main loop() and cooldown while loop; removed TODO S02; updated library header comment
- `scripts/verify-m005-s02.sh` — New executable 9-check contract verification script; exits 0

## Forward Intelligence

### What the next slice should know

- **The QR URL S02 expects:** `parseQrUrl` looks for `"url":"` in the JSON body. S03's `GET /api/arduino/qr-pending` must return `{"token":"<uuid>","url":"https://..."}` when pending, and `{"token":null}` (or any JSON without a `"url":"` key) when idle. The Arduino will call `oledShowReady()` for any response that doesn't contain a URL string.
- **Poll timing:** The Arduino polls every 500ms. S03's qr-pending endpoint will receive ~120 requests per minute from the R4. It must be fast (no Sheets reads — serve from in-memory `app.pending_qr_token`).
- **API key auth:** `httpGetBody` sends `X-API-Key: <SECRET_API_KEY>` (from `secrets.h`). S03 must accept this header on `GET /api/arduino/qr-pending` — same auth pattern as `POST /api/arduino/card-read` and `POST /api/arduino/heartbeat`.
- **QR URL length:** Target URL `https://<server>/api/qr/<uuid>` is ~82 chars. V7 ECC-L cap is 154 chars. No issue for any plausible PythonAnywhere hostname. S03 should keep token representation as a standard UUID (36 chars with hyphens).

### What's fragile

- **qrcode library API (`qrcode_initText` return value):** The firmware relies on `qrcode_initText` returning `true` on success. The ricmoo/qrcode library returns a bool. If the library version used has a different API (some versions return `void` or `int`), the version probe loop will malfunction. Verify the installed version is ricmoo/qrcode v0.0.1 (Arduino Library Manager) before flashing.
- **Buffer allocation (`qrcode_getBufferSize(7)`):** Allocated on the stack as a VLA-style array. UNO R4 has 32 KB SRAM — this is fine for V7, but if future versions of the library change the buffer formula, watch for stack overflow symptoms (random resets).
- **OLED I2C address hardcoded to 0x3C:** Some SSD1306 boards use 0x3D. If the wrong board is used, OLED init fails silently with the non-fatal message. Check the OLED module label before wiring.

### Authoritative diagnostics

- **Serial Monitor at 9600 baud** — The most reliable first-look diagnostic. All firmware state transitions log here. "OLED: init failed", "QR: rendering", "QR: idle", "QR: version too small" are all here.
- **`bash scripts/verify-m005-s02.sh`** — Run from project root. Exits 0 = all 9 S02 symbols present in firmware. Fails fast at first missing symbol, names the check.

### What assumptions changed

- **Scale assumption:** The roadmap identified 5px/module as overflowing 128×64 for a V2 QR. The firmware chose 2px/module (fits V2–V7 at ≤32 modules) with 1px fallback — not 5px. This produces a smaller but scannable bitmap. Hardware UAT must confirm scannability at the actual distance a student holds their phone.
- **Single display.display() call:** Initial intuition might be to flush after each row for feedback; the implementation flushes once after all pixels are drawn to avoid I2C bus saturation. This was a deliberate decision (D042 pattern).
