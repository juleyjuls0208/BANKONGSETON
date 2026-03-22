from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
BUDGET_VM_PATH = IOS_ROOT / "ViewModels" / "BudgetViewModel.swift"
LOST_CARD_VM_PATH = IOS_ROOT / "ViewModels" / "LostCardViewModel.swift"
LOST_CARD_VIEW_PATH = IOS_ROOT / "Views" / "LostCard" / "LostCardView.swift"
AUTH_MANAGER_PATH = IOS_ROOT / "Core" / "Auth" / "AuthManager.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_budget_view_model_has_explicit_load_and_save_failure_channels_with_retry_hooks():
    contents = read_text(BUDGET_VM_PATH)

    required_entries = [
        "@Published private(set) var loadErrorMessage: String?",
        "@Published private(set) var saveErrorMessage: String?",
        "@Published private(set) var pendingRetryLimit: Double?",
        "var hasLoadFailureState: Bool",
        "var hasSaveFailureState: Bool",
        "func retryLoad(apiClient: APIClient, authManager: AuthManager) async",
        "func retryLastSave(apiClient: APIClient, authManager: AuthManager) async",
        "loadErrorMessage = loadFailureMessage(for: failedSegments)",
        "pendingRetryLimit = newLimit",
        "saveErrorMessage = message",
        "guard let pendingRetryLimit else { return }",
        "Pull to refresh or tap Retry",
        "Tap Retry Save",
    ]

    for entry in required_entries:
        assert entry in contents, f"Budget failure-channel contract marker missing: {entry}"

    assert "catch {}" not in contents, "Budget load/save must not silently swallow errors"


def test_budget_view_model_preserves_auth_boundary_handlers_on_unauthorized_and_card_lost():
    contents = read_text(BUDGET_VM_PATH)

    required_entries = [
        "catch APIError.unauthorized {",
        "authManager.handleUnauthorized()",
        "catch APIError.cardLost {",
        "authManager.handleCardLost()",
    ]

    for entry in required_entries:
        assert entry in contents, f"Budget auth-boundary marker missing: {entry}"


def test_lost_card_view_model_defines_idle_loading_success_error_state_machine():
    contents = read_text(LOST_CARD_VM_PATH)

    required_entries = [
        "enum LostCardFlowPhase: String",
        "case idle",
        "case loading",
        "case success",
        "case error",
        "@Published private(set) var phase: LostCardFlowPhase = .idle",
        "func reportLostCard(apiClient: APIClient, authManager: AuthManager) async",
        "transition(to: .loading, reason: \"report_started\")",
        "transition(to: .success, reason: \"report_success\")",
        "transitionToError(",
        "func retryReport(apiClient: APIClient, authManager: AuthManager) async",
        "func resetToIdle()",
        "LostCardFlowPhase transition",
    ]

    for entry in required_entries:
        assert entry in contents, f"Lost-card flow-phase contract marker missing: {entry}"


def test_lost_card_view_model_handles_auth_session_boundaries_for_unauthorized_and_card_lost():
    contents = read_text(LOST_CARD_VM_PATH)

    required_entries = [
        "catch APIError.unauthorized {",
        "reason: \"report_unauthorized\"",
        "authManager.handleUnauthorized()",
        "catch APIError.cardLost {",
        "reason: \"report_card_already_lost\"",
        "authManager.handleCardLost()",
        "KeychainHelper.save(\"true\", forKey: \"isCardLost\")",
    ]

    for entry in required_entries:
        assert entry in contents, f"Lost-card auth/session marker missing: {entry}"


def test_lost_card_view_wires_each_phase_to_real_user_actions_without_dead_controls():
    contents = read_text(LOST_CARD_VIEW_PATH)

    required_entries = [
        "@StateObject private var viewModel = LostCardViewModel()",
        "switch viewModel.phase",
        "case .idle:",
        "Button(\"Report Lost Card\")",
        "await viewModel.reportLostCard(apiClient: apiClient, authManager: authManager)",
        "case .loading:",
        "ProgressView()",
        "case .error:",
        "Button(\"Retry Report\")",
        "await viewModel.retryReport(apiClient: apiClient, authManager: authManager)",
        "case .success:",
        "Button(\"Back to Settings\")",
        "dismiss()",
    ]

    for entry in required_entries:
        assert entry in contents, f"Lost-card view action wiring contract marker missing: {entry}"


def test_auth_manager_retains_session_boundary_contracts_relied_on_by_budget_and_lost_card_flows():
    contents = read_text(AUTH_MANAGER_PATH)

    required_entries = [
        "func handleUnauthorized()",
        "showSessionExpiredAlert = true",
        "func handleCardLost()",
        "KeychainHelper.save(\"true\", forKey: \"isCardLost\")",
        "clearAll()",
    ]

    for entry in required_entries:
        assert entry in contents, f"Auth/session boundary contract marker missing: {entry}"
