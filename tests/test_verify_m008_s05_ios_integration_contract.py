"""M008/S05 integration contract — chained S01-S04 verifiers + cross-slice coherence checks."""

from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")

MAIN_TAB_VIEW_PATH = IOS_ROOT / "Views" / "MainTabView.swift"
HOME_VIEW_PATH = IOS_ROOT / "Views" / "Home" / "HomeView.swift"
TRANSACTIONS_VIEW_PATH = IOS_ROOT / "Views" / "Transactions" / "TransactionsView.swift"
SETTINGS_VIEW_PATH = IOS_ROOT / "Views" / "Settings" / "SettingsView.swift"
BUDGET_VIEW_PATH = IOS_ROOT / "Views" / "Budget" / "BudgetView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def assert_required_markers(path: Path, contents: str, markers: list[str], contract: str) -> None:
    for marker in markers:
        assert marker in contents, f"{contract}: missing required marker in {path.name}: {marker}"


def assert_forbidden_markers(path: Path, contents: str, markers: list[str], contract: str) -> None:
    found = [marker for marker in markers if marker in contents]
    assert not found, f"{contract}: found forbidden markers in {path.name}: {found}"


# ---------------------------------------------------------------------------
# 1. MainTabView — native TabView with four Label tab items (from S02)
# ---------------------------------------------------------------------------

def test_main_tab_view_uses_native_tab_view_with_all_four_tab_items() -> None:
    """S02 source: MainTabView uses native SwiftUI TabView with four Label tab items."""
    contents = read_text(MAIN_TAB_VIEW_PATH)

    assert_required_markers(
        MAIN_TAB_VIEW_PATH,
        contents,
        [
            "TabView(selection: $selectedTab)",
            "Label(MainTab.home.title, systemImage: MainTab.home.systemImage)",
            "Label(MainTab.history.title, systemImage: MainTab.history.systemImage)",
            "Label(MainTab.budget.title, systemImage: MainTab.budget.systemImage)",
            "Label(MainTab.settings.title, systemImage: MainTab.settings.systemImage)",
            ".tag(MainTab.home)",
            ".tag(MainTab.history)",
            ".tag(MainTab.budget)",
            ".tag(MainTab.settings)",
        ],
        "integration_maintab_native_tabs",
    )


def test_main_tab_view_preserves_session_expired_alert() -> None:
    """S02 source: session-expired alert behaviour is preserved."""
    contents = read_text(MAIN_TAB_VIEW_PATH)

    assert_required_markers(
        MAIN_TAB_VIEW_PATH,
        contents,
        [
            'alert("Session Expired", isPresented: $authManager.showSessionExpiredAlert)',
            'Button("Sign In")',
            "authManager.clearAll()",
            'Text("Your session has expired. Please sign in again.")',
        ],
        "integration_maintab_session_alert",
    )


# ---------------------------------------------------------------------------
# 2. HomeView — QR entry CTA + credit-card balance hero (from S03)
# ---------------------------------------------------------------------------

def test_home_contains_qr_entry_cta() -> None:
    """S03 source: QR pay button is present with correct identifier."""
    contents = read_text(HOME_VIEW_PATH)

    assert_required_markers(
        HOME_VIEW_PATH,
        contents,
        [
            '.sheet(isPresented: $showQrPay)',
            "QRPayView {",
            'Button {',
            "showQrPay = true",
            '.accessibilityIdentifier("home-qr-pay-button")',
        ],
        "integration_home_qr_cta",
    )


def test_home_contains_credit_card_balance_presentation() -> None:
    """S03 source: credit-card hero with balance is present."""
    contents = read_text(HOME_VIEW_PATH)

    assert_required_markers(
        HOME_VIEW_PATH,
        contents,
        [
            "private var creditCardHero: some View",
            'Text("Current Balance")',
            'Text("₱\\(String(format: "%.2f", viewModel.balance))")',
            "RoundedRectangle(cornerRadius: 22, style: .continuous)",
            "LinearGradient(",
            '.accessibilityIdentifier("home-credit-card-hero")',
        ],
        "integration_home_credit_card_hero",
    )


def test_home_removes_m007_heavy_transition_scaffolding() -> None:
    """S03 source: heavy M007 transition scaffolding is gone."""
    contents = read_text(HOME_VIEW_PATH)

    assert_forbidden_markers(
        HOME_VIEW_PATH,
        contents,
        [
            "private var screenTransitionAnimation: Animation",
            "private var stateTransition: AnyTransition",
            "private var errorBannerStateKey",
            "private var recentTransactionStateKey",
            ".animation(screenTransitionAnimation, value: errorBannerStateKey)",
            ".animation(screenTransitionAnimation, value: recentTransactionStateKey)",
            ".id(recentTransactionStateKey)",
        ],
        "integration_home_heavy_scaffolding_removed",
    )


def test_home_qr_continuity_seam_preserved() -> None:
    """S03 source: QR post-success continuity tick is wired."""
    contents = read_text(HOME_VIEW_PATH)

    assert_required_markers(
        HOME_VIEW_PATH,
        contents,
        [
            'handleQRPaySuccessCompletion()',
            "@State private var didConsumePresentedQRSuccess = false",
            '@AppStorage("qr_payment_success_continuity_tick") private var qrPaymentSuccessContinuityTick = 0',
            "guard !didConsumePresentedQRSuccess else",
            "qrPaymentSuccessContinuityTick += 1",
            "await viewModel.refreshAfterQRSuccess(",
        ],
        "integration_home_qr_continuity",
    )


# ---------------------------------------------------------------------------
# 3. TransactionsView — filter-only chips, QR Pay/Card Pay/Load taxonomy
#                        no search bar (from S04)
# ---------------------------------------------------------------------------

def test_transactions_has_filter_only_picker_no_search_bar() -> None:
    """S04 source: filter picker is present; searchable surface is absent."""
    contents = read_text(TRANSACTIONS_VIEW_PATH)

    assert_forbidden_markers(
        TRANSACTIONS_VIEW_PATH,
        contents,
        [
            ".searchable(",
            ".searchable(text:",
            '"transactions-clear-search-filter-button"',
            '"home-clear-search-filter-button"',
        ],
        "integration_transactions_no_search",
    )

    assert_required_markers(
        TRANSACTIONS_VIEW_PATH,
        contents,
        [
            'Picker("Transaction Type", selection: $viewModel.selectedFilter)',
            "ForEach(TransactionFilter.allCases, id: \\.self)",
            '"transactions-filter-picker"',
            '"transactions-clear-filter-button"',
        ],
        "integration_transactions_filter_only",
    )


def test_transactions_uses_qr_pay_card_pay_load_taxonomy() -> None:
    """S04 source: filter titles use QR Pay / Card Pay / Load taxonomy."""
    contents = read_text(TRANSACTIONS_VIEW_PATH)

    assert_required_markers(
        TRANSACTIONS_VIEW_PATH,
        contents,
        [
            "case .qrPay:",
            'return "QR Pay"',
            "case .cardPay:",
            'return "Card Pay"',
            "case .load:",
            'return "Load"',
            "filterTitle(for:",
        ],
        "integration_transactions_taxonomy",
    )


def test_transactions_qr_continuity_seam_intact() -> None:
    """S04 source: QR continuity tick → refresh path is preserved."""
    contents = read_text(TRANSACTIONS_VIEW_PATH)

    assert_required_markers(
        TRANSACTIONS_VIEW_PATH,
        contents,
        [
            '@AppStorage("qr_payment_success_continuity_tick") private var qrPaymentSuccessContinuityTick = 0',
            ".task(id: qrPaymentSuccessContinuityTick)",
            "await viewModel.refreshAfterQRSuccessContinuity(",
        ],
        "integration_transactions_qr_continuity",
    )


def test_transactions_receipt_and_load_more_intact() -> None:
    """S04 source: receipt navigation and load-more remain actionable."""
    assert_required_markers(
        TRANSACTIONS_VIEW_PATH,
        read_text(TRANSACTIONS_VIEW_PATH),
        [
            '.navigationDestination(for: Transaction.self)',
            "ReceiptView(transaction: transaction)",
            '"transactions-load-more-button"',
        ],
        "integration_transactions_receipt_and_load_more",
    )


# ---------------------------------------------------------------------------
# 4. BudgetView — references budget endpoints (from S01)
# ---------------------------------------------------------------------------

def test_budget_view_references_budget_endpoints() -> None:
    """S01 source: BudgetView calls budget load / set through its ViewModel."""
    contents = read_text(BUDGET_VIEW_PATH)

    assert_required_markers(
        BUDGET_VIEW_PATH,
        contents,
        [
            "@StateObject private var viewModel = BudgetViewModel()",
            "await viewModel.load(apiClient: apiClient, authManager: authManager)",
            "await viewModel.setBudget(",
            ".accessibilityIdentifier(\"budget-screen-root\")",
            ".accessibilityIdentifier(\"budget-card-progress\")",
            ".accessibilityIdentifier(\"budget-limit-input-field\")",
            ".accessibilityIdentifier(\"budget-save-button\")",
        ],
        "integration_budget_endpoints",
    )


def test_budget_progress_and_limit_editor_present() -> None:
    """S01 source: progress card and limit editor are present."""
    contents = read_text(BUDGET_VIEW_PATH)

    assert_required_markers(
        BUDGET_VIEW_PATH,
        contents,
        [
            "private var progressCard: some View",
            "private var limitEditorCard: some View",
            '.alert("Budget Alert", isPresented: $viewModel.showAlert)',
        ],
        "integration_budget_ui_surfaces",
    )


# ---------------------------------------------------------------------------
# 5. SettingsView — theme + accent controls only, no personal info card
#                    (from S04)
# ---------------------------------------------------------------------------

def test_settings_has_appearance_and_account_cards() -> None:
    """S04 source: appearance card (theme+accent) and account actions card are present."""
    contents = read_text(SETTINGS_VIEW_PATH)

    assert_required_markers(
        SETTINGS_VIEW_PATH,
        contents,
        [
            "private var appearanceCard: some View",
            "private var accountActionsCard: some View",
            '.accessibilityIdentifier("settings-theme-picker")',
            '.accessibilityIdentifier("settings-apply-accent-button")',
            '.accessibilityIdentifier("settings-accent-status")',
            '"Report Lost Card"',
            '"Logout"',
        ],
        "integration_settings_appearance_and_account",
    )


def test_settings_removes_personal_info_card() -> None:
    """S04 source: personalInfoCard is absent."""
    contents = read_text(SETTINGS_VIEW_PATH)

    assert_forbidden_markers(
        SETTINGS_VIEW_PATH,
        contents,
        [
            "Personal Info",
            "personalInfoCard",
            '"settings-personal-info-status"',
        ],
        "integration_settings_no_personal_info",
    )


# ---------------------------------------------------------------------------
# 6. Forbidden markers — no StitchTabShell, no fullscreen-stitch elements
# ---------------------------------------------------------------------------

def test_no_stitch_tab_shell_in_main_tab() -> None:
    """Cross-slice regression: StitchTabShell must not be reintroduced."""
    contents = read_text(MAIN_TAB_VIEW_PATH)

    assert_forbidden_markers(
        MAIN_TAB_VIEW_PATH,
        contents,
        [
            "StitchTabShell(",
            "StitchTabItem<MainTab>",
            "private var shellTabs",
            "MainTab.allCases.map",
        ],
        "integration_no_stitch_tab_shell",
    )


def test_no_search_bar_in_transactions() -> None:
    """Cross-slice regression: searchable must not be reintroduced to Transactions."""
    contents = read_text(TRANSACTIONS_VIEW_PATH)

    assert_forbidden_markers(
        TRANSACTIONS_VIEW_PATH,
        contents,
        [
            ".searchable(",
            ".searchable(text:",
        ],
        "integration_no_searchable_transactions",
    )


def test_no_fullscreen_stitch_elements_in_home() -> None:
    """Cross-slice regression: fullscreen-stitch transition scaffolding absent in Home."""
    contents = read_text(HOME_VIEW_PATH)

    assert_forbidden_markers(
        HOME_VIEW_PATH,
        contents,
        [
            "private var screenTransitionAnimation: Animation",
            "private var stateTransition: AnyTransition",
            "private var errorBannerStateKey",
            "private var recentTransactionStateKey",
            ".animation(screenTransitionAnimation, value: errorBannerStateKey)",
            ".animation(screenTransitionAnimation, value: recentTransactionStateKey)",
            ".id(recentTransactionStateKey)",
        ],
        "integration_no_fullscreen_stitch_home",
    )
