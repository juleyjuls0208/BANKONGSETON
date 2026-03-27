#!/usr/bin/env bash
# M008/S01 one-command verifier.
# Proves backend budget contract + iOS contract + retry-visibility continuity.

set -euo pipefail

SCRIPT_NAME="verify-m008-s01"

BACKEND_CONTRACT_TEST="tests/test_verify_m008_s01_budget_contract.py"
IOS_CONTRACT_TEST="tests/test_verify_m008_s01_ios_budget_contract.py"
RETRY_VISIBILITY_TEST="tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py"

API_ENDPOINTS_FILE="mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift"
BUDGET_VIEW_FILE="mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift"
BUDGET_VM_FILE="mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift"

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
      "Restore/create the missing artifact, then re-run: rtk proxy \"C:\\Program Files\\Git\\bin\\bash.exe\" scripts/verify-m008-s01.sh"
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
      "Fix script wiring and re-run: rtk proxy \"C:\\Program Files\\Git\\bin\\bash.exe\" scripts/verify-m008-s01.sh"
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

assert_contains_literal() {
  local file="$1"
  local literal="$2"
  local label="$3"

  set +e
  rtk proxy python -c "from pathlib import Path; import sys; sys.exit(0 if sys.argv[2] in Path(sys.argv[1]).read_text(encoding='utf-8') else 1)" "${file}" "${literal}"
  local code=$?
  set -e

  if [[ ${code} -ne 0 ]]; then
    fail_with_guidance "static-contract" 2 \
      "Missing required marker (${label}) in ${file}" \
      "Expected literal: ${literal}" \
      "Restore the iOS budget contract marker, then re-run: rtk proxy \"C:\\Program Files\\Git\\bin\\bash.exe\" scripts/verify-m008-s01.sh"
  fi
}

run_preflight() {
  log "phase=preflight status=running"

  require_file "${BACKEND_CONTRACT_TEST}"
  require_file "${IOS_CONTRACT_TEST}"
  require_file "${RETRY_VISIBILITY_TEST}"
  require_file "${API_ENDPOINTS_FILE}"
  require_file "${BUDGET_VIEW_FILE}"
  require_file "${BUDGET_VM_FILE}"

  log "phase=preflight status=passed"
}

main() {
  log "status=starting"

  run_preflight

  run_phase "backend-contract" \
    "rtk proxy python -m pytest -q ${BACKEND_CONTRACT_TEST}" \
    "Backend budget route contract regressed (auth/status/sheet/retryable errors)." \
    "Run ${BACKEND_CONTRACT_TEST} directly, fix backend/api/api_server.py behavior, then re-run verifier." \
    -- rtk proxy python -m pytest -q "${BACKEND_CONTRACT_TEST}"

  run_phase "ios-contract" \
    "rtk proxy python -m pytest -q ${IOS_CONTRACT_TEST}" \
    "iOS endpoint/payload contract markers drifted from backend budget contract." \
    "Fix APIEndpoints/APIClient/BudgetViewModel/BudgetView markers, then re-run verifier." \
    -- rtk proxy python -m pytest -q "${IOS_CONTRACT_TEST}"

  run_phase "retry-visibility-regression" \
    "rtk proxy python -m pytest -q ${RETRY_VISIBILITY_TEST}" \
    "R074 retry/failure visibility continuity regressed in budget or lost-card flow." \
    "Restore explicit failure channels and retry actions, then re-run verifier." \
    -- rtk proxy python -m pytest -q "${RETRY_VISIBILITY_TEST}"

  log "phase=static-contract status=running"

  # High-risk contract literals where fast, file-local diagnosis helps more than test traceback.
  assert_contains_literal "${API_ENDPOINTS_FILE}" 'static let budget = "/student/budget"' "ios_budget_endpoint_path"
  assert_contains_literal "${API_ENDPOINTS_FILE}" 'static let budgetSummary = "/budget-summary"' "ios_budget_summary_endpoint_path"

  assert_contains_literal "${BUDGET_VIEW_FILE}" "budget-retry-load-button" "budget_retry_load_button_id"
  assert_contains_literal "${BUDGET_VIEW_FILE}" "budget-retry-save-button" "budget_retry_save_button_id"
  assert_contains_literal "${BUDGET_VIEW_FILE}" "await viewModel.retryLoad(apiClient: apiClient, authManager: authManager)" "budget_retry_load_action"
  assert_contains_literal "${BUDGET_VIEW_FILE}" "await viewModel.retryLastSave(apiClient: apiClient, authManager: authManager)" "budget_retry_save_action"

  assert_contains_literal "${BUDGET_VM_FILE}" "@Published private(set) var loadErrorMessage: String?" "budget_vm_load_error_channel"
  assert_contains_literal "${BUDGET_VM_FILE}" "@Published private(set) var saveErrorMessage: String?" "budget_vm_save_error_channel"

  log "phase=static-contract status=passed"
  log "status=passed"
}

main "$@"
