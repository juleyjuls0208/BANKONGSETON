from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")

TRANSACTIONS_VIEW_PATH = IOS_ROOT / "Views" / "Transactions" / "TransactionsView.swift"
TRANSACTIONS_VM_PATH = IOS_ROOT / "ViewModels" / "TransactionsViewModel.swift"
SETTINGS_VIEW_PATH = IOS_ROOT / "Views" / "Settings" / "SettingsView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def assert_required_markers(path: Path, markers: list[str], contract_label: str) -> None:
    contents = read_text(path)
    for marker in markers:
        assert marker in contents, f"{contract_label} marker missing in {path}: {marker}"


def assert_forbidden_markers(path: Path, markers: list[str], contract_label: str) -> None:
    contents = read_text(path)
    found = [marker for marker in markers if marker in contents]
    assert not found, f"{contract_label}: found forbidden markers in {path}: {found}"


def test_transactions_is_filter_only_with_no_searchable_surface() -> None:
    """S04 core: search bar UI is gone; filter picker remains."""
    assert_forbidden_markers(
        TRANSACTIONS_VIEW_PATH,
        [
            ".searchable(",
            ".searchable(text:",
            '"transactions-clear-search-filter-button"',
            '"home-clear-search-filter-button"',
        ],
        "transactions_filter_only_no_search",
    )

    assert_required_markers(
        TRANSACTIONS_VIEW_PATH,
        [
            'Picker("Transaction Type", selection: $viewModel.selectedFilter)',
            'ForEach(TransactionFilter.allCases, id: \\.self)',
            '"transactions-filter-picker"',
            '"transactions-clear-filter-button"',
        ],
        "transactions_filter_only",
    )


def test_transactions_qr_continuity_seam_remains_intact_after_rollback() -> None:
    """R076: QR success continuity tick → refresh path is preserved."""
    assert_required_markers(
        TRANSACTIONS_VIEW_PATH,
        [
            '@AppStorage("qr_payment_success_continuity_tick") private var qrPaymentSuccessContinuityTick = 0',
            ".task(id: qrPaymentSuccessContinuityTick)",
            "await viewModel.refreshAfterQRSuccessContinuity(",
        ],
        "transactions_qr_continuity_tick_view",
    )

    assert_required_markers(
        TRANSACTIONS_VM_PATH,
        [
            "private var lastHandledQRSuccessContinuityTick = 0",
            "func refreshAfterQRSuccessContinuity(",
            "guard continuityTick > lastHandledQRSuccessContinuityTick else {",
        ],
        "transactions_qr_continuity_tick_vm",
    )


def test_transactions_receipt_and_load_more_remain_actionable() -> None:
    """R071 continuity: receipt navigation and load-more are intact."""
    assert_required_markers(
        TRANSACTIONS_VIEW_PATH,
        [
            '.navigationDestination(for: Transaction.self)',
            "ReceiptView(transaction: transaction)",
            '"transactions-load-more-button"',
        ],
        "transactions_receipt_and_load_more",
    )

    assert_required_markers(
        TRANSACTIONS_VM_PATH,
        [
            "func loadMore(apiClient: APIClient",
            "guard hasMore && !isLoading && !isLoadingMore else { return }",
        ],
        "transactions_load_more_vm",
    )


def test_settings_appearance_and_account_cards_render_without_personal_info_card() -> None:
    """R072 continuity: appearance+account cards remain; personalInfoCard is removed."""
    assert_required_markers(
        SETTINGS_VIEW_PATH,
        [
            "appearanceCard",
            "accountActionsCard",
            '"Report Lost Card"',
            '"Logout"',
        ],
        "settings_in_scope_cards",
    )

    assert_forbidden_markers(
        SETTINGS_VIEW_PATH,
        [
            "Personal Info",
            "personalInfoCard",
            '"settings-personal-info-status"',
        ],
        "settings_personal_info_removed",
    )
