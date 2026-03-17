#!/usr/bin/env bash
set -euo pipefail

# S01 contract verification: RC522 Firmware Swap (R4 + R3)
# Run from project root: bash scripts/verify-m005-s01.sh

echo "=== S01: RC522 Firmware Swap — contract verification ==="

# Directory structure
echo "[1/9] R4 firmware file exists..."
test -f arduino/bankongseton_r4/bankongseton_r4.ino

echo "[2/9] R4 secrets.h exists..."
test -f arduino/bankongseton_r4/secrets.h

echo "[3/9] Old bankongseton_rfid/ directory is gone..."
! test -d arduino/bankongseton_rfid

# R4: correct reader library
echo "[4/9] R4 uses MFRC522..."
grep -q '#include <MFRC522.h>' arduino/bankongseton_r4/bankongseton_r4.ino

# R4: no PN532 / LCD / APDU references
echo "[5/9] R4 has no PN532/LCD/APDU code..."
! grep -qE 'PN532|pn532|Adafruit_PN532|lcd_|LCD_SDA|LCD_SCL|pcf8574|i2c_start|inDataExchange|SAMConfig|setRFField|httpPostNFC|NFC_TIMEOUT|APDU_MAX' arduino/bankongseton_r4/bankongseton_r4.ino

# R4: WiFi path preserved
echo "[6/9] R4 WiFi path preserved (httpPostCard, heartbeat, ensureWiFi)..."
grep -q 'httpPostCard' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'heartbeat' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'ensureWiFi' arduino/bankongseton_r4/bankongseton_r4.ino

# R4: OLED pin placeholder
echo "[7/9] R4 OLED placeholder present (Wire.h, OLED_ADDR)..."
grep -q '#include <Wire.h>' arduino/bankongseton_r4/bankongseton_r4.ino
grep -qE 'OLED_ADDR|OLED_WIDTH' arduino/bankongseton_r4/bankongseton_r4.ino

# R4: MFRC522 read pattern
echo "[8/9] R4 MFRC522 read pattern present..."
grep -qE 'PICC_IsNewCardPresent|PICC_ReadCardSerial' arduino/bankongseton_r4/bankongseton_r4.ino
grep -qE 'PICC_HaltA|PCD_StopCrypto1' arduino/bankongseton_r4/bankongseton_r4.ino

# R3: no PN532 references
echo "[9/9] R3 README and firmware have no PN532 references..."
! grep -qE 'PN532|pn532' arduino/bankongseton_nfc_r3/bankongseton_nfc_r3.ino
! grep -qE 'PN532|pn532' arduino/bankongseton_nfc_r3/README.md

echo ""
echo "✓ All S01 contract checks passed."
echo ""
echo "NEXT: Flash arduino/bankongseton_r4/bankongseton_r4.ino to R4 WiFi hardware,"
echo "      tap a physical RFID card, and confirm POST /api/arduino/card-read 200"
echo "      in the Flask log to complete integration verification."
