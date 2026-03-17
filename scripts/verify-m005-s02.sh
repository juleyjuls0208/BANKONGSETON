#!/usr/bin/env bash
set -euo pipefail

# S02 contract verification: OLED Driver + QR Polling on R4
# Run from project root: bash scripts/verify-m005-s02.sh

FIRMWARE="arduino/bankongseton_r4/bankongseton_r4.ino"

echo "=== S02: OLED Driver + QR Polling — contract verification ==="

echo "[1/9] Adafruit_SSD1306.h included..."
grep -q '#include <Adafruit_SSD1306.h>' "$FIRMWARE"

echo "[2/9] qrcode.h included..."
grep -q '#include "qrcode.h"' "$FIRMWARE"

echo "[3/9] display.begin() called in setup()..."
grep -q 'display.begin' "$FIRMWARE"

echo "[4/9] oledShowReady() function present..."
grep -q 'oledShowReady' "$FIRMWARE"

echo "[5/9] renderQr() function present..."
grep -q 'renderQr' "$FIRMWARE"

echo "[6/9] httpGetBody() function present..."
grep -q 'httpGetBody' "$FIRMWARE"

echo "[7/9] QR poll endpoint wired (/api/arduino/qr-pending)..."
grep -q 'qr-pending' "$FIRMWARE"

echo "[8/9] parseQrUrl() function present..."
grep -q 'parseQrUrl' "$FIRMWARE"

echo "[9/9] TODO S02 comment removed..."
! grep -q 'TODO S02' "$FIRMWARE"

echo ""
echo "✓ All S02 contract checks passed."
echo ""
echo "Diagnostic signals to verify on hardware (Arduino Serial Monitor @ 9600 baud):"
echo "  Boot (OLED present):  'BANKONGSETON RFID reader ready' + OLED shows 'Ready'"
echo "  Boot (OLED absent):   'OLED: init failed 0x3C — check I2C wiring (non-fatal)'"
echo "  QR rendered:          'QR: rendering v<N> scale=<N>px url=<url>'"
echo "  QR cleared:           'QR: idle (Ready)'"
echo "  URL too long:         'QR: version too small for URL length — max 154 chars (V7 ECC-L)'"
echo ""
echo "NEXT: Flash firmware → confirm OLED shows 'Ready' → test QR scan with phone camera."
