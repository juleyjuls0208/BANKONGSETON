import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = SettingsViewModel()

    var body: some View {
        NavigationStack {
            Form {
                // MARK: - Appearance
                Section("Appearance") {
                    Picker("Theme", selection: $viewModel.selectedTheme) {
                        Text("System").tag("system")
                        Text("Light").tag("light")
                        Text("Dark").tag("dark")
                    }
                    .pickerStyle(.segmented)
                }

                // MARK: - Account
                Section("Account") {
                    NavigationLink("Report Lost Card") {
                        LostCardView()
                    }

                    Button(role: .destructive) {
                        Task {
                            await viewModel.logout {
                                await authManager.logout(apiClient: apiClient)
                            }
                        }
                    } label: {
                        HStack {
                            Text("Logout")
                            if viewModel.isLoggingOut {
                                Spacer()
                                ProgressView()
                            }
                        }
                    }
                    .disabled(viewModel.isLoggingOut)
                }
            }
            .navigationTitle("Settings")
        }
        .preferredColorScheme(viewModel.colorScheme)
    }
}
