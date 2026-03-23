from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
SETTINGS_VM_PATH = IOS_ROOT / "ViewModels" / "SettingsViewModel.swift"
SETTINGS_VIEW_PATH = IOS_ROOT / "Views" / "Settings" / "SettingsView.swift"
AUTH_MANAGER_PATH = IOS_ROOT / "Core" / "Auth" / "AuthManager.swift"
HOME_VM_PATH = IOS_ROOT / "ViewModels" / "HomeViewModel.swift"
CONTENT_VIEW_PATH = IOS_ROOT / "App" / "ContentView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_settings_view_model_exposes_local_persistence_channels_and_explicit_save_apply_actions():
    contents = read_text(SETTINGS_VM_PATH)

    required_entries = [
        "settingsAccentHexKey",
        "settingsDisplayNameKey",
        "editableDisplayName",
        "selectedAccentHex",
        "func savePersonalInfo()",
        "func applyAccent(_ accentHex: String)",
        "func logout(_ action: () async -> Void) async",
        "SettingsPersistenceState",
        "case idle",
        "case applying",
        "case saved",
        "personalInfoSaveState",
        "accentApplyState",
        "Notification.Name",
        "settingsAccentDidChange",
        "settingsDisplayNameDidChange",
    ]

    for entry in required_entries:
        assert entry in contents, f"Settings persistence behavior marker missing: {entry}"


def test_settings_profile_persistence_stays_local_only_without_backend_profile_write_path():
    contents = read_text(SETTINGS_VM_PATH)

    assert "APIClient" not in contents, "Settings persistence logic must remain local-only"

    forbidden_backend_markers = [
        "apiClient.",
        "updateProfile",
        "updateStudentProfile",
        "patchProfile",
        "putProfile",
    ]

    for marker in forbidden_backend_markers:
        assert marker not in contents, f"Forbidden backend profile-write marker leaked into settings persistence path: {marker}"


def test_auth_manager_session_clear_does_not_delete_settings_owned_preferences():
    contents = read_text(AUTH_MANAGER_PATH)

    required_entries = [
        "func clearAll()",
        "settings_accent_hex",
        "settings_display_name",
    ]

    for entry in required_entries:
        assert entry in contents, f"Auth/session boundary marker missing: {entry}"

    forbidden_entries = [
        '"theme_mode",',
        '"settings_accent_hex",',
        '"settings_display_name",',
    ]

    for entry in forbidden_entries:
        assert entry not in contents, f"Settings preference should not be deleted by auth clear path: {entry}"


def test_settings_continuity_markers_cover_lost_card_navigation_and_logout_actionability():
    settings_view_contents = read_text(SETTINGS_VIEW_PATH)

    required_view_markers = [
        'NavigationLink("Report Lost Card")',
        "LostCardView()",
        "settings-report-lost-card-link",
        "settings-logout-button",
        "await viewModel.logout {",
        "await authManager.logout(apiClient: apiClient)",
    ]

    for marker in required_view_markers:
        assert marker in settings_view_contents, f"Settings continuity marker missing: {marker}"


def test_home_and_root_shell_include_settings_persistence_channels_for_display_name_and_accent():
    home_contents = read_text(HOME_VM_PATH)
    content_view_contents = read_text(CONTENT_VIEW_PATH)

    required_home_entries = [
        "resolvedDisplayName",
        "refreshResolvedDisplayName",
        "settings_display_name",
        "return \"Student\"",
    ]
    required_content_entries = [
        "selectedAccentHex",
        "settingsAccentDidChange",
        "reloadPersistedAccent",
        "settings_accent_hex",
        ".appThemeAccentHex(selectedAccentHex)",
    ]

    for entry in required_home_entries:
        assert entry in home_contents, f"Home/settings continuity marker missing: {entry}"

    for entry in required_content_entries:
        assert entry in content_view_contents, f"Root accent continuity marker missing: {entry}"
