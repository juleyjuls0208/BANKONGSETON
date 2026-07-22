/*
 * BANKONGSETON — Arduino UNO R3 RFID registration reader (RC522 over SPI)
 * Reads card UID and emits CARD|<UID-HEX> to the panel over USB serial.
 * No LCD (LCD code removed), no WiFi. Piezo for feedback only.
 *
 * Protocol (panel → reader):
 *   PING                 → replies PONG + connect beep
 * Reader → panel:
 *   CARD|<uid-hex>       → on tap
 *   PONG                 → reply to PING
 *   BANKONGSETON RFID reader ready   → at boot
 *
 * WIRING (RC522 SDA = SPI SS):
 *   RC522 SDA  → D10
 *   RC522 RST  → D2
 *   RC522 SCK  → D13
 *   RC522 MOSI → D11
 *   RC522 MISO → D12
 *   RC522 3.3V → 3.3V
 *   RC522 GND  → GND
 *   RC522 IRQ  → (nc)
 *   Piezo +    → D7
 *   Piezo -    → GND
 *
 * LIBRARY: "MFRC522" by GithubCommunity
 */

#include <SPI.h>
#include <MFRC522.h>

#define RC522_SS    10
#define RC522_RST    2
#define PIEZO_PIN    7
#define SCAN_COOLDOWN_MS  2000

MFRC522 rfid(RC522_SS, RC522_RST);
bool rc522Ok = true;

void boot_tone()    { tone(PIEZO_PIN, 660, 120); delay(150); tone(PIEZO_PIN, 660, 120); }
void connect_tone() { tone(PIEZO_PIN, 880, 120); }
void success_beep() { tone(PIEZO_PIN, 880, 90);  delay(110); tone(PIEZO_PIN, 1175, 150); }
void error_beep()   { tone(PIEZO_PIN, 220, 350); }
void read_beep()    { tone(PIEZO_PIN, 1000, 100); }

String uidToHex(byte *buf, byte len) {
  String result = "";
  for (byte i = 0; i < len; i++) {
    if (buf[i] < 0x10) result += "0";
    result += String(buf[i], HEX);
  }
  result.toUpperCase();
  return result;
}

void process_command(String cmd) {
  cmd.trim();
  if (cmd == "PING") {
    Serial.println("PONG");
    connect_tone();
  } else if (cmd.startsWith("<SUCCESS|")) {
    // The R3 has no display, but keep the panel's feedback contract.
    success_beep();
  } else if (cmd.startsWith("<ERROR|")) {
    error_beep();
  } else if (cmd.startsWith("<DISPLAY|")) {
    // Display commands are intentionally ignored in serial-only R3 mode.
  }
}

void read_serial_commands() {
  static String buf = "";
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (buf.length() > 0) { process_command(buf); buf = ""; }
    } else if (buf.length() < 64) {
      buf += c;
    }
  }
}

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000);

  pinMode(PIEZO_PIN, OUTPUT);
  boot_tone();

  SPI.begin();
  rfid.PCD_Init();
  rfid.PCD_AntennaOn();   // ponytail: clone RC522 often leaves antenna off

  byte ver = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  if (ver == 0x00 || ver == 0xFF) {
    rc522Ok = false;
    Serial.println("ERROR: RC522 not found — check SPI wiring (SDA=D10, RST=D2)");
    error_beep();
  } else {
    Serial.println("BANKONGSETON RFID reader ready");
  }
}

void loop() {
  read_serial_commands();
  if (!rc522Ok) return;

  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial())   return;

  String uidHex = uidToHex(rfid.uid.uidByte, rfid.uid.size);
  Serial.print("CARD|");
  Serial.println(uidHex);
  read_beep();

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(SCAN_COOLDOWN_MS);
}
