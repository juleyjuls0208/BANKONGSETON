import SwiftUI

struct BudgetView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = BudgetViewModel()

    @State private var limitInput: String = ""
    @State private var hasEditedLimit = false
    @State private var saveSuccessMessage: String?

    private var utilizationColor: Color {
        if viewModel.percent >= 100 { return AppTheme.Palette.danger }
        if viewModel.percent >= 80 { return .orange }
        return AppTheme.Palette.success
    }

    private var parsedLimitInput: Double? {
        Double(limitInput.trimmingCharacters(in: .whitespacesAndNewlines))
    }

    private var canSaveLimit: Bool {
        guard let parsedLimitInput else { return false }
        return parsedLimitInput > 0 && !viewModel.isLoading
    }

    var body: some View {
        NavigationStack {
            ZStack {
                AppTheme.Palette.background
                    .ignoresSafeArea()

                ScrollView {
                    VStack(spacing: AppTheme.Spacing.lg) {
                        progressCard
                        loadStateCard

                        if viewModel.hasSaveFailureState, let saveErrorMessage = viewModel.saveErrorMessage {
                            saveFailureCard(message: saveErrorMessage)
                        } else if let saveSuccessMessage {
                            saveSuccessCard(message: saveSuccessMessage)
                        }

                        limitEditorCard
                    }
                    .padding(.horizontal, AppTheme.Spacing.lg)
                    .padding(.vertical, AppTheme.Spacing.lg)
                    .accessibilityIdentifier("budget-screen-root")
                }
                .refreshable {
                    await refreshBudget()
                }
            }
            .navigationTitle("Budget")
            .task {
                await refreshBudget()
            }
            .alert("Budget Alert", isPresented: $viewModel.showAlert) {
                Button("OK") {}
            } message: {
                Text(viewModel.alertMessage)
            }
        }
    }

    private var progressCard: some View {
        StitchCard {
            VStack(spacing: AppTheme.Spacing.md) {
                ZStack {
                    Circle()
                        .stroke(AppTheme.Palette.surfaceSubtle, lineWidth: 16)
                        .frame(width: 196, height: 196)

                    Circle()
                        .trim(from: 0, to: min(CGFloat(viewModel.percent / 100), 1))
                        .stroke(
                            utilizationColor,
                            style: StrokeStyle(lineWidth: 16, lineCap: .round)
                        )
                        .frame(width: 196, height: 196)
                        .rotationEffect(.degrees(-90))
                        .animation(.easeOut(duration: 0.5), value: viewModel.percent)

                    VStack(spacing: AppTheme.Spacing.xxs) {
                        Text("\(Int(viewModel.percent))%")
                            .font(AppTheme.Typography.title)
                            .foregroundStyle(utilizationColor)

                        Text("Used")
                            .font(AppTheme.Typography.caption)
                            .foregroundStyle(AppTheme.Palette.textSecondary)
                    }
                }
                .frame(maxWidth: .infinity)

                HStack(spacing: AppTheme.Spacing.lg) {
                    amountColumn(title: "Spent", value: viewModel.spent)

                    Divider()
                        .frame(height: 40)

                    amountColumn(title: "Limit", value: viewModel.limit)
                }
                .frame(maxWidth: .infinity)
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel(
                "Budget usage \(Int(viewModel.percent)) percent. Spent \(String(format: "%.2f", viewModel.spent)) pesos out of \(String(format: "%.2f", viewModel.limit)) pesos."
            )
        }
        .accessibilityIdentifier("budget-card-progress")
    }

    @ViewBuilder
    private var loadStateCard: some View {
        if viewModel.isLoading {
            StitchCard {
                HStack(spacing: AppTheme.Spacing.sm) {
                    ProgressView()
                    Text("Refreshing budget details…")
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                }
                .frame(maxWidth: .infinity, alignment: .center)
            }
            .accessibilityIdentifier("budget-state-loading-card")
            .accessibilityLabel("Budget is loading")
            .accessibilityHint("Wait while your latest budget details are fetched")
        } else if let loadErrorMessage = viewModel.loadErrorMessage {
            StitchCard {
                VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                    Text("Couldn’t Refresh Budget")
                        .font(AppTheme.Typography.headline)
                        .foregroundStyle(AppTheme.Palette.danger)

                    Text(loadErrorMessage)
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                        .multilineTextAlignment(.leading)

                    Button {
                        Task {
                            await retryBudgetLoad()
                        }
                    } label: {
                        Label("Retry Load", systemImage: "arrow.clockwise")
                    }
                    .buttonStyle(StitchPrimaryButtonStyle())
                    .accessibilityIdentifier("budget-retry-load-button")
                    .accessibilityHint("Retries loading your monthly limit and spending summary")
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .accessibilityIdentifier("budget-state-load-error-card")
            .accessibilityLabel("Budget refresh failed")
        } else {
            StitchCard {
                VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                    Text("Budget is up to date")
                        .font(AppTheme.Typography.headline)
                        .foregroundStyle(AppTheme.Palette.textPrimary)

                    Text("Use pull-to-refresh or refresh below to fetch the latest totals.")
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                        .multilineTextAlignment(.leading)

                    Button {
                        Task {
                            await refreshBudget()
                        }
                    } label: {
                        Label("Refresh Budget", systemImage: "arrow.clockwise")
                    }
                    .buttonStyle(StitchPrimaryButtonStyle())
                    .accessibilityIdentifier("budget-refresh-button")
                    .accessibilityHint("Refreshes your budget totals from the server")
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .accessibilityIdentifier("budget-state-ready-card")
            .accessibilityLabel("Budget ready")
        }
    }

    private var limitEditorCard: some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Monthly Limit")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.textPrimary)

                Text("Set the amount you want to stay within this month.")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)

                TextField("Enter monthly limit", text: $limitInput)
                    .keyboardType(.decimalPad)
                    .stitchFieldStyle()
                    .onChange(of: limitInput) { _ in
                        hasEditedLimit = true
                        saveSuccessMessage = nil
                    }
                    .accessibilityIdentifier("budget-limit-input-field")
                    .accessibilityLabel("Monthly budget limit")
                    .accessibilityHint("Enter your monthly spending limit in pesos")

                Button {
                    Task {
                        await saveBudgetLimit()
                    }
                } label: {
                    Label("Save Limit", systemImage: "checkmark.circle")
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .disabled(!canSaveLimit)
                .accessibilityIdentifier("budget-save-button")
                .accessibilityHint("Saves your updated monthly budget limit")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityIdentifier("budget-limit-editor-card")
    }

    private func saveFailureCard(message: String) -> some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Couldn’t Save Limit")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.danger)

                Text(message)
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)

                Button {
                    Task {
                        await retryBudgetSave()
                    }
                } label: {
                    Label("Retry Save", systemImage: "arrow.clockwise")
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .accessibilityIdentifier("budget-retry-save-button")
                .accessibilityHint("Retries saving your latest monthly budget limit")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityIdentifier("budget-state-save-error-card")
        .accessibilityLabel("Budget save failed")
    }

    private func saveSuccessCard(message: String) -> some View {
        StitchCard {
            HStack(alignment: .top, spacing: AppTheme.Spacing.xs) {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(AppTheme.Palette.success)
                    .padding(.top, 1)

                Text(message)
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .accessibilityIdentifier("budget-state-save-success-card")
        .accessibilityLabel("Budget save succeeded")
    }

    private func amountColumn(title: String, value: Double) -> some View {
        VStack(spacing: AppTheme.Spacing.xxs) {
            Text(title)
                .font(AppTheme.Typography.caption)
                .foregroundStyle(AppTheme.Palette.textSecondary)

            Text("₱\(String(format: "%.2f", value))")
                .font(AppTheme.Typography.headline)
                .foregroundStyle(AppTheme.Palette.textPrimary)
        }
        .frame(maxWidth: .infinity)
    }

    private func refreshBudget() async {
        saveSuccessMessage = nil
        await viewModel.load(apiClient: apiClient, authManager: authManager)
        syncLimitInputFromModel()
    }

    private func retryBudgetLoad() async {
        saveSuccessMessage = nil
        await viewModel.retryLoad(apiClient: apiClient, authManager: authManager)
        syncLimitInputFromModel()
    }

    private func saveBudgetLimit() async {
        guard let parsedLimitInput, parsedLimitInput > 0 else { return }

        dismissKeyboard()
        saveSuccessMessage = nil

        await viewModel.setBudget(limit: parsedLimitInput, apiClient: apiClient, authManager: authManager)

        guard viewModel.pendingRetryLimit == nil, viewModel.saveErrorMessage == nil else {
            return
        }

        saveSuccessMessage = "Budget limit saved successfully."
        hasEditedLimit = false
        syncLimitInputFromModel()
    }

    private func retryBudgetSave() async {
        saveSuccessMessage = nil
        await viewModel.retryLastSave(apiClient: apiClient, authManager: authManager)

        guard viewModel.pendingRetryLimit == nil, viewModel.saveErrorMessage == nil else {
            return
        }

        saveSuccessMessage = "Budget limit saved successfully."
        hasEditedLimit = false
        syncLimitInputFromModel()
    }

    private func syncLimitInputFromModel() {
        guard !hasEditedLimit || limitInput.isEmpty else { return }
        limitInput = String(format: "%.2f", viewModel.limit)
    }

    private func dismissKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
}
