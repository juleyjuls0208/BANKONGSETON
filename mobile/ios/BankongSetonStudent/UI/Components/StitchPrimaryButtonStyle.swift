import SwiftUI

struct StitchPrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    @Environment(\.appAccentHex) private var accentHex
    @Environment(\.accessibilityReduceMotion) private var accessibilityReduceMotion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(AppTheme.Typography.bodyStrong)
            .frame(maxWidth: .infinity)
            .frame(minHeight: 52)
            .padding(.horizontal, AppTheme.Spacing.md)
            .background(background(isPressed: configuration.isPressed))
            .foregroundStyle(AppTheme.Palette.textInverse)
            .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous))
            .scaleEffect(
                AppTheme.Motion.pressedScale(
                    isPressed: configuration.isPressed,
                    accessibilityReduceMotion: accessibilityReduceMotion
                )
            )
            .animation(
                AppTheme.Motion.animation(
                    for: .primaryButtonPress,
                    accessibilityReduceMotion: accessibilityReduceMotion
                ),
                value: configuration.isPressed
            )
    }

    private func background(isPressed: Bool) -> AnyShapeStyle {
        if !isEnabled {
            return AnyShapeStyle(AppTheme.Palette.disabled)
        }

        let gradientColors = isPressed
            ? [AppTheme.accentSecondaryColor(for: accentHex), AppTheme.accentColor(for: accentHex)]
            : [AppTheme.accentColor(for: accentHex), AppTheme.accentSecondaryColor(for: accentHex)]

        return AnyShapeStyle(
            LinearGradient(
                colors: gradientColors,
                startPoint: isPressed ? .top : .topLeading,
                endPoint: isPressed ? .bottom : .bottomTrailing
            )
        )
    }
}
