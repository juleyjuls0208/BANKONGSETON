from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
BUDGET_VIEW_PATH = IOS_ROOT / "Views" / "Budget" / "BudgetView.swift"
RECEIPT_VIEW_PATH = IOS_ROOT / "Views" / "Receipt" / "ReceiptView.swift"
LOST_CARD_VIEW_PATH = IOS_ROOT / "Views" / "LostCard" / "LostCardView.swift"
HOME_VIEW_PATH = IOS_ROOT / "Views" / "Home" / "HomeView.swift"
TRANSACTIONS_VIEW_PATH = IOS_ROOT / "Views" / "Transactions" / "TransactionsView.swift"
SETTINGS_VIEW_PATH = IOS_ROOT / "Views" / "Settings" / "SettingsView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_s04_budget_receipt_lost_card_views_use_stitch_primitives_and_theme_tokens():
    budget_contents = read_text(BUDGET_VIEW_PATH)
    receipt_contents = read_text(RECEIPT_VIEW_PATH)
    lost_card_contents = read_text(LOST_CARD_VIEW_PATH)

    required_budget_entries = [
        "StitchCard",
        "StitchPrimaryButtonStyle",
        "AppTheme.Palette",
        "AppTheme.Spacing",
        "AppTheme.Typography",
    ]
    required_receipt_entries = [
        "StitchCard",
        "AppTheme.Palette",
        "AppTheme.Spacing",
        "AppTheme.Typography",
    ]
    required_lost_card_entries = [
        "StitchCard",
        "StitchPrimaryButtonStyle",
        "AppTheme.Palette",
        "AppTheme.Spacing",
        "AppTheme.Typography",
    ]

    for entry in required_budget_entries:
        assert entry in budget_contents, f"Budget stitch/theme contract missing: {entry}"

    for entry in required_receipt_entries:
        assert entry in receipt_contents, f"Receipt stitch/theme contract missing: {entry}"

    for entry in required_lost_card_entries:
        assert entry in lost_card_contents, f"Lost-card stitch/theme contract missing: {entry}"


def test_budget_view_has_explicit_state_cards_accessibility_markers_and_actionable_controls():
    contents = read_text(BUDGET_VIEW_PATH)

    required_entries = [
        "budget-state-loading-card",
        "budget-state-load-error-card",
        "budget-state-ready-card",
        "budget-state-save-error-card",
        "budget-state-save-success-card",
        "budget-save-button",
        "budget-retry-load-button",
        "budget-retry-save-button",
        "budget-refresh-button",
        "budget-limit-input-field",
        "await viewModel.load(apiClient: apiClient, authManager: authManager)",
        "await viewModel.retryLoad(apiClient: apiClient, authManager: authManager)",
        "await viewModel.setBudget(limit: parsedLimitInput, apiClient: apiClient, authManager: authManager)",
        "await viewModel.retryLastSave(apiClient: apiClient, authManager: authManager)",
        ".accessibilityHint(\"Retries loading your monthly limit and spending summary\")",
        ".accessibilityHint(\"Saves your updated monthly budget limit\")",
    ]

    for entry in required_entries:
        assert entry in contents, f"Budget explicit-state/action contract missing: {entry}"


def test_receipt_view_uses_stable_line_item_identity_and_scope_clean_surface():
    contents = read_text(RECEIPT_VIEW_PATH)

    required_entries = [
        "Array(lineItems.enumerated())",
        "ForEach(indexedLineItems, id: \\.index)",
        "receipt-line-item-row-\\(line.index)",
        "receipt-fallback-item-marker",
        "receipt-summary-card",
        "receipt-items-card",
        "Scope guard: no PDF/download/report utility actions belong to S04",
    ]

    forbidden_entries = [
        "ForEach(lineItems, id: \\.name)",
        "Download PDF",
        "Report Issue",
        "Report Receipt",
        "receipt-report-issue-button",
        "receipt-download-button",
    ]

    for entry in required_entries:
        assert entry in contents, f"Receipt rendering/scope contract missing: {entry}"

    for entry in forbidden_entries:
        assert entry not in contents, f"Receipt scope-clean contract violated by utility action marker: {entry}"


def test_lost_card_view_keeps_phase_bound_ctas_and_accessibility_markers():
    contents = read_text(LOST_CARD_VIEW_PATH)

    required_entries = [
        "switch viewModel.phase",
        "case .idle:",
        "case .loading:",
        "case .success:",
        "case .error:",
        "lost-card-state-idle",
        "lost-card-state-loading",
        "lost-card-state-success",
        "lost-card-state-error",
        "lost-card-report-button",
        "lost-card-retry-button",
        "lost-card-success-done-button",
        "lost-card-error-dismiss-button",
        "await viewModel.reportLostCard(apiClient: apiClient, authManager: authManager)",
        "await viewModel.retryReport(apiClient: apiClient, authManager: authManager)",
        "dismiss()",
        ".accessibilityHint(\"Reports this card as lost and blocks new transactions\")",
        ".accessibilityHint(\"Retries reporting your card as lost\")",
    ]

    for entry in required_entries:
        assert entry in contents, f"Lost-card phase/action/accessibility contract missing: {entry}"


def test_navigation_continuity_anchors_remain_for_home_transactions_and_settings_entrypoints():
    home_contents = read_text(HOME_VIEW_PATH)
    transactions_contents = read_text(TRANSACTIONS_VIEW_PATH)
    settings_contents = read_text(SETTINGS_VIEW_PATH)

    home_required = [
        ".navigationDestination(for: Transaction.self)",
        "ReceiptView(transaction: transaction)",
    ]
    transactions_required = [
        ".navigationDestination(for: Transaction.self)",
        "ReceiptView(transaction: transaction)",
    ]
    settings_required = [
        "NavigationLink(\"Report Lost Card\")",
        "LostCardView()",
    ]

    for entry in home_required:
        assert entry in home_contents, f"Home receipt continuity anchor missing: {entry}"

    for entry in transactions_required:
        assert entry in transactions_contents, f"Transactions receipt continuity anchor missing: {entry}"

    for entry in settings_required:
        assert entry in settings_contents, f"Settings lost-card continuity anchor missing: {entry}"
