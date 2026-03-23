import SwiftUI

struct StitchTabItem<Tab: Hashable>: Identifiable, Hashable {
    let id: Tab
    let title: String
    let systemImage: String
}

struct StitchTabShell<Tab: Hashable, Content: View>: View {
    @Binding var selection: Tab
    @Environment(\.appAccentHex) private var accentHex
    @Environment(\.accessibilityReduceMotion) private var accessibilityReduceMotion

    let tabs: [StitchTabItem<Tab>]
    @ViewBuilder let content: (Tab) -> Content

    var body: some View {
        ZStack(alignment: .bottom) {
            AppTheme.Palette.background
                .ignoresSafeArea()

            TabView(selection: $selection) {
                ForEach(tabs) { tab in
                    content(tab.id)
                        .tag(tab.id)
                        .toolbar(.hidden, for: .tabBar)
                }
            }

            tabBar
                .padding(.horizontal, AppTheme.Spacing.lg)
                .padding(.bottom, AppTheme.Spacing.sm)
        }
    }

    private var tabBar: some View {
        HStack(spacing: AppTheme.Spacing.xs) {
            ForEach(tabs) { tab in
                tabButton(for: tab)
            }
        }
        .padding(.horizontal, AppTheme.Spacing.sm)
        .padding(.vertical, AppTheme.Spacing.xs)
        .background(
            RoundedRectangle(cornerRadius: AppTheme.Radius.lg, style: .continuous)
                .fill(.ultraThinMaterial)
        )
        .overlay(
            RoundedRectangle(cornerRadius: AppTheme.Radius.lg, style: .continuous)
                .stroke(AppTheme.Palette.border.opacity(0.55), lineWidth: 1)
        )
        .appThemeShadow(AppTheme.Shadows.card)
    }

    private func tabButton(for tab: StitchTabItem<Tab>) -> some View {
        let isActive = tab.id == selection

        return Button {
            withAnimation(
                AppTheme.Motion.animation(
                    for: .tabSelection,
                    accessibilityReduceMotion: accessibilityReduceMotion
                )
            ) {
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
                isActive
                    ? AppTheme.Palette.textInverse
                    : AppTheme.Palette.textSecondary
            )
            .background(
                RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous)
                    .fill(activeBackground(isActive: isActive))
            )
            .overlay(
                RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous)
                    .stroke(
                        isActive
                            ? AppTheme.Palette.ghostBorder.opacity(0.20)
                            : AppTheme.Palette.border.opacity(0.35),
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("main-tab-\(tab.title.lowercased())")
        .accessibilityLabel(tab.title)
        .accessibilityValue(isActive ? "selected" : "not selected")
    }

    private func activeBackground(isActive: Bool) -> AnyShapeStyle {
        if !isActive {
            return AnyShapeStyle(AppTheme.Palette.surfaceSubtle.opacity(0.9))
        }

        return AnyShapeStyle(
            LinearGradient(
                colors: [
                    AppTheme.accentColor(for: accentHex),
                    AppTheme.accentSecondaryColor(for: accentHex)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
    }
}
