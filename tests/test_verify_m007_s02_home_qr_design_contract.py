from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
HOME_VIEW_PATH = IOS_ROOT / "Views" / "Home" / "HomeView.swift"
HOME_VM_PATH = IOS_ROOT / "ViewModels" / "HomeViewModel.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_home_qr_entry_uses_stitch_tokens_and_qr_only_copy():
    contents = read_text(HOME_VIEW_PATH)

    required_entries = [
        "private var qrEntryCard: some View",
        "StitchCard",
        "StitchPrimaryButtonStyle",
        "AppTheme.Palette",
        "AppTheme.Spacing",
        "AppTheme.Typography",
        "Pay with QR",
        "QR Pay is the only payment method available on iOS.",
    ]

    forbidden_payment_method_copy = [
        "Payment Method",
        "Select payment method",
        "Choose payment method",
        "Credit Card",
        "Debit Card",
    ]

    for entry in required_entries:
        assert entry in contents, f"Home QR design contract missing: {entry}"

    for entry in forbidden_payment_method_copy:
        assert entry not in contents, f"Home QR-only contract violated by payment-method copy: {entry}"


def test_home_qr_button_identifier_and_sheet_wiring_remain_stable():
    contents = read_text(HOME_VIEW_PATH)

    required_entries = [
        "Button {",
        "showQrPay = true",
        '.accessibilityIdentifier("home-qr-pay-button")',
        ".sheet(isPresented: $showQrPay)",
        "QRPayView {",
        ".environmentObject(apiClient)",
    ]

    for entry in required_entries:
        assert entry in contents, f"Home QR CTA wiring contract missing: {entry}"

    assert contents.count('accessibilityIdentifier("home-qr-pay-button")') == 1, (
        "Expected exactly one stable home-qr-pay-button accessibility identifier"
    )


def test_home_qr_success_callback_links_to_refresh_continuity_path():
    home_contents = read_text(HOME_VIEW_PATH)
    vm_contents = read_text(HOME_VM_PATH)

    home_required_entries = [
        "await viewModel.refreshAfterQRSuccess(apiClient: apiClient, authManager: authManager)",
    ]
    vm_required_entries = [
        "func refreshAfterQRSuccess(apiClient: APIClient, authManager: AuthManager) async",
        'log("Refreshing Home data after QR payment success dismiss")',
        "await load(apiClient: apiClient, authManager: authManager)",
    ]

    for entry in home_required_entries:
        assert entry in home_contents, f"Home success callback contract missing: {entry}"

    for entry in vm_required_entries:
        assert entry in vm_contents, f"Home refresh continuity contract missing: {entry}"
