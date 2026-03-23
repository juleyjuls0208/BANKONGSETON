import Foundation

// MARK: - HomeViewModel
// Loads balance and 3 most recent transactions for the Home screen.

@MainActor
final class HomeViewModel: ObservableObject {
    private static let settingsDisplayNameKey = "settings_display_name"
    private static let studentNameKey = "student_name"

    @Published var balance: Double = 0
    @Published var recentTransactions: [Transaction] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published private(set) var resolvedDisplayName: String = "Student"

    init() {
        if let cached = KeychainHelper.read(forKey: "last_balance"),
           let value = Double(cached) {
            balance = value
        }

        resolvedDisplayName = Self.resolveDisplayName(
            persistedDisplayName: KeychainHelper.read(forKey: Self.settingsDisplayNameKey),
            backendDisplayName: KeychainHelper.read(forKey: Self.studentNameKey)
        )
    }

    func load(apiClient: APIClient, authManager: AuthManager) async {
        refreshResolvedDisplayName(backendDisplayName: authManager.studentName)

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            async let balanceResp = apiClient.getBalance()
            async let txResp = apiClient.getTransactions(limit: 3, offset: 0)
            let (bal, txs) = try await (balanceResp, txResp)

            balance = bal.balance
            KeychainHelper.save(String(format: "%.2f", bal.balance), forKey: "last_balance")
            recentTransactions = txs.transactions
        } catch APIError.unauthorized {
            authManager.handleUnauthorized()
        } catch APIError.cardLost {
            authManager.handleCardLost()
        } catch {
            errorMessage = "Failed to load data. Pull to refresh."
        }
    }

    func refreshAfterQRSuccess(apiClient: APIClient, authManager: AuthManager) async {
        log("Refreshing Home data after QR payment success dismiss")
        await load(apiClient: apiClient, authManager: authManager)
        log("Completed Home refresh after QR payment success dismiss")
    }

    func refreshResolvedDisplayName(backendDisplayName: String) {
        resolvedDisplayName = Self.resolveDisplayName(
            persistedDisplayName: KeychainHelper.read(forKey: Self.settingsDisplayNameKey),
            backendDisplayName: backendDisplayName
        )
    }

    private static func resolveDisplayName(
        persistedDisplayName: String?,
        backendDisplayName: String?
    ) -> String {
        if let persistedDisplayName = normalizedNonEmpty(persistedDisplayName) {
            return persistedDisplayName
        }

        if let backendDisplayName = normalizedNonEmpty(backendDisplayName) {
            return backendDisplayName
        }

        if let cachedStudentName = normalizedNonEmpty(KeychainHelper.read(forKey: studentNameKey)) {
            return cachedStudentName
        }

        return "Student"
    }

    private static func normalizedNonEmpty(_ value: String?) -> String? {
        guard let trimmed = value?.trimmingCharacters(in: .whitespacesAndNewlines), !trimmed.isEmpty else {
            return nil
        }

        return trimmed
    }

    private func log(_ message: String) {
        print("[HomeViewModel] \(message)")
    }
}
