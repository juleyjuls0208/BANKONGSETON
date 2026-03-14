#!/usr/bin/env bash
# verify-s02.sh — S02: Cache Layer Wiring verification
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

echo "=== S02 Verification: Cache Layer Wiring ==="
echo ""

echo "--- T01: No merge conflict markers ---"
check "api_server.py has no conflict markers"        "! grep -qP '^(<{7} |={7}$|>{7} )' backend/api/api_server.py"
check "cashier_routes.py has no conflict markers"   "! grep -q '<<<<<<<\|=======\|>>>>>>>' backend/dashboard/cashier/cashier_routes.py"

echo ""
echo "--- T01: Syntax validity ---"
check "api_server.py compiles"        "python -m py_compile backend/api/api_server.py"
check "cashier_routes.py compiles"    "python -m py_compile backend/dashboard/cashier/cashier_routes.py"
check "admin_dashboard.py compiles"   "python -m py_compile backend/dashboard/admin_dashboard.py"

echo ""
echo "--- T01: NFC setup present in api_server.py ---"
check "nfc_service singleton defined"    "grep -q 'nfc_service = NFCService' backend/api/api_server.py"
check "_card_locks defined"              "grep -q '_card_locks.*dict' backend/api/api_server.py"
check "cache imported in api_server"     "grep -q 'from cache import.*get_cached.*set_cached' backend/api/api_server.py"
check "nfc_register endpoint present"    "grep -q 'def nfc_register' backend/api/api_server.py"
check "nfc_pay endpoint present"         "grep -q 'def nfc_pay' backend/api/api_server.py"

echo ""
echo "--- T01: cashier_routes.py SMS/FCM intact ---"
check "send_low_balance_sms present"   "grep -q 'send_low_balance_sms' backend/dashboard/cashier/cashier_routes.py"
check "send_purchase_sms present"      "grep -q 'send_purchase_sms' backend/dashboard/cashier/cashier_routes.py"
check "FCM push present"               "grep -q 'send_purchase_push' backend/dashboard/cashier/cashier_routes.py"

echo ""
echo "--- T02: admin_dashboard.py hot endpoint caching ---"
check "get_products_list uses get_cached"          "grep -A15 'def get_products_list' backend/dashboard/admin_dashboard.py | grep -q 'get_cached'"
check "get_products_list uses set_cached"          "grep -A15 'def get_products_list' backend/dashboard/admin_dashboard.py | grep -q 'set_cached'"
check "get_students uses get_cached"               "grep -A20 'def get_students' backend/dashboard/admin_dashboard.py | grep -q 'get_cached'"
check "analytics_summary uses get_cached"          "grep -A20 'def analytics_summary' backend/dashboard/admin_dashboard.py | grep -q 'get_cached'"
check "get_recent_transactions uses get_cached"    "grep -A20 'def get_recent_transactions' backend/dashboard/admin_dashboard.py | grep -q 'get_cached'"
check "get_stats uses get_cached"                  "grep -A20 'def get_stats' backend/dashboard/admin_dashboard.py | grep -q 'get_cached'"

echo ""
echo "--- T02: admin_dashboard.py mutation invalidation ---"
check "load_balance invalidates money_accounts"    "grep -A65 'def load_balance' backend/dashboard/admin_dashboard.py | grep -q 'invalidate_pattern.*money_accounts'"
check "load_balance invalidates transactions"      "grep -A65 'def load_balance' backend/dashboard/admin_dashboard.py | grep -q 'invalidate_pattern.*transactions'"
check "void_transaction invalidates transactions"  "grep -A80 'def void_transaction' backend/dashboard/admin_dashboard.py | grep -q 'invalidate_pattern.*transactions'"
check "void_transaction invalidates money_accounts" "grep -A80 'def void_transaction' backend/dashboard/admin_dashboard.py | grep -q 'invalidate_pattern.*money_accounts'"
check "update_product invalidates products"        "grep -A60 'def update_product' backend/dashboard/admin_dashboard.py | grep -q 'invalidate_pattern.*products'"

echo ""
echo "--- T03: cashier_routes.py cache wiring ---"
check "cashier_routes imports get_cached"          "grep -q 'from cache import.*get_cached\|get_cached.*=.*lambda' backend/dashboard/cashier/cashier_routes.py"
check "get_products uses get_cached"               "grep -A15 'def get_products' backend/dashboard/cashier/cashier_routes.py | grep -q 'get_cached'"
check "complete_sale invalidates transactions"     "grep -A120 'def complete_sale' backend/dashboard/cashier/cashier_routes.py | grep -q 'invalidate_pattern.*transactions'"
check "complete_sale invalidates money_accounts"   "grep -A120 'def complete_sale' backend/dashboard/cashier/cashier_routes.py | grep -q 'invalidate_pattern.*money_accounts'"

echo ""
echo "--- T03: api_server.py cache wiring ---"
check "api_server imports invalidate_pattern"             "grep -q 'from cache import.*invalidate_pattern' backend/api/api_server.py"
check "get_profile uses get_cached"                       "grep -A20 'def get_profile' backend/api/api_server.py | grep -q 'get_cached'"
check "process_cashier_transaction invalidates txns"      "grep -A120 'def process_cashier_transaction' backend/api/api_server.py | grep -q 'invalidate_pattern.*transactions'"
check "process_cashier_transaction invalidates accounts"  "grep -A120 'def process_cashier_transaction' backend/api/api_server.py | grep -q 'invalidate_pattern.*money_accounts'"

echo ""
echo "========================================"
echo "Results: ${PASS} passed, ${FAIL} failed"
if [ "$FAIL" -eq 0 ]; then
    echo "S02 verification PASSED ✓"
    exit 0
else
    echo "S02 verification FAILED ✗"
    exit 1
fi
