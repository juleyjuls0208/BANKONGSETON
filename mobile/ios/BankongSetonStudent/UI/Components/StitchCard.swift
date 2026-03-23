import SwiftUI

struct StitchCard<Content: View>: View {
    @Environment(\.accessibilityReduceMotion) private var accessibilityReduceMotion

    private let padding: CGFloat
    private let isHighlighted: Bool
    private let content: Content

    init(
        padding: CGFloat = AppTheme.Spacing.lg,
        isHighlighted: Bool = false,
        @ViewBuilder content: () -> Content
    ) {
        self.padding = padding
        self.isHighlighted = isHighlighted
        self.content = content()
    }

    var body: some View {
        content
            .padding(padding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(AppTheme.Palette.surface)
            .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.lg, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: AppTheme.Radius.lg, style: .continuous)
                    .stroke(AppTheme.Palette.border, lineWidth: 1)
            )
            .appThemeShadow(AppTheme.Shadows.card)
            .scaleEffect(
                AppTheme.Motion.cardScale(
                    isHighlighted: isHighlighted,
                    accessibilityReduceMotion: accessibilityReduceMotion
                )
            )
            .offset(
                y: AppTheme.Motion.cardVerticalOffset(
                    isHighlighted: isHighlighted,
                    accessibilityReduceMotion: accessibilityReduceMotion
                )
            )
            .animation(
                AppTheme.Motion.animation(
                    for: .cardSurface,
                    accessibilityReduceMotion: accessibilityReduceMotion
                ),
                value: isHighlighted
            )
    }
}
