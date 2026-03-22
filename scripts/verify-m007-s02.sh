#!/usr/bin/env bash
# M007/S02 one-command verifier.
# Runs behavior/design contract suites, then enforces static QR-only + state-coverage + camera-key guards.

set -euo pipefail

SCRIPT_NAME="verify-m007-s02"

QR_PAY_VIEW="mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift"
HOME_VIEW="mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift"
PBXPROJ="mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj"

TEST_BEHAVIOR="tests/test_verify_m007_s02_qr_behavior_contract.py"
TEST_QR_DESIGN="tests/test_verify_m007_s02_qr_design_contract.py"
TEST_HOME_DESIGN="tests/test_verify_m007_s02_home_qr_design_contract.py"

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
      "Restore the missing contract/input file, then re-run: rtk proxy bash scripts/verify-m007-s02.sh"
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
    fail_with_guidance "static-scope" 2 \
      "Missing required marker (${label}) in ${file}" \
      "Expected literal: ${literal}" \
      "Restore the required QR/Home contract marker, then re-run this verifier."
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
    fail_with_guidance "static-scope" 2 \
      "Forbidden marker present (${label}) in ${file}" \
      "Forbidden literal: ${literal}" \
      "Remove payment-method chooser language so S02 remains QR-only."
  fi
}

main() {
  log "status=starting"

  require_file "${TEST_BEHAVIOR}"
  require_file "${TEST_QR_DESIGN}"
  require_file "${TEST_HOME_DESIGN}"
  require_file "${QR_PAY_VIEW}"
  require_file "${HOME_VIEW}"
  require_file "${PBXPROJ}"

  run_phase "behavior-contract" \
    rtk proxy python -m pytest -q "${TEST_BEHAVIOR}"

  run_phase "design-contracts" \
    rtk proxy python -m pytest -q "${TEST_QR_DESIGN}" "${TEST_HOME_DESIGN}"

  log "phase=static-scope status=running"

  # Required QR state coverage markers in QRPayView.
  assert_contains_literal "${QR_PAY_VIEW}" "switch viewModel.state" "state_switch"
  assert_contains_literal "${QR_PAY_VIEW}" "case .scanning:" "state_scanning"
  assert_contains_literal "${QR_PAY_VIEW}" "case .loading:" "state_loading"
  assert_contains_literal "${QR_PAY_VIEW}" "case .confirming(let cart, let token):" "state_confirming"
  assert_contains_literal "${QR_PAY_VIEW}" "case .success(let newBalance):" "state_success"
  assert_contains_literal "${QR_PAY_VIEW}" "case .error(let message):" "state_error"

  # Required QR-only surfaces and controls.
  assert_contains_literal "${QR_PAY_VIEW}" "Pay with QR" "qr_title"
  assert_contains_literal "${QR_PAY_VIEW}" "Scan cashier QR" "qr_scan_copy"
  assert_contains_literal "${QR_PAY_VIEW}" "Confirm QR Payment" "qr_confirm_cta"
  assert_contains_literal "${QR_PAY_VIEW}" "Button(\"Retry Scan\")" "retry_control"
  assert_contains_literal "${QR_PAY_VIEW}" "Button(\"Cancel\")" "cancel_control"

  # Required Home QR-only entry markers.
  assert_contains_literal "${HOME_VIEW}" "Pay with QR" "home_qr_copy"
  assert_contains_literal "${HOME_VIEW}" "home-qr-pay-button" "home_qr_identifier"
  assert_contains_literal "${HOME_VIEW}" "QR Pay is the only payment method available on iOS." "home_qr_only_copy"

  # QR-only invariant: forbid payment method chooser language.
  assert_absent_literal "${QR_PAY_VIEW}" "Payment Method" "forbidden_payment_method_label"
  assert_absent_literal "${QR_PAY_VIEW}" "Select payment method" "forbidden_select_payment_method"
  assert_absent_literal "${QR_PAY_VIEW}" "Choose payment method" "forbidden_choose_payment_method"
  assert_absent_literal "${QR_PAY_VIEW}" "Credit Card" "forbidden_credit_card"
  assert_absent_literal "${QR_PAY_VIEW}" "Debit Card" "forbidden_debit_card"
  assert_absent_literal "${QR_PAY_VIEW}" "Apple Pay" "forbidden_apple_pay"
  assert_absent_literal "${QR_PAY_VIEW}" "Tap to Pay" "forbidden_tap_to_pay"

  assert_absent_literal "${HOME_VIEW}" "Payment Method" "home_forbidden_payment_method_label"
  assert_absent_literal "${HOME_VIEW}" "Select payment method" "home_forbidden_select_payment_method"
  assert_absent_literal "${HOME_VIEW}" "Choose payment method" "home_forbidden_choose_payment_method"
  assert_absent_literal "${HOME_VIEW}" "Credit Card" "home_forbidden_credit_card"
  assert_absent_literal "${HOME_VIEW}" "Debit Card" "home_forbidden_debit_card"

  # Camera usage key must remain in iOS project build settings.
  assert_contains_literal "${PBXPROJ}" "INFOPLIST_KEY_NSCameraUsageDescription =" "camera_usage_key"

  log "phase=static-scope status=passed"
  log "status=passed"
}

main "$@"
