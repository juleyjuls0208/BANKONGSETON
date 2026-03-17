---
estimated_steps: 8
estimated_files: 1
---

# T01: Add OLED driver, QR render, and poll loop to R4 firmware

**Slice:** S02 — OLED Driver + QR Polling on R4
**Milestone:** M005

## Description

Replace the `// TODO S02` placeholder in `bankongseton_r4.ino` with working OLED + QR code rendering. This involves: adding two library includes and a display global; writing four new functions (`oledShowReady`, `renderQr`, `httpGetBody`, `parseQrUrl`); wiring the OLED init into `setup()`; and inserting a QR poll timer block into both the main `loop()` and the cooldown `while` loop.

The firmware must compile unchanged for hardware that has no OLED attached — OLED init failure is non-fatal (logged to Serial, execution continues).

## Steps

1. **Read the current firmware** (`arduino/bankongseton_r4/bankongseton_r4.ino`) to confirm exact line numbers of the insertion points before editing.

2. **Add includes and display global at the top** — immediately after `#include <Wire.h>` (around line 6), before `#include <WiFiS3.h>`. Replace the entire `// TODO S02: add...` comment block with:
   ```cpp
   #include <Adafruit_GFX.h>
   #include <Adafruit_SSD1306.h>
   #include "qrcode.h"   // ricmoo/qrcode — QRCode, qrcode_initText, qrcode_getModule
   
   Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
   ```
   The OLED_WIDTH/OLED_HEIGHT/OLED_ADDR constants are already defined above this block — do not redefine them.

3. **Add QR poll globals** — add these near `lastHeartbeatMs` (just before the lifecycle section):
   ```cpp
   static const int     QR_POLL_INTERVAL_MS = 500;
   static unsigned long lastQrPollMs = 0;
   static String        lastQrUrl    = "";
   ```

4. **Add `oledShowReady()` function** — before `setup()`:
   ```cpp
   void oledShowReady() {
     display.clearDisplay();
     display.setTextSize(2);
     display.setTextColor(SSD1306_WHITE);
     display.setCursor(22, 24);  // roughly centered on 128×64
     display.print("Ready");
     display.display();
   }
   ```

5. **Add `renderQr(url)` function** — before `setup()`:
   ```cpp
   void renderQr(const String &url) {
     // Try versions 1–7 until the URL fits (ECC_LOW capacity: V1=17 … V7=154 bytes)
     QRCode qrcode;
     uint8_t qrData[qrcode_getBufferSize(7)];
     int usedVersion = -1;
     for (int v = 1; v <= 7; v++) {
       if (qrcode_initText(&qrcode, qrData, v, ECC_LOW, url.c_str()) == true) {
         usedVersion = v;
         break;
       }
     }
     if (usedVersion < 0) {
       Serial.println("QR: version too small for URL length — max 154 chars (V7 ECC-L)");
       oledShowReady();
       return;
     }
     // Auto-scale: 2px/module if it fits in OLED_HEIGHT, else 1px
     uint8_t scale = (qrcode.size * 2 <= OLED_HEIGHT) ? 2 : 1;
     // Center on display
     uint8_t xOff = (OLED_WIDTH  - qrcode.size * scale) / 2;
     uint8_t yOff = (OLED_HEIGHT - qrcode.size * scale) / 2;
     display.clearDisplay();
     for (uint8_t y = 0; y < qrcode.size; y++) {
       for (uint8_t x = 0; x < qrcode.size; x++) {
         if (qrcode_getModule(&qrcode, x, y)) {
           if (scale == 1) {
             display.drawPixel(xOff + x, yOff + y, SSD1306_WHITE);
           } else {
             // 2×2 block per module
             display.drawPixel(xOff + x*2,   yOff + y*2,   SSD1306_WHITE);
             display.drawPixel(xOff + x*2+1, yOff + y*2,   SSD1306_WHITE);
             display.drawPixel(xOff + x*2,   yOff + y*2+1, SSD1306_WHITE);
             display.drawPixel(xOff + x*2+1, yOff + y*2+1, SSD1306_WHITE);
           }
         }
       }
     }
     display.display();  // flush entire framebuffer ONCE — never inside the pixel loop
     Serial.print("QR: rendering v");
     Serial.print(usedVersion);
     Serial.print(" scale=");
     Serial.print(scale);
     Serial.print("px url=");
     Serial.println(url);
   }
   ```

6. **Add `httpGetBody(path)` function** — before `setup()` (after `httpPostCard`):
   ```cpp
   // Sends HTTP GET with X-API-Key header; reads through all headers (until blank line);
   // returns body string. Returns "" on failure.
   String httpGetBody(const String &path) {
     WiFiClient client;
     String host = String(FLASK_HOST);
     int colonIdx = host.indexOf(':');
     String ip   = (colonIdx >= 0) ? host.substring(0, colonIdx) : host;
     int    port  = (colonIdx >= 0) ? host.substring(colonIdx + 1).toInt() : 80;
   
     if (!client.connect(ip.c_str(), port)) return "";
   
     client.println("GET " + path + " HTTP/1.0");
     client.println("Host: " + String(FLASK_HOST));
     client.println("X-API-Key: " + String(SECRET_API_KEY));
     client.println("Connection: close");
     client.println();
   
     unsigned long start = millis();
     while (!client.available() && millis() - start < HTTP_TIMEOUT_MS) delay(10);
   
     // Skip headers: read lines until blank line (\r\n or \n only)
     while (client.available()) {
       String line = client.readStringUntil('\n');
       line.trim();
       if (line.length() == 0) break;  // blank line = end of headers
     }
   
     // Read body (first non-empty line after headers)
     String body = "";
     unsigned long bodyStart = millis();
     while (client.available() && millis() - bodyStart < 2000) {
       body = client.readStringUntil('\n');
       body.trim();
       if (body.length() > 0) break;
     }
     client.stop();
     return body;
   }
   ```

7. **Add `parseQrUrl(json)` function** — before `setup()`:
   ```cpp
   // Extracts "url" value from {"token":"...","url":"..."} or returns "" for {"token":null}.
   String parseQrUrl(const String &json) {
     int idx = json.indexOf("\"url\":\"");
     if (idx < 0) return "";
     int start = idx + 7;  // length of "\"url\":\""
     int end   = json.indexOf('"', start);
     if (end < 0) return "";
     return json.substring(start, end);
   }
   ```

8. **Update `setup()`** — after `Wire.begin()`, add the OLED init block. The `// TODO S02` comment block was already removed in step 2 (it was in the global declarations section). In `setup()`, locate step 5 (`Wire.begin();`) and insert immediately after:
   ```cpp
   // 5b. OLED init (SSD1306, I2C)
   if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
     Serial.println("OLED: init failed 0x3C — check I2C wiring (non-fatal)");
     // Continue — RFID payment still works without OLED
   } else {
     display.clearDisplay();
     display.display();
     oledShowReady();
   }
   ```

9. **Add QR poll block to main `loop()`** — insert after the heartbeat block and BEFORE the `if (!rfid.PICC_IsNewCardPresent()) return;` early-exit:
   ```cpp
   // ── QR poll: fetch and render pending QR from backend ──
   if (now - lastQrPollMs >= (unsigned long)QR_POLL_INTERVAL_MS) {
     lastQrPollMs = now;
     String body   = httpGetBody("/api/arduino/qr-pending");
     String qrUrl  = parseQrUrl(body);
     if (qrUrl != lastQrUrl) {
       lastQrUrl = qrUrl;
       if (qrUrl.length() == 0) {
         oledShowReady();
         Serial.println("QR: idle (Ready)");
       } else {
         renderQr(qrUrl);
       }
     }
   }
   ```
   Note: the `now` variable is already declared in the heartbeat block. No need to redeclare.

10. **Add QR poll block inside the cooldown `while` loop** — the cooldown loop currently calls `handleIncomingSerial()` every 50ms. Add the same QR poll check inside it:
    ```cpp
    unsigned long cooldownEnd = millis() + SCAN_COOLDOWN_MS;
    while (millis() < cooldownEnd) {
      handleIncomingSerial();
      unsigned long now2 = millis();
      if (now2 - lastQrPollMs >= (unsigned long)QR_POLL_INTERVAL_MS) {
        lastQrPollMs = now2;
        String body  = httpGetBody("/api/arduino/qr-pending");
        String qrUrl = parseQrUrl(body);
        if (qrUrl != lastQrUrl) {
          lastQrUrl = qrUrl;
          if (qrUrl.length() == 0) { oledShowReady(); Serial.println("QR: idle (Ready)"); }
          else                     { renderQr(qrUrl); }
        }
      }
      delay(50);
    }
    ```
    Use `now2` (not `now`) to avoid shadowing the outer `now` variable.

11. **Update the header comment** at the top of the file — change the REQUIRED LIBRARIES comment to add:
    ```
    *   - "Adafruit SSD1306" by Adafruit
    *   - "Adafruit GFX Library" by Adafruit
    *   - "QRCode" by Richard Moore (ricmoo/qrcode)
    ```
    Also remove the line `* Adafruit_SSD1306 is NOT included here — deferred to S02.`

## Must-Haves

- [ ] `#include <Adafruit_SSD1306.h>` and `#include "qrcode.h"` present in firmware (not in comments)
- [ ] `Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1)` global declared
- [ ] `display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)` called in `setup()` with non-fatal failure handling
- [ ] `oledShowReady()` function present and called in `setup()` (on success) and when QR clears
- [ ] `renderQr(url)` uses auto-scale: `scale = (qrcode.size * 2 <= OLED_HEIGHT) ? 2 : 1`; `display.display()` called only once per render, never inside the pixel loop
- [ ] `httpGetBody(path)` reads past all headers (blank-line detection) before returning body; uses X-API-Key header
- [ ] `parseQrUrl(json)` returns empty string for `{"token":null}` and for missing `"url":"` field
- [ ] QR poll block appears in BOTH main `loop()` and inside the cooldown `while` loop
- [ ] `lastQrUrl` guard prevents OLED redraw when URL hasn't changed
- [ ] `// TODO S02` comment removed
- [ ] All existing behaviour preserved: RC522 read loop, WiFi POST, heartbeat, serial fallback, piezo, cooldown

## Verification

```bash
grep -q '#include <Adafruit_SSD1306.h>' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q '#include "qrcode.h"' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'display.begin' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'oledShowReady' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'renderQr' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'httpGetBody' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'qr-pending' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'parseQrUrl' arduino/bankongseton_r4/bankongseton_r4.ino
! grep -q 'TODO S02' arduino/bankongseton_r4/bankongseton_r4.ino
```

All 9 commands must succeed (last one must return exit 0 from `! grep`).

## Observability Impact

- Signals added: `OLED: init failed 0x3C — check I2C wiring (non-fatal)` on OLED failure; `QR: rendering v<N> scale=<N>px url=<url>` on each QR render; `QR: idle (Ready)` on each clear; `QR: version too small for URL length` on capacity overflow
- How a future agent inspects this: Arduino Serial Monitor at 9600 baud; all QR state transitions print to Serial
- Failure state exposed: OLED init failure is explicitly non-fatal and logged; QR version overflow is explicitly logged with the URL that caused it; HTTP GET failure returns "" body → `parseQrUrl` returns "" → `oledShowReady()` called → no crash

## Inputs

- `arduino/bankongseton_r4/bankongseton_r4.ino` — S01 firmware: RC522 read loop, WiFi helpers (`httpPostJson`, `httpPostCard`, `ensureWiFi`, `connectWiFi`), heartbeat timer, piezo, cooldown loop, `Wire.begin()`, OLED constants (`OLED_WIDTH=128`, `OLED_HEIGHT=64`, `OLED_ADDR=0x3C`), `// TODO S02` comment
- `arduino/bankongseton_r4/secrets.h` — provides `FLASK_HOST` and `SECRET_API_KEY` used by `httpGetBody()`
- S02 Research doc — full function signatures, scaling formula, header-read logic, constraints on `display.display()` placement, pitfall list; do not deviate from these

## Expected Output

- `arduino/bankongseton_r4/bankongseton_r4.ino` — updated firmware (~430 lines) with OLED active, QR poll loop running at 500ms, 4 new functions, `// TODO S02` removed, all existing behaviour preserved
