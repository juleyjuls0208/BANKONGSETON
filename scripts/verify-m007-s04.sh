#!/usr/bin/env bash
# M007/S04 one-command verifier.
# Runs behavior/design contract suites and static guardrails for
# Budget + Receipt + Lost-Card redesign scope closure.

set -euo pipefail

SCRIPT_NAME="verify-m007-s04"

BEHAVIOR_TEST="tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py"
DESIGN_TEST="tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py"
UAT_CHECKLIST=".gsd/milestones/M007/slices/S04/S04-UAT.md"

BUDGET_VIEW="mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift"
RECEIPT_VIEW="mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift"
LOST_CARD_VIEW="mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift"

BUDGET_VM="mobile/ios/BankongSetonStudent/ViewModels/BudgetViewModel.swift"
LOST_CARD_VM="mobile/ios/BankongSetonStudent/ViewModels/LostCardViewModel.swift"

HOME_VIEW="mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift"
TRANSACTIONS_VIEW="mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift"
SETTINGS_VIEW="mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift"

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
      "Restore/create the missing artifact, then re-run: rtk proxy bash scripts/verify-m007-s04.sh"
  fi
}

run_phase() {
  local phase="$1"
  shift

  log "phase=${phase} status=running"
  set +e
  "$@"
  local code=$?
  set -e

  if [[ ${code} -ne 0 ]]; then
    fail_with_guidance "${phase}" "${code}" \
      "Command failed: $*" \
      "Inspect failing output above, fix the regression, then re-run this verifier."
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
      "Restore the S04 contract marker, then re-run this verifier."
  fi
}

assert_absent_literal() {
  local file="$1"
  local literal="$2"
  local label="$3"

  set +e
  rtk proxy python -c "from pathlib import Path; import sys; sys.exit(0 if sys.argv[2] not in Path(sys.argv[1]).read_text(encoding='utf-8') else 1)" "${file}" "${literal}"
  local code=$?
  set -e

  if [[ ${code} -ne 0 ]]; then
    fail_with_guidance "static-contract" 2 \
      "Forbidden marker present (${label}) in ${file}" \
      "Forbidden literal: ${literal}" \
      "Remove the out-of-scope utility marker, then re-run this verifier."
  fi
}

main() {
  log "status=starting"

  require_file "${BEHAVIOR_TEST}"
  require_file "${DESIGN_TEST}"
  require_file "${UAT_CHECKLIST}"

  require_file "${BUDGET_VIEW}"
  require_file "${RECEIPT_VIEW}"
  require_file "${LOST_CARD_VIEW}"
  require_file "${BUDGET_VM}"
  require_file "${LOST_CARD_VM}"
  require_file "${HOME_VIEW}"
  require_file "${TRANSACTIONS_VIEW}"
  require_file "${SETTINGS_VIEW}"

  run_phase "behavior-contract" \
    rtk proxy python -m pytest -q "${BEHAVIOR_TEST}"

  run_phase "design-contract" \
    rtk proxy python -m pytest -q "${DESIGN_TEST}"

  log "phase=static-contract status=running"

  # Budget explicit states + actions.
  assert_contains_literal "${BUDGET_VIEW}" "budget-state-loading-card" "budget_state_loading"
  assert_contains_literal "${BUDGET_VIEW}" "budget-state-load-error-card" "budget_state_load_error"
  assert_contains_literal "${BUDGET_VIEW}" "budget-state-ready-card" "budget_state_ready"
  assert_contains_literal "${BUDGET_VIEW}" "budget-state-save-error-card" "budget_state_save_error"
  assert_contains_literal "${BUDGET_VIEW}" "budget-state-save-success-card" "budget_state_save_success"
  assert_contains_literal "${BUDGET_VIEW}" "budget-save-button" "budget_save_button"
  assert_contains_literal "${BUDGET_VIEW}" "budget-retry-load-button" "budget_retry_load_button"
  assert_contains_literal "${BUDGET_VIEW}" "budget-retry-save-button" "budget_retry_save_button"
  assert_contains_literal "${BUDGET_VIEW}" "budget-refresh-button" "budget_refresh_button"
  assert_contains_literal "${BUDGET_VIEW}" "await viewModel.retryLoad(apiClient: apiClient, authManager: authManager)" "budget_retry_load_action"
  assert_contains_literal "${BUDGET_VIEW}" "await viewModel.retryLastSave(apiClient: apiClient, authManager: authManager)" "budget_retry_save_action"

  assert_contains_literal "${BUDGET_VM}" "@Published private(set) var loadErrorMessage: String?" "budget_vm_load_error_channel"
  assert_contains_literal "${BUDGET_VM}" "@Published private(set) var saveErrorMessage: String?" "budget_vm_save_error_channel"
  assert_contains_literal "${BUDGET_VM}" "func retryLoad(apiClient: APIClient, authManager: AuthManager) async" "budget_vm_retry_load"
  assert_contains_literal "${BUDGET_VM}" "func retryLastSave(apiClient: APIClient, authManager: AuthManager) async" "budget_vm_retry_save"

  # Lost-card explicit phases + actions.
  assert_contains_literal "${LOST_CARD_VIEW}" "switch viewModel.phase" "lost_card_phase_switch"
  assert_contains_literal "${LOST_CARD_VIEW}" "lost-card-state-idle" "lost_card_state_idle"
  assert_contains_literal "${LOST_CARD_VIEW}" "lost-card-state-loading" "lost_card_state_loading"
  assert_contains_literal "${LOST_CARD_VIEW}" "lost-card-state-success" "lost_card_state_success"
  assert_contains_literal "${LOST_CARD_VIEW}" "lost-card-state-error" "lost_card_state_error"
  assert_contains_literal "${LOST_CARD_VIEW}" "lost-card-report-button" "lost_card_report_button"
  assert_contains_literal "${LOST_CARD_VIEW}" "lost-card-retry-button" "lost_card_retry_button"
  assert_contains_literal "${LOST_CARD_VIEW}" "lost-card-success-done-button" "lost_card_success_done_button"
  assert_contains_literal "${LOST_CARD_VIEW}" "lost-card-error-dismiss-button" "lost_card_error_dismiss_button"

  assert_contains_literal "${LOST_CARD_VM}" "enum LostCardFlowPhase: String" "lost_card_vm_phase_enum"
  assert_contains_literal "${LOST_CARD_VM}" "case idle" "lost_card_vm_phase_idle"
  assert_contains_literal "${LOST_CARD_VM}" "case loading" "lost_card_vm_phase_loading"
  assert_contains_literal "${LOST_CARD_VM}" "case success" "lost_card_vm_phase_success"
  assert_contains_literal "${LOST_CARD_VM}" "case error" "lost_card_vm_phase_error"

  # Receipt stability + scope-clean constraints.
  assert_contains_literal "${RECEIPT_VIEW}" "Scope guard: no PDF/download/report utility actions belong to S04" "receipt_scope_guard_comment"
  assert_contains_literal "${RECEIPT_VIEW}" "Array(lineItems.enumerated())" "receipt_indexed_line_items"
  assert_contains_literal "${RECEIPT_VIEW}" 'ForEach(indexedLineItems, id: \.index)' "receipt_for_each_indexed_identity"
  assert_contains_literal "${RECEIPT_VIEW}" "receipt-fallback-item-marker" "receipt_fallback_marker"
  assert_contains_literal "${RECEIPT_VIEW}" "receipt-line-item-row-\\(line.index)" "receipt_line_item_row_marker"

  assert_absent_literal "${RECEIPT_VIEW}" 'ForEach(lineItems, id: \.name)' "receipt_forbidden_name_identity"
  assert_absent_literal "${RECEIPT_VIEW}" "Download PDF" "receipt_forbidden_download_pdf"
  assert_absent_literal "${RECEIPT_VIEW}" "Report Issue" "receipt_forbidden_report_issue"
  assert_absent_literal "${RECEIPT_VIEW}" "Report Receipt" "receipt_forbidden_report_receipt"
  assert_absent_literal "${RECEIPT_VIEW}" "receipt-report-issue-button" "receipt_forbidden_report_button"
  assert_absent_literal "${RECEIPT_VIEW}" "receipt-download-button" "receipt_forbidden_download_button"

  # Navigation continuity anchors from Home / Transactions / Settings.
  assert_contains_literal "${HOME_VIEW}" ".navigationDestination(for: Transaction.self)" "home_receipt_navigation_destination"
  assert_contains_literal "${HOME_VIEW}" "ReceiptView(transaction: transaction)" "home_receipt_navigation_target"

  assert_contains_literal "${TRANSACTIONS_VIEW}" ".navigationDestination(for: Transaction.self)" "transactions_receipt_navigation_destination"
  assert_contains_literal "${TRANSACTIONS_VIEW}" "ReceiptView(transaction: transaction)" "transactions_receipt_navigation_target"

  assert_contains_literal "${SETTINGS_VIEW}" 'NavigationLink("Report Lost Card")' "settings_lost_card_navigation_link"
  assert_contains_literal "${SETTINGS_VIEW}" "LostCardView()" "settings_lost_card_navigation_target"

  log "phase=static-contract status=passed"
  log "status=passed"
}

main "$@"
