import SwiftUI

struct StitchFieldStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .font(AppTheme.Typography.body)
            .padding(.horizontal, AppTheme.Spacing.md)
            .padding(.vertical, AppTheme.Spacing.sm)
            .frame(minHeight: 48)
            .background(AppTheme.Palette.surfaceSubtle)
            .foregroundStyle(AppTheme.Palette.textPrimary)
            .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous)
                    .stroke(AppTheme.Palette.border, lineWidth: 1)
            )
    }
}

extension View {
    func stitchFieldStyle() -> some View {
        self.modifier(StitchFieldStyle())
    }
}
