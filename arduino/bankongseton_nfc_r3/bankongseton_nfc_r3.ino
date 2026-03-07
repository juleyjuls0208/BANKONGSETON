/*
 * BANKONGSETON — Arduino UNO R3 NFC reader (PN532 over SPI)
 *
 * Reads PN532 card UID → Serial "CARD|{UID}" at 9600 baud
 * Python ArduinoBridge reads this line and processes the payment.
 *
 * UNO R3 has no WiFi — serial is the ONLY delivery path.
 * Do NOT add WiFiS3.h or any HTTP logic here.
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
 *   - "Adafruit PN532" by Adafruit
 *   - "Adafruit BusIO" by Adafruit  (dependency of PN532)
 *
 * LCD uses inline bit-bang I2C — no extra library required.
 * ═══════════════════════════════════════════════════════════════
 */

#include <SPI.h>
#include <Adafruit_PN532.h>

// ── Pin assignments ──────────────────────────────────────────────
#define PN532_SS   10   // SPI chip-select (NSS/CS on PN532 board)
#define PIEZO_PIN   9   // Passive or active piezo buzzer
#define LCD_SDA     6   // Software I2C data line to PCF8574
#define LCD_SCL     7   // Software I2C clock line to PCF8574

// ── LCD I2C configuration ────────────────────────────────────────
// Default PCF8574 backpack address is 0x27.
// If LCD does not respond, try 0x3F (some backpacks ship with this address).
#define LCD_ADDR    0x27
#define LCD_COLS    16
#define LCD_ROWS     2

// ── Tuning ───────────────────────────────────────────────────────
#define SCAN_COOLDOWN_MS  1500  // ms pause after card read (prevents double-scan)
#define NFC_TIMEOUT_MS     500  // ms readPassiveTargetID blocks waiting for card

// ── PN532 instance (SPI mode — pass only the SS pin) ─────────────
Adafruit_PN532 nfc(PN532_SS);

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
// ARDUINO LIFECYCLE
// ═══════════════════════════════════════════════════════════════

void setup() {
  // 1. Serial at 9600 baud — ArduinoBridge expects this rate
  Serial.begin(9600);
  while (!Serial && millis() < 3000);  // wait up to 3 s for Serial Monitor

  // 2. SPI bus — must start before nfc.begin()
  SPI.begin();

  // 3. PN532 init
  nfc.begin();
  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("ERROR: PN532 not found — check SPI wiring (NSS=D10, MOSI=D11, MISO=D12, SCK=D13)");
    while (1) delay(1000);  // halt — cannot continue without NFC reader
  }
  nfc.SAMConfig();  // configure for ISO14443A cards

  // 4. LCD init
  lcd_init();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  lcd_print("Ready...");

  // 5. Startup beep (100 ms) — confirms piezo wiring
  tone(PIEZO_PIN, 1000, 100);

  // 6. Ready message — ArduinoBridge listens for this line at startup
  Serial.println("BANKONGSETON NFC reader ready");
}

void loop() {
  uint8_t uid[7];
  uint8_t uidLen = 0;

  // readPassiveTargetID blocks for NFC_TIMEOUT_MS waiting for a card.
  // Returns true when a card is in range and its UID is read.
  bool found = nfc.readPassiveTargetID(
    PN532_MIFARE_ISO14443A, uid, &uidLen, NFC_TIMEOUT_MS
  );

  if (!found) return;  // no card yet — loop immediately (no extra delay)

  // ── Card detected ──────────────────────────────────────────
  String uidHex = uidToHex(uid, uidLen);

  // Serial output — exact format consumed by ArduinoBridge._read_serial_line
  Serial.print("CARD|");
  Serial.println(uidHex);

  // Piezo beep: 1 kHz, 200 ms
  tone(PIEZO_PIN, 1000, 200);

  // LCD update — show UID (first 8 chars if long)
  lcd_clear();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  // Truncate to 16 chars max (LCD width); UID is typically 8 chars
  String display = uidHex.substring(0, min((int)uidHex.length(), LCD_COLS));
  lcd_print(display.c_str());

  // Cooldown — prevents reading the same card twice in quick succession
  delay(SCAN_COOLDOWN_MS);

  // Reset LCD to idle state
  lcd_clear();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  lcd_print("Tap card...");
}
