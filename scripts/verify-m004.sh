#!/usr/bin/env bash
# verify-m004.sh — M004 structural assertions: APDU retry firmware + py_compile
# Usage: bash scripts/verify-m004.sh
# Exits 0 if all checks pass, 1 if any fail.

set -euo pipefail

INO="arduino/bankongseton_rfid/bankongseton_rfid.ino"

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

check_absent() {
  local desc="$1"
  local pattern="$2"
  local file="$3"

  if ! grep -q "$pattern" "$file"; then
    echo "  PASS  $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $desc (pattern should NOT be present)"
    echo "        pattern: $pattern"
    echo "        file:    $file"
    grep -n "$pattern" "$file" | head -5
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "=== M004 verify: APDU retry firmware + py_compile ==="
echo ""

# (a) APDU_MAX_RETRIES constant defined in firmware
check \
  "(a) APDU_MAX_RETRIES constant defined" \
  "APDU_MAX_RETRIES" \
  "$INO"

# (b) <= APDU_MAX_RETRIES wired as loop bound — confirms constant is actually used, not just declared
check \
  "(b) <= APDU_MAX_RETRIES wired in loop condition" \
  "<= APDU_MAX_RETRIES" \
  "$INO"

# (c) APDU_RETRY_DELAY_MS constant defined
check \
  "(c) APDU_RETRY_DELAY_MS constant defined" \
  "APDU_RETRY_DELAY_MS" \
  "$INO"

# (d) per-attempt diagnostic pattern present
check \
  '(d) "APDU attempt " per-attempt diagnostic present' \
  "APDU attempt " \
  "$INO"

# (e) cashier_routes.py parses cleanly
CASHIER="backend/dashboard/cashier/cashier_routes.py"
if python -m py_compile "$CASHIER" 2>&1; then
  echo "  PASS  (e) py_compile $CASHIER"
  PASS=$((PASS + 1))
else
  echo "  FAIL  (e) py_compile $CASHIER"
  FAIL=$((FAIL + 1))
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
echo ""

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
