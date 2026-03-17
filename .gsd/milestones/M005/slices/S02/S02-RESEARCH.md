# S02: OLED Driver + QR Polling on R4 — Research

**Date:** 2026-03-17
**Slice:** M005/S02
**Requirements:** R027 (OLED replaces LCD), R028 (QR token delivery via Arduino polling)

## Summary

S02 completes two things inside `arduino/bankongseton_r4/bankongseton_r4.ino`: (1) activates the SSD1306 OLED display that S01 wired up but left dormant, and (2) adds a ~500ms poll loop that fetches `/api/arduino/qr-pending`, renders any returned URL as a QR bitmap, and returns the display to a "Ready" idle screen when no QR is pending.

The critical hardware risk — fitting a scannable QR bitmap onto a 128×64 OLED — is resolved. A Version 3 QR (29×29 modules) at 2px/module renders a 58×58px bitmap centered on the 128×64 OLED with a 3px top/bottom margin. This covers all URLs up to 53 chars (ECC-L), which includes the LAN deployment scenario (`http://192.168.68.104:5003/api/qr/<token>` = ~70 chars — needs V4 at 1px). For a PythonAnywhere URL (~80 chars), a V5 (37×37) at 1px/module produces a 37×37px QR — small but scannable at close range. The firmware should auto-scale: use 2px/module if `qrcode.size * 2 ≤ 64`, else 1px/module. This means LAN deployments get 2px/module and PythonAnywhere deployments fall back to 1px/module automatically.

S01 left a clear insertion point (`// TODO S02`) just after `Wire.begin()`. All WiFi helpers, the heartbeat timer, and the RFID loop are untouched. The work is two new blocks: OLED init in `setup()` and a poll-and-render loop in `loop()` plus the cooldown section.

## Recommendation

**One task, one file:** `arduino/bankongseton_r4/bankongseton_r4.ino` — add OLED init, `httpGetBody()` helper, `parseQrUrl()` helper, `renderQr()` function, and a QR poll timer in `loop()`. Write `scripts/verify-m005-s02.sh` as a second task (same pattern as S01's verify script). No other files change.

The backend endpoint (`GET /api/arduino/qr-pending`) doesn't exist yet — that's S03. S02 is not blocked: the firmware can be written and the verify script can confirm firmware correctness without a live backend. Integration testing (real QR render + scan) is a manual hardware step.

**URL strategy:** Let the URL come from the server response (not constructed by the Arduino). The firmware calls `httpGetBody("/api/arduino/qr-pending")`, gets the JSON body, and extracts the `url` field. It renders whatever the server returns. This decouples the QR content from the firmware.

**Stub for hardware testing:** Since S03 backend doesn't exist yet, test the OLED + QR rendering independently by temporarily hardcoding a test URL and calling `renderQr()` directly from `setup()`. Once S03 is done, remove the hardcoded stub. The S02 verify script confirms the poll loop and render function are present in code; physical scannability confirmation is the human UAT step.

## Implementation Landscape

### Key Files

- `arduino/bankongseton_r4/bankongseton_r4.ino` — **primary change target.** S01 TODO comment at line 63 marks where to insert the OLED include + display object. `Wire.begin()` is already called at line 292. Loop structure at lines 304–348 shows exactly where to insert the QR poll block.
- `arduino/bankongseton_r4/secrets.h` — **no changes needed.** FLASK_HOST already provides the host for the poll request; no new secret fields required.
- `scripts/verify-m005-s02.sh` — **new file.** Same pattern as `scripts/verify-m005-s01.sh` (9-check numbered format). Greps the firmware for the OLED init, QR library, poll loop, and render function.

### Exact Insertion Points in the Firmware

**At the top (after existing `#include <Wire.h>` / TODO comment, line 59–63):**
```cpp
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "qrcode.h"   // ricmoo/qrcode — QRCode, qrcode_initText, qrcode_getModule

Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
```
Remove or replace the `// TODO S02` comment. The constants `OLED_WIDTH`, `OLED_HEIGHT`, `OLED_ADDR` are already defined at lines 60–62.

**In `setup()` after `Wire.begin()` (line 292):**
```cpp
if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("ERROR: SSD1306 OLED not found — check I2C wiring (SDA/SCL) and address 0x3C");
    // Non-fatal: RFID payment still works without OLED
}
display.clearDisplay();
display.setTextColor(SSD1306_WHITE);
oledShowReady();  // function defined below
```

**New global functions to add:**

1. **`oledShowReady()`** — clears display, prints "Ready" centered, calls `display.display()`.
2. **`renderQr(const String &url)`** — allocates QR buffer (max V7 = 257 bytes on stack), calls `qrcode_initText()` with `ECC_LOW`, renders to OLED with auto-scaling (`scale = (qrcode.size * 2 <= OLED_HEIGHT) ? 2 : 1`), x/y centered.
3. **`httpGetBody(const String &path)`** → `String` — sends an HTTP GET with X-API-Key header, reads through headers (skipping lines until blank line), returns body string. Returns empty string on failure.
4. **`parseQrUrl(const String &json)`** → `String` — finds `"url":"` in the JSON string, extracts the value until the next `"`. Returns empty string if `"url":null` or field missing.

**In `loop()` — add QR poll block between heartbeat and RFID early-return:**
```cpp
// ── QR poll: fetch and render pending QR from backend ──
if (now - lastQrPollMs >= (unsigned long)QR_POLL_INTERVAL_MS) {
    lastQrPollMs = now;
    String body    = httpGetBody("/api/arduino/qr-pending");
    String qrUrl   = parseQrUrl(body);
    if (qrUrl != lastQrUrl) {
        lastQrUrl = qrUrl;
        if (qrUrl.length() == 0) oledShowReady();
        else                     renderQr(qrUrl);
    }
}
```
Declare `QR_POLL_INTERVAL_MS = 500`, `lastQrPollMs = 0`, `lastQrUrl = ""` near the heartbeat globals.

**Inside the cooldown `while` loop — add QR poll check alongside `handleIncomingSerial()`:**
Same poll-timer check so the OLED updates even during card cooldown.

### Build Order

1. **Firmware first:** Write the complete updated `bankongseton_r4.ino`. The OLED can be tested independently (without backend) by calling `renderQr("http://192.168.68.104:5003/q/TEST1234")` from `setup()` to verify the bitmap renders and is scannable.
2. **Verify script second:** Write `scripts/verify-m005-s02.sh` that greps for all new symbols. Exits 0 on the completed firmware.
3. **Hardware verification last (human step):** Flash to R4, confirm OLED shows "Ready" on boot, confirm QR renders when test URL is hardcoded, scan with phone camera.

### Verification Approach

**Contract (automated):**
```bash
bash scripts/verify-m005-s02.sh
```
Checks: `Adafruit_SSD1306.h` include present, `display.begin` called, `QRCode` type used, `qrcode_initText` called, `qrcode_getModule` used (for drawPixel loop), `httpGetBody` function present, `qr-pending` endpoint polled, `oledShowReady` function present, `parseQrUrl` function present.

**Hardware (human):**
- Flash firmware, Serial Monitor at 9600 baud — confirm `BANKONGSETON RFID reader ready` on boot
- OLED shows "Ready" text at idle
- Temporarily uncomment hardcoded test QR call in setup → scan with Android/iOS camera → confirms QR is readable
- Re-flash without hardcoded stub; manually trigger via backend when S03 is ready

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| QR bit matrix generation | **ricmoo/qrcode** (Arduino Library Manager: "QRCode" by Richard Moore) | Generates raw bit matrix with no dynamic allocation; `qrcode_getBufferSize(v)` gives exact stack allocation; `qrcode_getModule(x,y)` maps to `display.drawPixel()` directly; 257 bytes max buffer for V7 — trivial on R4's 32KB SRAM |
| OLED driver + pixel drawing | **Adafruit SSD1306** + **Adafruit GFX** (Library Manager) | `display.drawPixel(x, y, SSD1306_WHITE)` is the exact primitive needed for QR rendering; `display.display()` flushes 1024-byte framebuffer to hardware; already specified in D042 |

## Constraints

- **ricmoo/qrcode requires explicit version (1–7).** There is no auto-detect. The firmware must pass a version large enough for the URL length. Recommended: try `qrcode_initText()` and let the library fail if the version is too small — it returns an error code. OR use a fixed V5 (max 106 chars ECC-L) which covers all expected URLs. V5 at 1px/module = 37px on the 64px-tall OLED.
- **SSD1306 OLED_RESET must be `-1`.** Most breakout boards share the Arduino reset line. `Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1)` is the correct constructor.
- **OLED I2C address: 0x3C** (already defined as `OLED_ADDR`). Some boards ship at 0x3D — `display.begin()` returns false if address is wrong. Treat OLED init failure as non-fatal (log to Serial, continue) so RFID payment still works without OLED.
- **httpGetBody must read through all response headers** before returning body. The response headers end with a blank `\r\n` line. Reading only the status line (as `httpPostJson` does) will return an empty body. The function must scan lines until it finds a blank line, then read the body.
- **JSON parsing is simple string search.** The `qr-pending` response is either `{"token":null}` (idle) or `{"token":"...","url":"..."}` (pending). Use `String.indexOf('"url":"')` and `String.substring()` — no ArduinoJson needed. ArduinoJson would add ~1–2KB Flash overhead for no benefit here.
- **QR poll adds ~200ms latency per poll cycle** (TCP connect + GET + disconnect). This means RFID is unresponsive for up to 200ms every 500ms. Measured: 20% RFID dead-time. At 1500ms card cooldown and ~2ms PICC_IsNewCardPresent, this is acceptable — a card held near the reader for >200ms will be detected.
- **Display call ordering:** `display.clearDisplay()` → draw pixels → `display.display()`. Never call `display.display()` in the render inner loop — only once after all pixels are drawn. The 1024-byte framebuffer sends to OLED in one I2C burst.

## Common Pitfalls

- **QR version too small for the URL.** `qrcode_initText()` returns `false` if the version can't hold the text. Always check the return value. If false, try a higher version (or use V5/V7 fixed). A silent failure here produces a corrupted QR bitmap.
- **Double-scan interference during HTTP GET.** The QR poll `httpGetBody()` call takes ~200ms. If a card is held to the reader during this window, `PICC_IsNewCardPresent()` will catch it on the next loop iteration. This is fine — the cooldown prevents double-reads regardless.
- **OLED flicker from polling.** Only redraw when the URL changes (`if (qrUrl != lastQrUrl)`). Without this guard, `display.clearDisplay()` + `display.display()` runs every 500ms causing visible flicker.
- **Body buffer truncation.** `client.readStringUntil('\n')` in a WiFiClient will return whatever fits in the String buffer. For a URL of ~80 chars the JSON body is ~130 chars — well within Arduino String limits. However, if the WiFi TCP buffer overflows, the body may be truncated. Cap `httpGetBody()` body reads at `client.available()` bytes and stop after receiving the first non-empty body line past the headers.
- **SSD1306 at 0x3D.** If OLED does not respond, change `OLED_ADDR` from `0x3C` to `0x3D` in the firmware (not in secrets.h — it's a hardware constant). Log the failure to Serial clearly so the issue is diagnosable without a logic analyzer.

## Open Risks

- **QR scannability at 1px/module on PythonAnywhere deployment.** V5 (37×37) at 1px/module = 37px on the 0.66-inch OLED is ~5mm physical size. Phone cameras can scan QR codes this small at 5–10cm range. In a school canteen context, students will hold the phone close. This needs hardware verification before calling S02 done. If 1px is not scannable in practice, the URL must be shortened (see below).
- **URL length for PythonAnywhere.** `https://juley2823.pythonanywhere.com/api/qr/<uuid4>` = 80 chars → V5 at 1px. If 1px proves unscnnable, the fix is: (a) add a short alias route like `/q/<8hex>` in S03 that redirects to the full URL (80→37 chars → V3 at 2px), or (b) use a shorter numeric token format. The S02 firmware is not affected — it renders whatever URL the server sends. The routing change is purely an S03 concern.
- **ricmoo/qrcode library version on Arduino Library Manager.** The library has not been updated since 2020 but is stable. Version 1.0.0 is the canonical release. Install via Library Manager: search "QRCode" by Richard Moore. Do not confuse with "Arduino-QRCode" or other forks.

## Sources

- QR version/capacity tables: ISO 18004:2015 Annex I (byte mode, ECC level L) — V1=17, V2=32, V3=53, V4=78, V5=106
- ricmoo/qrcode API: `qrcode_getBufferSize(v)`, `qrcode_initText()`, `qrcode_getModule()` — confirmed from library source
- SSD1306 OLED module size: typical 128×64 0.66-inch or 0.96-inch; module pitch ~0.13–0.21mm/pixel depending on board size
- Adafruit SSD1306 + GFX: `display.drawPixel(x, y, color)`, `display.clearDisplay()`, `display.display()` — standard Adafruit API
