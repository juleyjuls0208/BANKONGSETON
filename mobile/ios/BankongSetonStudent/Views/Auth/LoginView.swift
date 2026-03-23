import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var apiClient: APIClient
    @EnvironmentObject private var authManager: AuthManager
    @StateObject private var viewModel = LoginViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Logo / branding
                    VStack(spacing: 8) {
                        Image(systemName: "banknote")
                            .font(.system(size: 60))
                            .foregroundColor(.accentColor)
                        Text("BankongSeton")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        Text("Student Portal")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.top, 40)

                    // Form fields
                    VStack(spacing: 16) {
                        TextField("Student ID", text: $viewModel.studentId)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .textContentType(.username)
                            .padding()
                            .background(Color(.secondarySystemBackground))
                            .cornerRadius(10)
                    }
                    .padding(.horizontal)

                    // Error message
                    if let error = viewModel.errorMessage {
                        Text(error)
                            .foregroundColor(.red)
                            .font(.subheadline)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                    }

                    // Login button
                    Button {
                        Task {
                            await viewModel.login(apiClient: apiClient, authManager: authManager)
                        }
                    } label: {
                        HStack {
                            if viewModel.isLoading {
                                ProgressView()
                                    .tint(.white)
                            }
                            Text(viewModel.isLoading ? "Signing In..." : "Sign In")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(viewModel.canSubmit ? Color.accentColor : Color.gray)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    .disabled(!viewModel.canSubmit)
                    .padding(.horizontal)

                    Spacer(minLength: 20)
                }
            }
            .navigationTitle("")
            .navigationBarHidden(true)
        }
    }
}
