from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")

QR_VIEW_PATH = IOS_ROOT / "Views" / "QR" / "QRPayView.swift"
QR_VM_PATH = IOS_ROOT / "ViewModels" / "QRPayViewModel.swift"

HOME_VIEW_PATH = IOS_ROOT / "Views" / "Home" / "HomeView.swift"
HOME_VM_PATH = IOS_ROOT / "ViewModels" / "HomeViewModel.swift"

TRANSACTIONS_VIEW_PATH = IOS_ROOT / "Views" / "Transactions" / "TransactionsView.swift"
TRANSACTIONS_VM_PATH = IOS_ROOT / "ViewModels" / "TransactionsViewModel.swift"

SETTINGS_VIEW_PATH = IOS_ROOT / "Views" / "Settings" / "SettingsView.swift"
LOST_CARD_VIEW_PATH = IOS_ROOT / "Views" / "LostCard" / "LostCardView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def assert_required_markers(path: Path, markers: list[str], contract_label: str) -> None:
    contents = read_text(path)
    for marker in markers:
        assert marker in contents, f"{contract_label} marker missing in {path}: {marker}"


def test_qr_success_handoff_remains_wired_from_home_sheet_to_refresh_path() -> None:
    assert_required_markers(
        HOME_VIEW_PATH,
        [
            '.sheet(isPresented: $showQrPay) {',
            'QRPayView {',
            'handleQRPaySuccessCompletion()',
            'await viewModel.refreshAfterQRSuccess(apiClient: apiClient, authManager: authManager)',
            '@State private var didConsumePresentedQRSuccess = false',
            '@AppStorage("qr_payment_success_continuity_tick") private var qrPaymentSuccessContinuityTick = 0',
            'guard !didConsumePresentedQRSuccess else {',
            'qrPaymentSuccessContinuityTick += 1',
            '.environmentObject(apiClient)',
            'showQrPay = true',
            '"home-qr-pay-button"',
        ],
        "home_qr_success_handoff",
    )

    assert_required_markers(
        QR_VIEW_PATH,
        [
            'private var onSuccess: (() -> Void)?',
            'init(onSuccess: (() -> Void)? = nil)',
            '@State private var hasTriggeredSuccessCompletion = false',
            'Button("Done") {',
            'completeSuccessFlow(trigger: "manual_done")',
            'DispatchQueue.main.asyncAfter(deadline: .now() + 3)',
            'completeSuccessFlow(trigger: "auto_dismiss")',
            'private func completeSuccessFlow(trigger: String)',
            'guard !hasTriggeredSuccessCompletion else {',
            'onSuccess?()',
        ],
        "qr_success_completion",
    )

    assert_required_markers(
        HOME_VM_PATH,
        [
            'func refreshAfterQRSuccess(apiClient: APIClient, authManager: AuthManager) async',
            'log("Refreshing Home data after QR payment success dismiss")',
            'await load(apiClient: apiClient, authManager: authManager)',
            'log("Completed Home refresh after QR payment success dismiss")',
        ],
        "home_refresh_after_qr",
    )


def test_qr_state_machine_and_logs_keep_integration_observability_visible() -> None:
    assert_required_markers(
        QR_VM_PATH,
        [
            'enum QRPayState',
            'case scanning',
            'case loading',
            'case confirming(cart: QrCartResponse, token: String)',
            'case success(newBalance: Double?)',
            'case error(String)',
            'private func transition(to newState: QRPayState, reason: String)',
            'log("QRPayState transition',
            'log("Accepted QR payload source=',
            'redact(parsedPayload.token)',
            'private func redact(_ token: String) -> String',
            'print("[QRPayViewModel] \\(message)")',
        ],
        "qr_observability",
    )


def test_home_and_transactions_keep_receipt_access_paths_after_final_assembly() -> None:
    assert_required_markers(
        HOME_VIEW_PATH,
        [
            '.navigationDestination(for: Transaction.self)',
            'ReceiptView(transaction: transaction)',
        ],
        "home_receipt_access",
    )

    assert_required_markers(
        TRANSACTIONS_VIEW_PATH,
        [
            '.navigationDestination(for: Transaction.self)',
            'ReceiptView(transaction: transaction)',
        ],
        "transactions_receipt_access",
    )


def test_transactions_search_filter_load_more_continuity_markers_remain_intact() -> None:
    assert_required_markers(
        TRANSACTIONS_VIEW_PATH,
        [
            '.searchable(',
            'text: $viewModel.searchQuery',
            'Picker("Transaction Type", selection: $viewModel.selectedFilter)',
            '@AppStorage("qr_payment_success_continuity_tick") private var qrPaymentSuccessContinuityTick = 0',
            '.task(id: qrPaymentSuccessContinuityTick)',
            'await viewModel.refreshAfterQRSuccessContinuity(',
            'private var transactionStateKey: String',
            'private var stateCardTransition: AnyTransition',
            '.animation(screenTransitionAnimation, value: transactionStateKey)',
            '"transactions-clear-search-filter-button"',
            '"transactions-retry-initial-button"',
            '"transactions-retry-pagination-button"',
            '"transactions-load-more-button"',
            'viewModel.clearSearchAndFilter()',
        ],
        "transactions_view_continuity",
    )

    assert_required_markers(
        TRANSACTIONS_VM_PATH,
        [
            '@Published private(set) var allTransactions: [Transaction] = []',
            '@Published private(set) var transactions: [Transaction] = []',
            '@Published var searchQuery = ""',
            'didSet { recomputeDisplayedTransactions() }',
            '@Published private(set) var initialLoadErrorMessage: String?',
            '@Published private(set) var paginationErrorMessage: String?',
            'private var lastHandledQRSuccessContinuityTick = 0',
            'private enum FetchContext',
            'case initial',
            'case pagination',
            'func refreshAfterQRSuccessContinuity(',
            'guard continuityTick > 0 else { return }',
            'guard continuityTick > lastHandledQRSuccessContinuityTick else {',
            'log("Refreshing Transactions data after QR payment success continuity tick=',
            'var hasPaginationFailureState: Bool',
            'paginationErrorMessage != nil && !allTransactions.isEmpty',
            'guard hasMore && !isLoading && !isLoadingMore else { return }',
            'private func resolveHasMore(response: TransactionsResponse, fetchedCount: Int) -> Bool',
            'return fetchedCount == pageSize',
            'print("[TransactionsViewModel] \\(message)")',
        ],
        "transactions_vm_continuity",
    )


def test_settings_and_lost_card_actionability_seams_remain_in_scope_and_live() -> None:
    assert_required_markers(
        SETTINGS_VIEW_PATH,
        [
            'NavigationLink("Report Lost Card")',
            'LostCardView()',
            '"settings-report-lost-card-link"',
            '"settings-logout-button"',
            'await viewModel.logout {',
            'await authManager.logout(apiClient: apiClient)',
        ],
        "settings_actionability",
    )

    assert_required_markers(
        LOST_CARD_VIEW_PATH,
        [
            'switch viewModel.phase',
            '"lost-card-report-button"',
            '"lost-card-retry-button"',
            '"lost-card-success-done-button"',
            '"lost-card-error-dismiss-button"',
        ],
        "lost_card_actionability",
    )
