# Phase 18: Arduino UNO R4 WiFi Upgrade - Research

**Researched:** 2026-03-06  
**Domain:** Arduino UNO R4 WiFi firmware, WiFiS3 library, Flask HTTP endpoint auth  
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Endpoint:** `POST /api/arduino/card-read` added to `web_app.py`
- **Auth:** `X-API-Key: <secret>` header; validated against `ARDUINO_API_KEY` env var; 401 on mismatch
- **Credentials:** Hardcoded in `secrets.h` (gitignored); provide `secrets.h.example` template
- **Retry logic:** 3 retries per scan (~2 s apart), then silent serial fallback
- **WiFi reconnect:** Auto-reconnect in background between scans (not blocking)
- **JSON body:** `{"uid": "ABCD1234"}`
- **Library:** Must use `WiFiS3.h` (not ESP8266WiFi or standard WiFi.h)
- **SocketIO event:** New HTTP endpoint emits same `card_read` SocketIO event as the serial path

### Claude's Discretion
- Startup WiFi timeout value
- Server address format in `secrets.h` (IP vs hostname)
- Heartbeat/keepalive behavior
- Changes (if any) to "Connect Arduino" button in cashier UI
- Flask response when card POSTed outside active transaction
- Status badge/indicator in cashier UI for WiFi vs serial mode

### Deferred Ideas (OUT OF SCOPE)
- HTTPS / TLS on Arduino
- OTA firmware updates
- Multiple Arduino support
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ARDW-01 | Arduino firmware reads MFRC522 UID and POSTs `{"uid": "ABCD1234"}` to `POST /api/arduino/card-read` with `X-API-Key` header; retries 3× ~2 s apart on failure; falls back to serial | WiFiS3 `WiFiClient`, raw HTTP POST pattern verified from official examples |
| ARDW-02 | `POST /api/arduino/card-read` endpoint in `web_app.py`: validates API key from `ARDUINO_API_KEY` env var (401 on mismatch), validates UID format, emits `card_read` SocketIO event (same as serial path) | Existing `card_reader_state`, `UID_PATTERN`, `socketio.emit` patterns confirmed in codebase |
| ARDW-03 | `secrets.h` (gitignored) holds `SECRET_SSID`, `SECRET_PASS`, `SECRET_SERVER_IP`, `SECRET_SERVER_PORT`, `SECRET_API_KEY`; `secrets.h.example` template committed | Official Arduino pattern (`arduino_secrets.h` / `SECRET_*` macros) confirmed from WiFiS3 examples |
| ARDW-04 | WiFi reconnects automatically between scans without blocking card-read loop; startup timeout ~30 s then serial-only fallback | `WiFi.status()` polling pattern, `WL_CONNECTED` constant confirmed in WiFi.h source |
</phase_requirements>

---

## Summary

Phase 18 replaces the serial-only RFID card reading path with a dual-mode system: the Arduino UNO R4 WiFi firmware POSTs card UIDs to a new Flask endpoint over the school LAN via WiFi, while retaining serial as a fallback. The entire WiFi stack is provided by `WiFiS3.h`, which ships bundled inside `ArduinoCore-renesas` (not a separate install). The library's `WiFiClient` class provides raw TCP socket access; HTTP POST is hand-constructed using `client.print()` — there is no built-in `HttpClient`. On the Flask side, a single new route and a `ARDUINO_API_KEY` env var are all that is needed; the new endpoint reuses the existing `socketio.emit('card_read', ...)` call so the cashier frontend requires zero changes for core functionality.

Secrets management follows the established Arduino community convention of a gitignored `secrets.h` (or `arduino_secrets.h`) defining `SECRET_*` macros, paired with a committed `secrets.h.example`. This is the same pattern used by all official WiFiS3 examples. WiFi connection management uses `WiFi.status() == WL_CONNECTED` polling — there is no event callback API.

**Primary recommendation:** Build the firmware as a single `.ino` file with a `secrets.h` / `secrets.h.example` pair. Use raw `WiFiClient` HTTP POST (Content-Length required). Set startup WiFi timeout to 30 s then drop to serial-only. Poll `WiFi.status()` before each scan; reconnect inline if disconnected (non-blocking with millis-based timeout).

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `WiFiS3.h` | bundled with ArduinoCore-renesas | WiFi connectivity on UNO R4 WiFi | The only WiFi library for this board; ships with the core |
| `SPI.h` | bundled with Arduino | SPI bus for MFRC522 | Required by all MFRC522 libraries |
| `MFRC522.h` | 1.4.x (Arduino Library Manager) | Read RFID UID from card | De-facto standard; works on UNO R4 with SPI |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `arduino_secrets.h` / `secrets.h` | n/a (manual file) | Store SSID, password, server IP, API key | Always — keep out of git |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw `WiFiClient` HTTP | `ArduinoHttpClient` library | `ArduinoHttpClient` is cleaner but requires extra install; raw is self-contained and sufficient for one endpoint |
| `secrets.h` macros | `EEPROM` or SD card config | EEPROM adds complexity; school deployment benefits from simple reflash |

**Installation (board + library):**
```
Arduino IDE → Board Manager → "Arduino UNO R4 Boards" (installs ArduinoCore-renesas, includes WiFiS3)
Arduino IDE → Library Manager → "MFRC522" by GithubCommunity
```
No `pip install` or `npm install` needed. `WiFiS3.h` is already present once the board package is installed.

---

## Architecture Patterns

### Recommended Project Structure
```
arduino/
├── bankongseton_rfid/
│   ├── bankongseton_rfid.ino   # main sketch
│   ├── secrets.h               # gitignored — real credentials
│   └── secrets.h.example       # committed — template
```
Add to `.gitignore`:
```
arduino/bankongseton_rfid/secrets.h
```

### Pattern 1: WiFiS3 Connection + Reconnect
**What:** Connect at startup; poll `WiFi.status()` before each scan; reconnect if dropped.  
**When to use:** Always — there is no event-driven callback for disconnect.

```cpp
// Source: https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/WiFiS3/src/WiFi.h
#include "WiFiS3.h"
#include "secrets.h"

int wifiStatus = WL_IDLE_STATUS;

bool connectWiFi(unsigned long timeoutMs = 30000UL) {
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    wifiStatus = WiFi.begin(SECRET_SSID, SECRET_PASS);
    if (WiFi.status() == WL_CONNECTED) return true;
    if (millis() - start > timeoutMs) return false;
    delay(2000);
  }
  return true;
}

// In loop(), before each card scan:
bool wifiReady = (WiFi.status() == WL_CONNECTED);
if (!wifiReady) {
  wifiReady = connectWiFi(10000UL); // 10 s reconnect attempt
}
```

### Pattern 2: Raw HTTP POST via WiFiClient
**What:** Open TCP connection, write HTTP/1.1 POST by hand, read status line.  
**When to use:** Sending card UID to Flask endpoint. `Content-Length` is **required** or Flask will hang.

```cpp
// Source: https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/WiFiS3/examples/WiFiWebClientRepeating/WiFiWebClientRepeating.ino
// (adapted for POST with JSON body)
WiFiClient client;

bool postCardUID(const char* uid) {
  client.stop();
  if (!client.connect(SECRET_SERVER_IP, SECRET_SERVER_PORT)) {
    return false;
  }

  String body = String("{\"uid\":\"") + uid + "\"}";
  int contentLength = body.length();

  client.println("POST /api/arduino/card-read HTTP/1.1");
  client.print("Host: ");
  client.println(SECRET_SERVER_IP);
  client.println("Content-Type: application/json");
  client.print("Content-Length: ");
  client.println(contentLength);
  client.print("X-API-Key: ");
  client.println(SECRET_API_KEY);
  client.println("Connection: close");
  client.println();
  client.print(body);

  // Read HTTP status line
  unsigned long timeout = millis();
  while (client.available() == 0) {
    if (millis() - timeout > 5000) { client.stop(); return false; }
  }
  String statusLine = client.readStringUntil('\n');
  client.stop();
  return statusLine.indexOf("200") >= 0;
}
```

### Pattern 3: Retry Loop with Serial Fallback
**What:** Try WiFi POST up to 3 times; if all fail emit UID on Serial as `<CARD|ABCDEF12>`.

```cpp
bool delivered = false;
for (int attempt = 0; attempt < 3 && !delivered; attempt++) {
  if (attempt > 0) delay(2000);
  if (WiFi.status() == WL_CONNECTED) {
    delivered = postCardUID(uid);
  }
}
if (!delivered) {
  // Serial fallback — same format that ArduinoBridge already parses
  Serial.print("<CARD|");
  Serial.print(uid);
  Serial.println(">");
}
```

### Pattern 4: secrets.h / secrets.h.example
**What:** Official Arduino pattern — gitignored file with real values, committed example.  
**Source:** All official WiFiS3 examples use `arduino_secrets.h` with `SECRET_*` macros.

```cpp
// secrets.h  (GITIGNORED — never commit)
#define SECRET_SSID       "MySchoolWiFi"
#define SECRET_PASS       "wifipassword"
#define SECRET_SERVER_IP  "192.168.1.100"
#define SECRET_SERVER_PORT 5000
#define SECRET_API_KEY    "changeme-very-secret-key"
```
```cpp
// secrets.h.example  (COMMITTED)
#define SECRET_SSID       "your-wifi-ssid"
#define SECRET_PASS       "your-wifi-password"
#define SECRET_SERVER_IP  "192.168.x.x"       // Flask server LAN IP
#define SECRET_SERVER_PORT 5000
#define SECRET_API_KEY    "your-api-key-here"
```

### Pattern 5: Flask API Key Endpoint
**What:** New route in `web_app.py` using the existing `socketio.emit('card_read', ...)` path.

```python
# In web_app.py
import os

ARDUINO_API_KEY = os.environ.get('ARDUINO_API_KEY', '')

@app.route('/api/arduino/card-read', methods=['POST'])
def arduino_card_read():
    # 1. Validate API key
    api_key = request.headers.get('X-API-Key', '')
    if not ARDUINO_API_KEY or api_key != ARDUINO_API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401

    # 2. Validate UID
    data = request.get_json(silent=True) or {}
    uid = data.get('uid', '')
    if not UID_PATTERN.match(uid):
        return jsonify({'error': 'Invalid UID'}), 400

    # 3. Reuse existing card_read emission
    socketio.emit('card_read', {'uid': uid})
    logger.info("event=arduino_card_read uid=%s", uid)
    return jsonify({'status': 'ok'}), 200
```

### Anti-Patterns to Avoid
- **`while(true)` blocking connect loop in `loop()`:** Freezes card reading. Use millis-based timeout.
- **Missing `Content-Length` header:** Flask/Werkzeug hangs waiting for body. Always set it.
- **Using hostname instead of IP for `SECRET_SERVER_IP`:** DNS may fail on school LAN; use IP.
- **`client.connected()` instead of `client.connect(...)`:** `connected()` checks existing connection state; `connect()` opens a new one. Don't confuse them.
- **Reading full response body:** Wastes time. Only read the status line (first line ending `\n`).
- **Emitting `card_read` inside an active serial read:** The new endpoint is additive — existing serial path in `arduino_bridge.py` is unchanged.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| RFID UID reading | Custom SPI bit-banging | `MFRC522.h` library | Handles anticollision, CRC, HALT sequence |
| WiFi stack | TCP socket management | `WiFiS3.h` (built into board core) | Manages ESP32-S3 AT commands; not user-serviceable |
| JSON serialisation on Arduino | Manual string concat | Simple `String` concat is fine here (single field) | One-field payload doesn't justify `ArduinoJson` dependency |

**Key insight:** The only custom code needed is the glue: read UID → construct HTTP POST → check response → fallback. Everything else is library.

---

## Common Pitfalls

### Pitfall 1: `Content-Length` Missing on HTTP POST
**What goes wrong:** Flask's Werkzeug server stalls waiting for the rest of the body; Arduino times out; connection hangs.  
**Why it happens:** `WiFiClient` sends raw TCP bytes — no HTTP framework sets headers for you.  
**How to avoid:** Always compute `body.length()` before sending and include `Content-Length: N` header.  
**Warning signs:** Flask logs show request starts but never completes; Arduino `client.available()` never returns data.

### Pitfall 2: WiFi.begin() Blocking Indefinitely
**What goes wrong:** If school WiFi is down at startup, the Arduino hangs forever in the connect loop.  
**Why it happens:** The simple `while (status != WL_CONNECTED)` pattern from official examples has no timeout.  
**How to avoid:** Wrap connect loop with `millis()` timeout (30 s recommended). If exceeded, set `wifiEnabled = false` and operate serial-only.  
**Warning signs:** Arduino appears frozen at boot; serial monitor shows repeated connect attempts with no exit.

### Pitfall 3: `WL_NO_MODULE` Not Checked
**What goes wrong:** If the ESP32-S3 WiFi co-processor fails to communicate, all WiFi calls silently fail.  
**Why it happens:** Hardware issue or firmware not loaded on ESP32-S3 side.  
**How to avoid:** Check `WiFi.status() == WL_NO_MODULE` at startup; print diagnostic and run serial-only.

### Pitfall 4: ARDUINO_API_KEY Empty in Production
**What goes wrong:** If `ARDUINO_API_KEY` is unset in the `.env`, the check `api_key != ARDUINO_API_KEY` passes with an empty string — security hole.  
**Why it happens:** Missing env var defaults to `''`; Arduino sends no key, gets `''` — both match.  
**How to avoid:** In Flask endpoint, explicitly reject if `ARDUINO_API_KEY` is empty: `if not ARDUINO_API_KEY or api_key != ARDUINO_API_KEY: return 401`.

### Pitfall 5: UID String Format Mismatch
**What goes wrong:** Arduino sends lowercase hex (`abcd1234`); Flask `UID_PATTERN = re.compile(r'^[0-9A-Fa-f]{8}$')` accepts both cases, but `normalize_card_uid()` uppercases. If Arduino sends mixed/wrong-length, validation fails.  
**Why it happens:** MFRC522 library returns raw bytes; conversion to hex string is manual.  
**How to avoid:** On Arduino, format each byte as `%02X` (uppercase, zero-padded). Result: `"ABCD1234"` — matches existing `UID_PATTERN` and `normalize_card_uid()`.

### Pitfall 6: Dual Emission if Both Serial and WiFi Active
**What goes wrong:** Arduino sends via both Serial and WiFi simultaneously — `card_read` emitted twice.  
**Why it happens:** If `ArduinoBridge` serial reader is active while WiFi also POSTs.  
**How to avoid:** The retry pattern in Pattern 3 already handles this — Serial fallback only triggers if WiFi fails. Keep them mutually exclusive per scan attempt.

---

## Code Examples

### Complete Minimal Firmware Skeleton
```cpp
// Source: patterns verified from
//   https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/WiFiS3/examples/WiFiWebClientRepeating/WiFiWebClientRepeating.ino
//   https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/WiFiS3/src/WiFi.h

#include "WiFiS3.h"
#include "secrets.h"
#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN  9
#define SS_PIN   10

MFRC522 mfrc522(SS_PIN, RST_PIN);
WiFiClient client;
bool wifiEnabled = false;

void setup() {
  Serial.begin(9600);
  SPI.begin();
  mfrc522.PCD_Init();

  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("WiFi module not found - serial only mode");
  } else {
    wifiEnabled = connectWiFi(30000UL);
  }
}

void loop() {
  // Reconnect if dropped (non-blocking attempt)
  if (wifiEnabled && WiFi.status() != WL_CONNECTED) {
    connectWiFi(5000UL);
  }

  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  char uid[9];
  for (byte i = 0; i < 4; i++) {
    sprintf(uid + i*2, "%02X", mfrc522.uid.uidByte[i]);
  }
  uid[8] = '\0';
  mfrc522.PICC_HaltA();

  bool delivered = false;
  for (int attempt = 0; attempt < 3 && !delivered; attempt++) {
    if (attempt > 0) delay(2000);
    if (wifiEnabled && WiFi.status() == WL_CONNECTED) {
      delivered = postCardUID(uid);
    }
  }
  if (!delivered) {
    Serial.print("<CARD|");
    Serial.print(uid);
    Serial.println(">");
  }
}
```

### WiFi.status() Values (from WiFiTypes.h)
```cpp
// Source: ArduinoCore-renesas WiFiTypes.h
WL_NO_MODULE    = 255  // ESP32-S3 co-processor not responding
WL_IDLE_STATUS  = 0    // Initial state
WL_CONNECTED    = 3    // Successfully connected
WL_CONNECT_FAILED = 4  // Connection attempt failed
WL_DISCONNECTED = 6    // Disconnected from network
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Serial-only RFID (`<CARD|UID>` format) | WiFi HTTP POST with serial fallback | Phase 18 | Removes USB cable dependency |
| ESP8266WiFi / WiFi.h (old Uno) | `WiFiS3.h` (UNO R4 specific) | UNO R4 launch 2023 | Different include, same API shape |

**Deprecated/outdated:**
- `WiFi.h` from old `WiFiNINA` / `WiFi101` libraries: Do NOT use on UNO R4 WiFi. The board requires `WiFiS3.h`.
- `ESP8266WiFi.h`: Not applicable — UNO R4 WiFi uses ESP32-S3, not ESP8266.

---

## Claude's Discretion Recommendations

### Startup WiFi Timeout
**Recommendation:** 30 seconds. School deployments have predictable LAN but morning power-on races are common. 30 s is long enough for DHCP; short enough that a teacher doesn't think the device is broken.

### Server Address Format
**Recommendation:** Use IP address (`192.168.x.x`), not hostname. School LAN DNS is unreliable; WiFiS3 `hostByName()` adds latency. Document in `secrets.h.example` that the IP is the Flask server's LAN address.

### Heartbeat/Keepalive
**Recommendation:** No dedicated heartbeat. The retry-then-fallback pattern provides implicit health checking per scan. Adding a separate keepalive timer complicates the sketch for marginal benefit in a school canteen context.

### "Connect Arduino" Button in Cashier UI
**Recommendation:** No change needed for core functionality. The button triggers serial connect; WiFi path is independent. Optionally add a passive WiFi status indicator (see below) but don't change button behaviour.

### Flask Response Outside Active Transaction
**Recommendation:** Log the event at INFO level and return `200 OK` with `{"status": "ok", "note": "no active transaction"}`. Do NOT emit `card_read` if no transaction is active — or emit it and let the existing cashier JS ignore it (which it already does). Returning 200 prevents Arduino retry loop from firing unnecessarily.

### WiFi vs Serial Status Badge
**Recommendation:** Add a small read-only indicator in the cashier header — e.g., a coloured dot labelled "WiFi" / "Serial" — driven by a new SocketIO event `arduino_mode` emitted when the new endpoint receives its first card read. Keep it purely informational; no user action required.

---

## Open Questions

1. **`ARDUINO_API_KEY` in existing `.env.example`**
   - What we know: `.env.example` does not currently have `ARDUINO_API_KEY`
   - What's unclear: Whether to add it to `config/.env.example` as well (there are two `.env.example` files)
   - Recommendation: Add to both; the planner should create a task for this

2. **MFRC522 pin assignment on UNO R4**
   - What we know: Standard SPI pins on UNO R4 are SS=10, RST=9 (same as classic Uno)
   - What's unclear: Whether any R4-specific SPI initialisation is needed
   - Recommendation: Use standard pins (SS=10, RST=9); MFRC522 library handles SPI init via `SPI.begin()`

3. **Serial baud rate**
   - What we know: `ArduinoBridge` connects at `BAUD_RATE` from env (default not confirmed)
   - What's unclear: Whether existing deployed firmware uses 9600 or 115200
   - Recommendation: Use `9600` to match official examples and common deployments; document in `secrets.h.example`

---

## Sources

### Primary (HIGH confidence)
- `https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/WiFiS3/src/WiFi.h` — full CWifi class API
- `https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/WiFiS3/src/WiFiS3.h` — confirms `#include "WiFi.h"` structure
- `https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/WiFiS3/examples/WiFiWebClientRepeating/WiFiWebClientRepeating.ino` — official repeating HTTP client pattern
- `https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/WiFiS3/examples/ConnectWithWPA/ConnectWithWPA.ino` — official WPA connect pattern
- `backend/dashboard/arduino_bridge.py` — existing `<CARD|UID>` serial format, SocketIO events
- `backend/dashboard/web_app.py` — existing `UID_PATTERN`, `card_reader_state`, `socketio.emit`

### Secondary (MEDIUM confidence)
- `https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/WiFiS3/library.properties` — confirms architectures: `renesas,renesas_uno`; url points to official docs

### Tertiary (LOW confidence)
- General Arduino community pattern for `arduino_secrets.h` — confirmed by multiple official examples (HIGH by extension)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — WiFiS3.h source verified directly from ArduinoCore-renesas
- Architecture: HIGH — HTTP POST pattern verified from official WiFiWebClientRepeating example
- Flask integration: HIGH — existing codebase read directly
- Pitfalls: MEDIUM — derived from API inspection + common Arduino HTTP patterns

**Research date:** 2026-03-06  
**Valid until:** 2026-09-06 (WiFiS3 is stable; ArduinoCore-renesas changes slowly)
