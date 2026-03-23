import SwiftUI
import UIKit

struct QRPayView: View {
    @EnvironmentObject var apiClient: APIClient
    @StateObject private var viewModel = QRPayViewModel()
    @State private var hasTriggeredSuccessCompletion = false
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL
    @Environment(\.accessibilityReduceMotion) private var accessibilityReduceMotion
    private var onSuccess: (() -> Void)?

    init(onSuccess: (() -> Void)? = nil) {
        self.onSuccess = onSuccess
    }

    var body: some View {
        NavigationStack {
            ZStack {
                AppTheme.Palette.background
                    .ignoresSafeArea()

                stateContent
                    .id(stateTransitionKey)
                    .transition(stateTransition)
            }
            .animation(stateTransitionAnimation, value: stateTransitionKey)
            .navigationTitle("Pay with QR")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
        }
    }

    private var stateTransitionAnimation: Animation {
        AppTheme.Motion.animation(
            for: .cardSurface,
            accessibilityReduceMotion: accessibilityReduceMotion
        )
    }

    private var stateTransitionKey: String {
        switch viewModel.state {
        case .scanning:
            return "scanning"
        case .loading:
            return "loading"
        case .confirming:
            return "confirming"
        case .success:
            return "success"
        case .error:
            return "error"
        }
    }

    private var stateTransition: AnyTransition {
        if accessibilityReduceMotion {
            return .opacity
        }

        return .asymmetric(
            insertion: .opacity.combined(with: .move(edge: .bottom)),
            removal: .opacity.combined(with: .scale(scale: 0.98))
        )
    }

    @ViewBuilder
    private var stateContent: some View {
        switch viewModel.state {
        case .scanning:
            scanningView

        case .loading:
            loadingView

        case .confirming(let cart, let token):
            confirmView(cart: cart, token: token)

        case .success(let newBalance):
            successView(newBalance: newBalance)

        case .error(let message):
            errorView(message: message)
        }
    }

    // MARK: Scanning

    private var scanningView: some View {
        ZStack(alignment: .bottom) {
            QRScannerView(
                onCodeScanned: { scannedPayload in
                    viewModel.handleScannedURL(scannedPayload, apiClient: apiClient)
                },
                onScannerFailure: { failureMessage in
                    viewModel.handleScannerFailure(failureMessage)
                }
            )
            .ignoresSafeArea()

            LinearGradient(
                colors: [Color.clear, Color.black.opacity(0.55)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: AppTheme.Spacing.sm) {
                StitchCard {
                    VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                        HStack(alignment: .top, spacing: AppTheme.Spacing.sm) {
                            Image(systemName: "qrcode.viewfinder")
                                .font(.system(size: 22, weight: .semibold))
                                .foregroundStyle(AppTheme.Palette.brandPrimary)

                            VStack(alignment: .leading, spacing: AppTheme.Spacing.xxs) {
                                Text("Scan cashier QR")
                                    .font(AppTheme.Typography.headline)
                                    .foregroundStyle(AppTheme.Palette.textPrimary)

                                Text("Point the camera at the cashier QR code to load your cart details.")
                                    .font(AppTheme.Typography.body)
                                    .foregroundStyle(AppTheme.Palette.textSecondary)
                            }
                        }

                        Text("If camera permission was denied, retry from the error screen to open Settings.")
                            .font(AppTheme.Typography.caption)
                            .foregroundStyle(AppTheme.Palette.textSecondary)
                    }
                }
            }
            .padding(.horizontal, AppTheme.Spacing.lg)
            .padding(.bottom, AppTheme.Spacing.xl)
        }
    }

    // MARK: Loading

    private var loadingView: some View {
        VStack(spacing: AppTheme.Spacing.lg) {
            StitchCard {
                VStack(spacing: AppTheme.Spacing.md) {
                    ProgressView()
                        .tint(AppTheme.Palette.brandPrimary)
                        .scaleEffect(1.1)

                    Text("Loading QR payment details…")
                        .font(AppTheme.Typography.headline)
                        .foregroundStyle(AppTheme.Palette.textPrimary)

                    Text("Please wait while we fetch your cart from the cashier terminal.")
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
            }

            Button("Cancel") { dismiss() }
                .buttonStyle(.bordered)
                .tint(AppTheme.Palette.brandPrimary)
        }
        .padding(.horizontal, AppTheme.Spacing.lg)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: Confirmation

    private func confirmView(cart: QrCartResponse, token: String) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.md) {
                StitchCard {
                    VStack(alignment: .leading, spacing: AppTheme.Spacing.xs) {
                        Text("Confirm QR Payment")
                            .font(AppTheme.Typography.title)
                            .foregroundStyle(AppTheme.Palette.textPrimary)

                        Text("Cashier: \(cart.cashier)")
                            .font(AppTheme.Typography.bodyStrong)
                            .foregroundStyle(AppTheme.Palette.textPrimary)

                        Text("Review your cart before confirming payment.")
                            .font(AppTheme.Typography.caption)
                            .foregroundStyle(AppTheme.Palette.textSecondary)
                    }
                }

                StitchCard {
                    VStack(spacing: AppTheme.Spacing.sm) {
                        ForEach(Array(cart.items.enumerated()), id: \.offset) { index, item in
                            HStack(alignment: .firstTextBaseline, spacing: AppTheme.Spacing.sm) {
                                Text(item.name)
                                    .font(AppTheme.Typography.body)
                                    .foregroundStyle(AppTheme.Palette.textPrimary)
                                    .frame(maxWidth: .infinity, alignment: .leading)

                                Text("×\(item.qty)")
                                    .font(AppTheme.Typography.caption)
                                    .foregroundStyle(AppTheme.Palette.textSecondary)

                                Text("₱\(String(format: "%.2f", item.price * Double(item.qty)))")
                                    .font(AppTheme.Typography.bodyStrong)
                                    .foregroundStyle(AppTheme.Palette.textPrimary)
                            }

                            if index < cart.items.count - 1 {
                                Divider()
                                    .overlay(AppTheme.Palette.border)
                            }
                        }

                        Divider()
                            .overlay(AppTheme.Palette.border)

                        HStack {
                            Text("Total")
                                .font(AppTheme.Typography.headline)
                                .foregroundStyle(AppTheme.Palette.textPrimary)

                            Spacer()

                            Text("₱\(String(format: "%.2f", cart.total))")
                                .font(AppTheme.Typography.headline)
                                .foregroundStyle(AppTheme.Palette.brandPrimary)
                        }
                    }
                }

                StitchCard {
                    VStack(spacing: AppTheme.Spacing.sm) {
                        Button("Confirm QR Payment") {
                            viewModel.confirm(token: token, apiClient: apiClient)
                        }
                        .buttonStyle(StitchPrimaryButtonStyle())

                        Button("Cancel") { dismiss() }
                            .buttonStyle(.bordered)
                            .tint(AppTheme.Palette.brandPrimary)
                    }
                }
            }
            .padding(.horizontal, AppTheme.Spacing.lg)
            .padding(.vertical, AppTheme.Spacing.lg)
        }
    }

    // MARK: Success

    private func successView(newBalance: Double?) -> some View {
        VStack(spacing: AppTheme.Spacing.lg) {
            StitchCard {
                VStack(spacing: AppTheme.Spacing.md) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 66, weight: .semibold))
                        .foregroundStyle(AppTheme.Palette.success)

                    Text("Payment successful")
                        .font(AppTheme.Typography.title)
                        .foregroundStyle(AppTheme.Palette.textPrimary)

                    Text("Your QR payment has been recorded.")
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                        .multilineTextAlignment(.center)

                    if let balance = newBalance {
                        Text("New balance: ₱\(String(format: "%.2f", balance))")
                            .font(AppTheme.Typography.bodyStrong)
                            .foregroundStyle(AppTheme.Palette.textPrimary)
                    }

                    Button("Done") {
                        completeSuccessFlow(trigger: "manual_done")
                    }
                    .buttonStyle(StitchPrimaryButtonStyle())
                }
                .frame(maxWidth: .infinity)
            }
            .frame(maxWidth: 520)
        }
        .padding(.horizontal, AppTheme.Spacing.lg)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .onAppear {
            // Auto-dismiss success after 3 seconds.
            DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                completeSuccessFlow(trigger: "auto_dismiss")
            }
        }
    }

    private func completeSuccessFlow(trigger: String) {
        guard !hasTriggeredSuccessCompletion else {
            print("[QRPayView] Ignoring duplicate success completion trigger=\(trigger)")
            return
        }

        hasTriggeredSuccessCompletion = true
        print("[QRPayView] Completing success flow trigger=\(trigger)")
        onSuccess?()
        dismiss()
    }

    // MARK: Error

    private func errorView(message: String) -> some View {
        VStack(spacing: AppTheme.Spacing.lg) {
            StitchCard {
                VStack(spacing: AppTheme.Spacing.md) {
                    Image(systemName: "exclamationmark.circle.fill")
                        .font(.system(size: 66, weight: .semibold))
                        .foregroundStyle(AppTheme.Palette.danger)

                    Text("Payment Error")
                        .font(AppTheme.Typography.title)
                        .foregroundStyle(AppTheme.Palette.textPrimary)

                    Text(message)
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                        .multilineTextAlignment(.center)

                    VStack(spacing: AppTheme.Spacing.sm) {
                        if message.localizedCaseInsensitiveContains("Camera access") {
                            Button("Open Settings") {
                                guard let settingsURL = URL(string: UIApplication.openSettingsURLString) else { return }
                                openURL(settingsURL)
                            }
                            .buttonStyle(.bordered)
                            .tint(AppTheme.Palette.brandPrimary)
                        }

                        Button("Retry Scan") { viewModel.reset() }
                            .buttonStyle(StitchPrimaryButtonStyle())

                        Button("Close") { dismiss() }
                            .buttonStyle(.bordered)
                            .tint(AppTheme.Palette.brandPrimary)
                    }
                }
                .frame(maxWidth: .infinity)
            }
            .frame(maxWidth: 520)
        }
        .padding(.horizontal, AppTheme.Spacing.lg)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
