#!/usr/bin/env bash
# M008/S03 one-command verifier.
# Proves Home rollback contract + QR continuity seam + chained S02 regression guards.

set -euo pipefail

SCRIPT_NAME="verify-m008-s03"

HOME_VIEW_FILE="mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift"
S03_HOME_CONTRACT_TEST="tests/test_verify_m008_s03_ios_home_rollback_contract.py"
S07_CONTINUITY_TEST_NODE="tests/test_verify_m007_s07_integration_behavior_contract.py::test_qr_success_handoff_remains_wired_from_home_sheet_to_refresh_path"
S02_CHAIN_VERIFIER="scripts/verify-m008-s02.sh"

WINDOWS_GIT_BASH_EXE="C:\\Program Files\\Git\\bin\\bash.exe"
WINDOWS_GIT_BASH_POSIX="/c/Program Files/Git/bin/bash.exe"

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
      "Restore/create the missing artifact, then re-run: rtk proxy \"${WINDOWS_GIT_BASH_EXE}\" scripts/verify-m008-s03.sh"
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
      "Fix script wiring and re-run: rtk proxy \"${WINDOWS_GIT_BASH_EXE}\" scripts/verify-m008-s03.sh"
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

  require_file "${HOME_VIEW_FILE}"
  require_file "${S03_HOME_CONTRACT_TEST}"
  require_file "tests/test_verify_m007_s07_integration_behavior_contract.py"
  require_file "${S02_CHAIN_VERIFIER}"

  log "phase=preflight status=passed"
}

run_s02_regression_chain() {
  if [[ -x "${WINDOWS_GIT_BASH_POSIX}" ]]; then
    rtk proxy "${WINDOWS_GIT_BASH_EXE}" "${S02_CHAIN_VERIFIER}"
    return
  fi

  rtk proxy bash "${S02_CHAIN_VERIFIER}"
}

main() {
  log "status=starting"

  run_preflight

  run_phase "s03-home-contract" \
    "rtk proxy python -m pytest -q ${S03_HOME_CONTRACT_TEST}" \
    "S03 Home rollback contract failed (credit-card hero or rollback markers drifted)." \
    "Run ${S03_HOME_CONTRACT_TEST} directly, fix HomeView markers, then re-run verifier." \
    -- rtk proxy python -m pytest -q "${S03_HOME_CONTRACT_TEST}"

  run_phase "home-qr-continuity" \
    "rtk proxy python -m pytest -q ${S07_CONTINUITY_TEST_NODE}" \
    "R076 QR success continuity seam regressed from Home sheet to refresh path." \
    "Run ${S07_CONTINUITY_TEST_NODE} directly, restore Home/QR continuity seam markers, then re-run verifier." \
    -- rtk proxy python -m pytest -q "${S07_CONTINUITY_TEST_NODE}"

  run_phase "s02-regression-chain" \
    "scripts/verify-m008-s02.sh" \
    "S02 rollback regression chain failed; downstream shell/budget/QR/login guards regressed." \
    "If stderr includes 'execvpe(/bin/bash) failed', run with Git Bash explicitly: rtk proxy \"${WINDOWS_GIT_BASH_EXE}\" scripts/verify-m008-s02.sh" \
    -- run_s02_regression_chain

  log "status=passed"
}

main "$@"
