from pathlib import Path

THEME_FILE = Path("mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift")
PRIMITIVE_FILES = [
    Path("mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift"),
    Path("mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift"),
    Path("mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift"),
]
STATEFUL_FILES = [
    Path("mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift"),
    Path("mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift"),
    Path("mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift"),
    Path("mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift"),
    Path("mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift"),
]


def test_shared_motion_policy_surface_exists() -> None:
    theme_text = THEME_FILE.read_text(encoding="utf-8")

    assert "enum Motion" in theme_text
    assert "enum Duration" in theme_text
    assert "static func animation(" in theme_text
    assert "Animation" in theme_text


def test_reduce_motion_wiring_exists_for_primitives_and_stateful_views() -> None:
    primitive_text = "\n".join(path.read_text(encoding="utf-8") for path in PRIMITIVE_FILES)
    assert "accessibilityReduceMotion" in primitive_text

    missing_stateful_files = [
        str(path)
        for path in STATEFUL_FILES
        if "accessibilityReduceMotion" not in path.read_text(encoding="utf-8")
    ]

    assert not missing_stateful_files, (
        "Stateful view Reduce Motion wiring is incomplete: "
        + ", ".join(missing_stateful_files)
    )
