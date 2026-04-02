#!/usr/bin/env bash
# M008/S04 one-command verifier.
# Proves S04 transactions/settings rollback contract + chains S03 → S02 regression guards.

set -euo pipefail

SCRIPT_NAME="verify-m008-s04"

TRANSACTIONS_VIEW_FILE="mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift"
SETTINGS_VIEW_FILE="mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift"
S04_CONTRACT_TEST="tests/test_verify_m008_s04_ios_transactions_settings_rollback_contract.py"
S03_VERIFIER="scripts/verify-m008-s03.sh"

WINDOWS_GIT_BASH_EXE_SHORT="C:/Progra~1/Git/bin/bash.exe"

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
      "Restore/create the missing artifact, then re-run: rtk proxy ${WINDOWS_GIT_BASH_EXE_SHORT} scripts/verify-m008-s04.sh"
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
      "Fix script wiring and re-run: rtk proxy ${WINDOWS_GIT_BASH_EXE_SHORT} scripts/verify-m008-s04.sh"
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

  require_file "${TRANSACTIONS_VIEW_FILE}"
  require_file "${SETTINGS_VIEW_FILE}"
  require_file "${S04_CONTRACT_TEST}"
  require_file "${S03_VERIFIER}"

  log "phase=preflight status=passed"
}

run_s03_chain() {
  if [[ -x "${WINDOWS_GIT_BASH_EXE_SHORT}" ]]; then
    rtk proxy "${WINDOWS_GIT_BASH_EXE_SHORT}" "${S03_VERIFIER}"
    return
  fi

  rtk proxy bash "${S03_VERIFIER}"
}

main() {
  log "status=starting"

  run_preflight

  run_phase "s04-transactions-settings-contract" \
    "rtk proxy python -m pytest -q ${S04_CONTRACT_TEST}" \
    "S04 rollback contract failed (filter-only or Settings card markers drifted)." \
    "Run ${S04_CONTRACT_TEST} directly, fix TransactionsView/SettingsView markers, then re-run verifier." \
    -- rtk proxy python -m pytest -q "${S04_CONTRACT_TEST}"

  run_phase "s03-regression-chain" \
    "scripts/verify-m008-s03.sh (chains S02)" \
    "S03 regression chain failed; Home/QR/S02 downstream guards regressed." \
    "If stderr includes 'execvpe(/bin/bash) failed', run with Git Bash explicitly: rtk proxy ${WINDOWS_GIT_BASH_EXE_SHORT} scripts/verify-m008-s03.sh" \
    -- run_s03_chain

  log "status=passed"
}

main "$@"
