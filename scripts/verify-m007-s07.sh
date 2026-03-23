#!/usr/bin/env bash
# M007/S07 one-command verifier.
# Runs integration/scope contract suites and phased static diagnostics for
# final-assembly QR continuity, transactions continuity, and scoped closure surfaces.

set -euo pipefail

SCRIPT_NAME="verify-m007-s07"

INTEGRATION_TEST="tests/test_verify_m007_s07_integration_behavior_contract.py"
SCOPE_TEST="tests/test_verify_m007_s07_scope_guard_contract.py"
S07_UAT=".gsd/milestones/M007/slices/S07/S07-UAT.md"

QR_VIEW="mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift"
QR_VM="mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift"
HOME_VIEW="mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift"
HOME_VM="mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift"
TRANSACTIONS_VIEW="mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift"
TRANSACTIONS_VM="mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift"
SETTINGS_VIEW="mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift"
LOST_CARD_VIEW="mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift"
RECEIPT_VIEW="mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift"

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
      "Restore/create the missing artifact, then re-run: rtk proxy sh scripts/verify-m007-s07.sh"
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
      "Inspect failing output above, fix regression, then re-run this verifier."
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
    fail_with_guidance "integration" 2 \
      "Missing required marker (${label}) in ${file}" \
      "Expected literal: ${literal}" \
      "Restore the S07 integration marker, then re-run this verifier."
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
    fail_with_guidance "scope" 2 \
      "Forbidden marker present (${label}) in ${file}" \
      "Forbidden literal: ${literal}" \
      "Remove the out-of-scope regression, then re-run this verifier."
  fi
}

run_preflight() {
  log "phase=preflight status=running"

  require_file "${INTEGRATION_TEST}"
  require_file "${SCOPE_TEST}"
  require_file "${S07_UAT}"

  require_file "${QR_VIEW}"
  require_file "${QR_VM}"
  require_file "${HOME_VIEW}"
  require_file "${HOME_VM}"
  require_file "${TRANSACTIONS_VIEW}"
  require_file "${TRANSACTIONS_VM}"
  require_file "${SETTINGS_VIEW}"
  require_file "${LOST_CARD_VIEW}"
  require_file "${RECEIPT_VIEW}"

  log "phase=preflight status=passed"
}

run_integration_phase() {
  log "phase=integration status=running"

  # QR success handoff + observability seams.
  assert_contains_literal "${HOME_VIEW}" 'QRPayView {' "home_qr_sheet_handoff"
  assert_contains_literal "${HOME_VIEW}" 'await viewModel.refreshAfterQRSuccess(apiClient: apiClient, authManager: authManager)' "home_qr_refresh_handoff"
  assert_contains_literal "${HOME_VM}" 'log("Refreshing Home data after QR payment success dismiss")' "home_refresh_log_marker"

  assert_contains_literal "${QR_VIEW}" 'Button("Done") {' "qr_done_action"
  assert_contains_literal "${QR_VIEW}" 'onSuccess?()' "qr_success_callback"
  assert_contains_literal "${QR_VM}" 'private func transition(to newState: QRPayState, reason: String)' "qr_transition_function"
  assert_contains_literal "${QR_VM}" 'log("QRPayState transition' "qr_transition_observability"

  # Transactions continuity markers.
  assert_contains_literal "${TRANSACTIONS_VIEW}" '.searchable(' "transactions_searchable"
  assert_contains_literal "${TRANSACTIONS_VIEW}" 'text: $viewModel.searchQuery' "transactions_search_binding"
  assert_contains_literal "${TRANSACTIONS_VIEW}" 'Picker("Transaction Type", selection: $viewModel.selectedFilter)' "transactions_filter_binding"
  assert_contains_literal "${TRANSACTIONS_VIEW}" '"transactions-load-more-button"' "transactions_load_more_button"

  assert_contains_literal "${TRANSACTIONS_VM}" '@Published private(set) var allTransactions: [Transaction] = []' "transactions_vm_canonical_list"
  assert_contains_literal "${TRANSACTIONS_VM}" '@Published private(set) var paginationErrorMessage: String?' "transactions_vm_pagination_channel"
  assert_contains_literal "${TRANSACTIONS_VM}" 'guard hasMore && !isLoading && !isLoadingMore else { return }' "transactions_vm_load_more_guard"

  # Settings + lost-card actionability seams.
  assert_contains_literal "${SETTINGS_VIEW}" 'NavigationLink("Report Lost Card")' "settings_lost_card_link"
  assert_contains_literal "${SETTINGS_VIEW}" '"settings-logout-button"' "settings_logout_button"
  assert_contains_literal "${LOST_CARD_VIEW}" '"lost-card-report-button"' "lost_card_report_button"
  assert_contains_literal "${LOST_CARD_VIEW}" '"lost-card-retry-button"' "lost_card_retry_button"

  # Scope continuity guardrails.
  assert_absent_literal "${HOME_VIEW}" 'Pay with NFC' "home_forbidden_nfc_button"
  assert_absent_literal "${SETTINGS_VIEW}" 'Manage Payment Method' "settings_forbidden_manage_payment_method"
  assert_absent_literal "${RECEIPT_VIEW}" 'Download PDF' "receipt_forbidden_download"

  log "phase=integration status=passed"
}

run_diagnostic_surface_phase() {
  log "phase=diagnostic-surface status=running"

  assert_contains_literal "${S07_UAT}" '# S07 UAT Checklist' "uat_heading_root"
  assert_contains_literal "${S07_UAT}" '## Device & Build Context' "uat_heading_device_context"
  assert_contains_literal "${S07_UAT}" '## Journey Checkpoints' "uat_heading_journey"
  assert_contains_literal "${S07_UAT}" '## PASS / FAIL Summary' "uat_heading_pass_fail"

  log "phase=diagnostic-surface status=passed"
}

main() {
  log "status=starting"

  run_preflight

  run_phase "contract" \
    rtk proxy python -m pytest -q "${INTEGRATION_TEST}"

  run_phase "scope" \
    rtk proxy python -m pytest -q "${SCOPE_TEST}"

  run_integration_phase
  run_diagnostic_surface_phase

  log "status=passed"
}

main "$@"
