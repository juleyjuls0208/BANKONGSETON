import SwiftUI

struct StitchTabItem<Tab: Hashable>: Identifiable, Hashable {
    let id: Tab
    let title: String
    let systemImage: String
}

struct StitchTabShell<Tab: Hashable, Content: View>: View {
    @Binding var selection: Tab
    @Environment(\.appAccentHex) private var accentHex

    let tabs: [StitchTabItem<Tab>]
    @ViewBuilder let content: (Tab) -> Content

    var body: some View {
        VStack(spacing: 0) {
            TabView(selection: $selection) {
                ForEach(tabs) { tab in
                    content(tab.id)
                        .tag(tab.id)
                        .toolbar(.hidden, for: .tabBar)
                }
            }

            tabBar
        }
        .background(AppTheme.Palette.background.ignoresSafeArea())
    }

    private var tabBar: some View {
        HStack(spacing: AppTheme.Spacing.sm) {
            ForEach(tabs) { tab in
                let isActive = tab.id == selection
                let activeBackground = AppTheme.accentColor(for: accentHex)
                let activeBorder = AppTheme.accentSecondaryColor(for: accentHex).opacity(0.45)

                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        selection = tab.id
                    }
                } label: {
                    VStack(spacing: AppTheme.Spacing.xxs) {
                        Image(systemName: tab.systemImage)
                            .font(AppTheme.Typography.headline)
                        Text(tab.title)
                            .font(AppTheme.Typography.caption)
                            .lineLimit(1)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, AppTheme.Spacing.sm)
                    .foregroundStyle(
                        isActive ? AppTheme.Palette.textInverse : AppTheme.Palette.textSecondary
                    )
                    .background(
                        RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous)
                            .fill(
                                isActive
                                    ? activeBackground
                                    : AppTheme.Palette.surfaceSubtle
                            )
                    )
                    .overlay {
                        RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous)
                            .stroke(isActive ? activeBorder : AppTheme.Palette.border, lineWidth: 1)
                    }
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("main-tab-\(tab.title.lowercased())")
                .accessibilityLabel(tab.title)
                .accessibilityValue(isActive ? "selected" : "not selected")
            }
        }
        .padding(.horizontal, AppTheme.Spacing.md)
        .padding(.vertical, AppTheme.Spacing.sm)
        .background(AppTheme.Palette.surface)
        .overlay(alignment: .top) {
            Divider()
                .overlay(AppTheme.Palette.border)
        }
    }
}
