from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
QR_PAY_VIEW_PATH = IOS_ROOT / "Views" / "QR" / "QRPayView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_qr_pay_view_covers_all_required_qr_states_in_switch():
    contents = read_text(QR_PAY_VIEW_PATH)

    required_entries = [
        "switch viewModel.state",
        "case .scanning:",
        "case .loading:",
        "case .confirming(let cart, let token):",
        "case .success(let newBalance):",
        "case .error(let message):",
    ]

    for entry in required_entries:
        assert entry in contents, f"QR state coverage contract missing: {entry}"


def test_qr_pay_view_uses_stitch_primitives_and_theme_tokens_across_states():
    contents = read_text(QR_PAY_VIEW_PATH)

    required_entries = [
        "StitchCard",
        "StitchPrimaryButtonStyle",
        "AppTheme.Palette",
        "AppTheme.Spacing",
        "AppTheme.Typography",
    ]

    for entry in required_entries:
        assert entry in contents, f"Stitch primitive/theme usage contract missing: {entry}"

    assert contents.count("StitchCard {") >= 5, "Expected stitch card surfaces for all QR states"


def test_qr_state_ctas_are_actionable_and_wired_to_real_behaviors():
    contents = read_text(QR_PAY_VIEW_PATH)

    required_entries = [
        "onCodeScanned: { scannedPayload in",
        "viewModel.handleScannedURL(scannedPayload, apiClient: apiClient)",
        "Button(\"Confirm QR Payment\")",
        "viewModel.confirm(token: token, apiClient: apiClient)",
        "Button(\"Done\")",
        "Button(\"Retry Scan\") { viewModel.reset() }",
        "Button(\"Close\") { dismiss() }",
        "Button(\"Cancel\") { dismiss() }",
        "Button(\"Open Settings\")",
        "UIApplication.openSettingsURLString",
    ]

    for entry in required_entries:
        assert entry in contents, f"Actionable CTA contract missing: {entry}"


def test_qr_pay_copy_stays_qr_only_without_payment_method_selector_language():
    contents = read_text(QR_PAY_VIEW_PATH)

    required_qr_copy = [
        "Pay with QR",
        "Scan cashier QR",
        "Loading QR payment details…",
        "Confirm QR Payment",
    ]

    forbidden_payment_method_copy = [
        "Payment Method",
        "Select payment method",
        "Choose payment method",
        "Credit Card",
        "Debit Card",
        "Apple Pay",
        "Tap to Pay",
        "NFC",
    ]

    for entry in required_qr_copy:
        assert entry in contents, f"QR-specific copy contract missing: {entry}"

    for entry in forbidden_payment_method_copy:
        assert entry not in contents, f"QR-only contract violated by payment-method copy: {entry}"
