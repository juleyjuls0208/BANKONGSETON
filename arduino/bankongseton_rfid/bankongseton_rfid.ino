/*
 * BANKONGSETON — Arduino UNO R4 WiFi NFC reader (PN532 over SPI)
 *
 * Dual-mode operation:
 *   1. APDU path  — phone running HCE app → WiFi POST token + Serial "NFC|{48-char-token}"
 *   2. UID path   — plain NFC tag (NTAG215, MIFARE, 7-byte UID) → WiFi POST uid + Serial "CARD|{UID}"
 *                   APDU is skipped entirely for non-HCE targets (avoids PN532 lockup on NTAG cards)
 *
 * Python ArduinoBridge reads the serial line and processes the payment.
 *
 * ═══════════════════════════════════════════════════════════════
 * HARDWARE WIRING
 * ═══════════════════════════════════════════════════════════════
 *
 * PN532 NFC Module (SPI mode — set SEL0=LOW, SEL1=HIGH on board):
 *   NSS/CS  → D10  (PN532_SS)
 *   MOSI    → D11  (SPI hardware, no define needed)
 *   MISO    → D12  (SPI hardware, no define needed)
 *   SCK     → D13  (SPI hardware, no define needed)
 *   VCC     → 3.3V
 *   GND     → GND
 *
 * LCD 16x2 with PCF8574 I2C backpack (software I2C, no extra lib):
 *   SDA     → D6  (LCD_SDA)
 *   SCL     → D7  (LCD_SCL)
 *   VCC     → 5V
 *   GND     → GND
 *   Default I2C address: 0x27 (change LCD_ADDR below if needed)
 *
 * Piezo buzzer:
 *   +       → D9  (PIEZO_PIN)
 *   -       → GND
 *
 * ═══════════════════════════════════════════════════════════════
 * REQUIRED LIBRARIES (install via Arduino Library Manager)
 * ═══════════════════════════════════════════════════════════════
 *   - "PN532" by Elechouse  (also installs PN532_SPI, PN532_HSU, etc.)
 *   - WiFiS3 (built-in for UNO R4 WiFi)
 *
 * LCD uses inline bit-bang I2C — no extra library required.
 * ═══════════════════════════════════════════════════════════════
 */

#include <SPI.h>
#include <PN532_SPI.h>
#include <PN532.h>
#include <WiFiS3.h>
#include "secrets.h"

// ── Pin assignments ──────────────────────────────────────────────
#define PN532_SS    10   // SPI chip-select (NSS/CS on PN532 board)
#define PIEZO_PIN    9   // Passive or active piezo buzzer
#define LCD_SDA      6   // Software I2C data line to PCF8574
#define LCD_SCL      7   // Software I2C clock line to PCF8574

// ── LCD I2C configuration ────────────────────────────────────────
// Default PCF8574 backpack address is 0x27.
// If LCD does not respond, try 0x3F (some backpacks ship with this address).
#define LCD_ADDR    0x27
#define LCD_COLS    16
#define LCD_ROWS     2

// ── Tuning ───────────────────────────────────────────────────────
#define SCAN_COOLDOWN_MS  1500  // ms pause after card read (prevents double-scan)
#define NFC_TIMEOUT_MS     500  // ms readPassiveTargetID blocks waiting for card

// ── HTTP tuning ──────────────────────────────────────────────────
static const int MAX_RETRIES    = 3;
static const int RETRY_DELAY_MS = 2000;
static const int HTTP_TIMEOUT_MS = 5000;

// ── PN532 instance (Elechouse SPI — handles SPI.begin() internally) ─
PN532_SPI pn532spi(SPI, PN532_SS);
PN532 nfc(pn532spi);

// ═══════════════════════════════════════════════════════════════
// INLINE BIT-BANG I2C + PCF8574 LCD DRIVER
// No external library required — uses D6 (SDA) and D7 (SCL).
// Implements HD44780 4-bit mode via PCF8574 I2C expander.
// ═══════════════════════════════════════════════════════════════

// PCF8574 bit layout for common LCD I2C backpacks:
//   P7  P6  P5  P4  P3  P2  P1  P0
//   D7  D6  D5  D4  BL  E   RW  RS
#define LCD_BL  0x08  // backlight
#define LCD_E   0x04  // enable strobe
#define LCD_RW  0x02  // read/write (always 0 = write)
#define LCD_RS  0x01  // register select (0=cmd, 1=data)

// ── Low-level bit-bang I2C ───────────────────────────────────────

void i2c_sda_high() { pinMode(LCD_SDA, INPUT);  }   // open-drain: float = HIGH
void i2c_sda_low()  { pinMode(LCD_SDA, OUTPUT); digitalWrite(LCD_SDA, LOW); }
void i2c_scl_high() { pinMode(LCD_SCL, INPUT);  }
void i2c_scl_low()  { pinMode(LCD_SCL, OUTPUT); digitalWrite(LCD_SCL, LOW); }

void i2c_start() {
  i2c_sda_high(); i2c_scl_high();
  delayMicroseconds(4);
  i2c_sda_low();
  delayMicroseconds(4);
  i2c_scl_low();
}

void i2c_stop() {
  i2c_sda_low(); i2c_scl_low();
  delayMicroseconds(4);
  i2c_scl_high();
  delayMicroseconds(4);
  i2c_sda_high();
  delayMicroseconds(4);
}

// Returns true if ACK received (SDA low after 9th clock).
bool i2c_write_byte(uint8_t data) {
  for (int i = 7; i >= 0; i--) {
    if (data & (1 << i)) i2c_sda_high();
    else                  i2c_sda_low();
    delayMicroseconds(1);
    i2c_scl_high();
    delayMicroseconds(4);
    i2c_scl_low();
    delayMicroseconds(1);
  }
  // ACK cycle
  i2c_sda_high();            // release SDA for slave to pull low
  delayMicroseconds(1);
  i2c_scl_high();
  delayMicroseconds(4);
  bool ack = (digitalRead(LCD_SDA) == LOW);
  i2c_scl_low();
  return ack;
}

// Send one byte to PCF8574 at LCD_ADDR.
void pcf8574_write(uint8_t val) {
  i2c_start();
  i2c_write_byte((LCD_ADDR << 1) | 0x00);  // address + write bit
  i2c_write_byte(val);
  i2c_stop();
}

// ── HD44780 via PCF8574 ──────────────────────────────────────────

// Strobe the HD44780 Enable pin (E) to latch 4 bits.
void lcd_pulse_enable(uint8_t val) {
  pcf8574_write(val | LCD_E);
  delayMicroseconds(1);
  pcf8574_write(val & ~LCD_E);
  delayMicroseconds(50);
}

// Send a 4-bit nibble (upper nibble of `val` contains the data).
void lcd_write_nibble(uint8_t nibble, uint8_t flags) {
  uint8_t byte = (nibble & 0xF0) | flags | LCD_BL;
  lcd_pulse_enable(byte);
}

// Send a full 8-bit command or data byte as two nibbles.
void lcd_send(uint8_t data, bool rs) {
  uint8_t flags = rs ? LCD_RS : 0x00;
  lcd_write_nibble(data & 0xF0, flags);
  lcd_write_nibble((data << 4) & 0xF0, flags);
}

void lcd_command(uint8_t cmd)  { lcd_send(cmd,  false); }
void lcd_data(uint8_t ch)      { lcd_send(ch,   true);  }

// ── HD44780 row addresses (standard 16x2) ───────────────────────
static const uint8_t LCD_ROW_ADDR[2] = { 0x00, 0x40 };

void lcd_set_cursor(uint8_t col, uint8_t row) {
  lcd_command(0x80 | (LCD_ROW_ADDR[row] + col));
}

void lcd_clear() {
  lcd_command(0x01);
  delay(2);  // clear needs >1.5 ms
}

void lcd_print(const char *str) {
  while (*str) lcd_data(*str++);
}

void lcd_init() {
  delay(50);  // power-up settling

  // Initialisation sequence per HD44780 datasheet (4-bit mode entry)
  pcf8574_write(LCD_BL);  // backlight on, all control pins low

  // Send 0x03 three times (8-bit mode reset)
  lcd_write_nibble(0x30, 0x00); delay(5);
  lcd_write_nibble(0x30, 0x00); delayMicroseconds(150);
  lcd_write_nibble(0x30, 0x00); delayMicroseconds(150);

  // Switch to 4-bit mode
  lcd_write_nibble(0x20, 0x00);

  // Configure: 4-bit, 2-line, 5x8 font
  lcd_command(0x28);
  // Display ON, cursor OFF, blink OFF
  lcd_command(0x0C);
  // Entry mode: increment, no shift
  lcd_command(0x06);
  lcd_clear();
}

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
    lcd_clear();
    lcd_set_cursor(0, 0);
    lcd_print("WiFi module");
    lcd_set_cursor(0, 1);
    lcd_print("NOT FOUND");
    while (true) delay(1000);
  }

  lcd_clear();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  lcd_print("WiFi...");

  WiFi.begin(SECRET_SSID, SECRET_PASS);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi connected. IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WARNING: WiFi connect failed — will retry before each scan");
  }
#else
  Serial.println("WiFi disabled — serial-only mode");
  lcd_clear();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  lcd_print("Serial mode");
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
// HTTP POST HELPER
// ═══════════════════════════════════════════════════════════════

// Posts {"token": "<value>"} to Flask /api/nfc/tap.
// Returns true on HTTP 200, false on any error.
bool httpPost(const String &value) {
  WiFiClient client;

  String host = String(FLASK_HOST);
  int colonIdx = host.indexOf(':');
  String ip   = (colonIdx >= 0) ? host.substring(0, colonIdx) : host;
  int    port  = (colonIdx >= 0) ? host.substring(colonIdx + 1).toInt() : 80;

  if (!client.connect(ip.c_str(), port)) {
    Serial.println("HTTP: connect failed");
    return false;
  }

  String body = "{\"token\":\"" + value + "\"}";

  client.println("POST /api/nfc/tap HTTP/1.0");
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

// ═══════════════════════════════════════════════════════════════
// UNIFIED DELIVERY
// Tries WiFi POST first (with retries), then serial fallback.
// prefix is "NFC" or "CARD" — used in the serial fallback line.
// ═══════════════════════════════════════════════════════════════

void deliver(const String &value, const String &prefix) {
  bool wifiOk = ensureWiFi();

  if (wifiOk) {
    for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
      Serial.print("HTTP attempt ");
      Serial.print(attempt);
      Serial.print("/");
      Serial.println(MAX_RETRIES);

      if (httpPost(value)) {
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
// ARDUINO LIFECYCLE
// ═══════════════════════════════════════════════════════════════

void setup() {
  // 1. Serial at 9600 baud — ArduinoBridge expects this rate
  Serial.begin(9600);
  while (!Serial && millis() < 3000);

  // 2. Piezo — pinMode required before tone() on UNO R4
  pinMode(PIEZO_PIN, OUTPUT);

  // 3. LCD init (before WiFi so user sees status)
  lcd_init();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  lcd_print("Starting...");

  // 4. PN532 init (Elechouse PN532_SPI handles SPI.begin() internally)
  nfc.begin();
  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("ERROR: PN532 not found — check SPI wiring (NSS=D10, MOSI=D11, MISO=D12, SCK=D13)");
    lcd_clear();
    lcd_set_cursor(0, 0);
    lcd_print("PN532 ERROR");
    lcd_set_cursor(0, 1);
    lcd_print("Check wiring");
    while (1) delay(1000);  // halt — cannot continue without NFC reader
  }
  nfc.SAMConfig();  // configure for ISO14443A cards

  // 5. WiFi connect (shows "WiFi..." on LCD during connect)
  connectWiFi();

  // 6. Startup beep (200 ms at 1 kHz — audible on both active and passive piezo)
  tone(PIEZO_PIN, 1000, 200);

  // 7. Show ready on LCD
  lcd_clear();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  lcd_print("Ready...");

  // 8. Ready message — ArduinoBridge listens for this line at startup
  Serial.println("BANKONGSETON NFC reader ready");
}

void loop() {
  uint8_t uid[7];
  uint8_t uidLen = 0;

  // Show idle state: waiting for phone/card tap
  lcd_clear();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  lcd_print("Tap Phone...");

  // readPassiveTargetID blocks for NFC_TIMEOUT_MS waiting for a card.
  // Returns true when a card/phone is in range and its UID is read.
  bool found = nfc.readPassiveTargetID(
    PN532_MIFARE_ISO14443A, uid, &uidLen, NFC_TIMEOUT_MS
  );

  if (!found) return;  // no card yet — loop immediately

  // ── Target detected — decide path based on UID length ──────
  // HCE phones (Android/iOS) present a 4-byte UID.
  // Plain NFC tags (NTAG215, MIFARE, etc.) present a 7-byte UID.
  // NTAG215 does NOT support ISO 7816-4 APDUs — sending one can lock
  // up inDataExchange for its full timeout and leave the PN532 RF
  // field in a bad state. So we skip the APDU entirely for non-HCE targets.

  String uidHex = uidToHex(uid, uidLen);

  // Show "Reading..." while processing
  lcd_clear();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  lcd_print("Reading...");

  // Detect beep: 1 kHz, 100 ms
  tone(PIEZO_PIN, 1000, 100);

  if (uidLen != 4) {
    // ── Plain NFC tag (7-byte UID = NTAG21x, MIFARE, etc.) ──────
    // Skip APDU — deliver UID directly
    Serial.print("CARD detected (uidLen=");
    Serial.print(uidLen);
    Serial.println(") — skipping APDU");

    deliver(uidHex, "CARD");

    // Fallback beep: single 200 ms at 800 Hz
    tone(PIEZO_PIN, 800, 200);

    // LCD: show card UID
    lcd_clear();
    lcd_set_cursor(0, 0);
    lcd_print("Card Read");
    lcd_set_cursor(0, 1);
    // Show first 8 chars of UID on LCD
    lcd_print(uidHex.substring(0, LCD_COLS).c_str());

  } else {
    // ── 4-byte UID: likely HCE phone — attempt APDU ─────────────
    // APDU SELECT AID command (19 bytes):
    //   CLA=0x00, INS=0xA4, P1=0x04, P2=0x00, Lc=0x0D
    //   AID: F0 42 41 4E 4B 4F 4E 47 53 45 54 4F 4E  (BANKONGSETON)
    //   Le=0x00
    uint8_t apduCmd[19] = {
      0x00, 0xA4, 0x04, 0x00, 0x0D,
      0xF0, 0x42, 0x41, 0x4E, 0x4B, 0x4F, 0x4E, 0x47, 0x53, 0x45, 0x54, 0x4F, 0x4E,
      0x00
    };

    uint8_t response[60];
    uint8_t responseLength = 60;

    // inDataExchange MUST be called after readPassiveTargetID (uses _inListedTag internally).
    bool apduOk = nfc.inDataExchange(apduCmd, 19, response, &responseLength);

    if (apduOk && responseLength == 50 && response[48] == 0x90 && response[49] == 0x00) {
      // ── APDU success: extract 48-char ASCII token ──────────
      String token = "";
      for (int i = 0; i < 48; i++) token += (char)response[i];

      // Deliver via WiFi POST (token key), serial fallback "NFC|<token>"
      deliver(token, "NFC");

      // Success beep: two short tones at 1.5 kHz
      tone(PIEZO_PIN, 1500, 100);
      delay(120);
      tone(PIEZO_PIN, 1500, 100);

      // LCD: show OK
      lcd_clear();
      lcd_set_cursor(0, 0);
      lcd_print("OK");
      lcd_set_cursor(0, 1);
      lcd_print("Payment sent");

    } else {
      // ── APDU failed on 4-byte target — reset RF and fall back to UID
      // Reset RF field to clear any PN532 error state from the failed APDU
      nfc.setRFField(0, 0);  // RF off
      delay(20);
      nfc.setRFField(1, 1);  // RF on
      delay(10);

      Serial.println("APDU failed on 4-byte target — using UID fallback");

      deliver(uidHex, "CARD");

      // Fallback beep: single 200 ms at 800 Hz
      tone(PIEZO_PIN, 800, 200);

      // LCD: show NFC Error
      lcd_clear();
      lcd_set_cursor(0, 0);
      lcd_print("NFC Error");
      lcd_set_cursor(0, 1);
      lcd_print("Using card UID");
    }
  }

  // Cooldown — prevents reading the same card/phone twice in quick succession
  delay(SCAN_COOLDOWN_MS);

  // Idle state reset is handled at top of next loop() iteration
}
