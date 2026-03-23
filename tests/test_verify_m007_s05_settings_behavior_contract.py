from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
SETTINGS_VM_PATH = IOS_ROOT / "ViewModels" / "SettingsViewModel.swift"
AUTH_MANAGER_PATH = IOS_ROOT / "Core" / "Auth" / "AuthManager.swift"
HOME_VM_PATH = IOS_ROOT / "ViewModels" / "HomeViewModel.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_settings_view_model_exposes_local_persistence_state_and_explicit_actions():
    contents = read_text(SETTINGS_VM_PATH)

    required_entries = [
        "settingsAccentHexKey",
        "settingsDisplayNameKey",
        "editableDisplayName",
        "selectedAccentHex",
        "func savePersonalInfo()",
        "func applyAccent(_ accentHex: String)",
        "personalInfoSaveState",
        "accentApplyState",
        "SettingsPersistenceState",
    ]

    for entry in required_entries:
        assert entry in contents, f"Settings persistence behavior marker missing: {entry}"

    assert "APIClient" not in contents, "Settings persistence logic must remain local-only"


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


def test_home_view_model_exposes_resolved_display_name_for_settings_persistence_flow():
    contents = read_text(HOME_VM_PATH)

    required_entries = [
        "resolvedDisplayName",
    ]

    for entry in required_entries:
        assert entry in contents, f"Home/settings continuity marker missing: {entry}"
