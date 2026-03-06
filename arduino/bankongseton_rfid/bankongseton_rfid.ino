/*
 * BANKONGSETON — Arduino UNO R4 WiFi RFID reader
 *
 * Reads MFRC522 card UID → POST /api/arduino/card-read → Flask
 * Falls back to Serial ("CARD|UID") after MAX_RETRIES failures.
 *
 * Hardware:
 *   MFRC522 SS=10, RST=9 (standard SPI)
 *
 * Required libraries:
 *   MFRC522 by miguelbalboa
 *   WiFiS3 (built-in for UNO R4 WiFi)
 *
 * Setup: copy secrets.h.example → secrets.h, fill in credentials.
 */

#include <SPI.h>
#include <MFRC522.h>
#include <WiFiS3.h>
#include "secrets.h"

// ── Pin assignments ─────────────────────────────────────────────
#define SS_PIN  10
#define RST_PIN  9

// ── Tuning constants ────────────────────────────────────────────
static const int   MAX_RETRIES       = 3;
static const int   RETRY_DELAY_MS    = 2000;
static const int   SCAN_COOLDOWN_MS  = 1000;  // avoid double-reads
static const int   HTTP_TIMEOUT_MS   = 5000;

MFRC522 mfrc522(SS_PIN, RST_PIN);

// ─────────────────────────────────────────────────────────────────
// WiFi helpers
// ─────────────────────────────────────────────────────────────────

void connectWiFi() {
  // Detect missing WiFi module before attempting anything
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("ERROR: WiFi module not found");
    while (true) delay(1000);  // halt — no point continuing
  }

  Serial.print("Connecting to ");
  Serial.println(SECRET_SSID);

  WiFi.begin(SECRET_SSID, SECRET_PASS);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("WiFi connected. IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("WARNING: WiFi connect failed — will retry before each scan");
  }
}

// Ensure WiFi is connected; reconnect non-blocking if dropped.
// Returns true if connected after the attempt.
bool ensureWiFi() {
  if (WiFi.status() == WL_CONNECTED) return true;

  Serial.println("WiFi lost — reconnecting...");
  WiFi.begin(SECRET_SSID, SECRET_PASS);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 8000) {
    delay(500);
  }

  return WiFi.status() == WL_CONNECTED;
}

// ─────────────────────────────────────────────────────────────────
// HTTP POST helper
// ─────────────────────────────────────────────────────────────────

// Posts {"uid": "<uid>"} to Flask.
// Returns true on HTTP 200, false on any error.
bool httpPost(const String &uid) {
  WiFiClient client;

  // FLASK_HOST format: "192.168.x.x:5000"
  String host = String(FLASK_HOST);
  int colonIdx = host.indexOf(':');
  String ip   = (colonIdx >= 0) ? host.substring(0, colonIdx) : host;
  int    port  = (colonIdx >= 0) ? host.substring(colonIdx + 1).toInt() : 80;

  if (!client.connect(ip.c_str(), port)) {
    Serial.println("HTTP: connect failed");
    return false;
  }

  // Build JSON body
  String body = "{\"uid\":\"" + uid + "\"}";

  // Raw HTTP/1.0 POST — Content-Length header is REQUIRED (Flask hangs without it)
  client.println("POST /api/arduino/card-read HTTP/1.0");
  client.println("Host: " + String(FLASK_HOST));
  client.println("Content-Type: application/json");
  client.println("X-API-Key: " + String(SECRET_API_KEY));
  client.println("Content-Length: " + String(body.length()));
  client.println("Connection: close");
  client.println();
  client.println(body);

  // Wait for response with timeout
  unsigned long start = millis();
  while (!client.available() && millis() - start < HTTP_TIMEOUT_MS) {
    delay(10);
  }

  // Read status line (e.g. "HTTP/1.0 200 OK")
  String statusLine = client.readStringUntil('\n');
  client.stop();

  bool ok = statusLine.indexOf("200") >= 0;
  if (!ok) {
    Serial.print("HTTP: non-200 response: ");
    Serial.println(statusLine);
  }
  return ok;
}

// ─────────────────────────────────────────────────────────────────
// UID → string helper
// ─────────────────────────────────────────────────────────────────

String uidToHex(MFRC522::Uid &uid) {
  String result = "";
  for (byte i = 0; i < uid.size; i++) {
    if (uid.uidByte[i] < 0x10) result += "0";
    result += String(uid.uidByte[i], HEX);
  }
  result.toUpperCase();
  return result;
}

// ─────────────────────────────────────────────────────────────────
// Card scan + delivery
// ─────────────────────────────────────────────────────────────────

// Attempts to deliver uid to Flask with MAX_RETRIES.
// Falls back to serial on all failures (ARDW-04).
void deliverUID(const String &uid) {
  // Ensure WiFi is up before first attempt
  bool wifiOk = ensureWiFi();

  if (wifiOk) {
    for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
      Serial.print("HTTP attempt ");
      Serial.print(attempt);
      Serial.print("/");
      Serial.println(MAX_RETRIES);

      if (httpPost(uid)) {
        Serial.println("HTTP: card delivered — " + uid);
        return;  // success — no serial fallback needed
      }

      if (attempt < MAX_RETRIES) {
        delay(RETRY_DELAY_MS);
        ensureWiFi();  // reconnect between retries if needed
      }
    }
  }

  // All retries exhausted (or WiFi never connected) — serial fallback
  Serial.print("CARD|");
  Serial.println(uid);
}

// ─────────────────────────────────────────────────────────────────
// Arduino lifecycle
// ─────────────────────────────────────────────────────────────────

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000);  // wait up to 3 s for Serial Monitor

  Serial.println("BANKONGSETON RFID reader starting...");

  SPI.begin();
  mfrc522.PCD_Init();
  mfrc522.PCD_DumpVersionToSerial();  // confirm reader is wired correctly

  connectWiFi();
  Serial.println("Ready — waiting for card...");
}

void loop() {
  // Wait for a card
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial())   return;

  String uid = uidToHex(mfrc522.uid);
  Serial.println("Card detected: " + uid);

  deliverUID(uid);

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();

  delay(SCAN_COOLDOWN_MS);  // debounce — prevent double-reads
}
