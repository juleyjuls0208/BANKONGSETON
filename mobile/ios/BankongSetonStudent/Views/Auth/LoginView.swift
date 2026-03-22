import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var apiClient: APIClient
    @EnvironmentObject private var authManager: AuthManager
    @StateObject private var viewModel = LoginViewModel()

    var body: some View {
        NavigationStack {
            ZStack {
                AppTheme.Palette.background
                    .ignoresSafeArea()

                ScrollView(showsIndicators: false) {
                    VStack(spacing: AppTheme.Spacing.xl) {
                        branding

                        StitchCard {
                            VStack(spacing: AppTheme.Spacing.md) {
                                Text("Sign In")
                                    .font(AppTheme.Typography.headline)
                                    .foregroundStyle(AppTheme.Palette.textPrimary)
                                    .frame(maxWidth: .infinity, alignment: .leading)

                                Text("Use your Student ID and PIN to continue.")
                                    .font(AppTheme.Typography.caption)
                                    .foregroundStyle(AppTheme.Palette.textSecondary)
                                    .frame(maxWidth: .infinity, alignment: .leading)

                                TextField("Student ID", text: $viewModel.studentId)
                                    .textInputAutocapitalization(.never)
                                    .autocorrectionDisabled()
                                    .textContentType(.username)
                                    .stitchFieldStyle()
                                    .accessibilityIdentifier("login-student-id-field")

                                SecureField("PIN", text: $viewModel.pin)
                                    .textContentType(.oneTimeCode)
                                    .stitchFieldStyle()
                                    .accessibilityIdentifier("login-pin-field")

                                if let error = viewModel.errorMessage {
                                    HStack(alignment: .top, spacing: AppTheme.Spacing.xs) {
                                        Image(systemName: "exclamationmark.circle.fill")
                                            .foregroundStyle(AppTheme.Palette.danger)
                                            .padding(.top, 1)

                                        Text(error)
                                            .font(AppTheme.Typography.caption)
                                            .foregroundStyle(AppTheme.Palette.danger)
                                            .multilineTextAlignment(.leading)
                                            .frame(maxWidth: .infinity, alignment: .leading)
                                    }
                                    .padding(AppTheme.Spacing.sm)
                                    .background(AppTheme.Palette.danger.opacity(0.08))
                                    .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous)
                                            .stroke(AppTheme.Palette.danger.opacity(0.25), lineWidth: 1)
                                    )
                                    .accessibilityLabel("Sign-in error: \(error)")
                                }

                                Button {
                                    Task {
                                        await viewModel.login(apiClient: apiClient, authManager: authManager)
                                    }
                                } label: {
                                    HStack(spacing: AppTheme.Spacing.xs) {
                                        if viewModel.isLoading {
                                            ProgressView()
                                                .tint(AppTheme.Palette.textInverse)
                                                .accessibilityLabel("Signing in")
                                        }

                                        Text(viewModel.isLoading ? "Signing In..." : "Sign In")
                                    }
                                }
                                .buttonStyle(StitchPrimaryButtonStyle())
                                .disabled(!viewModel.canSubmit)
                                .accessibilityHint("Authenticates your account")
                            }
                        }

                        Text("Never share your PIN with anyone.")
                            .font(AppTheme.Typography.caption)
                            .foregroundStyle(AppTheme.Palette.textSecondary)
                            .frame(maxWidth: .infinity, alignment: .center)
                    }
                    .padding(.horizontal, AppTheme.Spacing.lg)
                    .padding(.vertical, AppTheme.Spacing.xxl)
                }
            }
            .navigationTitle("")
            .navigationBarHidden(true)
        }
    }

    private var branding: some View {
        VStack(spacing: AppTheme.Spacing.sm) {
            ZStack {
                Circle()
                    .fill(AppTheme.Palette.surface)
                    .frame(width: 84, height: 84)
                    .overlay(
                        Circle()
                            .stroke(AppTheme.Palette.border, lineWidth: 1)
                    )
                    .appThemeShadow(AppTheme.Shadows.card)

                Image(systemName: "banknote.fill")
                    .font(.system(size: 34, weight: .semibold))
                    .foregroundStyle(AppTheme.Palette.brandPrimary)
            }

            Text("BankongSeton")
                .font(AppTheme.Typography.title)
                .foregroundStyle(AppTheme.Palette.textPrimary)

            Text("Student Portal")
                .font(AppTheme.Typography.body)
                .foregroundStyle(AppTheme.Palette.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, AppTheme.Spacing.sm)
    }
}
