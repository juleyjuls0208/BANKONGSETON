/*
 * BANGKO NG SETON - CASHIER STATION
 * Payment & Attendance System
 * 
 * PURPOSE: Process student payments at cashier
 * 
 * WORKFLOW:
 * 1. Student taps Money Card → System validates and shows balance
 * 2. Student taps ID Card → System processes payment & logs attendance
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
// SYSTEM STATE MACHINE
// ============================================

enum SystemState {
  IDLE,
  WAITING_MONEY_CARD,
  VALIDATING_MONEY,
  WAITING_ID_CARD,
  PROCESSING,
  SUCCESS,
  ERROR
};

SystemState currentState = IDLE;

// ============================================
// GLOBAL VARIABLES
// ============================================

String moneyCardUID = "";
String idCardUID = "";
unsigned long stateStartTime = 0;
const unsigned long STATE_TIMEOUT = 60000;

const char START_MARKER = '<';
const char END_MARKER = '>';
const char SEPARATOR = '|';

// ============================================
// SETUP
// ============================================

void setup() {
  Serial.begin(9600);
  while (!Serial);
  
  Serial.println("\n========================================");
  Serial.println("BANGKO NG SETON - CASHIER STATION");
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
  
  Serial.println("\n✓ Cashier Station Ready!");
  Serial.println("Waiting for money card...\n");
  
  displayIdle();
  currentState = WAITING_MONEY_CARD;
  stateStartTime = millis();
}

// ============================================
// MAIN LOOP
// ============================================

void loop() {
  // Timeout check
  if (millis() - stateStartTime > STATE_TIMEOUT) {
    if (currentState != WAITING_MONEY_CARD && currentState != IDLE) {
      Serial.println("Timeout! Resetting...");
      resetToIdle();
    }
  }
  
  // Check for backend responses
  checkSerialResponse();
  
  // State machine
  switch (currentState) {
    case WAITING_MONEY_CARD:
      checkForCard(true);
      break;
      
    case VALIDATING_MONEY:
      // Waiting for backend
      break;
      
    case WAITING_ID_CARD:
      checkForCard(false);
      break;
      
    case PROCESSING:
      // Waiting for backend
      break;
      
    case SUCCESS:
    case ERROR:
      // Handled by response handlers
      break;
  }
}

// ============================================
// CARD READING
// ============================================

void checkForCard(bool isMoneyCard) {
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
  
  shortBeep();
  
  if (isMoneyCard) {
    // Money card tap
    moneyCardUID = cardUID;
    Serial.println("Money Card: " + moneyCardUID);
    
    // Send CHECK command
    Serial.print(START_MARKER);
    Serial.print("CHECK");
    Serial.print(SEPARATOR);
    Serial.print(moneyCardUID);
    Serial.println(END_MARKER);
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Checking Card...");
    lcd.setCursor(0, 1);
    lcd.print("Please Wait");
    
    currentState = VALIDATING_MONEY;
    stateStartTime = millis();
    
  } else {
    // ID card tap
    idCardUID = cardUID;
    Serial.println("ID Card: " + idCardUID);
    
    // Send VERIFY command with both cards
    Serial.print(START_MARKER);
    Serial.print("VERIFY");
    Serial.print(SEPARATOR);
    Serial.print(moneyCardUID);
    Serial.print(SEPARATOR);
    Serial.print(idCardUID);
    Serial.println(END_MARKER);
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Processing...");
    lcd.setCursor(0, 1);
    lcd.print("Please Wait");
    
    currentState = PROCESSING;
    stateStartTime = millis();
  }
}

// ============================================
// SERIAL COMMUNICATION
// ============================================

void checkSerialResponse() {
  if (Serial.available() > 0) {
    String response = Serial.readStringUntil('\n');
    response.trim();
    
    Serial.println("Response: " + response);
    
    if (response.startsWith("<") && response.endsWith(">")) {
      response = response.substring(1, response.length() - 1);
      
      int firstSep = response.indexOf(SEPARATOR);
      if (firstSep > 0) {
        String status = response.substring(0, firstSep);
        String message = response.substring(firstSep + 1);
        
        if (status == "SUCCESS") {
          handleSuccess(message);
        } else if (status == "ERROR") {
          handleError(message);
        } else if (status == "BALANCE") {
          handleBalance(message);
        }
      }
    }
  }
}

// ============================================
// RESPONSE HANDLERS
// ============================================

void handleBalance(String balance) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Balance: P");
  lcd.print(balance);
  lcd.setCursor(0, 1);
  lcd.print("Tap ID Card Now");
  
  Serial.println("✓ Card valid. Balance: P" + balance);
  Serial.println("Waiting for ID card tap...");
  
  currentState = WAITING_ID_CARD;
  stateStartTime = millis();
}

void handleSuccess(String message) {
  int sep1 = message.indexOf(SEPARATOR);
  int sep2 = message.indexOf(SEPARATOR, sep1 + 1);
  
  if (sep1 == -1 || sep2 == -1) {
    handleError("Invalid response");
    return;
  }
  
  String userName = message.substring(0, sep1);
  String amount = message.substring(sep1 + 1, sep2);
  String newBalance = message.substring(sep2 + 1);
  
  successBeep();
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Welcome ");
  if (userName.length() > 7) {
    lcd.print(userName.substring(0, 7));
  } else {
    lcd.print(userName);
  }
  lcd.print("!");
  
  lcd.setCursor(0, 1);
  lcd.print("Paid: P");
  lcd.print(amount);
  
  Serial.println("✓ SUCCESS: " + userName + " paid P" + amount);
  
  delay(3000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("New Balance:");
  lcd.setCursor(0, 1);
  lcd.print("P");
  lcd.print(newBalance);
  
  delay(2000);
  resetToIdle();
}

void handleError(String errorMsg) {
  errorBeep();
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ERROR:");
  lcd.setCursor(0, 1);
  if (errorMsg.length() > 16) {
    lcd.print(errorMsg.substring(0, 16));
  } else {
    lcd.print(errorMsg);
  }
  
  Serial.println("✗ ERROR: " + errorMsg);
  
  delay(3000);
  resetToIdle();
}

// ============================================
// DISPLAY FUNCTIONS
// ============================================

void displayIdle() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Bangko ng Seton");
  lcd.setCursor(0, 1);
  lcd.print("Tap Money Card");
}

void displayError(String msg) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ERROR:");
  lcd.setCursor(0, 1);
  lcd.print(msg);
}

void resetToIdle() {
  moneyCardUID = "";
  idCardUID = "";
  currentState = WAITING_MONEY_CARD;
  stateStartTime = millis();
  displayIdle();
  Serial.println("\nReset to idle.\n");
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
