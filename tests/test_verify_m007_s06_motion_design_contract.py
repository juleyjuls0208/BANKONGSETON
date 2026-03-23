from pathlib import Path

PRIMITIVE_FILES = [
    Path("mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift"),
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
SLICE_ARTIFACTS = [
    Path("scripts/verify-m007-s06.sh"),
    Path(".gsd/milestones/M007/slices/S06/S06-UAT.md"),
]


def test_no_repeat_forever_in_in_scope_motion_surfaces() -> None:
    offenders = [
        str(path)
        for path in PRIMITIVE_FILES + STATEFUL_FILES
        if "repeatForever" in path.read_text(encoding="utf-8")
    ]

    assert not offenders, "Decorative infinite animations detected in: " + ", ".join(offenders)


def test_slice_observability_artifacts_exist() -> None:
    missing = [str(path) for path in SLICE_ARTIFACTS if not path.exists()]
    assert not missing, "Missing S06 observability artifacts: " + ", ".join(missing)
