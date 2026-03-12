import SwiftUI

@MainActor
final class SettingsViewModel: ObservableObject {
    @Published var selectedTheme: String {
        didSet {
            KeychainHelper.save(selectedTheme, forKey: "theme_mode")
        }
    }

    @Published var isLoggingOut = false

    // Valid theme values: "light", "dark", "system"
    let themeOptions = ["system", "light", "dark"]

    init() {
        selectedTheme = KeychainHelper.read(forKey: "theme_mode") ?? "system"
    }

    var colorScheme: ColorScheme? {
        switch selectedTheme {
        case "light": return .light
        case "dark":  return .dark
        default:      return nil   // nil = follow system
        }
    }

    func logout(apiClient: APIClient, authManager: AuthManager) async {
        isLoggingOut = true
        await authManager.logout(apiClient: apiClient)
        isLoggingOut = false
    }
}
