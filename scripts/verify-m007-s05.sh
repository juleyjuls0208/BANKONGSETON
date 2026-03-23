#!/usr/bin/env bash
# M007/S05 one-command verifier.
# Runs behavior/design contracts and static guardrails for
# Settings local persistence, scope cleanup, and shared accent/profile continuity.

set -euo pipefail

SCRIPT_NAME="verify-m007-s05"

BEHAVIOR_TEST="tests/test_verify_m007_s05_settings_behavior_contract.py"
DESIGN_TEST="tests/test_verify_m007_s05_settings_design_contract.py"
UAT_CHECKLIST=".gsd/milestones/M007/slices/S05/S05-UAT.md"

SETTINGS_VIEW="mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift"
SETTINGS_VM="mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift"
AUTH_MANAGER="mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift"
HOME_VM="mobile/ios/BankongSetonStudent/ViewModels/HomeViewModel.swift"
CONTENT_VIEW="mobile/ios/BankongSetonStudent/App/ContentView.swift"
APP_THEME="mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift"
STITCH_PRIMARY_BUTTON="mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift"
STITCH_TAB_SHELL="mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift"

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
      "Restore/create the missing artifact, then re-run: rtk proxy sh scripts/verify-m007-s05.sh"
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
      "Restore the S05 contract marker, then re-run this verifier."
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
      "Remove the out-of-scope/leaked marker, then re-run this verifier."
  fi
}

run_preflight() {
  log "phase=preflight status=running"

  require_file "${BEHAVIOR_TEST}"
  require_file "${DESIGN_TEST}"
  require_file "${UAT_CHECKLIST}"

  require_file "${SETTINGS_VIEW}"
  require_file "${SETTINGS_VM}"
  require_file "${AUTH_MANAGER}"
  require_file "${HOME_VM}"
  require_file "${CONTENT_VIEW}"
  require_file "${APP_THEME}"
  require_file "${STITCH_PRIMARY_BUTTON}"
  require_file "${STITCH_TAB_SHELL}"

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

  # Settings screen stitch/actionable markers.
  assert_contains_literal "${SETTINGS_VIEW}" "settings-screen-root" "settings_screen_root"
  assert_contains_literal "${SETTINGS_VIEW}" "settings-display-name-field" "settings_display_name_field"
  assert_contains_literal "${SETTINGS_VIEW}" "settings-save-personal-info-button" "settings_save_personal_info_button"
  assert_contains_literal "${SETTINGS_VIEW}" "settings-theme-picker" "settings_theme_picker"
  assert_contains_literal "${SETTINGS_VIEW}" "settings-apply-accent-button" "settings_apply_accent_button"
  assert_contains_literal "${SETTINGS_VIEW}" "settings-personal-info-status" "settings_personal_info_status"
  assert_contains_literal "${SETTINGS_VIEW}" "settings-accent-status" "settings_accent_status"
  assert_contains_literal "${SETTINGS_VIEW}" "settings-report-lost-card-link" "settings_report_lost_card_link"
  assert_contains_literal "${SETTINGS_VIEW}" "settings-logout-button" "settings_logout_button"
  assert_contains_literal "${SETTINGS_VIEW}" "NavigationLink(\"Report Lost Card\")" "settings_lost_card_navigation"
  assert_contains_literal "${SETTINGS_VIEW}" "await viewModel.logout {" "settings_logout_action_wrapper"
  assert_contains_literal "${SETTINGS_VIEW}" "await authManager.logout(apiClient: apiClient)" "settings_logout_action_target"

  assert_absent_literal "${SETTINGS_VIEW}" "Privacy & Security" "settings_forbidden_privacy"
  assert_absent_literal "${SETTINGS_VIEW}" "Tuition Auto-Pay" "settings_forbidden_autopay"
  assert_absent_literal "${SETTINGS_VIEW}" "Campus Discounts" "settings_forbidden_discounts"
  assert_absent_literal "${SETTINGS_VIEW}" "Payment Method" "settings_forbidden_payment_method"
  assert_absent_literal "${SETTINGS_VIEW}" "Manage Payment Method" "settings_forbidden_manage_payment_method"

  # Settings persistence channels and local-only semantics.
  assert_contains_literal "${SETTINGS_VM}" "settingsAccentHexKey" "vm_settings_accent_key"
  assert_contains_literal "${SETTINGS_VM}" "settingsDisplayNameKey" "vm_settings_display_name_key"
  assert_contains_literal "${SETTINGS_VM}" "func savePersonalInfo()" "vm_save_personal_info"
  assert_contains_literal "${SETTINGS_VM}" "func applyAccent(_ accentHex: String)" "vm_apply_accent"
  assert_contains_literal "${SETTINGS_VM}" "func logout(_ action: () async -> Void) async" "vm_logout_action"
  assert_contains_literal "${SETTINGS_VM}" "personalInfoSaveState = .applying" "vm_personal_info_state_applying"
  assert_contains_literal "${SETTINGS_VM}" "accentApplyState = .applying" "vm_accent_state_applying"
  assert_contains_literal "${SETTINGS_VM}" "KeychainHelper.save(editableDisplayName, forKey: settingsDisplayNameKey)" "vm_save_display_name_local"
  assert_contains_literal "${SETTINGS_VM}" "KeychainHelper.save(normalizedAccentHex, forKey: settingsAccentHexKey)" "vm_save_accent_local"
  assert_contains_literal "${SETTINGS_VM}" "NotificationCenter.default.post(name: .settingsDisplayNameDidChange" "vm_display_name_notification"
  assert_contains_literal "${SETTINGS_VM}" "NotificationCenter.default.post(name: .settingsAccentDidChange" "vm_accent_notification"

  assert_absent_literal "${SETTINGS_VM}" "APIClient" "vm_forbidden_api_client_coupling"
  assert_absent_literal "${SETTINGS_VM}" "updateProfile" "vm_forbidden_profile_update"

  # Auth/session boundary must preserve settings-owned local keys.
  assert_contains_literal "${AUTH_MANAGER}" "func clearAll()" "auth_clear_all"
  assert_contains_literal "${AUTH_MANAGER}" "settings_accent_hex" "auth_settings_accent_reference"
  assert_contains_literal "${AUTH_MANAGER}" "settings_display_name" "auth_settings_display_name_reference"
  assert_absent_literal "${AUTH_MANAGER}" '"settings_accent_hex",' "auth_forbidden_delete_settings_accent"
  assert_absent_literal "${AUTH_MANAGER}" '"settings_display_name",' "auth_forbidden_delete_settings_display_name"
  assert_absent_literal "${AUTH_MANAGER}" '"theme_mode",' "auth_forbidden_delete_theme_mode"

  # Display-name and accent continuity beyond Settings.
  assert_contains_literal "${HOME_VM}" "resolvedDisplayName" "home_resolved_display_name"
  assert_contains_literal "${HOME_VM}" "settings_display_name" "home_settings_display_name_key"
  assert_contains_literal "${HOME_VM}" "return \"Student\"" "home_student_fallback"

  assert_contains_literal "${CONTENT_VIEW}" "selectedAccentHex" "content_selected_accent"
  assert_contains_literal "${CONTENT_VIEW}" "settingsAccentDidChange" "content_settings_accent_notification"
  assert_contains_literal "${CONTENT_VIEW}" "reloadPersistedAccent" "content_reload_persisted_accent"
  assert_contains_literal "${CONTENT_VIEW}" ".appThemeAccentHex(selectedAccentHex)" "content_accent_environment_application"

  # Shared shell/button consumers of propagated accent environment.
  assert_contains_literal "${APP_THEME}" "var appAccentHex: String" "theme_app_accent_environment_key"
  assert_contains_literal "${APP_THEME}" "func appThemeAccentHex(_ accentHex: String)" "theme_app_accent_modifier"

  assert_contains_literal "${STITCH_PRIMARY_BUTTON}" "@Environment(\\.appAccentHex) private var accentHex" "button_accent_env_consumer"
  assert_contains_literal "${STITCH_PRIMARY_BUTTON}" "AppTheme.accentColor(for: accentHex)" "button_accent_color_usage"

  assert_contains_literal "${STITCH_TAB_SHELL}" "@Environment(\\.appAccentHex) private var accentHex" "shell_accent_env_consumer"
  assert_contains_literal "${STITCH_TAB_SHELL}" "AppTheme.accentColor(for: accentHex)" "shell_accent_color_usage"

  log "phase=static-contract status=passed"
  log "status=passed"
}

main "$@"
