/*
 * BANKONGSETON — Arduino UNO R3 RFID registration reader (RC522 over SPI)
 *
 * Role: card registration only.
 *   Reads physical RFID cards (MIFARE, NTAG via RC522) and emits:
 *     CARD|<UID-HEX>   → ArduinoBridge → link_money_card()
 *
 * No WiFi, no APDU, no phone NFC — RC522 is UID-read only.
 *
 * ═══════════════════════════════════════════════════════════════
 * HARDWARE WIRING
 * ═══════════════════════════════════════════════════════════════
 *
 * RC522 RFID Module (SPI):
 *   SDA/SS  → D10  (RC522_SS)
 *   MOSI    → D11  (SPI hardware)
 *   MISO    → D12  (SPI hardware)
 *   SCK     → D13  (SPI hardware)
 *   RST     → D8   (RC522_RST)
 *   VCC     → 3.3V
 *   GND     → GND
 *
 * LCD 16x2 with PCF8574 I2C backpack (software I2C):
 *   SDA     → D6   (LCD_SDA)
 *   SCL     → D7   (LCD_SCL)
 *   VCC     → 5V
 *   GND     → GND
 *   Default I2C address: 0x27 (try 0x3F if LCD is blank)
 *
 * Piezo buzzer:
 *   +       → D9   (PIEZO_PIN)
 *   -       → GND
 *
 * ═══════════════════════════════════════════════════════════════
 * REQUIRED LIBRARIES (install via Arduino Library Manager)
 * ═══════════════════════════════════════════════════════════════
 *   - "MFRC522" by GithubCommunity
 *
 * LCD uses inline bit-bang I2C — no extra library required.
 * ═══════════════════════════════════════════════════════════════
 */

#include <SPI.h>
#include <MFRC522.h>

// ── Pin assignments ──────────────────────────────────────────────
#define RC522_SS    10   // SPI chip-select
#define RC522_RST    8   // RC522 reset line
#define PIEZO_PIN    9   // Passive or active piezo buzzer
#define LCD_SDA      6   // Software I2C data line to PCF8574
#define LCD_SCL      7   // Software I2C clock line to PCF8574

// ── LCD I2C configuration ────────────────────────────────────────
#define LCD_ADDR    0x27
#define LCD_COLS    16
#define LCD_ROWS     2

// ── Tuning ───────────────────────────────────────────────────────
#define SCAN_COOLDOWN_MS  2000  // ms pause after card read (prevents double-scan)

// ── RC522 instance ───────────────────────────────────────────────
MFRC522 rfid(RC522_SS, RC522_RST);

// ═══════════════════════════════════════════════════════════════
// INLINE BIT-BANG I2C + PCF8574 LCD DRIVER
// No external library required — uses D6 (SDA) and D7 (SCL).
// ═══════════════════════════════════════════════════════════════

#define LCD_BL  0x08
#define LCD_E   0x04
#define LCD_RW  0x02
#define LCD_RS  0x01

void i2c_sda_high() { pinMode(LCD_SDA, INPUT);  }
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
  i2c_sda_high();
  delayMicroseconds(1);
  i2c_scl_high();
  delayMicroseconds(4);
  bool ack = (digitalRead(LCD_SDA) == LOW);
  i2c_scl_low();
  return ack;
}

void pcf8574_write(uint8_t val) {
  i2c_start();
  i2c_write_byte((LCD_ADDR << 1) | 0x00);
  i2c_write_byte(val);
  i2c_stop();
}

void lcd_pulse_enable(uint8_t val) {
  pcf8574_write(val | LCD_E);
  delayMicroseconds(1);
  pcf8574_write(val & ~LCD_E);
  delayMicroseconds(50);
}

void lcd_write_nibble(uint8_t nibble, uint8_t flags) {
  uint8_t b = (nibble & 0xF0) | flags | LCD_BL;
  lcd_pulse_enable(b);
}

void lcd_send(uint8_t data, bool rs) {
  uint8_t flags = rs ? LCD_RS : 0x00;
  lcd_write_nibble(data & 0xF0, flags);
  lcd_write_nibble((data << 4) & 0xF0, flags);
}

void lcd_command(uint8_t cmd) { lcd_send(cmd, false); }
void lcd_data(uint8_t ch)     { lcd_send(ch,  true);  }

static const uint8_t LCD_ROW_ADDR[2] = { 0x00, 0x40 };

void lcd_set_cursor(uint8_t col, uint8_t row) {
  lcd_command(0x80 | (LCD_ROW_ADDR[row] + col));
}

void lcd_clear() {
  lcd_command(0x01);
  delay(2);
}

void lcd_print(const char *str) {
  while (*str) lcd_data(*str++);
}

void lcd_init() {
  delay(50);
  pcf8574_write(LCD_BL);
  lcd_write_nibble(0x30, 0x00); delay(5);
  lcd_write_nibble(0x30, 0x00); delayMicroseconds(150);
  lcd_write_nibble(0x30, 0x00); delayMicroseconds(150);
  lcd_write_nibble(0x20, 0x00);
  lcd_command(0x28);
  lcd_command(0x0C);
  lcd_command(0x06);
  lcd_clear();
}

// ═══════════════════════════════════════════════════════════════
// UID HELPER
// ═══════════════════════════════════════════════════════════════

String uidToHex(byte *buf, byte len) {
  String result = "";
  for (byte i = 0; i < len; i++) {
    if (buf[i] < 0x10) result += "0";
    result += String(buf[i], HEX);
  }
  result.toUpperCase();
  return result;
}

// ═══════════════════════════════════════════════════════════════
// ARDUINO LIFECYCLE
// ═══════════════════════════════════════════════════════════════

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000);

  pinMode(PIEZO_PIN, OUTPUT);

  lcd_init();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  lcd_print("Starting...");

  SPI.begin();
  rfid.PCD_Init();

  // Verify RC522 is responding
  byte ver = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  if (ver == 0x00 || ver == 0xFF) {
    Serial.println("ERROR: RC522 not found — check SPI wiring (SS=D10, RST=D8)");
    lcd_clear();
    lcd_set_cursor(0, 0);
    lcd_print("RC522 ERROR");
    lcd_set_cursor(0, 1);
    lcd_print("Check wiring");
    while (1) delay(1000);
  }

  tone(PIEZO_PIN, 1000, 200);

  lcd_clear();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  lcd_print("Register mode");

  Serial.println("BANKONGSETON RFID registration ready");
}

void loop() {
  lcd_clear();
  lcd_set_cursor(0, 0);
  lcd_print("BANKONGSETON");
  lcd_set_cursor(0, 1);
  lcd_print("Tap card...");

  // Wait for a card to be present
  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial())   return;

  String uidHex = uidToHex(rfid.uid.uidByte, rfid.uid.size);

  // Emit to ArduinoBridge — triggers link_money_card()
  Serial.print("CARD|");
  Serial.println(uidHex);

  tone(PIEZO_PIN, 1000, 100);

  lcd_clear();
  lcd_set_cursor(0, 0);
  lcd_print("Card Read");
  lcd_set_cursor(0, 1);
  lcd_print(uidHex.substring(0, LCD_COLS).c_str());

  // Halt card and stop crypto — required before next read
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(SCAN_COOLDOWN_MS);
}
