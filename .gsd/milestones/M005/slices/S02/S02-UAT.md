# S02: OLED Driver + QR Polling on R4 — UAT

**Milestone:** M005
**Written:** 2026-03-17

## UAT Type

- UAT mode: mixed (artifact-driven contract verification + human-experience hardware validation)
- Why this mode is sufficient: The firmware is non-executable in CI (requires real Arduino hardware), so contract-level grep checks prove structure; human UAT on real hardware proves the QR is actually scannable. Both are required for R027/R028 to move to validated.

## Preconditions

1. Arduino UNO R4 WiFi wired with:
   - RC522 RFID module (SPI: SS=D10, RST=D8, MOSI=D11, MISO=D12, SCK=D13, VCC=3.3V)
   - SSD1306 OLED 128×64 (I2C: SDA→SDA, SCL→SCL, VCC=3.3V or 5V, GND=GND, address 0x3C)
   - Piezo buzzer on D9
2. Arduino IDE or arduino-cli installed with:
   - "MFRC522" by GithubCommunity
   - "Adafruit SSD1306" by Adafruit
   - "Adafruit GFX Library" by Adafruit
   - "QRCode" by Richard Moore (ricmoo/qrcode)
   - WiFiS3 (built-in for UNO R4 WiFi)
3. `arduino/bankongseton_r4/secrets.h` filled with real SSID, password, FLASK_HOST, and SECRET_API_KEY
4. Contract verify script must have already passed: `bash scripts/verify-m005-s02.sh` exits 0 from project root

## Smoke Test

Flash `arduino/bankongseton_r4/bankongseton_r4.ino` → open Serial Monitor at 9600 baud → confirm "BANKONGSETON RFID reader ready" appears → confirm OLED shows "Ready" in white text on dark background.

---

## Test Cases

### 1. Contract Verification (Run First — No Hardware Required)

From the project root directory:

1. Run `bash scripts/verify-m005-s02.sh`
2. **Expected:** All 9 checks print PASS, final line is "✓ All S02 contract checks passed.", exit code 0
3. **Failure signal:** Any `[N/9]` check that does not print PASS — identify the failing check name, locate and restore the missing symbol in `bankongseton_r4.ino`

---

### 2. OLED Boot — "Ready" at Idle

1. Flash `arduino/bankongseton_r4/bankongseton_r4.ino` to R4
2. Power via USB or powerbank
3. Open Serial Monitor at 9600 baud
4. **Expected (Serial):** `BANKONGSETON RFID reader ready` within ~5 seconds of power-on
5. **Expected (OLED):** White "Ready" text displayed centered on the 128×64 screen, dark background; no garbage pixels, no blank screen

---

### 3. Serial Monitor Startup Sequence

1. Power on R4 with OLED wired correctly
2. Watch Serial Monitor at 9600 baud from the first moment
3. **Expected sequence:**
   - `BANKONGSETON` (banner line 1)
   - `WiFi...` (WiFi connecting)
   - `WiFi connected. IP: <192.168.x.x>` (DHCP success)
   - `BANKONGSETON RFID reader ready` (setup complete)
4. **Expected (OLED):** Shows "Ready" immediately after startup beep

---

### 4. QR Render on Real OLED

1. Flash firmware
2. Modify `setup()` to call `renderQr("https://yourname.pythonanywhere.com/api/qr/test-token-1234")` immediately after `oledShowReady()` (before `connectWiFi()`)
   - Alternatively: temporarily modify `parseQrUrl` to always return the test URL
3. Flash the modified firmware
4. **Expected (OLED):** A black-and-white QR code bitmap appears, centered on the screen, within 2 seconds of power-on
5. **Expected (Serial):** `QR: rendering v<N> scale=<N>px url=https://yourname.pythonanywhere.com/api/qr/test-token-1234`
6. Point an Android or iOS camera app at the OLED QR code from ~15–30cm distance
7. **Expected:** Camera app decodes the QR and shows the URL `https://yourname.pythonanywhere.com/api/qr/test-token-1234`
8. Re-flash the original firmware (without the hardcoded test call) before deploying

---

### 5. QR Poll Cycle — Backend Delivers URL → OLED Renders → Backend Clears → OLED Returns to Ready

*Requires S03 backend running with `GET /api/arduino/qr-pending` and `POST /cashier/api/qr-generate` implemented.*

1. Flash production firmware (no test stub), power on R4
2. Confirm OLED shows "Ready"
3. POST to `/cashier/api/qr-generate` with a valid cashier JWT → receive `{token, url}` in response
4. Within 500ms (one poll cycle), **Expected (OLED):** QR bitmap appears for the returned URL
5. **Expected (Serial):** `QR: rendering v<N> scale=<N>px url=<url>`
6. Clear the pending QR: call the confirm or cancel endpoint (or directly clear `app.pending_qr_token` for test purposes)
7. Within 500ms, **Expected (OLED):** Returns to "Ready" display
8. **Expected (Serial):** `QR: idle (Ready)`

---

### 6. RFID Tap During Active QR (Cooldown Loop QR Poll)

*Requires S03 backend with a pending QR already active.*

1. Ensure a QR is rendered on OLED (from test case 5)
2. Tap a physical RFID card at the RC522 reader
3. **Expected:** Card UID delivered via WiFi POST `/api/arduino/card-read` (check Flask log for POST 200)
4. During the 1500ms cooldown after the tap, **Expected (OLED):** QR state is maintained (or transitions to Ready if cleared) — OLED does not freeze or show garbage during cooldown
5. **Expected (Serial):** Both RFID scan line (`SCAN: FOUND uid=...`) and QR poll lines appear without error

---

### 7. RFID Still Works Without OLED (Non-Fatal OLED Failure)

1. Disconnect OLED I2C wires (SDA and/or SCL) before powering on
2. Power on R4, open Serial Monitor at 9600 baud
3. **Expected (Serial):** `OLED: init failed 0x3C — check I2C wiring (non-fatal)` appears during startup
4. **Expected:** Firmware continues booting; `BANKONGSETON RFID reader ready` still appears
5. Tap a physical RFID card
6. **Expected:** RFID scan completes normally; Flask log shows `POST /api/arduino/card-read 200` — payment flow unaffected by OLED absence

---

## Edge Cases

### URL Length at Limit (154 chars — V7 ECC-L cap)

1. Temporarily modify firmware so `httpGetBody` returns a hardcoded JSON with a 155-character URL (one over limit)
2. Flash and power on
3. **Expected (Serial):** `QR: version too small for URL length — max 154 chars (V7 ECC-L)`
4. **Expected (OLED):** Returns to "Ready" display (no crash, no garbage)
5. Restore firmware

---

### Backend Unreachable (WiFi up but Flask not responding)

1. Flash firmware with FLASK_HOST pointing to an unreachable address (or take backend offline)
2. Power on R4, let it connect to WiFi
3. Watch Serial Monitor
4. **Expected:** No crash, no error loop — `httpGetBody` returns `""` → `parseQrUrl("")` returns `""` → `oledShowReady()` is called silently
5. **Expected (OLED):** Stays on "Ready" — no flickering, no blank screen
6. Heartbeat attempts may log "HTTP: connect failed" — this is expected and non-fatal

---

### Rapid QR URL Change (Backend Updates Token Quickly)

1. Create a pending QR so OLED shows QR #1
2. Within 500ms, replace `app.pending_qr_token` with a different URL on the backend
3. **Expected (OLED):** On next poll cycle, OLED re-renders with QR #2 (no visual artifacts from #1)
4. **Expected:** No flicker during the unchanged-state cycles (lastQrUrl guard prevents redundant redraws)

---

## Failure Signals

- **OLED blank on boot, no Serial error:** Wrong I2C address (try 0x3D) or power issue — check OLED VCC
- **OLED blank on boot, Serial shows init failed:** Expected if OLED absent/mis-wired; RFID still works
- **Firmware does not compile:** Missing library — install "Adafruit SSD1306", "Adafruit GFX Library", or "QRCode" (ricmoo) in Arduino Library Manager
- **QR bitmap renders but camera cannot decode:** Module scale too small at scan distance; try 1px modules (will be automatic for larger QR versions) or move camera closer; check QR is not overflowing OLED bounds
- **QR never appears on OLED (backend connected):** Check that `GET /api/arduino/qr-pending` returns `{"token":"...","url":"..."}` format with double-quoted `url` key — `parseQrUrl` requires this exact structure
- **OLED flickers/redraws constantly:** `lastQrUrl` guard is missing or malfunctioning — check the guard condition in both loop() and cooldown while loop
- **Firmware crashes/resets during QR render:** Possible stack overflow from `uint8_t qrData[qrcode_getBufferSize(7)]` — check available SRAM with `Serial.println(freeMemory())` if freeMemory library is installed

## Requirements Proved By This UAT

- **R027** (OLED Replaces LCD on R4) — Test cases 2, 3, 4, and 7 prove the OLED driver is activated, renders correctly, and degrades non-fatally when absent
- **R028** (QR Token Delivery to OLED via Arduino Polling) — Test cases 4 and 5 prove the poll loop fetches and renders QR URLs; test cases 6 and 7 prove resilience; edge cases prove graceful failure modes

## Not Proven By This UAT

- **End-to-end QR payment** (R029 — requires S03 backend endpoints to exist)
- **Android/iOS QR scanner integration** (R030, R033 — requires S04 app changes)
- **Sheets balance debit via QR** (requires S03 + S04 complete)
- **Powerbank behavior unchanged after firmware swap** (R023 — operational, not tested here; S01 validated this pattern; S02 adds minimal current draw from OLED)

## Notes for Tester

- For test case 4 (QR render on real OLED), the hardcoded test URL should be your real PythonAnywhere URL with `/api/qr/test-token` appended — this makes the QR decoding test meaningful for S03 integration later.
- When scanning the OLED QR with a phone camera, ambient light on the screen and glare can affect readability. A dark room or direct-angle shot works best. Try both Android Camera and iOS Camera (both have built-in QR decode).
- The `scripts/verify-m005-s02.sh` contract check (test case 1) should be run before every hardware flash as a sanity check — it only takes 2 seconds.
- After any test that modifies the firmware (test case 4 hardcoded URL, edge case URL-length test), always re-flash the unmodified production firmware before deployment.
- Do not skip test case 7 (OLED absent / non-fatal). This confirms the "RFID still works even if the OLED fails" guarantee that the S02 design intentionally provides.
