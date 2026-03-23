from pathlib import Path

IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
THEME_FILE = IOS_ROOT / "UI" / "Theme" / "AppTheme.swift"

PRIMITIVE_FILES = {
    "button": IOS_ROOT / "UI" / "Components" / "StitchPrimaryButtonStyle.swift",
    "tab_shell": IOS_ROOT / "UI" / "Shell" / "StitchTabShell.swift",
    "card": IOS_ROOT / "UI" / "Components" / "StitchCard.swift",
}

STATEFUL_FILES = {
    "qr": IOS_ROOT / "Views" / "QR" / "QRPayView.swift",
    "transactions": IOS_ROOT / "Views" / "Transactions" / "TransactionsView.swift",
    "budget": IOS_ROOT / "Views" / "Budget" / "BudgetView.swift",
    "lost_card": IOS_ROOT / "Views" / "LostCard" / "LostCardView.swift",
    "home": IOS_ROOT / "Views" / "Home" / "HomeView.swift",
}

ACTIONABILITY_MARKERS = {
    STATEFUL_FILES["qr"]: [
        'Button("Confirm QR Payment")',
        "viewModel.confirm(token: token, apiClient: apiClient)",
        'Button("Retry Scan") { viewModel.reset() }',
        'Button("Done")',
    ],
    STATEFUL_FILES["transactions"]: [
        '"transactions-retry-initial-button"',
        '"transactions-retry-pagination-button"',
        '"transactions-load-more-button"',
        '"transactions-clear-search-filter-button"',
    ],
    STATEFUL_FILES["budget"]: [
        '"budget-save-button"',
        '"budget-refresh-button"',
        '"budget-retry-load-button"',
        '"budget-retry-save-button"',
    ],
    STATEFUL_FILES["lost_card"]: [
        '"lost-card-report-button"',
        '"lost-card-retry-button"',
        '"lost-card-success-done-button"',
        '"lost-card-error-dismiss-button"',
    ],
    STATEFUL_FILES["home"]: [
        '"home-qr-pay-button"',
        "showQrPay = true",
    ],
}


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_shared_motion_policy_surface_exists() -> None:
    theme_text = read_text(THEME_FILE)

    required_markers = [
        "enum Motion",
        "enum Duration",
        "enum Primitive",
        "case primaryButtonPress",
        "case tabSelection",
        "case cardSurface",
        "static func animation(",
        "accessibilityReduceMotion",
    ]

    for marker in required_markers:
        assert marker in theme_text, f"Missing motion-policy marker in AppTheme: {marker}"


def test_reduce_motion_wiring_exists_for_primitives_and_stateful_views() -> None:
    primitive_text = "\n".join(read_text(path) for path in PRIMITIVE_FILES.values())
    assert "accessibilityReduceMotion" in primitive_text

    missing_stateful_files = [
        str(path)
        for path in STATEFUL_FILES.values()
        if "accessibilityReduceMotion" not in read_text(path)
    ]

    assert not missing_stateful_files, (
        "Stateful view Reduce Motion wiring is incomplete: "
        + ", ".join(missing_stateful_files)
    )


def test_motion_policy_usage_is_tokenized_in_shared_primitives() -> None:
    button_text = read_text(PRIMITIVE_FILES["button"])
    tab_shell_text = read_text(PRIMITIVE_FILES["tab_shell"])
    card_text = read_text(PRIMITIVE_FILES["card"])

    button_markers = [
        "AppTheme.Motion.pressedScale(",
        "AppTheme.Motion.animation(",
        "for: .primaryButtonPress",
    ]
    tab_shell_markers = [
        "withAnimation(",
        "AppTheme.Motion.animation(",
        "for: .tabSelection",
    ]
    card_markers = [
        "AppTheme.Motion.cardScale(",
        "AppTheme.Motion.cardVerticalOffset(",
        "AppTheme.Motion.animation(",
        "for: .cardSurface",
    ]

    for marker in button_markers:
        assert marker in button_text, f"Primary-button motion marker missing: {marker}"

    for marker in tab_shell_markers:
        assert marker in tab_shell_text, f"Tab-shell motion marker missing: {marker}"

    for marker in card_markers:
        assert marker in card_text, f"Card motion marker missing: {marker}"


def test_in_scope_controls_remain_actionable_after_motion_tuning() -> None:
    for path, markers in ACTIONABILITY_MARKERS.items():
        contents = read_text(path)
        for marker in markers:
            assert marker in contents, f"Actionability marker missing in {path}: {marker}"
