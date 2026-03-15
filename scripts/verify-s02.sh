#!/usr/bin/env bash
# verify-s02.sh — S02 structural grep assertions for Phone NFC Cashier Payment
# Usage: bash scripts/verify-s02.sh
# Exits 0 if all checks pass, 1 if any fail.

set -euo pipefail

CASHIER_PY="backend/dashboard/cashier/cashier_routes.py"
CASHIER_HTML="backend/dashboard/cashier/templates/cashier_index.html"

PASS=0
FAIL=0

check() {
  local desc="$1"
  local pattern="$2"
  local file="$3"

  if grep -q "$pattern" "$file"; then
    echo "  PASS  $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $desc"
    echo "        pattern: $pattern"
    echo "        file:    $file"
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "=== S02 verify: Phone NFC Cashier Payment ==="
echo ""

# (a) complete_sale_nfc function defined in backend
check \
  "(a) complete_sale_nfc function defined" \
  "def complete_sale_nfc" \
  "$CASHIER_PY"

# (b) /api/complete-sale-nfc route registered in backend
check \
  "(b) /api/complete-sale-nfc route registered" \
  "complete-sale-nfc" \
  "$CASHIER_PY"

# (c) VirtualCardToken field name present in backend
check \
  "(c) VirtualCardToken field name present" \
  "VirtualCardToken" \
  "$CASHIER_PY"

# (d) IsActive guard present in backend
check \
  "(d) IsActive guard present" \
  "IsActive" \
  "$CASHIER_PY"

# (e) NFC Purchase transaction label present in backend
check \
  "(e) NFC Purchase transaction label present" \
  "NFC Purchase" \
  "$CASHIER_PY"

# (f) flask_session.pop('pending_transaction') present in backend
check \
  "(f) flask_session.pop('pending_transaction') present" \
  "pop.*pending_transaction" \
  "$CASHIER_PY"

# (g) socket.on('nfc_payment') in cashier UI
check \
  "(g) socket.on('nfc_payment') in cashier UI" \
  "nfc_payment" \
  "$CASHIER_HTML"

# (h) completeNFCSale function defined in cashier UI
check \
  "(h) completeNFCSale function defined in cashier UI" \
  "function completeNFCSale" \
  "$CASHIER_HTML"

# (i) /cashier/api/complete-sale-nfc URL in cashier UI JS
check \
  "(i) /cashier/api/complete-sale-nfc URL in JS" \
  "complete-sale-nfc" \
  "$CASHIER_HTML"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
echo ""

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
