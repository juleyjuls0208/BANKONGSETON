import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager

    @StateObject private var viewModel = SettingsViewModel()

    private let accentOptions: [AccentOption] = [
        .init(title: "Sky", hex: "#2D9CDB"),
        .init(title: "Ocean", hex: "#1565C0"),
        .init(title: "Indigo", hex: "#4F46E5"),
        .init(title: "Teal", hex: "#0F766E"),
        .init(title: "Amber", hex: "#B45309")
    ]

    var body: some View {
        NavigationStack {
            ZStack {
                AppTheme.Palette.background
                    .ignoresSafeArea()

                ScrollView(showsIndicators: false) {
                    VStack(spacing: AppTheme.Spacing.lg) {
                        appearanceCard
                        accountActionsCard
                    }
                    .padding(.horizontal, AppTheme.Spacing.lg)
                    .padding(.vertical, AppTheme.Spacing.lg)
                    .accessibilityIdentifier("settings-screen-root")
                }
            }
            .navigationTitle("Settings")
        }
        .preferredColorScheme(viewModel.colorScheme)
    }

    private var appearanceCard: some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Appearance")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.textPrimary)

                Text("Pick how the app looks and apply your preferred accent color.")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)

                Picker("Theme", selection: $viewModel.selectedTheme) {
                    ForEach(viewModel.themeOptions, id: \.self) { option in
                        Text(themeTitle(for: option)).tag(option)
                    }
                }
                .pickerStyle(.segmented)
                .accessibilityIdentifier("settings-theme-picker")
                .accessibilityLabel("Theme")
                .stitchFieldStyle()

                LazyVGrid(
                    columns: [
                        GridItem(.flexible(minimum: 120), spacing: AppTheme.Spacing.sm),
                        GridItem(.flexible(minimum: 120), spacing: AppTheme.Spacing.sm)
                    ],
                    spacing: AppTheme.Spacing.sm
                ) {
                    ForEach(accentOptions) { option in
                        accentOptionButton(option)
                    }
                }

                Button {
                    viewModel.applyAccent(viewModel.selectedAccentHex)
                } label: {
                    HStack(spacing: AppTheme.Spacing.xs) {
                        if isApplyingAccent {
                            ProgressView()
                                .tint(AppTheme.Palette.textInverse)
                                .accessibilityLabel("Applying accent")
                        }

                        Text(isApplyingAccent ? "Applying Accent..." : "Apply Accent")
                    }
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .disabled(!canApplyAccent)
                .accessibilityIdentifier("settings-apply-accent-button")
                .accessibilityHint("Applies the selected accent color across shared app surfaces")

                Text(accentStatusMessage)
                    .font(AppTheme.Typography.caption)
                    .foregroundStyle(accentStatusColor)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .accessibilityIdentifier("settings-accent-status")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var accountActionsCard: some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Account Actions")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.textPrimary)

                Text("Use these actions to secure your card and manage your session.")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)

                NavigationLink("Report Lost Card") {
                    LostCardView()
                }
                .font(AppTheme.Typography.bodyStrong)
                .foregroundStyle(AppTheme.Palette.brandPrimary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, AppTheme.Spacing.xs)
                .accessibilityIdentifier("settings-report-lost-card-link")
                .accessibilityHint("Opens the lost-card reporting flow")

                Button(role: .destructive) {
                    Task {
                        await viewModel.logout {
                            await authManager.logout(apiClient: apiClient)
                        }
                    }
                } label: {
                    HStack(spacing: AppTheme.Spacing.xs) {
                        if viewModel.isLoggingOut {
                            ProgressView()
                                .tint(AppTheme.Palette.danger)
                                .accessibilityLabel("Logging out")
                        }

                        Text(viewModel.isLoggingOut ? "Logging Out..." : "Logout")
                            .font(AppTheme.Typography.bodyStrong)
                            .frame(maxWidth: .infinity, alignment: .center)
                    }
                    .frame(minHeight: 52)
                    .padding(.horizontal, AppTheme.Spacing.md)
                }
                .buttonStyle(.plain)
                .foregroundStyle(AppTheme.Palette.danger)
                .background(AppTheme.Palette.danger.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous)
                        .stroke(AppTheme.Palette.danger.opacity(0.25), lineWidth: 1)
                )
                .disabled(viewModel.isLoggingOut)
                .accessibilityIdentifier("settings-logout-button")
                .accessibilityHint("Signs you out of your account")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var canApplyAccent: Bool {
        !isApplyingAccent
    }

    private var isApplyingAccent: Bool {
        if case .applying = viewModel.accentApplyState {
            return true
        }

        return false
    }

    private var accentStatusMessage: String {
        switch viewModel.accentApplyState {
        case .idle:
            return "Select a color and tap Apply Accent."
        case .applying:
            return "Applying accent..."
        case .saved:
            return "Accent applied across the app."
        }
    }

    private var accentStatusColor: Color {
        switch viewModel.accentApplyState {
        case .idle:
            return AppTheme.Palette.textSecondary
        case .applying:
            return AppTheme.Palette.brandPrimary
        case .saved:
            return AppTheme.Palette.success
        }
    }

    @ViewBuilder
    private func accentOptionButton(_ option: AccentOption) -> some View {
        let normalizedSelectedAccent = AppTheme.normalizedAccentHex(viewModel.selectedAccentHex)
        let isSelected = normalizedSelectedAccent == option.id

        Button {
            viewModel.selectedAccentHex = option.id
        } label: {
            HStack(spacing: AppTheme.Spacing.xs) {
                Circle()
                    .fill(AppTheme.accentColor(for: option.hex))
                    .frame(width: 16, height: 16)
                    .accessibilityHidden(true)

                Text(option.title)
                    .font(AppTheme.Typography.caption)
                    .foregroundStyle(AppTheme.Palette.textPrimary)

                Spacer(minLength: AppTheme.Spacing.xxs)

                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(AppTheme.accentColor(for: option.hex))
                        .accessibilityHidden(true)
                }
            }
            .padding(.horizontal, AppTheme.Spacing.sm)
            .frame(maxWidth: .infinity)
            .frame(minHeight: 44)
            .background(AppTheme.Palette.surfaceSubtle)
            .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous)
                    .stroke(
                        isSelected
                            ? AppTheme.accentColor(for: option.hex)
                            : AppTheme.Palette.border,
                        lineWidth: isSelected ? 2 : 1
                    )
            )
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("settings-accent-option-\(option.id)")
        .accessibilityLabel("\(option.title) accent")
        .accessibilityHint("Selects \(option.title) as the accent option")
    }

    private func themeTitle(for option: String) -> String {
        switch option {
        case "light":
            return "Light"
        case "dark":
            return "Dark"
        default:
            return "System"
        }
    }
}

private struct AccentOption: Identifiable {
    let title: String
    let hex: String

    var id: String {
        AppTheme.normalizedAccentHex(hex)
    }
}
