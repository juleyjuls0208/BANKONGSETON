#!/usr/bin/env bash
# verify-s01.sh — S01 structural grep assertions for firmware WiFi routing fix
# Usage: bash scripts/verify-s01.sh
# Exits 0 if all checks pass, 1 if any fail.

set -euo pipefail

INO="arduino/bankongseton_rfid/bankongseton_rfid.ino"
SECRETS="arduino/bankongseton_rfid/secrets.h"

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
echo "=== S01 verify: firmware WiFi routing fix ==="
echo ""

# (a) httpPost( is not a call site in deliver() — verify no bare httpPost( call remains
#     (the definition httpPostJson is fine, but the old httpPost call must be gone)
check_absent \
  "(a) no bare httpPost() call site anywhere in firmware" \
  "httpPost(" \
  "$INO"

# (b) httpPostCard function exists
check \
  "(b) httpPostCard function defined" \
  "bool httpPostCard" \
  "$INO"

# (b2) httpPostNFC function exists
check \
  "(b2) httpPostNFC function defined" \
  "bool httpPostNFC" \
  "$INO"

# (c) prefix == "CARD" dispatch exists in deliver()
check \
  "(c) prefix == \"CARD\" dispatch in deliver()" \
  'prefix == "CARD"' \
  "$INO"

# (d) /api/arduino/card-read endpoint path present
check \
  "(d) /api/arduino/card-read path present" \
  '/api/arduino/card-read' \
  "$INO"

# (e) {"uid": payload pattern present (card helper)
check \
  '(e) {"uid": payload present in firmware' \
  '"uid":' \
  "$INO"

# (f) HEARTBEAT_INTERVAL_MS constant in .ino
check \
  "(f) HEARTBEAT_INTERVAL_MS constant in firmware" \
  "HEARTBEAT_INTERVAL_MS" \
  "$INO"

# (g) secrets.h template mentions HEARTBEAT_INTERVAL_MS
check \
  "(g) secrets.h mentions HEARTBEAT_INTERVAL_MS" \
  "HEARTBEAT_INTERVAL_MS" \
  "$SECRETS"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
echo ""

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
