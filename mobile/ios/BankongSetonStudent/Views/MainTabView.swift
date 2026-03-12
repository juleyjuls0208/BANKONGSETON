import SwiftUI

// MARK: - MainTabView
// Root tab container wiring all four app tabs.

struct MainTabView: View {
    @EnvironmentObject var authManager: AuthManager

    var body: some View {
        TabView {
            HomeView()
                .tabItem {
                    Label("Home", systemImage: "house.fill")
                }

            TransactionsView()
                .tabItem {
                    Label("History", systemImage: "list.bullet")
                }

            BudgetView()
                .tabItem {
                    Label("Budget", systemImage: "chart.pie.fill")
                }

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape.fill")
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
