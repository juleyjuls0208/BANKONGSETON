import SwiftUI
import UIKit

struct QRPayView: View {
    @EnvironmentObject var apiClient: APIClient
    @StateObject private var viewModel = QRPayViewModel()
    @Environment(\.dismiss) private var dismiss
    private var onSuccess: (() -> Void)?

    init(onSuccess: (() -> Void)? = nil) {
        self.onSuccess = onSuccess
    }

    var body: some View {
        NavigationStack {
            Group {
                switch viewModel.state {
                case .scanning:
                    scanningView

                case .loading:
                    VStack(spacing: 16) {
                        ProgressView()
                        Text("Loading cart…")
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                case .confirming(let cart, let token):
                    confirmView(cart: cart, token: token)

                case .success(let newBalance):
                    successView(newBalance: newBalance)

                case .error(let message):
                    errorView(message: message)
                }
            }
            .navigationTitle("Pay with QR")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
        }
    }

    // MARK: Scanning

    private var scanningView: some View {
        ZStack(alignment: .bottom) {
            QRScannerView(
                onCodeScanned: { scannedURL in
                    viewModel.handleScannedURL(scannedURL, apiClient: apiClient)
                },
                onError: { errorMessage in
                    viewModel.handleScannerError(errorMessage)
                }
            )
            .ignoresSafeArea()

            Text("Point camera at QR code on terminal")
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(Color.black.opacity(0.6))
                .cornerRadius(8)
                .padding(.bottom, 48)
        }
    }

    // MARK: Confirmation

    private func confirmView(cart: QrCartResponse, token: String) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Confirm Payment")
                        .font(.title2).bold()
                    Text("Cashier: \(cart.cashier)")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding(.top, 8)

                Divider()

                ForEach(cart.items, id: \.name) { item in
                    HStack {
                        Text(item.name)
                            .frame(maxWidth: .infinity, alignment: .leading)
                        Text("×\(item.qty)")
                            .foregroundColor(.secondary)
                            .frame(width: 40)
                        Text("₱\(String(format: "%.2f", item.price * Double(item.qty)))")
                            .frame(width: 80, alignment: .trailing)
                    }
                    .font(.subheadline)
                }

                Divider()

                HStack {
                    Text("Total").font(.headline)
                    Spacer()
                    Text("₱\(String(format: "%.2f", cart.total))")
                        .font(.headline)
                        .foregroundColor(.accentColor)
                }

                VStack(spacing: 12) {
                    Button(action: { viewModel.confirm(token: token, apiClient: apiClient) }) {
                        Text("Confirm QR Payment")
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.accentColor)
                            .foregroundColor(.white)
                            .cornerRadius(12)
                    }
                    Button(action: { dismiss() }) {
                        Text("Cancel")
                            .frame(maxWidth: .infinity)
                            .padding()
                            .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.accentColor))
                    }
                }
                .padding(.top, 8)
            }
            .padding()
        }
    }

    // MARK: Success

    private func successView(newBalance: Double?) -> some View {
        VStack(spacing: 20) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 64))
                .foregroundColor(.green)
            Text("Payment Successful!")
                .font(.title2).bold()
            if let balance = newBalance {
                Text("New balance: ₱\(String(format: "%.2f", balance))")
                    .foregroundColor(.secondary)
            }
            Button("Done") {
                onSuccess?()
                dismiss()
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .onAppear {
            // Auto-dismiss success after 3 seconds
            DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                onSuccess?()
                dismiss()
            }
        }
    }

    // MARK: Error

    private func errorView(message: String) -> some View {
        VStack(spacing: 20) {
            Image(systemName: "exclamationmark.circle.fill")
                .font(.system(size: 64))
                .foregroundColor(.red)
            Text("Payment Error")
                .font(.title2).bold()
            Text(message)
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)

            if isCameraPermissionIssue(message) {
                Button("Open Settings") {
                    openAppSettings()
                }
                .buttonStyle(.bordered)
            }

            Button("Retry Scan") {
                viewModel.reset()
            }
            .buttonStyle(.borderedProminent)

            Button("Close") { dismiss() }
                .buttonStyle(.bordered)
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func isCameraPermissionIssue(_ message: String) -> Bool {
        let normalized = message.lowercased()
        return normalized.contains("camera") || normalized.contains("permission") || normalized.contains("settings")
    }

    private func openAppSettings() {
        guard let settingsURL = URL(string: UIApplication.openSettingsURLString),
              UIApplication.shared.canOpenURL(settingsURL) else {
            return
        }
        UIApplication.shared.open(settingsURL)
    }
}
