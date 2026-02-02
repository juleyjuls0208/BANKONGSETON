/*
 * BANGKO NG SETON - ADMIN STATION
 * Card Registration & Balance Loading
 * 
 * PURPOSE: Register students, link cards, and load balances
 * 
 * This Arduino simply reads RFID cards and sends UIDs to Python.
 * All registration logic is handled by Python backend.
 * 
 * Hardware:
 * - Arduino UNO R3
 * - 1x RFID RC522 Module (SS=10, RST=9)
 * - 16x2 LCD with I2C (0x27 or 0x3F)
 * - Buzzer (Pin 8)
 * 
 * Pin Configuration:
 * - RFID: SS=10, RST=9, MOSI=11, MISO=12, SCK=13, VCC=3.3V
 * - LCD I2C: SDA=A4, SCL=A5, VCC=5V
 * - Buzzer: Pin 8
 */

#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ============================================
// PIN DEFINITIONS
// ============================================

#define SS_PIN          10
#define RST_PIN         9
#define PIEZO_PIN       8

// ============================================
// HARDWARE INITIALIZATION
// ============================================

MFRC522 rfid(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ============================================
// GLOBAL VARIABLES
// ============================================

String lastCardUID = "";
unsigned long lastReadTime = 0;
const unsigned long DEBOUNCE_TIME = 2000; // 2 seconds between reads

const char START_MARKER = '<';
const char END_MARKER = '>';

// ============================================
// SETUP
// ============================================

void setup() {
  Serial.begin(9600);
  while (!Serial);
  
  Serial.println("\n========================================");
  Serial.println("BANGKO NG SETON - ADMIN STATION");
  Serial.println("========================================\n");
  
  // Initialize buzzer
  pinMode(PIEZO_PIN, OUTPUT);
  digitalWrite(PIEZO_PIN, LOW);
  
  // Initialize SPI and RFID
  Serial.print("Initializing RFID reader... ");
  SPI.begin();
  rfid.PCD_Init();
  
  byte version = rfid.PCD_ReadRegister(rfid.VersionReg);
  if (version == 0x00 || version == 0xFF) {
    Serial.println("FAILED!");
    displayError("RFID Error");
    while(1);
  }
  Serial.println("OK");
  
  // Initialize LCD
  Serial.print("Initializing LCD... ");
  lcd.init();
  lcd.backlight();
  Serial.println("OK");
  
  // Test buzzer
  Serial.print("Testing buzzer... ");
  shortBeep();
  delay(500);
  Serial.println("OK");
  
  Serial.println("\n✓ Admin Station Ready!");
  Serial.println("Waiting for commands from Python...\n");
  
  displayIdle();
}

// ============================================
// MAIN LOOP
// ============================================

void loop() {
  // Check for commands from Python
  checkSerialCommands();
  
  // Continuously read cards
  readCard();
  
  delay(100);
}

// ============================================
// CARD READING
// ============================================

void readCard() {
  if (!rfid.PICC_IsNewCardPresent()) {
    return;
  }
  
  if (!rfid.PICC_ReadCardSerial()) {
    return;
  }
  
  // Build UID
  String cardUID = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) {
      cardUID += "0";
    }
    cardUID += String(rfid.uid.uidByte[i], HEX);
  }
  cardUID.toUpperCase();
  
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  
  // Debounce - avoid reading same card multiple times
  if (cardUID == lastCardUID && (millis() - lastReadTime) < DEBOUNCE_TIME) {
    return;
  }
  
  lastCardUID = cardUID;
  lastReadTime = millis();
  
  // Send card UID to Python
  Serial.print(START_MARKER);
  Serial.print("CARD");
  Serial.print("|");
  Serial.print(cardUID);
  Serial.println(END_MARKER);
  
  shortBeep();
  
  // Display on LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Card Read:");
  lcd.setCursor(0, 1);
  if (cardUID.length() > 16) {
    lcd.print(cardUID.substring(0, 16));
  } else {
    lcd.print(cardUID);
  }
  
  Serial.println("Card Read: " + cardUID);
}

// ============================================
// SERIAL COMMUNICATION
// ============================================

void checkSerialCommands() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.startsWith("<") && command.endsWith(">")) {
      command = command.substring(1, command.length() - 1);
      
      int sepIndex = command.indexOf('|');
      if (sepIndex > 0) {
        String cmd = command.substring(0, sepIndex);
        String message = command.substring(sepIndex + 1);
        
        if (cmd == "DISPLAY") {
          // Display message on LCD
          displayMessage(message);
        } else if (cmd == "SUCCESS") {
          // Success feedback
          successBeep();
          displaySuccess(message);
        } else if (cmd == "ERROR") {
          // Error feedback
          errorBeep();
          displayError(message);
        } else if (cmd == "CLEAR") {
          // Clear display
          displayIdle();
        }
      }
    }
  }
}

// ============================================
// DISPLAY FUNCTIONS
// ============================================

void displayIdle() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Admin Station");
  lcd.setCursor(0, 1);
  lcd.print("Ready...");
}

void displayMessage(String message) {
  lcd.clear();
  lcd.setCursor(0, 0);
  
  // Split message by | for two lines
  int sepIndex = message.indexOf('|');
  if (sepIndex > 0) {
    String line1 = message.substring(0, sepIndex);
    String line2 = message.substring(sepIndex + 1);
    
    if (line1.length() > 16) {
      line1 = line1.substring(0, 16);
    }
    if (line2.length() > 16) {
      line2 = line2.substring(0, 16);
    }
    
    lcd.print(line1);
    lcd.setCursor(0, 1);
    lcd.print(line2);
  } else {
    if (message.length() > 16) {
      lcd.print(message.substring(0, 16));
      lcd.setCursor(0, 1);
      lcd.print(message.substring(16, 32));
    } else {
      lcd.print(message);
    }
  }
}

void displaySuccess(String message) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SUCCESS!");
  lcd.setCursor(0, 1);
  if (message.length() > 16) {
    lcd.print(message.substring(0, 16));
  } else {
    lcd.print(message);
  }
  
  delay(2000);
  displayIdle();
}

void displayError(String message) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ERROR:");
  lcd.setCursor(0, 1);
  if (message.length() > 16) {
    lcd.print(message.substring(0, 16));
  } else {
    lcd.print(message);
  }
  
  delay(3000);
  displayIdle();
}

// ============================================
// BUZZER FUNCTIONS
// ============================================

void shortBeep() {
  for (int i = 0; i < 100; i++) {
    digitalWrite(PIEZO_PIN, HIGH);
    delayMicroseconds(250);
    digitalWrite(PIEZO_PIN, LOW);
    delayMicroseconds(250);
  }
  digitalWrite(PIEZO_PIN, LOW);
}

void successBeep() {
  shortBeep();
  delay(100);
  shortBeep();
  digitalWrite(PIEZO_PIN, LOW);
}

void errorBeep() {
  for (int i = 0; i < 200; i++) {
    digitalWrite(PIEZO_PIN, HIGH);
    delayMicroseconds(500);
    digitalWrite(PIEZO_PIN, LOW);
    delayMicroseconds(500);
  }
  digitalWrite(PIEZO_PIN, LOW);
}
