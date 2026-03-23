from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
APP_BOOTSTRAP_PATH = IOS_ROOT / "App" / "BankongSetonStudentApp.swift"
LOGIN_VIEW_PATH = IOS_ROOT / "Views" / "Auth" / "LoginView.swift"
LOGIN_VIEW_MODEL_PATH = IOS_ROOT / "ViewModels" / "LoginViewModel.swift"
LOGIN_MODELS_PATH = IOS_ROOT / "Models" / "LoginModels.swift"
API_CLIENT_PATH = IOS_ROOT / "Core" / "Network" / "APIClient.swift"
TRANSACTIONS_VIEW_PATH = IOS_ROOT / "Views" / "Transactions" / "TransactionsView.swift"
TRANSACTION_MODELS_PATH = IOS_ROOT / "Models" / "TransactionModels.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_dark_mode_default_contract_is_present_at_app_bootstrap() -> None:
    contents = read_text(APP_BOOTSTRAP_PATH)

    has_dark_marker = ".preferredColorScheme(.dark)" in contents or "UIUserInterfaceStyle" in contents
    assert has_dark_marker, "dark_mode_default: app bootstrap is missing the dark-mode startup marker"


def test_login_view_removes_pin_surface_and_keeps_stitch_primitives() -> None:
    contents = read_text(LOGIN_VIEW_PATH)

    forbidden_entries = [
        "PIN",
        "login-pin-field",
        "viewModel.pin",
        'SecureField("PIN"',
    ]
    found_forbidden = [entry for entry in forbidden_entries if entry in contents]
    assert not found_forbidden, f"login_pin_present: forbidden login markers found: {found_forbidden}"

    required_entries = [
        'TextField("Student ID", text: $viewModel.studentId)',
        "StitchCard",
        "StitchPrimaryButtonStyle",
        'accessibilityIdentifier("login-student-id-field")',
    ]
    missing_required = [entry for entry in required_entries if entry not in contents]
    assert not missing_required, f"stitch_drift: login surface missing expected stitch markers: {missing_required}"


def test_login_state_and_payload_are_student_id_only() -> None:
    view_model = read_text(LOGIN_VIEW_MODEL_PATH)
    login_models = read_text(LOGIN_MODELS_PATH)
    api_client = read_text(API_CLIENT_PATH)

    vm_forbidden = [
        "@Published var pin",
        "pin.count",
        "pin:",
    ]
    vm_found = [entry for entry in vm_forbidden if entry in view_model]
    assert not vm_found, f"login_pin_present: login view-model still contains pin state markers: {vm_found}"

    assert "func login(studentId: String) async throws -> LoginResponse" in api_client, (
        "stitch_drift: API login signature must accept studentId-only credentials"
    )
    assert "LoginRequest(studentId: studentId)" in api_client, (
        "stitch_drift: API login request must encode only student ID"
    )
    assert "let pin: String" not in login_models, (
        "login_pin_present: LoginRequest model must not declare a pin field"
    )


def test_transactions_view_uses_override_filter_taxonomy_and_removes_legacy_labels() -> None:
    contents = read_text(TRANSACTIONS_VIEW_PATH)

    required_entries = [
        'return "QR Pay"',
        'return "Card Pay"',
        'return "Load"',
        "case .qrPay:",
        "case .cardPay:",
        "case .load:",
    ]
    missing_required = [entry for entry in required_entries if entry not in contents]
    assert not missing_required, f"tx_filter_taxonomy: missing override filter markers: {missing_required}"

    forbidden_entries = [
        'return "Debit"',
        'return "Credit Card"',
        "case .debit:",
        "case .credit:",
    ]
    found_forbidden = [entry for entry in forbidden_entries if entry in contents]
    assert not found_forbidden, f"legacy_filter_label: legacy filter labels still present: {found_forbidden}"


def test_transaction_filter_model_maps_to_override_categories() -> None:
    contents = read_text(TRANSACTION_MODELS_PATH)

    required_entries = [
        "enum TransactionFilter: String, CaseIterable, Codable",
        'case qrPay = "qr_pay"',
        'case cardPay = "card_pay"',
        "case load",
        "var normalizedFilterCategory: TransactionFilter",
        "case .qrPay, .cardPay, .load:",
    ]
    missing_required = [entry for entry in required_entries if entry not in contents]
    assert not missing_required, f"tx_filter_taxonomy: model taxonomy/mapping markers missing: {missing_required}"

    legacy_switch_markers = [
        "case .debit:\n            return isDebitLike",
        "case .credit:\n            return isCreditLike",
    ]
    found_legacy_switch = [entry for entry in legacy_switch_markers if entry in contents]
    assert not found_legacy_switch, (
        "legacy_filter_label: Transaction filter switch still routes to deprecated debit/credit taxonomy"
    )
