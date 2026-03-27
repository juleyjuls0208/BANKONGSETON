#!/usr/bin/env bash
# M008/S02 one-command verifier.
# Proves native tab-shell rollback contract while guarding budget/QR/login regressions.

set -euo pipefail

SCRIPT_NAME="verify-m008-s02"

MAIN_TAB_VIEW_FILE="mobile/ios/BankongSetonStudent/Views/MainTabView.swift"
ROLLBACK_CONTRACT_TEST="tests/test_verify_m008_s02_ios_rollback_contract.py"
BUDGET_REGRESSION_TEST="tests/test_verify_m008_s01_ios_budget_contract.py"
QR_REGRESSION_TEST="tests/test_verify_m007_s02_qr_behavior_contract.py"
LOGIN_REGRESSION_TEST="tests/test_verify_m007_s09_override_contract.py::test_login_state_and_payload_are_student_id_only"

log() {
  echo "[${SCRIPT_NAME}] $*"
}

fail_with_guidance() {
  local phase="$1"
  local code="$2"
  shift 2

  log "phase=${phase} status=failed exit_code=${code}"
  for line in "$@"; do
    log "guidance=${line}"
  done
  exit "${code}"
}

require_file() {
  local file="$1"

  if [[ ! -f "${file}" ]]; then
    fail_with_guidance "preflight" 2 \
      "Required file is missing: ${file}" \
      "Restore/create the missing artifact, then re-run: rtk proxy bash scripts/verify-m008-s02.sh"
  fi
}

run_phase() {
  local phase="$1"
  local command_label="$2"
  local guidance_1="$3"
  local guidance_2="$4"
  shift 4

  if [[ "${1:-}" != "--" ]]; then
    fail_with_guidance "preflight" 2 \
      "run_phase invocation is missing '--' delimiter for command arguments" \
      "Fix script wiring and re-run: rtk proxy bash scripts/verify-m008-s02.sh"
  fi
  shift

  log "phase=${phase} status=running"

  set +e
  "$@"
  local code=$?
  set -e

  if [[ ${code} -ne 0 ]]; then
    fail_with_guidance "${phase}" "${code}" \
      "Command failed: ${command_label}" \
      "${guidance_1}" \
      "${guidance_2}"
  fi

  log "phase=${phase} status=passed"
}

run_preflight() {
  log "phase=preflight status=running"

  require_file "${MAIN_TAB_VIEW_FILE}"
  require_file "${ROLLBACK_CONTRACT_TEST}"
  require_file "${BUDGET_REGRESSION_TEST}"
  require_file "${QR_REGRESSION_TEST}"

  # Login regression uses pytest node-id syntax, so only the file path is validated in preflight.
  require_file "tests/test_verify_m007_s09_override_contract.py"

  log "phase=preflight status=passed"
}

main() {
  log "status=starting"

  run_preflight

  run_phase "s02-rollback-contract" \
    "rtk proxy python -m pytest -q ${ROLLBACK_CONTRACT_TEST}" \
    "Native TabView rollback contract failed (tab shell drift or session alert wiring regression)." \
    "Run ${ROLLBACK_CONTRACT_TEST} directly, restore MainTabView markers, then re-run verifier." \
    -- rtk proxy python -m pytest -q "${ROLLBACK_CONTRACT_TEST}"

  run_phase "budget-regression" \
    "rtk proxy python -m pytest -q ${BUDGET_REGRESSION_TEST}" \
    "S01 budget compatibility guard regressed during shell rollback changes." \
    "Fix budget endpoint/payload/retry markers, then re-run verifier." \
    -- rtk proxy python -m pytest -q "${BUDGET_REGRESSION_TEST}"

  run_phase "qr-regression" \
    "rtk proxy python -m pytest -q ${QR_REGRESSION_TEST}" \
    "M007 QR continuity guard regressed while restoring baseline structure." \
    "Fix QR payload/scanner/failure-path wiring, then re-run verifier." \
    -- rtk proxy python -m pytest -q "${QR_REGRESSION_TEST}"

  run_phase "login-regression" \
    "rtk proxy python -m pytest -q ${LOGIN_REGRESSION_TEST}" \
    "Login student-ID-only contract regressed (pin/state or request payload drift)." \
    "Restore student-ID-only login wiring in LoginViewModel/APIClient/Login models, then re-run verifier." \
    -- rtk proxy python -m pytest -q "${LOGIN_REGRESSION_TEST}"

  log "status=passed"
}

main "$@"
