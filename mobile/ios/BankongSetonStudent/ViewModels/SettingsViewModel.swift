import SwiftUI

@MainActor
final class SettingsViewModel: ObservableObject {
    private let themeModeKey = "theme_mode"
    private let studentNameKey = "student_name"

    let settingsAccentHexKey = "settings_accent_hex"
    let settingsDisplayNameKey = "settings_display_name"
    private let defaultAccentHex = AppTheme.defaultAccentHex

    @Published var selectedTheme: String {
        didSet {
            KeychainHelper.save(selectedTheme, forKey: themeModeKey)
        }
    }

    @Published var editableDisplayName: String
    @Published var selectedAccentHex: String
    @Published private(set) var personalInfoSaveState: SettingsPersistenceState = .idle
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
        selectedTheme = KeychainHelper.read(forKey: themeModeKey, default: "system")

        let persistedAccentHex = KeychainHelper.read(forKey: settingsAccentHexKey, default: defaultAccentHex)
        selectedAccentHex = AppTheme.normalizedAccentHex(persistedAccentHex)

        editableDisplayName = Self.loadPersistedDisplayName(
            settingsDisplayNameKey: settingsDisplayNameKey,
            studentNameKey: studentNameKey
        )
    }

    var colorScheme: ColorScheme? {
        switch selectedTheme {
        case "light": return .light
        case "dark": return .dark
        default: return nil   // nil = follow system
        }
    }

    func savePersonalInfo() {
        personalInfoSaveState = .applying

        editableDisplayName = editableDisplayName.trimmingCharacters(in: .whitespacesAndNewlines)
        KeychainHelper.save(editableDisplayName, forKey: settingsDisplayNameKey)

        personalInfoSaveState = .saved
        NotificationCenter.default.post(name: .settingsDisplayNameDidChange, object: nil)
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

    private static func loadPersistedDisplayName(
        settingsDisplayNameKey: String,
        studentNameKey: String
    ) -> String {
        if let persistedDisplayName = KeychainHelper.read(forKey: settingsDisplayNameKey) {
            return persistedDisplayName
        }

        return KeychainHelper.read(forKey: studentNameKey, default: "")
    }
}

extension Notification.Name {
    static let settingsAccentDidChange = Notification.Name("settings.accent.didChange")
    static let settingsDisplayNameDidChange = Notification.Name("settings.display-name.didChange")
}
