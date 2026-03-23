from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
SETTINGS_VIEW_PATH = IOS_ROOT / "Views" / "Settings" / "SettingsView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_settings_scope_cleanup_keeps_only_in_scope_actions_visible():
    contents = read_text(SETTINGS_VIEW_PATH)

    required_entries = [
        "Personal Info",
        "Appearance",
        "Account Actions",
        "Report Lost Card",
        "Logout",
    ]

    forbidden_entries = [
        "Privacy & Security",
        "Tuition Auto-Pay",
        "Campus Discounts",
        "Payment Method",
        "Manage Payment Method",
    ]

    for entry in required_entries:
        assert entry in contents, f"Settings scope continuity marker missing: {entry}"

    for entry in forbidden_entries:
        assert entry not in contents, f"Out-of-scope Settings action leaked into UI: {entry}"


def test_settings_design_contract_requires_stitch_surface_tokens_status_markers_and_actionable_controls():
    contents = read_text(SETTINGS_VIEW_PATH)

    required_entries = [
        "NavigationStack",
        "StitchCard",
        "StitchPrimaryButtonStyle",
        "stitchFieldStyle()",
        "AppTheme.Palette",
        "AppTheme.Spacing",
        "AppTheme.Typography",
        "AppTheme.Radius",
        "settings-screen-root",
        "settings-display-name-field",
        "settings-save-personal-info-button",
        "settings-theme-picker",
        "settings-apply-accent-button",
        "settings-personal-info-status",
        "settings-accent-status",
        "settings-report-lost-card-link",
        "settings-logout-button",
        "settings-accent-option-\\(option.id)",
        "editableDisplayName",
        "selectedAccentHex",
        "savePersonalInfo",
        "applyAccent",
    ]

    forbidden_entries = [
        "Form {",
        "Section(\"Personal Info\")",
    ]

    for entry in required_entries:
        assert entry in contents, f"Settings stitch/persistence design marker missing: {entry}"

    for entry in forbidden_entries:
        assert entry not in contents, f"Legacy non-stitch settings structure leaked into S05 surface: {entry}"
