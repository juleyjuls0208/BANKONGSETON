import SwiftUI

// MARK: - ContentView
// Routes between LoginView and MainTabView based on auth state.

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var selectedAccentHex: String = AppTheme.defaultAccentHex
    @State private var selectedThemeMode: String = "system"

    private var resolvedColorScheme: ColorScheme? {
        switch selectedThemeMode {
        case "light":
            return .light
        case "dark":
            return .dark
        default:
            return nil
        }
    }

    var body: some View {
        Group {
            if authManager.isLoggedIn {
                MainTabView()
            } else {
                LoginView()
            }
        }
        .appThemeAccentHex(selectedAccentHex)
        .preferredColorScheme(resolvedColorScheme)
        .onAppear {
            reloadPersistedAccent()
            reloadPersistedThemeMode()
        }
        .onReceive(NotificationCenter.default.publisher(for: .settingsAccentDidChange)) { notification in
            if let accentHex = notification.object as? String {
                selectedAccentHex = AppTheme.normalizedAccentHex(accentHex)
                return
            }

            reloadPersistedAccent()
        }
        .onReceive(NotificationCenter.default.publisher(for: .settingsThemeDidChange)) { notification in
            if let themeMode = notification.object as? String {
                selectedThemeMode = normalizeThemeMode(themeMode)
                return
            }

            reloadPersistedThemeMode()
        }
    }

    private func reloadPersistedAccent() {
        selectedAccentHex = AppTheme.normalizedAccentHex(
            KeychainHelper.read(forKey: "settings_accent_hex")
        )
    }

    private func reloadPersistedThemeMode() {
        selectedThemeMode = normalizeThemeMode(
            KeychainHelper.read(forKey: "theme_mode", default: "system")
        )
    }

    private func normalizeThemeMode(_ candidate: String?) -> String {
        switch candidate?.lowercased() {
        case "light":
            return "light"
        case "dark":
            return "dark"
        default:
            return "system"
        }
    }
}
