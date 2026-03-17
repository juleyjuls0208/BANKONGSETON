/*
 * BANKONGSETON — Arduino UNO R4 WiFi RFID payment reader (RC522 over SPI)
 *
 * Role: payment card tap delivery.
 *   Reads physical RFID cards (MIFARE, NTAG via RC522) and delivers:
 *     CARD|<UID-HEX>  → WiFi POST /api/arduino/card-read (primary)
 *                     → Serial fallback (if WiFi unavailable)
 *   ArduinoBridge reads the serial line and processes the payment.
 *
 * ═══════════════════════════════════════════════════════════════
 * HARDWARE WIRING
 * ═══════════════════════════════════════════════════════════════
 *
 * RC522 RFID Module (SPI):
 *   SDA/SS  → D10  (RC522_SS)
 *   MOSI    → D11  (SPI hardware, no define needed)
 *   MISO    → D12  (SPI hardware, no define needed)
 *   SCK     → D13  (SPI hardware, no define needed)
 *   RST     → D8   (RC522_RST)
 *   VCC     → 3.3V
 *   GND     → GND
 *
 * OLED 128x64 (hardware I2C — deferred to S02):
 *   SDA     → SDA (hardware I2C)
 *   SCL     → SCL (hardware I2C)
 *   VCC     → 3.3V or 5V
 *   GND     → GND
 *   I2C address: 0x3C (OLED_ADDR)
 *
 * Piezo buzzer:
 *   +       → D9   (PIEZO_PIN)
 *   -       → GND
 *
 * ═══════════════════════════════════════════════════════════════
 * REQUIRED LIBRARIES (install via Arduino Library Manager)
 * ═══════════════════════════════════════════════════════════════
 *   - "MFRC522" by GithubCommunity
 *   - WiFiS3 (built-in for UNO R4 WiFi)
 *   - Wire (built-in)
 *   - SPI (built-in)
 *   - "Adafruit SSD1306" by Adafruit
 *   - "Adafruit GFX Library" by Adafruit
 *   - "QRCode" by Richard Moore (ricmoo/qrcode)
 * ═══════════════════════════════════════════════════════════════
 */

#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "qrcode.h"   // ricmoo/qrcode — QRCode, qrcode_initText, qrcode_getModule
#include <WiFiS3.h>
#include "secrets.h"

// ── RC522 pin assignments ────────────────────────────────────────
#define RC522_SS    10   // SPI chip-select (SDA/SS on RC522 board)
#define RC522_RST    8   // RC522 reset line

// ── RC522 instance ───────────────────────────────────────────────
MFRC522 rfid(RC522_SS, RC522_RST);

// ── OLED (SSD1306, I2C) ──────────────────────────────────────────
#define OLED_WIDTH  128
#define OLED_HEIGHT  64
#define OLED_ADDR   0x3C

Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);

// ── Piezo ────────────────────────────────────────────────────────
#define PIEZO_PIN    9   // Passive or active piezo buzzer

// ── Tuning ───────────────────────────────────────────────────────
#define SCAN_COOLDOWN_MS  1500  // ms pause after card read (prevents double-scan)

// ── HTTP tuning ──────────────────────────────────────────────────
static const int MAX_RETRIES           = 3;
static const int RETRY_DELAY_MS        = 2000;
static const int HTTP_TIMEOUT_MS       = 5000;
static const int HEARTBEAT_INTERVAL_MS = 30000;  // 30s — keeps powerbank alive and drives WiFi badge in cashier UI

// ═══════════════════════════════════════════════════════════════
// UID HELPER
// ═══════════════════════════════════════════════════════════════

// Convert uid bytes to uppercase hex string (e.g. "A3B2C1D0").
String uidToHex(uint8_t *uid, uint8_t len) {
  String result = "";
  for (uint8_t i = 0; i < len; i++) {
    if (uid[i] < 0x10) result += "0";
    result += String(uid[i], HEX);
  }
  result.toUpperCase();
  return result;
}

// ═══════════════════════════════════════════════════════════════
// WIFI HELPERS
// ═══════════════════════════════════════════════════════════════

void connectWiFi() {
#ifdef SECRET_SSID
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("ERROR: WiFi module not found");
    while (true) delay(1000);
  }

  Serial.println("BANKONGSETON");
  Serial.println("WiFi...");

  WiFi.begin(SECRET_SSID, SECRET_PASS);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    // Wait for DHCP to assign a real IP (WL_CONNECTED fires before DHCP completes)
    unsigned long dhcpStart = millis();
    while (WiFi.localIP() == IPAddress(0, 0, 0, 0) && millis() - dhcpStart < 5000) {
      delay(100);
    }
    Serial.print("WiFi connected. IP: ");
    Serial.println(WiFi.localIP());
    if (WiFi.localIP() == IPAddress(0, 0, 0, 0)) {
      Serial.println("WARNING: DHCP failed — got 0.0.0.0. Check router or try again.");
    }
  } else {
    Serial.println("WARNING: WiFi connect failed — will retry before each scan");
  }
#else
  Serial.println("WiFi disabled — serial-only mode");
#endif
}

// Ensure WiFi is connected; reconnect non-blocking if dropped.
// Returns true if connected after the attempt.
bool ensureWiFi() {
#ifdef SECRET_SSID
  if (WiFi.status() == WL_CONNECTED) return true;

  Serial.println("WiFi lost — reconnecting...");
  WiFi.begin(SECRET_SSID, SECRET_PASS);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 8000) {
    delay(500);
  }

  return WiFi.status() == WL_CONNECTED;
#else
  return false;  // WiFi disabled — always use serial fallback
#endif
}

// ═══════════════════════════════════════════════════════════════
// HTTP POST HELPERS
// ═══════════════════════════════════════════════════════════════

// Shared TCP connect/header/response logic.
// path: e.g. "/api/arduino/card-read"
// body: raw JSON string to POST
// Returns true on HTTP 200, false on any error.
bool httpPostJson(const String &path, const String &body) {
  WiFiClient client;

  String host = String(FLASK_HOST);
  int colonIdx = host.indexOf(':');
  String ip   = (colonIdx >= 0) ? host.substring(0, colonIdx) : host;
  int    port  = (colonIdx >= 0) ? host.substring(colonIdx + 1).toInt() : 80;

  if (!client.connect(ip.c_str(), port)) {
    Serial.println("HTTP: connect failed");
    return false;
  }

  client.println("POST " + path + " HTTP/1.0");
  client.println("Host: " + String(FLASK_HOST));
  client.println("Content-Type: application/json");
  client.println("X-API-Key: " + String(SECRET_API_KEY));
  client.println("Content-Length: " + String(body.length()));
  client.println("Connection: close");
  client.println();
  client.println(body);

  unsigned long start = millis();
  while (!client.available() && millis() - start < HTTP_TIMEOUT_MS) {
    delay(10);
  }

  String statusLine = client.readStringUntil('\n');
  client.stop();

  bool ok = statusLine.indexOf("200") >= 0;
  if (!ok) {
    Serial.print("HTTP: non-200 response: ");
    Serial.println(statusLine);
  }
  return ok;
}

// POSTs {"uid": "<uid>"} to /api/arduino/card-read (physical RFID card tap).
bool httpPostCard(const String &uid) {
  return httpPostJson("/api/arduino/card-read", "{\"uid\":\"" + uid + "\"}");
}

// ═══════════════════════════════════════════════════════════════
// UNIFIED DELIVERY
// Tries WiFi POST first (with retries), then serial fallback.
// CARD prefix only — no NFC/APDU branch.
// ═══════════════════════════════════════════════════════════════

void deliver(const String &value, const String &prefix) {
  bool wifiOk = ensureWiFi();

  if (wifiOk) {
    for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
      Serial.print("HTTP attempt ");
      Serial.print(attempt);
      Serial.print("/");
      Serial.println(MAX_RETRIES);

      bool ok = httpPostCard(value);
      if (ok) {
        Serial.println("HTTP: delivered — " + prefix + "|" + value);
        return;  // success — no serial fallback needed
      }

      if (attempt < MAX_RETRIES) {
        delay(RETRY_DELAY_MS);
        ensureWiFi();
      }
    }
  }

  // All retries exhausted (or WiFi never connected) — serial fallback
  Serial.print(prefix);
  Serial.print("|");
  Serial.println(value);
}

// ═══════════════════════════════════════════════════════════════
// INCOMING SERIAL COMMAND HANDLER
// Dashboard → Arduino commands (newline-terminated):
//   PING  → play connected sound + reply PONG
//   (extensible: add more commands here)
// Call at the start of every loop() so commands are handled promptly.
// ═══════════════════════════════════════════════════════════════

void handleIncomingSerial() {
  while (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "PING") {
      // Three ascending tones — audible "I'm connected" confirmation
      tone(PIEZO_PIN, 800,  100); delay(120);
      tone(PIEZO_PIN, 1200, 100); delay(120);
      tone(PIEZO_PIN, 1800, 150);

      Serial.println("Dashboard connected!");

      // Reply so dashboard knows the channel is live
      Serial.println("PONG");
    }
  }
}

// ── Heartbeat state ──────────────────────────────────────────────
static unsigned long lastHeartbeatMs = 0;  // tracks last POST /api/arduino/heartbeat; file-scope so it survives across loop() calls

// ── QR poll state ────────────────────────────────────────────────
static const int     QR_POLL_INTERVAL_MS = 500;
static unsigned long lastQrPollMs = 0;
static String        lastQrUrl    = "";

// ═══════════════════════════════════════════════════════════════
// ARDUINO LIFECYCLE
// ═══════════════════════════════════════════════════════════════

void oledShowReady() {
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(22, 24);  // roughly centered on 128×64
  display.print("Ready");
  display.display();
}

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

// Extracts "url" value from {"token":"...","url":"..."} or returns "" for {"token":null}.
String parseQrUrl(const String &json) {
  int idx = json.indexOf("\"url\":\"");
  if (idx < 0) return "";
  int start = idx + 7;  // length of "\"url\":\""
  int end   = json.indexOf('"', start);
  if (end < 0) return "";
  return json.substring(start, end);
}

void setup() {
  // 1. Serial at 9600 baud — ArduinoBridge expects this rate
  Serial.begin(9600);
  while (!Serial && millis() < 3000);

  // 2. Piezo — pinMode required before tone() on UNO R4
  pinMode(PIEZO_PIN, OUTPUT);

  // 3. RC522 SPI init — SPI.begin() MUST precede PCD_Init()
  SPI.begin();
  rfid.PCD_Init();

  // 4. Verify RC522 is responding via VersionReg
  byte ver = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  if (ver == 0x00 || ver == 0xFF) {
    Serial.println("ERROR: RC522 not found — check SPI wiring (SS=D10, RST=D8)");
    while (1) delay(1000);  // halt — cannot continue without RFID reader
  }

  // 5. Wire.begin() for I2C bus
  Wire.begin();

  // 5b. OLED init (SSD1306, I2C)
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("OLED: init failed 0x3C — check I2C wiring (non-fatal)");
    // Continue — RFID payment still works without OLED
  } else {
    display.clearDisplay();
    display.display();
    oledShowReady();
  }

  // 6. WiFi connect
  connectWiFi();

  // 7. Startup beep (200 ms at 1 kHz — audible on both active and passive piezo)
  tone(PIEZO_PIN, 1000, 200);

  // 8. Ready message — ArduinoBridge listens for this line at startup
  Serial.println("BANKONGSETON RFID reader ready");
}

void loop() {
  // Process any commands sent by the dashboard (PING etc.) before doing RFID work.
  handleIncomingSerial();

  // ── Heartbeat: keep powerbank alive + drive WiFi badge in cashier UI ──
  unsigned long now = millis();
  if (now - lastHeartbeatMs >= (unsigned long)HEARTBEAT_INTERVAL_MS) {
    lastHeartbeatMs = now;
    ensureWiFi();
    httpPostJson("/api/arduino/heartbeat", "{\"status\":\"ok\"}");
  }

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

  // Wait for a card to be present — early-exit if none
  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial())   return;

  String uidHex = uidToHex(rfid.uid.uidByte, rfid.uid.size);

  Serial.print("SCAN: FOUND uidLen=");
  Serial.print(rfid.uid.size);
  Serial.print(" uid=");
  Serial.println(uidHex);

  // Detect beep: 1 kHz, 100 ms
  tone(PIEZO_PIN, 1000, 100);

  // Deliver via WiFi POST (primary) or serial fallback
  deliver(uidHex, "CARD");

  // Success beep: two short tones at 800 Hz
  tone(PIEZO_PIN, 800, 200);

  // Halt card and stop crypto — REQUIRED before next read to prevent stuck card state
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  // Cooldown — prevents reading the same card twice in quick succession.
  // Check serial during the wait so PING is handled without a full loop delay.
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
}
