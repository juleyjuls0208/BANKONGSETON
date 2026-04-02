import SwiftUI

@MainActor
final class SettingsViewModel: ObservableObject {
    private let themeModeKey = "theme_mode"

    let settingsAccentHexKey = "settings_accent_hex"
    private let defaultAccentHex = AppTheme.defaultAccentHex

    @Published var selectedTheme: String {
        didSet {
            let normalizedTheme = Self.normalizedThemeMode(selectedTheme)
            if normalizedTheme != selectedTheme {
                selectedTheme = normalizedTheme
                return
            }

            KeychainHelper.save(normalizedTheme, forKey: themeModeKey)
            NotificationCenter.default.post(name: .settingsThemeDidChange, object: normalizedTheme)
        }
    }

    @Published var selectedAccentHex: String {
        didSet {
            let normalizedAccentHex = AppTheme.normalizedAccentHex(selectedAccentHex)
            if normalizedAccentHex != selectedAccentHex {
                selectedAccentHex = normalizedAccentHex
                return
            }

            accentApplyState = .idle
        }
    }
    @Published private(set) var accentApplyState: SettingsPersistenceState = .idle
    @Published var isLoggingOut = false

    // Valid theme values: "light", "dark", "system"
    let themeOptions = ["system", "light", "dark"]

    enum SettingsPersistenceState: String {
        case idle
        case applying
        case saved
    }

    init() {
        selectedTheme = Self.normalizedThemeMode(
            KeychainHelper.read(forKey: themeModeKey, default: "system")
        )

        let persistedAccentHex = KeychainHelper.read(forKey: settingsAccentHexKey, default: defaultAccentHex)
        selectedAccentHex = AppTheme.normalizedAccentHex(persistedAccentHex)
    }

    var colorScheme: ColorScheme? {
        switch selectedTheme {
        case "light": return .light
        case "dark": return .dark
        default: return nil   // nil = follow system
        }
    }

    func applyAccent(_ accentHex: String) {
        accentApplyState = .applying

        let normalizedAccentHex = AppTheme.normalizedAccentHex(accentHex)
        selectedAccentHex = normalizedAccentHex
        KeychainHelper.save(normalizedAccentHex, forKey: settingsAccentHexKey)

        accentApplyState = .saved
        NotificationCenter.default.post(name: .settingsAccentDidChange, object: normalizedAccentHex)
    }

    func logout(_ action: () async -> Void) async {
        isLoggingOut = true
        await action()
        isLoggingOut = false
    }

    private static func normalizedThemeMode(_ candidate: String?) -> String {
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

extension Notification.Name {
    static let settingsThemeDidChange = Notification.Name("settings.theme.didChange")
    static let settingsAccentDidChange = Notification.Name("settings.accent.didChange")
}
