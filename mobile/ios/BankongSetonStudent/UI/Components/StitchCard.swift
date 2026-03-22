import SwiftUI

struct StitchCard<Content: View>: View {
    private let padding: CGFloat
    private let content: Content

    init(padding: CGFloat = AppTheme.Spacing.lg, @ViewBuilder content: () -> Content) {
        self.padding = padding
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
    }
}
