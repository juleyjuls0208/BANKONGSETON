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

    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView()
                .tabItem {
                    Label(MainTab.home.title, systemImage: MainTab.home.systemImage)
                }
                .tag(MainTab.home)

            TransactionsView()
                .tabItem {
                    Label(MainTab.history.title, systemImage: MainTab.history.systemImage)
                }
                .tag(MainTab.history)

            BudgetView()
                .tabItem {
                    Label(MainTab.budget.title, systemImage: MainTab.budget.systemImage)
                }
                .tag(MainTab.budget)

            SettingsView()
                .tabItem {
                    Label(MainTab.settings.title, systemImage: MainTab.settings.systemImage)
                }
                .tag(MainTab.settings)
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
