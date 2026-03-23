import SwiftUI

// MARK: - ContentView
// Routes between LoginView and MainTabView based on auth state.

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var selectedAccentHex: String = AppTheme.defaultAccentHex

    var body: some View {
        Group {
            if authManager.isLoggedIn {
                MainTabView()
            } else {
                LoginView()
            }
        }
        .appThemeAccentHex(selectedAccentHex)
        .onAppear(perform: reloadPersistedAccent)
        .onReceive(NotificationCenter.default.publisher(for: .settingsAccentDidChange)) { notification in
            if let accentHex = notification.object as? String {
                selectedAccentHex = AppTheme.normalizedAccentHex(accentHex)
                return
            }

            reloadPersistedAccent()
        }
    }

    private func reloadPersistedAccent() {
        selectedAccentHex = AppTheme.normalizedAccentHex(
            KeychainHelper.read(forKey: "settings_accent_hex")
        )
    }
}
