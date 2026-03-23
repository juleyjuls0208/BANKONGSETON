from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")

HOME_VIEW_PATH = IOS_ROOT / "Views" / "Home" / "HomeView.swift"
SETTINGS_VIEW_PATH = IOS_ROOT / "Views" / "Settings" / "SettingsView.swift"
RECEIPT_VIEW_PATH = IOS_ROOT / "Views" / "Receipt" / "ReceiptView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def assert_forbidden_markers_absent(path: Path, markers: list[str], scope_label: str) -> None:
    contents = read_text(path)
    for marker in markers:
        assert marker not in contents, f"Forbidden {scope_label} marker leaked into {path}: {marker}"


def test_qr_only_payment_direction_stays_intact_and_nfc_surfaces_do_not_return() -> None:
    home_contents = read_text(HOME_VIEW_PATH)

    assert "QR Pay is the only payment method available on iOS." in home_contents

    forbidden_payment_method_markers = [
        'Button("Pay with NFC")',
        'Label("Pay with NFC"',
        'Button("Manage Payment Method")',
        'NavigationLink("Payment Method")',
        '"home-nfc-pay-button"',
        '"home-payment-method-button"',
    ]

    for marker in forbidden_payment_method_markers:
        assert marker not in home_contents, f"Forbidden payment-method marker leaked into Home: {marker}"


def test_settings_screen_does_not_reintroduce_out_of_scope_utility_surfaces() -> None:
    assert_forbidden_markers_absent(
        SETTINGS_VIEW_PATH,
        [
            "Payment Method",
            "Manage Payment Method",
            "Tuition Auto-Pay",
            "Campus Discounts",
            "Privacy & Security",
            "settings-payment-method",
            "settings-autopay",
        ],
        "settings_scope",
    )


def test_receipt_surface_remains_scoped_to_view_only_without_report_or_download_actions() -> None:
    assert_forbidden_markers_absent(
        RECEIPT_VIEW_PATH,
        [
            "Download PDF",
            "Report Issue",
            "Report Receipt",
            "receipt-download-button",
            "receipt-report-issue-button",
            "receipt-share-button",
        ],
        "receipt_scope",
    )
