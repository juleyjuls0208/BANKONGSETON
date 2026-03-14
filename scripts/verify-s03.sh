#!/usr/bin/env bash
# verify-s03.sh — S03: FraudDetector Constraint & Health Standardization verification
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

echo "=== S03 Verification: FraudDetector Constraint & Health Standardization ==="
echo ""

echo "--- Group 1: Syntax (4 checks) ---"
check "web_app.py compiles"          "python -m py_compile backend/dashboard/web_app.py"
check "admin_dashboard.py compiles"  "python -m py_compile backend/dashboard/admin_dashboard.py"
check "dashboard_core.py compiles"   "python -m py_compile backend/dashboard/dashboard_core.py"
check "api_server.py compiles"       "python -m py_compile backend/api/api_server.py"

echo ""
echo "--- Group 2: WEB_CONCURRENCY guard (4 checks) ---"
check "WEB_CONCURRENCY checked in web_app.py"             "grep -q 'WEB_CONCURRENCY' backend/dashboard/web_app.py"
check "GUNICORN_WORKERS checked in web_app.py"            "grep -q 'GUNICORN_WORKERS' backend/dashboard/web_app.py"
check "Guard message present in web_app.py"               "grep -q 'FraudDetector requires single-worker' backend/dashboard/web_app.py"
check "Guard message present in admin_dashboard.py"       "grep -q 'FraudDetector requires single-worker' backend/dashboard/admin_dashboard.py"

echo ""
echo "--- Group 3: Health schema fields — dashboard_core.py (4 checks) ---"
check "sheets_ok field in dashboard_core.py health handler"    "grep -A40 'def health_check' backend/dashboard/dashboard_core.py | grep -q 'sheets_ok'"
check "latency_ms field in dashboard_core.py health handler"   "grep -A40 'def health_check' backend/dashboard/dashboard_core.py | grep -q 'latency_ms'"
check "queue_pending field in dashboard_core.py health handler" "grep -A40 'def health_check' backend/dashboard/dashboard_core.py | grep -q 'queue_pending'"
check "timestamp field in dashboard_core.py health handler"    "grep -A40 'def health_check' backend/dashboard/dashboard_core.py | grep -q 'timestamp'"

echo ""
echo "--- Group 4: Health schema fields — api_server.py (4 checks) ---"
check "sheets_ok field in api_server.py health handler"        "grep -A40 'def health_check' backend/api/api_server.py | grep -q 'sheets_ok'"
check "latency_ms field in api_server.py health handler"       "grep -A40 'def health_check' backend/api/api_server.py | grep -q 'latency_ms'"
check "queue_pending field in api_server.py health handler"    "grep -A40 'def health_check' backend/api/api_server.py | grep -q 'queue_pending'"
check "get_offline_queue import attempted in api_server.py"    "grep -q 'get_offline_queue\|offline_queue' backend/api/api_server.py"

echo ""
echo "--- Group 5: 503 on Sheets failure (2 checks) ---"
check "503 returned in dashboard_core.py health_check"         "grep -A40 'def health_check' backend/dashboard/dashboard_core.py | grep -q '503'"
check "503 returned in api_server.py health_check"             "grep -A40 'def health_check' backend/api/api_server.py | grep -q '503'"

echo ""
echo "========================================"
echo "Results: ${PASS} passed, ${FAIL} failed"
if [ "$FAIL" -eq 0 ]; then
    echo "S03 verification PASSED ✓"
    exit 0
else
    echo "S03 verification FAILED ✗"
    exit 1
fi
