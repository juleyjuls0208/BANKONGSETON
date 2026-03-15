---
estimated_steps: 3
estimated_files: 2
---

# T02: Write README-wireless.md and verify script

**Slice:** S04 — Powerbank Hardening + Wireless Docs
**Milestone:** M003

## Description

Satisfies R024. Writes `arduino/README-wireless.md` — the complete standalone deployment guide for running the Arduino UNO R4 WiFi on a powerbank without a USB cable to a PC. Also writes `scripts/verify-m003-s04.sh`, the single-command exit-0 proof that T01's firmware changes and T02's README are structurally complete.

The README documents hardware, wiring, required libraries, `secrets.h` field-by-field configuration (with explicit callouts for port 5003 and API key matching), flashing steps, powerbank selection, and how to verify the WiFi badge goes green. Format follows `arduino/bankongseton_nfc_r3/README.md` (section structure, table formatting).

The verify script adds to the existing `scripts/verify-m003-s01.sh` / `verify-m003-s03.sh` pattern — grep assertions with exit-on-first-failure and a final `echo "All checks passed"`.

## Steps

1. Write `arduino/README-wireless.md` with these sections (follow R3 README table/heading format):
   - **Hardware Required** — table: Arduino UNO R4 WiFi, PN532 NFC/RFID module (SPI), 16×2 LCD with PCF8574 I2C backpack, piezo buzzer, USB powerbank (≥10,000mAh, ≥2A output port, name-brand recommended)
   - **Wiring** — PN532 → UNO R4 WiFi (NSS=D10, MOSI=D11, MISO=D12, SCK=D13, VCC=3.3V, GND=GND); LCD I2C backpack → UNO R4 (SDA=D6, SCL=D7, VCC=5V, GND=GND); Buzzer → D9/GND; note SPI DIP switch selection (SEL0=0, SEL1=1)
   - **Required Libraries** — table: Adafruit PN532, Adafruit BusIO, WiFiS3 (included with Arduino UNO R4 board package)
   - **secrets.h Configuration** — field-by-field: `SECRET_SSID` / `SECRET_PASS` (school WiFi), `FLASK_HOST` (must be `<ip>:5003` — port 5003 is the dashboard server hosting both `/api/arduino/card-read` and `/api/arduino/heartbeat`; not port 5000), `SECRET_API_KEY` (must match `ARDUINO_API_KEY` in Flask `.env` exactly — mismatch causes 401 and badge stays red), `HEARTBEAT_INTERVAL_MS` (defined in `.ino` not in `secrets.h` — change it there before flashing if needed)
   - **Flashing** — Arduino IDE: File → Open → `arduino/bankongseton_rfid/bankongseton_rfid.ino`, copy `secrets.h.example` to `secrets.h` and fill values, select board "Arduino UNO R4 WiFi", select COM port, Sketch → Upload
   - **Verification** — Serial Monitor at 9600 baud: expect `WiFi connected — IP: <ip>` at boot; every 30s expect `HTTP: POST /api/arduino/heartbeat` line; open cashier UI → WiFi badge should turn green within 30s of boot
   - **Powerbank Selection** — ≥2A output USB-A port required (some banks cut at <1A); ≥10,000mAh for a full 8-hour school day; name-brand (Anker, Xiaomi, Baseus) recommended; avoid no-name banks with aggressive auto-shutoff; the Arduino's ~180-200mA baseline draw keeps most quality banks alive, and the 30s heartbeat burst adds extra margin
   - **Troubleshooting** — table or list: badge stays red (check API key, check port 5003, check Serial Monitor for POST line); WiFi never connects (check SSID/password, check Arduino is on school LAN); LCD blank (check I2C address, try 0x3F)

2. Write `scripts/verify-m003-s04.sh` with the following checks (use the pattern from `scripts/verify-m003-s03.sh` — grep with `-q`, echo PASS/FAIL, exit 1 on failure):
   - (a) `lastHeartbeatMs` variable present in firmware
   - (b) `httpPostJson.*heartbeat` call present in firmware
   - (c) `HEARTBEAT_INTERVAL_MS` comment does not contain "stub" or "not yet"
   - (d) `ensureWiFi` appears in proximity to heartbeat call (use grep -A context or just check it exists after the heartbeat block)
   - (e) `arduino/README-wireless.md` file exists
   - (f) README contains "5003" (correct Flask port documented)
   - (g) README contains "ARDUINO_API_KEY" (API key env var name documented)
   - (h) README contains "powerbank" or "Powerbank" (powerbank guidance present)
   - Final: `echo "verify-m003-s04: all N checks passed"`; exit 0

3. Make `scripts/verify-m003-s04.sh` executable: `chmod +x scripts/verify-m003-s04.sh`. Run `bash scripts/verify-m003-s04.sh` and confirm exit 0. Also run `bash scripts/verify-m003-s03.sh` to confirm no regression.

## Must-Haves

- [ ] `arduino/README-wireless.md` exists and is a complete human-readable guide — not a stub
- [ ] README documents port 5003 explicitly (not 5000 or generic `<port>`)
- [ ] README calls out `ARDUINO_API_KEY` in Flask `.env` as the matching env var for `SECRET_API_KEY` in `secrets.h`
- [ ] README includes powerbank selection guidance with minimum specs
- [ ] `scripts/verify-m003-s04.sh` has ≥8 assertions and exits 0 when run
- [ ] `bash scripts/verify-m003-s03.sh` still exits 0 after this task (no regression)

## Verification

- `bash scripts/verify-m003-s04.sh` — exits 0; prints "all N checks passed"
- `bash scripts/verify-m003-s03.sh` — exits 0 (regression check)
- `test -f arduino/README-wireless.md && echo OK` — file exists
- `grep "5003" arduino/README-wireless.md` — port callout present
- `grep "ARDUINO_API_KEY" arduino/README-wireless.md` — API key env var named

## Inputs

- `arduino/bankongseton_nfc_r3/README.md` — format template (section structure, table markdown, heading levels)
- `arduino/bankongseton_rfid/secrets.h` — canonical field names (`SECRET_SSID`, `SECRET_PASS`, `FLASK_HOST`, `SECRET_API_KEY`); port 5003 example in comments
- `scripts/verify-m003-s03.sh` — pattern template for the verify script (grep -q, PASS/FAIL echo, exit 1 on failure)
- T01 output: heartbeat loop in firmware — README Verification section can describe exactly what Serial Monitor output to expect

## Expected Output

- `arduino/README-wireless.md` — complete standalone WiFi deployment guide
- `scripts/verify-m003-s04.sh` — ≥8-check grep assertion script; exits 0; executable

## Observability Impact

**Signals this task makes inspectable:**
- `bash scripts/verify-m003-s04.sh` — single-command exit-0 proof; each check prints ✓/✗ so a future agent can see exactly which assertion failed and why
- `grep "5003\|ARDUINO_API_KEY\|powerbank" arduino/README-wireless.md` — spot-check that the three most deployment-critical callouts are present without running the full script
- `grep -n "lastHeartbeatMs\|httpPostJson.*heartbeat" arduino/bankongseton_rfid/bankongseton_rfid.ino` — firmware check surfaced directly by the verify script so inspection requires no manual firmware reading

**Failure state:**
- Script exits 1 and prints ✗ on the first failed assertion — check label names which file or pattern is missing
- `README-wireless.md` absent → check (e) fails with "file does not exist"; create the file and rerun
- Firmware checks (a–d) fail → T01 heartbeat loop was not applied; re-execute T01 or check the correct `.ino` path
- README port check (f) fails → README mentions only 5000 or a generic `<port>`; add explicit "5003" callout

**No runtime signal change:** this task produces only documentation and a verification script — it does not alter any server endpoint, socket event, or Serial Monitor output. The runtime observability introduced in T01 (Serial `HTTP: POST /api/arduino/heartbeat`, Flask access log `POST /api/arduino/heartbeat 200`, and `#wifiBadge` turning green) is unaffected.
