from pathlib import Path

IOS_ROOT = Path("mobile/ios/BankongSetonStudent")

IN_SCOPE_MOTION_FILES = {
    "theme": IOS_ROOT / "UI" / "Theme" / "AppTheme.swift",
    "button": IOS_ROOT / "UI" / "Components" / "StitchPrimaryButtonStyle.swift",
    "tab_shell": IOS_ROOT / "UI" / "Shell" / "StitchTabShell.swift",
    "card": IOS_ROOT / "UI" / "Components" / "StitchCard.swift",
    "qr": IOS_ROOT / "Views" / "QR" / "QRPayView.swift",
    "transactions": IOS_ROOT / "Views" / "Transactions" / "TransactionsView.swift",
    "budget": IOS_ROOT / "Views" / "Budget" / "BudgetView.swift",
    "lost_card": IOS_ROOT / "Views" / "LostCard" / "LostCardView.swift",
    "home": IOS_ROOT / "Views" / "Home" / "HomeView.swift",
}

STATEFUL_MOTION_MARKERS = {
    IN_SCOPE_MOTION_FILES["qr"]: [
        "private var stateTransitionAnimation: Animation",
        "private var stateTransitionKey: String",
        ".id(stateTransitionKey)",
        ".transition(stateTransition)",
        ".animation(stateTransitionAnimation, value: stateTransitionKey)",
        "if accessibilityReduceMotion {",
        "return .opacity",
        "case .scanning:",
        "case .loading:",
        "case .confirming:",
        "case .success:",
        "case .error:",
    ],
    IN_SCOPE_MOTION_FILES["transactions"]: [
        "private var screenTransitionAnimation: Animation",
        "private var stateCardTransition: AnyTransition",
        "private var transactionStateKey: String",
        ".animation(screenTransitionAnimation, value: transactionStateKey)",
        ".transition(stateCardTransition)",
        "if accessibilityReduceMotion {",
        "return .opacity",
    ],
    IN_SCOPE_MOTION_FILES["budget"]: [
        "private var stateTransitionAnimation: Animation",
        "private var loadStateKey: String",
        "private var saveStateKey: String",
        ".animation(stateTransitionAnimation, value: loadStateKey)",
        ".animation(stateTransitionAnimation, value: saveStateKey)",
        ".transition(stateTransition)",
        "if accessibilityReduceMotion {",
        "return .opacity",
    ],
    IN_SCOPE_MOTION_FILES["lost_card"]: [
        "private var stateTransitionAnimation: Animation",
        ".id(viewModel.phase.rawValue)",
        ".animation(stateTransitionAnimation, value: viewModel.phase.rawValue)",
        ".transition(stateTransition)",
        "if accessibilityReduceMotion {",
        "return .opacity",
    ],
    IN_SCOPE_MOTION_FILES["home"]: [
        "private var screenTransitionAnimation: Animation",
        "private var errorBannerStateKey: String",
        "private var recentTransactionStateKey: String",
        ".animation(screenTransitionAnimation, value: errorBannerStateKey)",
        ".animation(screenTransitionAnimation, value: recentTransactionStateKey)",
        ".transition(stateTransition)",
        "if accessibilityReduceMotion {",
        "return .opacity",
    ],
}

SLICE_ARTIFACTS = [
    Path("scripts/verify-m007-s06.sh"),
    Path(".gsd/milestones/M007/slices/S06/S06-UAT.md"),
]


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_stateful_surfaces_include_explicit_motion_transition_markers() -> None:
    for path, markers in STATEFUL_MOTION_MARKERS.items():
        contents = read_text(path)
        assert "AppTheme.Motion.animation(" in contents, (
            f"Stateful motion policy usage missing in {path}: AppTheme.Motion.animation("
        )
        assert "accessibilityReduceMotion" in contents, (
            f"Reduce Motion marker missing in {path}: accessibilityReduceMotion"
        )

        for marker in markers:
            assert marker in contents, f"State-transition design marker missing in {path}: {marker}"


def test_no_repeat_forever_in_in_scope_motion_surfaces() -> None:
    offenders = [
        str(path)
        for path in IN_SCOPE_MOTION_FILES.values()
        if "repeatForever" in read_text(path)
    ]

    assert not offenders, "Decorative infinite animations detected in: " + ", ".join(offenders)


def test_slice_observability_artifacts_exist() -> None:
    missing = [str(path) for path in SLICE_ARTIFACTS if not path.exists()]
    assert not missing, "Missing S06 observability artifacts: " + ", ".join(missing)
