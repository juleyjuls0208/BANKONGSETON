import SwiftUI

/// Centralized design tokens for stitch-faithful styling across the app.
enum AppTheme {
    static let defaultAccentHex = "#2D9CDB"

    private static let accentPairsByHex: [String: (primary: String, secondary: String)] = [
        "#2D9CDB": ("#2D9CDB", "#1E88E5"),
        "#1565C0": ("#1565C0", "#1E88E5"),
        "#4F46E5": ("#4F46E5", "#4338CA"),
        "#0F766E": ("#0F766E", "#0D9488"),
        "#B45309": ("#B45309", "#C2410C")
    ]

    static func normalizedAccentHex(_ persistedAccentHex: String?) -> String {
        let normalized = persistedAccentHex?
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .uppercased()

        guard let normalized, accentPairsByHex[normalized] != nil else {
            return defaultAccentHex
        }

        return normalized
    }

    static func accentColor(for persistedAccentHex: String?) -> Color {
        let normalized = normalizedAccentHex(persistedAccentHex)
        let resolved = accentPairsByHex[normalized] ?? accentPairsByHex[defaultAccentHex]!
        return Color(hex: resolved.primary)
    }

    static func accentSecondaryColor(for persistedAccentHex: String?) -> Color {
        let normalized = normalizedAccentHex(persistedAccentHex)
        let resolved = accentPairsByHex[normalized] ?? accentPairsByHex[defaultAccentHex]!
        return Color(hex: resolved.secondary)
    }

    enum Palette {
        static let background = Color(hex: "#F4F7FB")
        static let surface = Color.white
        static let surfaceSubtle = Color(hex: "#EEF3FB")

        static let brandPrimary = Color(hex: "#1565C0")
        static let brandSecondary = Color(hex: "#1E88E5")
        static let accent = Color(hex: "#2D9CDB")

        static let textPrimary = Color(hex: "#0F172A")
        static let textSecondary = Color(hex: "#64748B")
        static let textInverse = Color.white

        static let success = Color(hex: "#22C55E")
        static let danger = Color(hex: "#EF4444")
        static let disabled = Color(hex: "#94A3B8")
        static let border = Color(hex: "#D7E0ED")
    }

    enum Spacing {
        static let xxs: CGFloat = 4
        static let xs: CGFloat = 8
        static let sm: CGFloat = 12
        static let md: CGFloat = 16
        static let lg: CGFloat = 20
        static let xl: CGFloat = 24
        static let xxl: CGFloat = 32
    }

    enum Radius {
        static let sm: CGFloat = 10
        static let md: CGFloat = 14
        static let lg: CGFloat = 20
        static let pill: CGFloat = 999
    }

    enum Typography {
        static let display = Font.system(size: 42, weight: .bold, design: .rounded)
        static let title = Font.system(size: 28, weight: .bold, design: .rounded)
        static let headline = Font.system(size: 18, weight: .semibold, design: .rounded)
        static let body = Font.system(size: 16, weight: .regular, design: .rounded)
        static let bodyStrong = Font.system(size: 16, weight: .semibold, design: .rounded)
        static let caption = Font.system(size: 13, weight: .medium, design: .rounded)
    }

    enum Shadows {
        static let card = AppShadow(
            color: Color.black.opacity(0.08),
            radius: 14,
            x: 0,
            y: 8
        )
        static let pressed = AppShadow(
            color: Color.black.opacity(0.05),
            radius: 6,
            x: 0,
            y: 3
        )
    }

    enum Motion {
        enum Duration {
            static let quick: Double = 0.12
            static let standard: Double = 0.20
            static let emphasized: Double = 0.24
            static let reduced: Double = 0.08
        }

        enum Curve {
            case easeOut
            case easeInOut
        }

        enum Primitive {
            case primaryButtonPress
            case tabSelection
            case cardSurface
        }

        static func animation(
            for primitive: Primitive,
            accessibilityReduceMotion: Bool
        ) -> Animation {
            if accessibilityReduceMotion {
                return .linear(duration: Duration.reduced)
            }

            switch primitive {
            case .primaryButtonPress:
                return makeAnimation(duration: Duration.quick, curve: .easeOut)
            case .tabSelection:
                return makeAnimation(duration: Duration.standard, curve: .easeInOut)
            case .cardSurface:
                return makeAnimation(duration: Duration.emphasized, curve: .easeOut)
            }
        }

        static func pressedScale(
            isPressed: Bool,
            accessibilityReduceMotion: Bool
        ) -> CGFloat {
            guard isPressed else {
                return 1
            }

            return accessibilityReduceMotion ? 0.992 : 0.98
        }

        static func cardScale(
            isHighlighted: Bool,
            accessibilityReduceMotion: Bool
        ) -> CGFloat {
            guard isHighlighted else {
                return 1
            }

            return accessibilityReduceMotion ? 1 : 1.01
        }

        static func cardVerticalOffset(
            isHighlighted: Bool,
            accessibilityReduceMotion: Bool
        ) -> CGFloat {
            guard isHighlighted else {
                return 0
            }

            return accessibilityReduceMotion ? 0 : -1
        }

        private static func makeAnimation(duration: Double, curve: Curve) -> Animation {
            switch curve {
            case .easeOut:
                return .easeOut(duration: duration)
            case .easeInOut:
                return .easeInOut(duration: duration)
            }
        }
    }
}

private struct AppAccentHexEnvironmentKey: EnvironmentKey {
    static let defaultValue: String = AppTheme.defaultAccentHex
}

extension EnvironmentValues {
    var appAccentHex: String {
        get { self[AppAccentHexEnvironmentKey.self] }
        set { self[AppAccentHexEnvironmentKey.self] = AppTheme.normalizedAccentHex(newValue) }
    }
}

struct AppShadow {
    let color: Color
    let radius: CGFloat
    let x: CGFloat
    let y: CGFloat
}

extension View {
    func appThemeShadow(_ shadow: AppShadow) -> some View {
        self.shadow(color: shadow.color, radius: shadow.radius, x: shadow.x, y: shadow.y)
    }

    func appThemeAccentHex(_ accentHex: String) -> some View {
        environment(\.appAccentHex, AppTheme.normalizedAccentHex(accentHex))
    }
}
