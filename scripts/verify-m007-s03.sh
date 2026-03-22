#!/usr/bin/env bash
# M007/S03 one-command verifier.
# Runs behavior/design contract suites and static guardrails for
# Transactions search/filter wiring, state fidelity markers, and pagination continuity.

set -euo pipefail

SCRIPT_NAME="verify-m007-s03"

TRANSACTIONS_VIEW="mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift"
TRANSACTIONS_VM="mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift"
BEHAVIOR_TEST="tests/test_verify_m007_s03_transactions_behavior_contract.py"
DESIGN_TEST="tests/test_verify_m007_s03_transactions_design_contract.py"
UAT_CHECKLIST=".gsd/milestones/M007/slices/S03/S03-UAT.md"

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
      "Restore/create the missing artifact, then re-run: rtk proxy bash scripts/verify-m007-s03.sh"
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
      "Inspect the failing output above, fix the regression, then re-run this verifier."
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
      "Restore the Transactions S03 marker and re-run this verifier."
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
      "Remove the regression and re-run this verifier."
  fi
}

main() {
  log "status=starting"

  require_file "${BEHAVIOR_TEST}"
  require_file "${DESIGN_TEST}"
  require_file "${TRANSACTIONS_VIEW}"
  require_file "${TRANSACTIONS_VM}"
  require_file "${UAT_CHECKLIST}"

  run_phase "behavior-contract" \
    rtk proxy python -m pytest -q "${BEHAVIOR_TEST}"

  run_phase "design-contract" \
    rtk proxy python -m pytest -q "${DESIGN_TEST}"

  log "phase=static-contract status=running"

  # Search + filter wiring markers.
  assert_contains_literal "${TRANSACTIONS_VIEW}" ".searchable(" "searchable_control"
  assert_contains_literal "${TRANSACTIONS_VIEW}" 'text: $viewModel.searchQuery' "search_query_binding"
  assert_contains_literal "${TRANSACTIONS_VIEW}" 'Picker("Transaction Type", selection: $viewModel.selectedFilter)' "filter_picker_binding"
  assert_contains_literal "${TRANSACTIONS_VIEW}" "ForEach(TransactionFilter.allCases, id: \\.self)" "filter_options"
  assert_contains_literal "${TRANSACTIONS_VIEW}" "viewModel.clearSearchAndFilter()" "clear_filter_action"
  assert_contains_literal "${TRANSACTIONS_VIEW}" "transactions-filter-picker" "filter_identifier"

  # Explicit state-surface markers (loading/base-empty/filtered-empty/error/pagination-error/populated).
  assert_contains_literal "${TRANSACTIONS_VIEW}" "transactions-state-loading" "state_loading"
  assert_contains_literal "${TRANSACTIONS_VIEW}" "transactions-state-initial-error" "state_initial_error"
  assert_contains_literal "${TRANSACTIONS_VIEW}" "transactions-state-base-empty" "state_base_empty"
  assert_contains_literal "${TRANSACTIONS_VIEW}" "transactions-state-filtered-empty" "state_filtered_empty"
  assert_contains_literal "${TRANSACTIONS_VIEW}" "transactions-state-pagination-error" "state_pagination_error"
  assert_contains_literal "${TRANSACTIONS_VIEW}" "ForEach(viewModel.transactions)" "state_populated_rows"

  # Load-more continuity + non-blocking pagination error handling.
  assert_contains_literal "${TRANSACTIONS_VIEW}" "if viewModel.hasMore" "load_more_gate"
  assert_contains_literal "${TRANSACTIONS_VIEW}" "await viewModel.loadMore(apiClient: apiClient, authManager: authManager)" "load_more_hook"
  assert_contains_literal "${TRANSACTIONS_VIEW}" "transactions-load-more-button" "load_more_identifier"

  assert_contains_literal "${TRANSACTIONS_VM}" "@Published private(set) var initialLoadErrorMessage: String?" "vm_initial_error_channel"
  assert_contains_literal "${TRANSACTIONS_VM}" "@Published private(set) var paginationErrorMessage: String?" "vm_pagination_error_channel"
  assert_contains_literal "${TRANSACTIONS_VM}" "guard hasMore && !isLoading && !isLoadingMore else { return }" "vm_load_more_guard"
  assert_contains_literal "${TRANSACTIONS_VM}" "var hasPaginationFailureState: Bool" "vm_pagination_failure_state"
  assert_contains_literal "${TRANSACTIONS_VM}" "paginationErrorMessage != nil && !allTransactions.isEmpty" "vm_non_blocking_pagination_failure"

  # Pagination errors must not route through the global initial-error channel.
  assert_absent_literal "${TRANSACTIONS_VM}" "case .pagination:\n                errorMessage =" "vm_forbidden_pagination_global_error"

  log "phase=static-contract status=passed"
  log "status=passed"
}

main "$@"
