from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
TRANSACTIONS_VM_PATH = IOS_ROOT / "ViewModels" / "TransactionsViewModel.swift"
TRANSACTION_MODELS_PATH = IOS_ROOT / "Models" / "TransactionModels.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_view_model_maintains_canonical_and_derived_transaction_lists():
    contents = read_text(TRANSACTIONS_VM_PATH)

    required_entries = [
        "@Published private(set) var allTransactions: [Transaction] = []",
        "@Published private(set) var transactions: [Transaction] = []",
        "@Published var searchQuery = \"\"",
        "@Published var selectedFilter: TransactionFilter = .all",
        "didSet { recomputeDisplayedTransactions() }",
        "private func recomputeDisplayedTransactions()",
        "transaction.matchesFilter(selectedFilter) && transaction.matchesSearchQuery(searchQuery)",
    ]

    for entry in required_entries:
        assert entry in contents, f"Canonical/derived transaction-state contract missing: {entry}"


def test_filter_and_search_semantics_are_centralized_in_transaction_models():
    contents = read_text(TRANSACTION_MODELS_PATH)

    required_entries = [
        "enum TransactionFilter: String, CaseIterable, Codable",
        "case all",
        "case debit",
        "case credit",
        "enum TransactionDirection: String, Codable",
        "private static let debitTypeSignals",
        "private static let creditTypeSignals",
        "var normalizedTypeValue: String",
        "var normalizedDirection: TransactionDirection",
        "func matchesFilter(_ filter: TransactionFilter) -> Bool",
        "func matchesSearchQuery(_ query: String) -> Bool",
    ]

    for entry in required_entries:
        assert entry in contents, f"Filter/type normalization contract missing: {entry}"


def test_view_model_splits_initial_and_pagination_failure_channels():
    contents = read_text(TRANSACTIONS_VM_PATH)

    required_entries = [
        "@Published private(set) var initialLoadErrorMessage: String?",
        "@Published private(set) var paginationErrorMessage: String?",
        "private enum FetchContext",
        "case initial",
        "case pagination",
        "switch context",
        "case .initial:",
        "initialLoadErrorMessage = \"Failed to load transactions.\"",
        "errorMessage = initialLoadErrorMessage",
        "case .pagination:",
        "paginationErrorMessage = \"Couldn’t load more transactions. Tap Load More to retry.\"",
    ]

    for entry in required_entries:
        assert entry in contents, f"Split initial/pagination error-channel contract missing: {entry}"


def test_has_more_continuity_uses_defensive_fallback_when_has_more_is_omitted():
    contents = read_text(TRANSACTIONS_VM_PATH)

    required_entries = [
        "private func resolveHasMore(response: TransactionsResponse, fetchedCount: Int) -> Bool",
        "if let explicitHasMore = response.hasMore",
        "if let total = response.total",
        "return fetchedCount == pageSize",
    ]

    for entry in required_entries:
        assert entry in contents, f"hasMore defensive fallback contract missing: {entry}"


def test_pagination_failure_is_non_blocking_for_preloaded_history_state():
    contents = read_text(TRANSACTIONS_VM_PATH)

    required_entries = [
        "var hasPaginationFailureState: Bool",
        "paginationErrorMessage != nil && !allTransactions.isEmpty",
        "paginationErrorMessage = nil",
        "guard hasMore && !isLoading && !isLoadingMore else { return }",
    ]

    for entry in required_entries:
        assert entry in contents, f"Non-blocking pagination-failure marker missing: {entry}"

    pagination_case_anchor = "case .pagination:\n                paginationErrorMessage = \"Couldn’t load more transactions. Tap Load More to retry.\""
    assert pagination_case_anchor in contents, "Pagination failure branch marker missing"

    forbidden_branch = "case .pagination:\n                errorMessage ="
    assert forbidden_branch not in contents, "Pagination failures must not route into global initial-load error channel"
