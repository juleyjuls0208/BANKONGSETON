from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
THEME_ROOT = IOS_ROOT / "UI" / "Theme"
COMPONENTS_ROOT = IOS_ROOT / "UI" / "Components"
PBXPROJ_PATH = IOS_ROOT / "BankongSetonStudent.xcodeproj" / "project.pbxproj"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_design_system_foundation_files_exist():
    expected_files = [
        THEME_ROOT / "AppTheme.swift",
        THEME_ROOT / "Color+Hex.swift",
        COMPONENTS_ROOT / "StitchCard.swift",
        COMPONENTS_ROOT / "StitchFieldStyle.swift",
        COMPONENTS_ROOT / "StitchPrimaryButtonStyle.swift",
    ]

    missing = [str(path) for path in expected_files if not path.exists()]
    assert not missing, f"Missing design foundation files: {missing}"


def test_app_theme_exposes_semantic_token_groups():
    contents = read_text(THEME_ROOT / "AppTheme.swift")

    required_symbols = [
        "enum AppTheme",
        "enum Palette",
        "enum Spacing",
        "enum Radius",
        "enum Typography",
        "enum Shadows",
        "struct AppShadow",
    ]

    for symbol in required_symbols:
        assert symbol in contents, f"Expected AppTheme token symbol missing: {symbol}"


def test_shared_primitives_export_expected_symbols():
    stitch_card = read_text(COMPONENTS_ROOT / "StitchCard.swift")
    stitch_field = read_text(COMPONENTS_ROOT / "StitchFieldStyle.swift")
    stitch_button = read_text(COMPONENTS_ROOT / "StitchPrimaryButtonStyle.swift")

    assert "struct StitchCard" in stitch_card
    assert "struct StitchFieldStyle" in stitch_field
    assert "func stitchFieldStyle()" in stitch_field
    assert "struct StitchPrimaryButtonStyle" in stitch_button


def test_color_hex_is_shared_theme_utility_not_localized_to_transaction_row():
    color_helper = read_text(THEME_ROOT / "Color+Hex.swift")
    transaction_row = read_text(IOS_ROOT / "Views" / "Transactions" / "TransactionRowView.swift")

    assert "extension Color" in color_helper
    assert "init(hex: String)" in color_helper

    assert "extension Color" not in transaction_row
    assert "init(hex: String)" not in transaction_row


def test_xcode_project_registers_design_system_sources():
    project_contents = read_text(PBXPROJ_PATH)

    required_entries = [
        "AppTheme.swift",
        "Color+Hex.swift",
        "StitchCard.swift",
        "StitchFieldStyle.swift",
        "StitchPrimaryButtonStyle.swift",
        "AA000030 /* AppTheme.swift in Sources */",
        "AA000031 /* Color+Hex.swift in Sources */",
        "AA000032 /* StitchCard.swift in Sources */",
        "AA000033 /* StitchFieldStyle.swift in Sources */",
        "AA000034 /* StitchPrimaryButtonStyle.swift in Sources */",
        "EE000018 /* UI */",
        "EE000019 /* Theme */",
        "EE000020 /* Components */",
    ]

    for entry in required_entries:
        assert entry in project_contents, f"Missing Xcode project registration entry: {entry}"
