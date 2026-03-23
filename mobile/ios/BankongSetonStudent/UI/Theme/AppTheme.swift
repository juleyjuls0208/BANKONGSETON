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
        // Surfaces
        static let background = Color.adaptive(light: "#F4F7FB", dark: "#0E0E10")
        static let surface = Color.adaptive(light: "#FFFFFF", dark: "#171A23")
        static let surfaceSubtle = Color.adaptive(light: "#EDF2FA", dark: "#1F2430")
        static let surfaceElevated = Color.adaptive(light: "#FFFFFF", dark: "#252B3A")
        static let chrome = Color.adaptive(light: "#F9FBFF", dark: "#121723")

        // Brand and accent anchors
        static let brandPrimary = Color.adaptive(light: "#1565C0", dark: "#4C8DFF")
        static let brandSecondary = Color.adaptive(light: "#1E88E5", dark: "#9DBEFF")
        static let accent = Color.adaptive(light: "#2D9CDB", dark: "#78A8FF")

        // Typography
        static let textPrimary = Color.adaptive(light: "#0F172A", dark: "#F4F7FF")
        static let textSecondary = Color.adaptive(light: "#64748B", dark: "#A1A9BE")
        static let textTertiary = Color.adaptive(light: "#93A2B9", dark: "#7E879B")
        static let textInverse = Color.white

        // Semantic
        static let success = Color.adaptive(light: "#16A34A", dark: "#34D399")
        static let danger = Color.adaptive(light: "#DC2626", dark: "#F87171")
        static let warning = Color.adaptive(light: "#D97706", dark: "#FBBF24")
        static let disabled = Color.adaptive(light: "#A8B5C8", dark: "#3A435A")

        // Structural
        static let border = Color.adaptive(light: "#D5DFEE", dark: "#2B3448")
        static let ghostBorder = Color.adaptive(light: "#FFFFFF", dark: "#B3C1E9")
        static let shadow = Color.adaptive(light: "#0B1020", dark: "#000000")
    }

    enum Spacing {
        static let xxs: CGFloat = 4
        static let xs: CGFloat = 8
        static let sm: CGFloat = 12
        static let md: CGFloat = 16
        static let lg: CGFloat = 20
        static let xl: CGFloat = 24
        static let xxl: CGFloat = 32
        static let xxxl: CGFloat = 40
    }

    enum Radius {
        static let sm: CGFloat = 12
        static let md: CGFloat = 16
        static let lg: CGFloat = 24
        static let pill: CGFloat = 999
    }

    enum Typography {
        static let display = Font.system(size: 54, weight: .bold, design: .rounded)
        static let title = Font.system(size: 32, weight: .bold, design: .rounded)
        static let headline = Font.system(size: 18, weight: .semibold, design: .rounded)
        static let body = Font.system(size: 16, weight: .regular, design: .rounded)
        static let bodyStrong = Font.system(size: 16, weight: .semibold, design: .rounded)
        static let caption = Font.system(size: 13, weight: .medium, design: .rounded)
        static let micro = Font.system(size: 12, weight: .medium, design: .rounded)
    }

    enum Shadows {
        static let card = AppShadow(
            color: AppTheme.Palette.shadow.opacity(0.22),
            radius: 24,
            x: 0,
            y: 10
        )
        static let pressed = AppShadow(
            color: AppTheme.Palette.shadow.opacity(0.14),
            radius: 8,
            x: 0,
            y: 4
        )
        static let glow = AppShadow(
            color: AppTheme.Palette.brandPrimary.opacity(0.20),
            radius: 26,
            x: 0,
            y: 0
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
