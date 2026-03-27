"""M008/S02 rollback contract markers for native iOS tab shell restoration."""

from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
MAIN_TAB_VIEW_PATH = IOS_ROOT / "Views" / "MainTabView.swift"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_main_tab_view_uses_native_tab_view_with_all_four_tab_items() -> None:
    contents = read_text(MAIN_TAB_VIEW_PATH)

    required_entries = [
        "TabView(selection: $selectedTab)",
        "Label(MainTab.home.title, systemImage: MainTab.home.systemImage)",
        "Label(MainTab.history.title, systemImage: MainTab.history.systemImage)",
        "Label(MainTab.budget.title, systemImage: MainTab.budget.systemImage)",
        "Label(MainTab.settings.title, systemImage: MainTab.settings.systemImage)",
        ".tag(MainTab.home)",
        ".tag(MainTab.history)",
        ".tag(MainTab.budget)",
        ".tag(MainTab.settings)",
    ]

    for entry in required_entries:
        assert entry in contents, f"main_tab_view_native_tabs: missing required marker: {entry}"


def test_main_tab_view_removes_stitch_shell_markers() -> None:
    contents = read_text(MAIN_TAB_VIEW_PATH)

    forbidden_entries = [
        "StitchTabShell(",
        "StitchTabItem<MainTab>",
        "private var shellTabs",
        "MainTab.allCases.map",
    ]

    found_forbidden = [entry for entry in forbidden_entries if entry in contents]
    assert not found_forbidden, (
        "main_tab_view_stitch_shell_drift: forbidden floating-shell markers are still present: "
        f"{found_forbidden}"
    )


def test_main_tab_view_preserves_session_expired_alert_behavior() -> None:
    contents = read_text(MAIN_TAB_VIEW_PATH)

    required_entries = [
        'alert("Session Expired", isPresented: $authManager.showSessionExpiredAlert)',
        'Button("Sign In")',
        "authManager.clearAll()",
        'Text("Your session has expired. Please sign in again.")',
    ]

    for entry in required_entries:
        assert entry in contents, f"main_tab_view_session_alert_contract: missing marker: {entry}"
