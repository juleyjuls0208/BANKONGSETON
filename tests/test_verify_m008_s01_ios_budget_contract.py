"""M008/S01 iOS budget contract markers for backend compatibility and retry UX."""

from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
API_ENDPOINTS_PATH = IOS_ROOT / "Core" / "Network" / "APIEndpoints.swift"
API_CLIENT_PATH = IOS_ROOT / "Core" / "Network" / "APIClient.swift"
BUDGET_VM_PATH = IOS_ROOT / "ViewModels" / "BudgetViewModel.swift"
BUDGET_VIEW_PATH = IOS_ROOT / "Views" / "Budget" / "BudgetView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_budget_endpoint_contract_constants_keep_student_budget_and_summary_paths_stable():
    contents = read_text(API_ENDPOINTS_PATH)

    required_entries = [
        'static let budget = "/student/budget"',
        'static let budgetSummary = "/budget-summary"',
    ]

    for entry in required_entries:
        assert entry in contents, f"Budget endpoint contract marker missing: {entry}"


def test_api_client_budget_calls_target_contract_endpoints_and_decode_monthly_spend_key():
    contents = read_text(API_CLIENT_PATH)

    required_entries = [
        "func getBudget() async throws -> BudgetResponse",
        "let req = try authenticatedRequest(path: APIEndpoints.budget)",
        "func fetchBudgetSummary() async throws -> BudgetSummaryResponse",
        "let req = try authenticatedRequest(path: APIEndpoints.budgetSummary)",
        "struct BudgetSummaryResponse: Decodable",
        'case spent = "monthly_spend"',
    ]

    for entry in required_entries:
        assert entry in contents, f"API client budget-summary contract marker missing: {entry}"


def test_budget_view_model_loads_limit_and_summary_segments_with_explicit_retryable_failure_channels():
    contents = read_text(BUDGET_VM_PATH)

    required_entries = [
        "async let budgetTask: BudgetResponse = apiClient.getBudget()",
        "async let summaryTask: BudgetSummaryResponse = apiClient.fetchBudgetSummary()",
        "failedSegments.append(.monthlyLimit)",
        "failedSegments.append(.monthlySpend)",
        "loadErrorMessage = loadFailureMessage(for: failedSegments)",
        "func retryLoad(apiClient: APIClient, authManager: AuthManager) async",
        "func retryLastSave(apiClient: APIClient, authManager: AuthManager) async",
    ]

    for entry in required_entries:
        assert entry in contents, f"Budget view-model contract marker missing: {entry}"


def test_budget_view_keeps_retry_controls_wired_to_view_model_recovery_actions():
    contents = read_text(BUDGET_VIEW_PATH)

    required_entries = [
        "budget-retry-load-button",
        "budget-retry-save-button",
        "await viewModel.retryLoad(apiClient: apiClient, authManager: authManager)",
        "await viewModel.retryLastSave(apiClient: apiClient, authManager: authManager)",
        '.accessibilityHint("Retries loading your monthly limit and spending summary")',
        '.accessibilityHint("Retries saving your latest monthly budget limit")',
    ]

    for entry in required_entries:
        assert entry in contents, f"Budget view retry wiring marker missing: {entry}"
