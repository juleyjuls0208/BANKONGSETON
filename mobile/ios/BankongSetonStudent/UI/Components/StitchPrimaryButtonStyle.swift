import SwiftUI

struct StitchPrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(AppTheme.Typography.bodyStrong)
            .frame(maxWidth: .infinity)
            .frame(minHeight: 52)
            .padding(.horizontal, AppTheme.Spacing.md)
            .background(background(isPressed: configuration.isPressed))
            .foregroundStyle(AppTheme.Palette.textInverse)
            .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous))
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }

    private func background(isPressed: Bool) -> AnyShapeStyle {
        if !isEnabled {
            return AnyShapeStyle(AppTheme.Palette.disabled)
        }

        if isPressed {
            return AnyShapeStyle(
                LinearGradient(
                    colors: [AppTheme.Palette.brandSecondary, AppTheme.Palette.brandPrimary],
                    startPoint: .top,
                    endPoint: .bottom
                )
            )
        }

        return AnyShapeStyle(
            LinearGradient(
                colors: [AppTheme.Palette.brandPrimary, AppTheme.Palette.brandSecondary],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
    }
}
