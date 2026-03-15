#!/usr/bin/env bash
# verify-m003-s04.sh — S04: Powerbank Hardening + Wireless Docs structural grep assertions
# Usage: bash scripts/verify-m003-s04.sh
# Run from the repository root.
set -euo pipefail

PASS=0
FAIL=0

check() {
    local desc="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        echo "  ✓ $desc"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $desc"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== M003/S04 Verification: Powerbank Hardening + Wireless Docs ==="
echo ""

echo "--- Group 1: Firmware — bankongseton_rfid.ino (4 checks) ---"
check "(a) lastHeartbeatMs variable declared in firmware" \
    "grep -q 'lastHeartbeatMs' arduino/bankongseton_rfid/bankongseton_rfid.ino"
check "(b) httpPostJson heartbeat call present in firmware" \
    "grep -qE 'httpPostJson.*heartbeat' arduino/bankongseton_rfid/bankongseton_rfid.ino"
check "(c) HEARTBEAT_INTERVAL_MS constant not a stub" \
    "! grep -qiE 'HEARTBEAT_INTERVAL_MS.*(stub|not yet)' arduino/bankongseton_rfid/bankongseton_rfid.ino"
check "(d) ensureWiFi present in firmware (keep-alive called before heartbeat POST)" \
    "grep -q 'ensureWiFi' arduino/bankongseton_rfid/bankongseton_rfid.ino"

echo ""
echo "--- Group 2: Documentation — arduino/README-wireless.md (4 checks) ---"
check "(e) arduino/README-wireless.md file exists" \
    "test -f arduino/README-wireless.md"
check "(f) README documents port 5003 explicitly" \
    "grep -q '5003' arduino/README-wireless.md"
check "(g) README names ARDUINO_API_KEY (Flask env var for API key matching)" \
    "grep -q 'ARDUINO_API_KEY' arduino/README-wireless.md"
check "(h) README includes powerbank guidance" \
    "grep -qi 'powerbank' arduino/README-wireless.md"

echo ""
echo "========================================"
echo "Results: ${PASS} passed, ${FAIL} failed"
if [ "$FAIL" -eq 0 ]; then
    echo "verify-m003-s04: all 8 checks passed ✓"
    exit 0
else
    echo "M003/S04 verification FAILED ✗"
    exit 1
fi
