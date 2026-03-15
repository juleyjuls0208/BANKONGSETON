#!/usr/bin/env bash
# verify-m003-s03.sh — S03: WiFi Status Indicator structural grep assertions
# Usage: bash scripts/verify-m003-s03.sh
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

echo "=== M003/S03 Verification: WiFi Status Indicator ==="
echo ""

echo "--- Group 1: Backend — web_app.py (5 checks) ---"
check "(a) import time at module level in web_app.py" \
    "grep -q '^import time' backend/dashboard/web_app.py"
check "(b) ARDUINO_WIFI_OFFLINE_S constant defined in web_app.py" \
    "grep -q 'ARDUINO_WIFI_OFFLINE_S' backend/dashboard/web_app.py"
check "(c) app.arduino_last_heartbeat initialized in web_app.py" \
    "grep -q 'app\.arduino_last_heartbeat' backend/dashboard/web_app.py"
check "(d) /api/arduino/heartbeat route in web_app.py" \
    "grep -q 'arduino/heartbeat' backend/dashboard/web_app.py"
check "(e) socketio.emit arduino_wifi_status in web_app.py" \
    "grep -q 'arduino_wifi_status' backend/dashboard/web_app.py"

echo ""
echo "--- Group 2: Backend — cashier_routes.py (2 checks) ---"
check "(f) /api/arduino-wifi-status route in cashier_routes.py" \
    "grep -q 'arduino-wifi-status\|arduino_wifi_status' backend/dashboard/cashier/cashier_routes.py"
check "(g) jwt_required on arduino wifi status route" \
    "grep -B2 'arduino.wifi.status\|arduino-wifi-status' backend/dashboard/cashier/cashier_routes.py | grep -q 'jwt_required'"

echo ""
echo "--- Group 3: Frontend — cashier_index.html (3 checks) ---"
check "(h) wifiBadge span present in cashier_index.html" \
    "grep -q 'wifiBadge' backend/dashboard/cashier/templates/cashier_index.html"
check "(i) arduino_wifi_status socket listener in cashier_index.html" \
    "grep -q 'arduino_wifi_status' backend/dashboard/cashier/templates/cashier_index.html"
check "(j) old COM-port-only alert text removed from cashier_index.html" \
    "! grep -q 'COM port first' backend/dashboard/cashier/templates/cashier_index.html"

echo ""
echo "--- Compile checks ---"
check "(k) web_app.py compiles cleanly" \
    "python -m py_compile backend/dashboard/web_app.py"
check "(l) cashier_routes.py compiles cleanly" \
    "python -m py_compile backend/dashboard/cashier/cashier_routes.py"

echo ""
echo "========================================"
echo "Results: ${PASS} passed, ${FAIL} failed"
if [ "$FAIL" -eq 0 ]; then
    echo "M003/S03 verification PASSED ✓"
    exit 0
else
    echo "M003/S03 verification FAILED ✗"
    exit 1
fi
