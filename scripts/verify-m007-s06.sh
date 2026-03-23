#!/usr/bin/env bash
# M007/S06 one-command verifier.
# Runs behavior/design motion contracts and static guardrails for
# centralized motion policy, Reduce Motion branches, and in-scope actionability.

set -euo pipefail

SCRIPT_NAME="verify-m007-s06"

BEHAVIOR_TEST="tests/test_verify_m007_s06_motion_behavior_contract.py"
DESIGN_TEST="tests/test_verify_m007_s06_motion_design_contract.py"
UAT_CHECKLIST=".gsd/milestones/M007/slices/S06/S06-UAT.md"

THEME_FILE="mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift"
PRIMARY_BUTTON_FILE="mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift"
TAB_SHELL_FILE="mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift"
CARD_FILE="mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift"

QR_VIEW_FILE="mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift"
TRANSACTIONS_VIEW_FILE="mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift"
BUDGET_VIEW_FILE="mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift"
LOST_CARD_VIEW_FILE="mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift"
HOME_VIEW_FILE="mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift"

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
      "Restore/create the missing artifact, then re-run: rtk proxy sh scripts/verify-m007-s06.sh"
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
    fail_with_guidance "static-contract" 2 \
      "Missing required marker (${label}) in ${file}" \
      "Expected literal: ${literal}" \
      "Restore the S06 motion contract marker, then re-run this verifier."
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
      "Remove decorative/infinite animation marker, then re-run this verifier."
  fi
}

run_preflight() {
  log "phase=preflight status=running"

  require_file "${BEHAVIOR_TEST}"
  require_file "${DESIGN_TEST}"
  require_file "${UAT_CHECKLIST}"

  require_file "${THEME_FILE}"
  require_file "${PRIMARY_BUTTON_FILE}"
  require_file "${TAB_SHELL_FILE}"
  require_file "${CARD_FILE}"

  require_file "${QR_VIEW_FILE}"
  require_file "${TRANSACTIONS_VIEW_FILE}"
  require_file "${BUDGET_VIEW_FILE}"
  require_file "${LOST_CARD_VIEW_FILE}"
  require_file "${HOME_VIEW_FILE}"

  log "phase=preflight status=passed"
}

main() {
  log "status=starting"

  run_preflight

  run_phase "behavior-contract" \
    rtk proxy python -m pytest -q "${BEHAVIOR_TEST}"

  run_phase "design-contract" \
    rtk proxy python -m pytest -q "${DESIGN_TEST}"

  log "phase=static-contract status=running"

  # Shared motion policy seam.
  assert_contains_literal "${THEME_FILE}" "enum Motion" "theme_motion_enum"
  assert_contains_literal "${THEME_FILE}" "enum Primitive" "theme_motion_primitive_enum"
  assert_contains_literal "${THEME_FILE}" "case primaryButtonPress" "theme_motion_primary_button_case"
  assert_contains_literal "${THEME_FILE}" "case tabSelection" "theme_motion_tab_selection_case"
  assert_contains_literal "${THEME_FILE}" "case cardSurface" "theme_motion_card_surface_case"
  assert_contains_literal "${THEME_FILE}" "static func animation(" "theme_motion_animation_function"
  assert_contains_literal "${THEME_FILE}" "accessibilityReduceMotion" "theme_motion_reduce_motion_branch"

  # Shared primitive consumption of motion policy.
  assert_contains_literal "${PRIMARY_BUTTON_FILE}" "@Environment(\\.accessibilityReduceMotion)" "button_reduce_motion_environment"
  assert_contains_literal "${PRIMARY_BUTTON_FILE}" "AppTheme.Motion.pressedScale(" "button_motion_pressed_scale"
  assert_contains_literal "${PRIMARY_BUTTON_FILE}" "AppTheme.Motion.animation(" "button_motion_animation"
  assert_contains_literal "${PRIMARY_BUTTON_FILE}" "for: .primaryButtonPress" "button_motion_primitive"

  assert_contains_literal "${TAB_SHELL_FILE}" "@Environment(\\.accessibilityReduceMotion)" "shell_reduce_motion_environment"
  assert_contains_literal "${TAB_SHELL_FILE}" "AppTheme.Motion.animation(" "shell_motion_animation"
  assert_contains_literal "${TAB_SHELL_FILE}" "for: .tabSelection" "shell_motion_primitive"

  assert_contains_literal "${CARD_FILE}" "@Environment(\\.accessibilityReduceMotion)" "card_reduce_motion_environment"
  assert_contains_literal "${CARD_FILE}" "AppTheme.Motion.cardScale(" "card_motion_scale"
  assert_contains_literal "${CARD_FILE}" "AppTheme.Motion.cardVerticalOffset(" "card_motion_offset"
  assert_contains_literal "${CARD_FILE}" "AppTheme.Motion.animation(" "card_motion_animation"
  assert_contains_literal "${CARD_FILE}" "for: .cardSurface" "card_motion_primitive"

  # QR state transitions + actionability.
  assert_contains_literal "${QR_VIEW_FILE}" "private var stateTransitionKey: String" "qr_state_transition_key"
  assert_contains_literal "${QR_VIEW_FILE}" ".id(stateTransitionKey)" "qr_state_transition_id"
  assert_contains_literal "${QR_VIEW_FILE}" ".animation(stateTransitionAnimation, value: stateTransitionKey)" "qr_state_transition_animation"
  assert_contains_literal "${QR_VIEW_FILE}" "if accessibilityReduceMotion {" "qr_reduce_motion_branch"
  assert_contains_literal "${QR_VIEW_FILE}" "return .opacity" "qr_reduce_motion_opacity_transition"
  assert_contains_literal "${QR_VIEW_FILE}" 'Button("Confirm QR Payment")' "qr_confirm_button"
  assert_contains_literal "${QR_VIEW_FILE}" "viewModel.confirm(token: token, apiClient: apiClient)" "qr_confirm_action"
  assert_contains_literal "${QR_VIEW_FILE}" 'Button("Retry Scan") { viewModel.reset() }' "qr_retry_action"

  # Transactions state transitions + actionability.
  assert_contains_literal "${TRANSACTIONS_VIEW_FILE}" "private var transactionStateKey: String" "transactions_state_transition_key"
  assert_contains_literal "${TRANSACTIONS_VIEW_FILE}" "private var stateCardTransition: AnyTransition" "transactions_state_transition_def"
  assert_contains_literal "${TRANSACTIONS_VIEW_FILE}" ".animation(screenTransitionAnimation, value: transactionStateKey)" "transactions_state_transition_animation"
  assert_contains_literal "${TRANSACTIONS_VIEW_FILE}" "if accessibilityReduceMotion {" "transactions_reduce_motion_branch"
  assert_contains_literal "${TRANSACTIONS_VIEW_FILE}" "return .opacity" "transactions_reduce_motion_opacity_transition"
  assert_contains_literal "${TRANSACTIONS_VIEW_FILE}" '"transactions-retry-initial-button"' "transactions_retry_initial_button"
  assert_contains_literal "${TRANSACTIONS_VIEW_FILE}" '"transactions-retry-pagination-button"' "transactions_retry_pagination_button"
  assert_contains_literal "${TRANSACTIONS_VIEW_FILE}" '"transactions-load-more-button"' "transactions_load_more_button"

  # Budget state transitions + actionability.
  assert_contains_literal "${BUDGET_VIEW_FILE}" "private var loadStateKey: String" "budget_load_state_key"
  assert_contains_literal "${BUDGET_VIEW_FILE}" "private var saveStateKey: String" "budget_save_state_key"
  assert_contains_literal "${BUDGET_VIEW_FILE}" ".animation(stateTransitionAnimation, value: loadStateKey)" "budget_load_state_animation"
  assert_contains_literal "${BUDGET_VIEW_FILE}" ".animation(stateTransitionAnimation, value: saveStateKey)" "budget_save_state_animation"
  assert_contains_literal "${BUDGET_VIEW_FILE}" "if accessibilityReduceMotion {" "budget_reduce_motion_branch"
  assert_contains_literal "${BUDGET_VIEW_FILE}" "return .opacity" "budget_reduce_motion_opacity_transition"
  assert_contains_literal "${BUDGET_VIEW_FILE}" '"budget-save-button"' "budget_save_button"
  assert_contains_literal "${BUDGET_VIEW_FILE}" '"budget-retry-load-button"' "budget_retry_load_button"
  assert_contains_literal "${BUDGET_VIEW_FILE}" '"budget-retry-save-button"' "budget_retry_save_button"

  # Lost-card state transitions + actionability.
  assert_contains_literal "${LOST_CARD_VIEW_FILE}" ".id(viewModel.phase.rawValue)" "lost_card_state_transition_id"
  assert_contains_literal "${LOST_CARD_VIEW_FILE}" ".animation(stateTransitionAnimation, value: viewModel.phase.rawValue)" "lost_card_state_transition_animation"
  assert_contains_literal "${LOST_CARD_VIEW_FILE}" "if accessibilityReduceMotion {" "lost_card_reduce_motion_branch"
  assert_contains_literal "${LOST_CARD_VIEW_FILE}" "return .opacity" "lost_card_reduce_motion_opacity_transition"
  assert_contains_literal "${LOST_CARD_VIEW_FILE}" '"lost-card-report-button"' "lost_card_report_button"
  assert_contains_literal "${LOST_CARD_VIEW_FILE}" '"lost-card-retry-button"' "lost_card_retry_button"
  assert_contains_literal "${LOST_CARD_VIEW_FILE}" '"lost-card-success-done-button"' "lost_card_success_done_button"
  assert_contains_literal "${LOST_CARD_VIEW_FILE}" '"lost-card-error-dismiss-button"' "lost_card_error_dismiss_button"

  # Home state transitions + QR entry actionability.
  assert_contains_literal "${HOME_VIEW_FILE}" "private var errorBannerStateKey: String" "home_error_state_key"
  assert_contains_literal "${HOME_VIEW_FILE}" "private var recentTransactionStateKey: String" "home_recent_state_key"
  assert_contains_literal "${HOME_VIEW_FILE}" ".animation(screenTransitionAnimation, value: errorBannerStateKey)" "home_error_state_animation"
  assert_contains_literal "${HOME_VIEW_FILE}" ".animation(screenTransitionAnimation, value: recentTransactionStateKey)" "home_recent_state_animation"
  assert_contains_literal "${HOME_VIEW_FILE}" "if accessibilityReduceMotion {" "home_reduce_motion_branch"
  assert_contains_literal "${HOME_VIEW_FILE}" "return .opacity" "home_reduce_motion_opacity_transition"
  assert_contains_literal "${HOME_VIEW_FILE}" '"home-qr-pay-button"' "home_qr_button"
  assert_contains_literal "${HOME_VIEW_FILE}" "showQrPay = true" "home_qr_action"

  # Restraint guardrail in all in-scope surfaces.
  assert_absent_literal "${THEME_FILE}" "repeatForever" "theme_forbidden_repeat_forever"
  assert_absent_literal "${PRIMARY_BUTTON_FILE}" "repeatForever" "button_forbidden_repeat_forever"
  assert_absent_literal "${TAB_SHELL_FILE}" "repeatForever" "tab_shell_forbidden_repeat_forever"
  assert_absent_literal "${CARD_FILE}" "repeatForever" "card_forbidden_repeat_forever"
  assert_absent_literal "${QR_VIEW_FILE}" "repeatForever" "qr_forbidden_repeat_forever"
  assert_absent_literal "${TRANSACTIONS_VIEW_FILE}" "repeatForever" "transactions_forbidden_repeat_forever"
  assert_absent_literal "${BUDGET_VIEW_FILE}" "repeatForever" "budget_forbidden_repeat_forever"
  assert_absent_literal "${LOST_CARD_VIEW_FILE}" "repeatForever" "lost_card_forbidden_repeat_forever"
  assert_absent_literal "${HOME_VIEW_FILE}" "repeatForever" "home_forbidden_repeat_forever"

  log "phase=static-contract status=passed"
  log "status=passed"
}

main "$@"
