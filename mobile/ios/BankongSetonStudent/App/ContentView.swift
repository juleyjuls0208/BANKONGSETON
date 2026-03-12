import SwiftUI

// MARK: - ContentView
// Routes between LoginView and MainTabView based on auth state.

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager

    var body: some View {
        if authManager.isLoggedIn {
            MainTabView()
        } else {
            LoginView()
        }
    }
}
