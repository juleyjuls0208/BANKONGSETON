import SwiftUI

/// Centralized design tokens for stitch-faithful styling across the app.
enum AppTheme {
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
}
