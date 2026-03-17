#!/usr/bin/env bash
set -euo pipefail

# S02 contract verification: OLED Driver + QR Polling on R4
# Run from project root: bash scripts/verify-m005-s02.sh

echo "=== S02: OLED Driver + QR Polling on R4 — contract verification ==="

# OLED driver
echo "[1/9] Adafruit_SSD1306.h include present..."
grep -q '^#include <Adafruit_SSD1306.h>' arduino/bankongseton_r4/bankongseton_r4.ino

echo "[2/9] qrcode.h include present..."
grep -q '#include "qrcode.h"' arduino/bankongseton_r4/bankongseton_r4.ino

echo "[3/9] display.begin called in setup..."
grep -q 'display\.begin' arduino/bankongseton_r4/bankongseton_r4.ino

echo "[4/9] oledShowReady function present..."
grep -q 'oledShowReady' arduino/bankongseton_r4/bankongseton_r4.ino

echo "[5/9] renderQr function present (qrcode_initText + qrcode_getModule)..."
grep -q 'qrcode_initText' arduino/bankongseton_r4/bankongseton_r4.ino
grep -q 'qrcode_getModule' arduino/bankongseton_r4/bankongseton_r4.ino

echo "[6/9] httpGetBody function present..."
grep -q 'httpGetBody' arduino/bankongseton_r4/bankongseton_r4.ino

echo "[7/9] qr-pending endpoint polled..."
grep -q 'qr-pending' arduino/bankongseton_r4/bankongseton_r4.ino

echo "[8/9] parseQrUrl function present..."
grep -q 'parseQrUrl' arduino/bankongseton_r4/bankongseton_r4.ino

echo "[9/9] TODO S02 comment removed..."
! grep -q 'TODO S02' arduino/bankongseton_r4/bankongseton_r4.ino

echo ""
echo "✓ All S02 contract checks passed."
echo ""
echo "NEXT: Flash arduino/bankongseton_r4/bankongseton_r4.ino to R4 hardware."
echo "      Serial Monitor (9600 baud): confirm 'BANKONGSETON RFID reader ready'."
echo "      OLED should show 'Ready' on boot."
echo "      Trigger a QR via /api/arduino/qr-pending and confirm OLED renders scannable code."
