/*
 * BANGONGSETON — Loading Kiosk Firmware (Arduino UNO R4 WiFi)
 *
 * A dedicated top-up terminal. Reads money cards (RFID) and cash (bill
 * validator) and reports them over USB-Serial to the Python kiosk app
 * (backend/kiosk/kiosk_app.py), which credits the student's card.
 *
 * Serial wire protocol (consumed by ArduinoBridge + kiosk_app):
 *   CARD|<UID-HEX>      → a money card was tapped
 *   BILL|<amount>       → a bill was accepted (e.g. BILL|100)
 *   PONG                → heartbeat reply (optional)
 *
 * The same CARD| line is understood by the existing dashboard/tech apps, so
 * this firmware is drop-in compatible with the whole fleet.
 *
 * ───────────────────────────────────────────────────────────────────
 * HARDWARE WIRING
 * ───────────────────────────────────────────────────────────────────
 * RC522 RFID Module (SPI):
 *   SDA/SS  → D10        MOSI → D11   MISO → D12   SCK → D13   RST → D9
 *   VCC     → 3.3V       GND  → GND
 *
 * Bill Validator (pulse / serial type, e.g. CNC or generic 3-wire):
 *   Connect the "credit pulse" line to BILL_PULSE_PIN (D2, interrupt-capable).
 *   Each pulse = one bill denomination (see BILL_DENOMINATIONS below).
 *   (For a serial bill acceptor, adapt billAccepted() to parse its frame and
 *    call reportBill(<amount>).)
 *
 * QR Scanner Module (USB/HID or serial):
 *   Most standalone QR scanner modules appear as a serial keyboard or UART.
 *   If yours outputs UART, connect its TX → D0/RX (or a SoftwareSerial pin)
 *   and forward scanned text with QR|<text>. For an HID scanner the phone
 *   shows the QR; this firmware only needs to forward serial QR modules.
 *
 * OLED 128x64 (I2C, 0x3C): SDA → A4   SCL → A5   VCC → 3.3V/5V   GND → GND
 * Piezo buzzer: + → D8   - → GND
 *
 * ───────────────────────────────────────────────────────────────────
 * REQUIRED LIBRARIES (Arduino Library Manager)
 *   - MFRC522 (GithubCommunity)
 *   - Adafruit SSD1306 + Adafruit GFX
 *   - Wire, SPI (built-in)
 * ───────────────────────────────────────────────────────────────────
 */

#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ── RC522 ──────────────────────────────────────────────────────────
#define RC522_SS   10
#define RC522_RST  9
MFRC522 rfid(RC522_SS, RC522_RST);

// ── OLED ───────────────────────────────────────────────────────────
#define SCREEN_W 128
#define SCREEN_H 64
#define OLED_ADDR 0x3C
Adafruit_SSD1306 oled(SCREEN_W, SCREEN_H, &Wire, -1);

// ── Buzzer / pins ──────────────────────────────────────────────────
#define PIEZO_PIN 8
#define BILL_PULSE_PIN 2   // interrupt pin for bill validator pulse

// ── Bill validator: pulses per bill denomination ───────────────────
// If your acceptor sends 1 pulse per accepted bill of a FIXED value, set
// BILL_PULSE_VALUE to that value (e.g. 100 for a ₱100-only acceptor).
// For multi-denomination acceptors, wire each denomination to its own pin
// or parse the serial frame and call reportBill() directly.
#define BILL_PULSE_VALUE 0   // 0 = disabled (use preset buttons in UI)

// ── QR scanner (optional UART module) ──────────────────────────────
// Set QR_UART to true if a serial QR module is wired to QR_RX_PIN.
#define QR_UART false
#define QR_RX_PIN 0          // connect QR module TX here (e.g. via SoftwareSerial)

// ── State ──────────────────────────────────────────────────────────
volatile int billPulseCount = 0;
unsigned long lastPulseMs = 0;
bool oledOk = false;   // set from oled.begin() in setup; gates OLED writes if absent

void setup() {
  Serial.begin(9600);
  while (!Serial) { delay(10); }

  SPI.begin();
  rfid.PCD_Init();

  pinMode(PIEZO_PIN, OUTPUT);
  if (BILL_PULSE_VALUE > 0) {
    pinMode(BILL_PULSE_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(BILL_PULSE_PIN), onBillPulse, FALLING);
  }

  oledOk = oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
  if (!oledOk) {
    // OLED optional; continue without it.
  } else {
    oled.clearDisplay();
    oled.setTextSize(1);
    oled.setTextColor(SSD1306_WHITE);
    oled.setCursor(0, 0);
    oled.println("Bangko ng Seton");
    oled.println("Loading Kiosk");
    oled.display();
  }
  showReady();
}

void loop() {
  // Drain any QR-module UART input (if enabled).
  if (QR_UART && Serial1.available()) {
    String qr = Serial1.readStringUntil('\n');
    qr.trim();
    if (qr.length()) {
      Serial.print("QR|");
      Serial.println(qr);
    }
  }

  // Card tap?
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    String uid = uidHex();
    Serial.print("CARD|");
    Serial.println(uid);
    beep(1);
    showCard(uid);
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
    delay(800);  // debounce
    showReady();
  }

  // Flush accumulated bill pulses (debounced) every 50ms.
  if (billPulseCount > 0 && millis() - lastPulseMs > 50) {
    int pulses = billPulseCount;
    billPulseCount = 0;
    float amount = pulses * (float)BILL_PULSE_VALUE;
    reportBill(amount);
  }

  // Heartbeat / echo for the bridge.
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "PING") { Serial.println("PONG"); }
  }

  delay(20);
}

// ── Helpers ────────────────────────────────────────────────────────
void onBillPulse() {
  // Debounce within ISR.
  unsigned long now = millis();
  if (now - lastPulseMs > 30) {
    billPulseCount++;
    lastPulseMs = now;
  }
}

void reportBill(float amount) {
  Serial.print("BILL|");
  Serial.println(amount, 0);
  beep(2);
  showLoad(amount);
}

String uidHex() {
  String s;
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) s += "0";
    s += String(rfid.uid.uidByte[i], HEX);
  }
  s.toUpperCase();
  return s;
}

void beep(int n) {
  for (int i = 0; i < n; i++) {
    digitalWrite(PIEZO_PIN, HIGH);
    delay(80);
    digitalWrite(PIEZO_PIN, LOW);
    delay(80);
  }
}

void showReady() {
  if (!oledInitialized()) return;
  oled.clearDisplay();
  oled.setCursor(0, 0);
  oled.println("Tap money card");
  oled.println("or scan app QR");
  oled.display();
}

void showCard(String uid) {
  if (!oledInitialized()) return;
  oled.clearDisplay();
  oled.setCursor(0, 0);
  oled.println("Card read:");
  oled.println(uid);
  oled.display();
}

void showLoad(float amt) {
  if (!oledInitialized()) return;
  oled.clearDisplay();
  oled.setCursor(0, 0);
  oled.print("Bill: PHP ");
  oled.println((int)amt);
  oled.display();
}

bool oledInitialized() {
  // True only when oled.begin() succeeded in setup (display present).
  return oledOk;
}
