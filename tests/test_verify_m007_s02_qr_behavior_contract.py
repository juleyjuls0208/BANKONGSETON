from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
QR_VM_PATH = IOS_ROOT / "ViewModels" / "QRPayViewModel.swift"
QR_SCANNER_PATH = IOS_ROOT / "Views" / "QR" / "QRScannerView.swift"
QR_PAY_VIEW_PATH = IOS_ROOT / "Views" / "QR" / "QRPayView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_qr_view_model_supports_url_and_token_payload_ingestion():
    contents = read_text(QR_VM_PATH)

    required_entries = [
        "private func parseScannedPayload",
        "extractTokenFromQRURL(payload)",
        'ParsedQRPayload(token: urlToken, source: "url")',
        "if isValidToken(payload)",
        'ParsedQRPayload(token: payload, source: "token")',
        "private func isValidToken(_ token: String)",
        '#\"^[A-Za-z0-9_-]{6,128}$\"#',
    ]

    for entry in required_entries:
        assert entry in contents, f"QR payload parsing contract entry missing: {entry}"


def test_duplicate_scan_frames_are_ignored_once_state_leaves_scanning():
    contents = read_text(QR_VM_PATH)

    required_entries = [
        "guard case .scanning = state else",
        "Ignoring duplicate scan while state is",
        "transition(to: .loading, reason: \"scan_accepted_",
    ]

    for entry in required_entries:
        assert entry in contents, f"Duplicate-scan guard contract missing: {entry}"


def test_malformed_payloads_are_rejected_with_explicit_state_transition():
    contents = read_text(QR_VM_PATH)

    required_entries = [
        "invalid_scan_payload",
        "This QR is invalid for payment.",
        "empty_scan_payload",
        "We couldn't read that QR code.",
    ]

    for entry in required_entries:
        assert entry in contents, f"Malformed payload rejection contract missing: {entry}"


def test_scanner_permission_and_setup_failures_emit_actionable_messages():
    contents = read_text(QR_SCANNER_PATH)

    required_entries = [
        "case .denied:",
        "case .restricted:",
        "AVCaptureDevice.requestAccess(for: .video)",
        "reportScannerFailure(\"Camera access is denied.",
        "Enable Camera access in Settings, then tap Retry.",
        "Failed to configure camera input. Tap Retry to try again.",
        "Failed to configure QR scanner output. Tap Retry to try again.",
        "QR scanning is unavailable on this device. Tap Retry or use another device.",
    ]

    for entry in required_entries:
        assert entry in contents, f"Scanner failure-path contract missing: {entry}"


def test_qr_pay_view_wires_scanner_failures_to_actionable_ui_controls():
    contents = read_text(QR_PAY_VIEW_PATH)

    required_entries = [
        "onScannerFailure: { failureMessage in",
        "viewModel.handleScannerFailure(failureMessage)",
        "message.localizedCaseInsensitiveContains(\"Camera access\")",
        "Button(\"Open Settings\")",
        "UIApplication.openSettingsURLString",
        "Button(\"Retry Scan\") { viewModel.reset() }",
    ]

    for entry in required_entries:
        assert entry in contents, f"QRPayView failure-action wiring contract missing: {entry}"
