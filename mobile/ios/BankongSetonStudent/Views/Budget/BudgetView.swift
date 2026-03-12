import SwiftUI

struct BudgetView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = BudgetViewModel()
    @State private var limitInput: String = ""
    @State private var hasEdited = false

    // Ring color based on percentage
    private var ringColor: Color {
        if viewModel.percent >= 100 { return .red }
        if viewModel.percent >= 80  { return .orange }
        return .green
    }

    var body: some View {
        NavigationStack {
            ZStack {
                ScrollView {
                    VStack(spacing: 28) {

                        // MARK: - Progress Ring
                        ZStack {
                            // Background track
                            Circle()
                                .stroke(Color(.systemGray5), lineWidth: 20)
                                .frame(width: 200, height: 200)

                            // Filled arc
                            Circle()
                                .trim(from: 0, to: CGFloat(viewModel.percent / 100))
                                .stroke(ringColor, style: StrokeStyle(lineWidth: 20, lineCap: .round))
                                .frame(width: 200, height: 200)
                                .rotationEffect(.degrees(-90))
                                .animation(.easeOut(duration: 0.6), value: viewModel.percent)

                            // Center label
                            Text("\(Int(viewModel.percent))%")
                                .font(.system(size: 36, weight: .bold, design: .rounded))
                                .foregroundColor(ringColor)
                        }
                        .padding(.top, 16)

                        // MARK: - Spent / Limit Amounts
                        HStack(spacing: 32) {
                            VStack(spacing: 4) {
                                Text("Spent")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Text("₱\(String(format: "%.2f", viewModel.spent))")
                                    .font(.title3).bold()
                            }
                            Divider().frame(height: 40)
                            VStack(spacing: 4) {
                                Text("Limit")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Text("₱\(String(format: "%.2f", viewModel.limit))")
                                    .font(.title3).bold()
                            }
                        }
                        .padding(.horizontal)

                        // MARK: - Set Limit Form
                        VStack(alignment: .leading, spacing: 10) {
                            Text("Monthly Limit")
                                .font(.headline)
                                .padding(.horizontal)

                            HStack {
                                TextField("Monthly limit", text: $limitInput)
                                    .keyboardType(.decimalPad)
                                    .padding(10)
                                    .background(Color(.secondarySystemBackground))
                                    .cornerRadius(8)
                                    .onChange(of: limitInput) { _ in hasEdited = true }

                                Button("Save Limit") {
                                    if let newLimit = Double(limitInput), newLimit > 0 {
                                        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
                                        Task {
                                            await viewModel.setBudget(
                                                limit: newLimit,
                                                apiClient: apiClient,
                                                authManager: authManager
                                            )
                                        }
                                    }
                                }
                                .buttonStyle(.borderedProminent)
                                .disabled(Double(limitInput) == nil || (Double(limitInput) ?? 0) <= 0)
                            }
                            .padding(.horizontal)
                        }

                        Spacer(minLength: 40)
                    }
                    .padding(.top, 8)
                }
                .refreshable {
                    await viewModel.load(apiClient: apiClient, authManager: authManager)
                }

                // MARK: - Loading Overlay
                if viewModel.isLoading {
                    Color(.systemBackground).opacity(0.6)
                    ProgressView()
                        .scaleEffect(1.5)
                }
            }
            .navigationTitle("Budget")
            .task {
                await viewModel.load(apiClient: apiClient, authManager: authManager)
                if !hasEdited {
                    limitInput = String(format: "%.2f", viewModel.limit)
                }
            }
            .alert("Budget Alert", isPresented: $viewModel.showAlert) {
                Button("OK") {}
            } message: {
                Text(viewModel.alertMessage)
            }
            .onDisappear { hasEdited = false }
        }
    }
}
