import SwiftUI

struct StitchFieldStyle: ViewModifier {
    func body(content: Content) -> some View {
        let shape = RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous)

        content
            .font(AppTheme.Typography.body)
            .padding(.horizontal, AppTheme.Spacing.md)
            .padding(.vertical, AppTheme.Spacing.sm)
            .frame(minHeight: 50)
            .background(
                shape
                    .fill(
                        LinearGradient(
                            colors: [
                                AppTheme.Palette.surfaceSubtle,
                                AppTheme.Palette.surface
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            )
            .foregroundStyle(AppTheme.Palette.textPrimary)
            .overlay(
                shape
                    .stroke(AppTheme.Palette.border.opacity(0.6), lineWidth: 1)
            )
    }
}

extension View {
    func stitchFieldStyle() -> some View {
        self.modifier(StitchFieldStyle())
    }
}
