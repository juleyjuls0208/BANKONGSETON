from pathlib import Path


IOS_ROOT = Path("mobile/ios/BankongSetonStudent")
SHELL_ROOT = IOS_ROOT / "UI" / "Shell"
VIEWS_ROOT = IOS_ROOT / "Views"
APP_ROOT = IOS_ROOT / "App"
PBXPROJ_PATH = IOS_ROOT / "BankongSetonStudent.xcodeproj" / "project.pbxproj"


def read_text(path: Path) -> str:
    assert path.exists(), f"Expected file does not exist: {path}"
    return path.read_text(encoding="utf-8")


def test_tab_shell_file_exists_and_is_project_registered():
    shell_file = SHELL_ROOT / "StitchTabShell.swift"
    assert shell_file.exists(), f"Missing shell file: {shell_file}"

    project_contents = read_text(PBXPROJ_PATH)
    required_entries = [
        "StitchTabShell.swift",
        "AA000035 /* StitchTabShell.swift in Sources */",
        "BB000035 /* StitchTabShell.swift */",
        "EE000021 /* Shell */",
    ]

    for entry in required_entries:
        assert entry in project_contents, f"Missing Xcode project shell entry: {entry}"


def test_tab_shell_uses_shared_theme_tokens_for_chrome():
    shell_contents = read_text(SHELL_ROOT / "StitchTabShell.swift")

    required_symbols = [
        "struct StitchTabShell",
        "struct StitchTabItem",
        "@Binding var selection",
        "AppTheme.Palette",
        "AppTheme.Spacing",
        "AppTheme.Radius",
        "AppTheme.Typography",
        ".accessibilityValue",
    ]

    for symbol in required_symbols:
        assert symbol in shell_contents, f"Missing tab shell token/state symbol: {symbol}"


def test_tab_shell_metadata_and_order_are_preserved_in_main_tab_view():
    main_tab_contents = read_text(VIEWS_ROOT / "MainTabView.swift")

    required_entries = [
        "enum MainTab",
        "case home",
        "case history",
        "case budget",
        "case settings",
        'return "Home"',
        'return "History"',
        'return "Budget"',
        'return "Settings"',
        'return "house.fill"',
        'return "list.bullet"',
        'return "chart.pie.fill"',
        'return "gearshape.fill"',
        "MainTab.allCases",
        "StitchTabShell(selection: $selectedTab, tabs: shellTabs)",
        "case .home:\n                HomeView()",
        "case .history:\n                TransactionsView()",
        "case .budget:\n                BudgetView()",
        "case .settings:\n                SettingsView()",
    ]

    for entry in required_entries:
        assert entry in main_tab_contents, f"MainTabView contract entry missing: {entry}"


def test_session_alert_wiring_is_unchanged_on_shell_path():
    main_tab_contents = read_text(VIEWS_ROOT / "MainTabView.swift")

    assert 'alert("Session Expired", isPresented: $authManager.showSessionExpiredAlert)' in main_tab_contents
    assert 'Button("Sign In")' in main_tab_contents
    assert "authManager.clearAll()" in main_tab_contents


def test_auth_gate_still_routes_between_login_and_main_shell():
    content_view_contents = read_text(APP_ROOT / "ContentView.swift")

    required_entries = [
        "if authManager.isLoggedIn",
        "MainTabView()",
        "LoginView()",
    ]

    for entry in required_entries:
        assert entry in content_view_contents, f"ContentView auth-gate entry missing: {entry}"
