import SwiftUI

// MARK: - MainTabView
// Root tab container wiring all four app tabs.

private enum MainTab: String, CaseIterable {
    case home
    case history
    case budget
    case settings

    var title: String {
        switch self {
        case .home:
            return "Home"
        case .history:
            return "History"
        case .budget:
            return "Budget"
        case .settings:
            return "Settings"
        }
    }

    var systemImage: String {
        switch self {
        case .home:
            return "house.fill"
        case .history:
            return "list.bullet"
        case .budget:
            return "chart.pie.fill"
        case .settings:
            return "gearshape.fill"
        }
    }
}

struct MainTabView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var selectedTab: MainTab = .home

    private var shellTabs: [StitchTabItem<MainTab>] {
        MainTab.allCases.map {
            StitchTabItem(id: $0, title: $0.title, systemImage: $0.systemImage)
        }
    }

    var body: some View {
        StitchTabShell(selection: $selectedTab, tabs: shellTabs) { tab in
            switch tab {
            case .home:
                HomeView()
            case .history:
                TransactionsView()
            case .budget:
                BudgetView()
            case .settings:
                SettingsView()
            }
        }
        .alert("Session Expired", isPresented: $authManager.showSessionExpiredAlert) {
            Button("Sign In") {
                authManager.clearAll()
            }
        } message: {
            Text("Your session has expired. Please sign in again.")
        }
    }
}
