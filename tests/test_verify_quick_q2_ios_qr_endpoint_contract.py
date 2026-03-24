from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
QR_VM_PATH = IOS_ROOT / "ViewModels" / "QRPayViewModel.swift"
API_CLIENT_PATH = IOS_ROOT / "Core" / "Network" / "APIClient.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_qr_view_model_tracks_and_reuses_scanned_endpoint_override():
    contents = read_text(QR_VM_PATH)

    required_entries = [
        "private var activeQRAPIBaseURLOverride: String?",
        "activeQRAPIBaseURLOverride = parsedPayload.apiBaseURLOverride",
        "apiBaseURLOverride: parsedPayload.apiBaseURLOverride",
        "let apiBaseURLOverride = activeQRAPIBaseURLOverride",
        "apiBaseURLOverride: apiBaseURLOverride",
        "activeQRAPIBaseURLOverride = nil",
    ]

    for entry in required_entries:
        assert entry in contents, f"QR endpoint-override behavior missing: {entry}"


def test_qr_view_model_derives_trusted_url_base_and_blocks_untrusted_hosts():
    contents = read_text(QR_VM_PATH)

    required_entries = [
        "extractTrustedAPIBaseURLOverride(from: payload, token: urlToken)",
        "isTrustedQRHost(host, scheme: scheme)",
        "Ignoring untrusted QR host=",
        "private func isPrivateIPv4Host(_ host: String) -> Bool",
        "return ParsedQRPayload(",
        "source: \"url_direct\"",
    ]

    for entry in required_entries:
        assert entry in contents, f"Trusted QR URL handling contract missing: {entry}"


def test_api_client_supports_qr_base_url_override_for_cart_and_confirm_calls():
    contents = read_text(API_CLIENT_PATH)

    required_entries = [
        "baseURLOverride: String? = nil",
        "buildURL(baseURL: targetBaseURL, path: path)",
        "func getQrCart(token: String, apiBaseURLOverride: String? = nil)",
        "func confirmQrPayment(token: String, apiBaseURLOverride: String? = nil)",
        "baseURLOverride: apiBaseURLOverride",
    ]

    for entry in required_entries:
        assert entry in contents, f"APIClient QR base-override contract missing: {entry}"
