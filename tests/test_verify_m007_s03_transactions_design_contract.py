from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
TRANSACTIONS_VIEW_PATH = IOS_ROOT / "Views" / "Transactions" / "TransactionsView.swift"
TRANSACTION_ROW_PATH = IOS_ROOT / "Views" / "Transactions" / "TransactionRowView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_transactions_view_has_search_and_type_filter_controls_wired_to_view_model_state():
    contents = read_text(TRANSACTIONS_VIEW_PATH)

    required_entries = [
        ".searchable(",
        "text: $viewModel.searchQuery",
        "prompt: \"Search by type, date, or amount\"",
        "Picker(\"Transaction Type\", selection: $viewModel.selectedFilter)",
        "ForEach(TransactionFilter.allCases, id: \\.self)",
        "viewModel.clearSearchAndFilter()",
        "transactions-filter-picker",
        "transactions-clear-search-filter-button",
    ]

    for entry in required_entries:
        assert entry in contents, f"Search/filter wiring contract missing: {entry}"


def test_transactions_view_renders_explicit_state_surfaces_for_loading_empty_errors_and_filtered_empty():
    contents = read_text(TRANSACTIONS_VIEW_PATH)

    required_entries = [
        "viewModel.isLoading && viewModel.allTransactions.isEmpty",
        "viewModel.initialLoadErrorMessage",
        "viewModel.isBaseEmptyState",
        "viewModel.isFilteredEmptyState",
        "viewModel.hasPaginationFailureState",
        "viewModel.paginationErrorMessage",
        "Loading transactions…",
        "Couldn’t Load Transactions",
        "No transactions yet",
        "No matching transactions",
        "Couldn’t load more transactions.",
        "transactions-state-loading",
        "transactions-state-initial-error",
        "transactions-state-base-empty",
        "transactions-state-filtered-empty",
        "transactions-state-pagination-error",
    ]

    for entry in required_entries:
        assert entry in contents, f"Transactions explicit-state surface contract missing: {entry}"


def test_transactions_populated_state_keeps_row_navigation_and_load_more_continuity():
    contents = read_text(TRANSACTIONS_VIEW_PATH)

    required_entries = [
        "ForEach(viewModel.transactions)",
        "if transaction.isNavigable",
        "NavigationLink(value: transaction)",
        "ReceiptView(transaction: transaction)",
        "if viewModel.hasMore",
        "await viewModel.loadMore(apiClient: apiClient, authManager: authManager)",
        "Label(\"Load More\", systemImage: \"arrow.down.circle\")",
        "transactions-load-more-button",
    ]

    for entry in required_entries:
        assert entry in contents, f"Populated-state continuity contract missing: {entry}"


def test_transactions_ctas_are_actionable_and_non_decorative():
    contents = read_text(TRANSACTIONS_VIEW_PATH)

    required_entries = [
        "Label(\"Retry\", systemImage: \"arrow.clockwise\")",
        "Label(\"Retry Load More\", systemImage: \"arrow.clockwise\")",
        "Label(\"Refresh Transactions\", systemImage: \"arrow.clockwise\")",
        "Label(\"Clear Search & Filter\", systemImage: \"xmark.circle\")",
        "await viewModel.loadInitial(apiClient: apiClient, authManager: authManager)",
        "await viewModel.loadMore(apiClient: apiClient, authManager: authManager)",
        "viewModel.clearSearchAndFilter()",
        "transactions-retry-initial-button",
        "transactions-retry-pagination-button",
        "transactions-refresh-empty-button",
        "transactions-clear-no-match-button",
    ]

    for entry in required_entries:
        assert entry in contents, f"Actionable CTA contract missing: {entry}"


def test_transactions_view_uses_stitch_primitives_and_theme_tokens():
    contents = read_text(TRANSACTIONS_VIEW_PATH)

    required_entries = [
        "StitchCard",
        "StitchPrimaryButtonStyle",
        "AppTheme.Palette",
        "AppTheme.Spacing",
        "AppTheme.Typography",
    ]

    for entry in required_entries:
        assert entry in contents, f"Stitch primitive/theme usage contract missing: {entry}"

    assert contents.count("StitchCard") >= 6, "Expected dedicated stitch card surfaces for filters and transaction states"


def test_transaction_row_uses_shared_direction_semantics_for_visual_continuity():
    contents = read_text(TRANSACTION_ROW_PATH)

    required_entries = [
        "transaction.isDebitLike",
        "transaction.normalizedTypeValue",
        "transaction.isNavigable",
        "StitchCard",
        "accessibilityLabel",
        "accessibilityHint",
    ]

    for entry in required_entries:
        assert entry in contents, f"Transaction row continuity/accessibility contract missing: {entry}"
