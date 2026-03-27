from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
HOME_VIEW_PATH = IOS_ROOT / "Views" / "Home" / "HomeView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def assert_required_markers(contents: str, markers: list[str], contract: str) -> None:
    for marker in markers:
        assert marker in contents, f"{contract}: missing required marker: {marker}"


def assert_forbidden_markers(contents: str, markers: list[str], contract: str) -> None:
    found = [marker for marker in markers if marker in contents]
    assert not found, f"{contract}: found forbidden markers: {found}"


def test_home_exposes_minimal_credit_card_hero_contract() -> None:
    contents = read_text(HOME_VIEW_PATH)

    assert_required_markers(
        contents,
        [
            "private var creditCardHero: some View",
            "Text(viewModel.resolvedDisplayName)",
            "Text(\"₱\\(String(format: \"%.2f\", viewModel.balance))\")",
            "Text(\"Current Balance\")",
            '.accessibilityIdentifier("home-credit-card-hero")',
            "RoundedRectangle(cornerRadius: 22, style: .continuous)",
            "LinearGradient(",
        ],
        "home_minimal_credit_card_hero",
    )


def test_home_removes_m007_heavy_transition_scaffolding() -> None:
    contents = read_text(HOME_VIEW_PATH)

    assert_forbidden_markers(
        contents,
        [
            "private var screenTransitionAnimation: Animation",
            "private var stateTransition: AnyTransition",
            "private var errorBannerStateKey",
            "private var recentTransactionStateKey",
            ".animation(screenTransitionAnimation, value: errorBannerStateKey)",
            ".animation(screenTransitionAnimation, value: recentTransactionStateKey)",
            ".id(recentTransactionStateKey)",
        ],
        "home_rollback_minimalism",
    )


def test_home_keeps_qr_entry_and_post_success_continuity_seam() -> None:
    contents = read_text(HOME_VIEW_PATH)

    assert_required_markers(
        contents,
        [
            '.sheet(isPresented: $showQrPay) {',
            "QRPayView {",
            "handleQRPaySuccessCompletion()",
            "@State private var didConsumePresentedQRSuccess = false",
            '@AppStorage("qr_payment_success_continuity_tick") private var qrPaymentSuccessContinuityTick = 0',
            "guard !didConsumePresentedQRSuccess else {",
            "qrPaymentSuccessContinuityTick += 1",
            "await viewModel.refreshAfterQRSuccess(apiClient: apiClient, authManager: authManager)",
            '.accessibilityIdentifier("home-qr-pay-button")',
            "showQrPay = true",
        ],
        "home_qr_continuity",
    )


def test_home_negative_paths_keep_stable_empty_and_retry_surfaces() -> None:
    contents = read_text(HOME_VIEW_PATH)

    assert_required_markers(
        contents,
        [
            "No recent transactions.",
            "Pull to refresh or tap retry.",
            'Button("Retry")',
            "await viewModel.load(apiClient: apiClient, authManager: authManager)",
        ],
        "home_negative_paths",
    )
